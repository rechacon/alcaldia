import base64
import pandas as pd
import time

from multiprocesspandas import applyparallel
from odoo_csv_tools import import_threaded
from odoo import models, fields

TEMPLATE_IDS = {}
TAX_IDS = {}
PARTNER_IDS = {}


def get_template(x):
    template_id = TEMPLATE_IDS.get(x, False)
    if template_id:
        return template_id
    return False


def get_tax(x):
    tax_id = TAX_IDS.get(x, False)
    if tax_id:
        return tax_id
    return False


def get_partner(x):
    x = x.strip().replace(',', '').replace(' ', '')
    partner_id = PARTNER_IDS.get(x, False)
    if partner_id:
        return partner_id
    return False


def multiprocess_data(x):
    x['template_id.id'] = x['template_id.id'].transform(get_template)
    x['tax_id.id'] = x['tax_id.id'].transform(get_tax)
    x['partner_id.id'] = x['partner_id.id'].transform(get_partner)
    return x


class ATR(models.Model):
    _inherit = 'atr'

    csv = fields.Binary('CSV')
    file_name = fields.Char('Nombre del archivo')

    def get_template_dict(self):
        global TEMPLATE_IDS
        template_ids = self.env['account.template.type'].sudo().search([])
        for template in template_ids:
            TEMPLATE_IDS.update({template.name: template.id})

    def get_tax_dict(self):
        global TAX_IDS
        tax_ids = self.env['account.declaration.tax.type'].sudo().search([])
        for tax in tax_ids:
            TAX_IDS.update({tax.name: tax.id})

    def get_partner_dict(self):
        global PARTNER_IDS
        cursor = self._cr
        cursor.execute("""SELECT vat, id FROM res_partner WHERE active = True AND vat != '' ORDER BY vat ASC""")
        data = cursor.fetchall()
        for rec in data:
            PARTNER_IDS.update({rec[0]: rec[1]})

    def import_csv_to_odoo(self):
        """Este método es temportal"""
        # Variables globales
        config = """[Connection]
hostname = localhost
database = alcaldia
login = admin
password = 123
protocol = xmlrpc
port = 8015
uid = 2"""
        model = 'account.tax.return'
        file_csv = base64.b64decode(self.csv)
        context = "{'tracking_disable' : True}"
        fail_file = 'fail.csv'
        encoding = 'utf-8'
        separator = ';'
        ignore = False
        import_threaded.import_data(config, model, file_csv=file_csv, context=context,
                                    fail_file=fail_file, encoding=encoding, separator=separator,
                                    ignore=ignore, max_connection=4, batch_size=10)

    def create_tax(self):
        """Crear Declaraciones de impuestos"""
        start = time.time()
        cursor = self.env['atr.connect'].search([('type', '=', 'atr')], limit=1)
        cursor = cursor.credentials_atr()
        # Obtener log
        log_id = self.get_last_log(cursor.cursor())
        if not log_id:
            return False
        # Consulta SQL
        sql_query = pd.read_sql_query(self.sql.replace('{offset}', str(log_id.flag)).replace('{limit}', str(self.lote)), cursor)

        header = ['id_tax', 'partner_id.id', 'account',
                  'amount', 'concept', 'date', 'date_due',
                  'template_id.id', 'tax_id.id', 'state']

        df_tax = pd.DataFrame(sql_query)  # Convertir la consulta en un dataframe
        del(df_tax['contribuyente'])  # Eliminar la columna de contribuyente
        df_tax.columns = header  # Asignando el nuevo header

        # Creando nuevas columnas
        df_tax['name'] = df_tax['account'].values
        df_tax['type_tax'] = 'tax'
        df_tax['id'] = df_tax['id_tax'].map('tax_{}'.format).values

        # Cambiar valores de las columnas según una condición
        df_tax.loc[df_tax.state == 'PAGADA', 'state'] = 'payment'
        df_tax.loc[df_tax.state == 'PENDIENTE', 'state'] = 'pending'

        # Llenar data maestra de las variables globales
        self.get_template_dict()
        self.get_tax_dict()
        self.get_partner_dict()

        df_tax = df_tax.groupby(["partner_id.id"]).apply_parallel(multiprocess_data, num_processes=4)

        # Borrar filas que no tienen partner
        df_tax.drop(df_tax.loc[df_tax['partner_id.id'] == False].index, inplace=True)

        # Crear CSV
        csv = df_tax.to_csv(sep=';', index=False)
        b64 = base64.b64encode(csv.encode())
        self.csv = b64
        self.file_name = 'data.csv'
        end = time.time()
        # self.import_csv_to_odoo()
        print(f'\n\nTIME: {end - start}\n\n')
        # data = base64.b64decode(self.csv)
