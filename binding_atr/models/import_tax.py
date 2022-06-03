import time
import threading
import pandas as pd
import odoo

from odoo import models, fields, api

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

    def _run_process_load(self, *list_df):
        """Aplicar el multiproceso"""
        header = ['id_tax', 'partner_id.id', 'account', 'amount', 'concept', 'date', 'date_due', 'template_id.id', 'tax_id.id', 'state', 'name', 'type_tax', 'company_id.id', 'id']
        with api.Environment.manage():
            with odoo.registry(self.env.cr.dbname).cursor() as new_cr:
                new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                new_env['account.tax.return'].load(header, list_df)

    def create_tax(self):
        """Crear Declaraciones de impuestos"""
        start = time.time()
        cursor = self.env['atr.connect'].search([('type', '=', 'atr')], limit=1)
        company_id = cursor.company_id
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
        df_tax['company_id.id'] = company_id.id
        df_tax['id'] = df_tax['id_tax'].map('tax_{}'.format).values

        # Cambiar valores de las columnas según una condición
        df_tax.loc[df_tax.state == 'PAGADA', 'state'] = 'payment'
        df_tax.loc[df_tax.state == 'PENDIENTE', 'state'] = 'pending'

        # Llenar data maestra de las variables globales
        self.get_template_dict()
        self.get_tax_dict()
        self.get_partner_dict()

        total = len(df_tax)

        df_tax = df_tax.groupby(["partner_id.id"]).apply(multiprocess_data)

        # Borrar filas que no tienen partner
        df_tax.drop(df_tax.loc[df_tax['partner_id.id'] == False].index, inplace=True)

        # Multiproceso
        list_df = df_tax.to_numpy().tolist()  # Convertir dataframe en lista
        length = len(list_df)  # Longitud de las listas
        list_1, list_2, list_3, list_4, list_5, list_6 = [list_df[i * length // 6: (i + 1) * length // 6] for i in range(6)]
        # Separando los procesos
        process_1 = threading.Thread(target=self._run_process_load, args=(list_1))
        process_2 = threading.Thread(target=self._run_process_load, args=(list_2))
        process_3 = threading.Thread(target=self._run_process_load, args=(list_3))
        process_4 = threading.Thread(target=self._run_process_load, args=(list_4))
        process_5 = threading.Thread(target=self._run_process_load, args=(list_5))
        process_6 = threading.Thread(target=self._run_process_load, args=(list_6))

        # Iniciando los procesos
        process_1.start()
        process_2.start()
        process_3.start()
        process_4.start()
        process_5.start()
        process_6.start()

        import_total = len(df_tax)
        ignore = total - import_total
        # Establecer el log
        log_id.date_end = fields.Datetime.now()
        log_id.ignore += ignore
        log_id.flag += total

        end = time.time()

        print(f'\n\nTIME: {end - start}\n\n')
