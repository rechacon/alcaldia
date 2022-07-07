import psycopg2
import xmlrpc.client
from odoo import api, models, fields


TYPE_ATR = [('partner', 'Contactos'),
            ('payment', 'Planillas de pagos'),
            ('tax', 'Declaraciones de Impuestos'),
            ('update_address', 'Actualizar dirección de contactos'), ]


class ATR(models.Model):
    _name = 'atr'
    _description = 'Registros de ATR'

    name = fields.Char('Nombre', required=True)
    type_atr = fields.Selection(TYPE_ATR, 'Tipo de conexión', required=True)
    lote = fields.Integer(default=1000, help='Registros máximos que se importaran en cada llamada')
    sql = fields.Text('SQL')
    sql_count = fields.Text('Consulta SQL para saber el total de los registros')
    log_ids = fields.One2many('atr.log', 'atr_id', 'Logs')

    def _cron_update_partner(self):
        """Cron para actualizar los contactos"""
        atr = self.env['atr'].search([('type_atr', '=', 'partner')])
        atr.connect_atr()

    def _cron_update_payment(self):
        """Cron para actualizar los pagos"""
        atr = self.env['atr'].search([('type_atr', '=', 'payment')])
        atr.connect_atr()

    def _cron_update_tax(self):
        """Cron para actualizar las declaraciones"""
        atr = self.env['atr'].search([('type_atr', '=', 'tax')])
        atr.connect_atr()

    def _cron_update_address(self):
        """Cron para actualizar la dirección de los contribuyentes"""
        atr = self.env['atr'].search([('type_atr', '=', 'update_address')])
        atr.connect_atr()

    def get_last_log(self, cursor, company_id=False):
        """Obtener último log"""
        # Obtener número total de registros
        cursor.execute(self.sql_count.replace('{company_id}', str(company_id.id)))
        total = cursor.fetchall()[0][0]
        atr_obj = self.env['atr.log']
        if self.log_ids:
            date_now = fields.Datetime.now().strftime('%Y-%m-%d')
            last_id = self.log_ids.filtered(lambda x: x.company_id.id == company_id.id).mapped('id')
            if not last_id:
                new_log = atr_obj.create({
                    'date_start': fields.Datetime.now(),
                    'atr_id': self.id,
                    'flag': 0,
                    'total': total,
                    'company_id': company_id.id,
                })
                return new_log
            last_id = max(last_id)
            log_id = self.log_ids.filtered(lambda x: x.id == last_id)
            # Obtener la fecha del ultimo id
            date = log_id.create_date.strftime('%Y-%m-%d')

            log_id.total = total
            if log_id.total != log_id.flag and date == date_now and company_id.id == log_id.company_id.id:
                return log_id
            if log_id.total == log_id.flag and date == date_now and company_id.id == log_id.company_id.id:
                return False
        new_log = atr_obj.create({
            'date_start': fields.Datetime.now(),
            'atr_id': self.id,
            'flag': 0,
            'total': total,
            'company_id': company_id.id,
        })
        return new_log

    def connect_atr(self):
        """Conectar con ATR"""
        if self.type_atr == 'partner':
            self.create_partner()
        elif self.type_atr == 'payment':
            self.create_payment()
        elif self.type_atr == 'update_address':
            self.create_update_address()
        elif self.type_atr == 'tax':
            self.create_tax()

    def create_payment(self):
        """Crear planilla de pagos"""
        cursor = self.env['atr.connect'].search([('type', '=', 'atr')], limit=1)
        company_id = cursor.company_id
        cursor = cursor.credentials_atr().cursor()
        # Obtener log
        log_id = self.get_last_log(cursor)
        if not log_id:
            return False
        # Consulta SQL
        cursor.execute(self.sql.replace('{offset}', str(log_id.flag)).replace('{limit}', str(self.lote)))
        records = cursor.fetchall()
        # Objetos
        declaration_id = self.env['account.tax.return']
        template_id = self.env['account.template.type']
        tax_id = self.env['account.declaration.tax.type']
        for rec in records:
            vat = rec[0].strip().replace(',', '').replace(' ', '')
            name = rec[2].strip().replace(',', '').replace(' ', '')
            amount = rec[3]
            date = rec[4]
            date_due = rec[5]
            if template_id.search([('name', '=', rec[6])]):
                template_id = template_id.search([('name', '=', rec[6])])
            else:
                template_id = template_id.create({'name': rec[6]})
            account = rec[7].strip().replace(',', '').replace(' ', '')
            if tax_id.search([('name', '=', rec[8])]):
                tax_id = tax_id.search([('name', '=', rec[8])])
            else:
                tax_id = tax_id.create({'name': rec[8]})
            state = 'payment' if rec[9] == 'PAGADA' else 'pending'
            partner_id = self.env['res.partner'].search([('vat', '=', vat)])
            type_tax = 'payment'
            if not partner_id:
                log_id.ignore += 1
                log_id.flag += 1
                log_id.date_end = fields.Datetime.now()
                self.env.cr.commit()
                continue

            values = {
                'partner_id': partner_id.id,
                'name': name,
                'amount': amount,
                'date': date,
                'date_due': date_due,
                'account': account,
                'state': state,
                'template_id': template_id.id,
                'tax_id': tax_id.id,
                'type_tax': type_tax,
                'company_id': company_id.id,
            }
            print(f'\n{values}\n')

            if declaration_id.search(['&', ('name', '=', name), ('state', '=', 'payment')]):
                log_id.ignore += 1
            elif declaration_id.search([('name', '=', name)]):
                declaration_id = declaration_id.search([('name', '=', name)])
                del values['partner_id']
                del values['name']
                del values['account']
                del values['type_tax']
                declaration_id.write(values)
                log_id.upd += 1
            else:
                declaration_id = declaration_id.create(values)
                log_id.qty += 1
            log_id.flag += 1
            log_id.date_end = fields.Datetime.now()
            self.env.cr.commit()
        if log_id.flag == log_id.total:
            # Aquí enviar correo
            log_id.send = True
            self.env.cr.commit()
        else:
            self.create_payment()


class ATRLog(models.Model):
    _name = 'atr.log'
    _description = 'Logs de conexion Odoo-ATR'

    name = fields.Char('Descripción', compute='_compute_get_name')
    qty = fields.Integer('Creados', help='Número total de registros importados')
    ignore = fields.Integer('Ignorados', help='Número total de registros ignorados')
    upd = fields.Integer('Actualizados', help='Número total de registros actualizados')
    flag = fields.Integer('Recorridos')
    total = fields.Integer(help='Número total de registros')
    date_start = fields.Datetime(string='Fecha de inicio', )
    date_end = fields.Datetime(string='Fecha de final', )
    send = fields.Boolean(string='¿Correo enviado?')
    atr_id = fields.Many2one('atr', 'Conexión', ondelete='cascade')
    company_id = fields.Many2one('res.company', 'Alcaldía')

    def _compute_get_name(self):
        """Obtener nombre"""
        for rec in self:
            type_atr = {
                'partner': 'Contactos',
                'payment': 'Pagos',
                'tax': 'Impuestos',
                'update_address': 'Dirección de Contribuyentes',
            }
            type_name = type_atr[rec.atr_id.type_atr]
            rec.name = f'Importación de {type_name} - {rec.date_start.strftime("%m/%d/%Y")}'


class ATRConnect(models.Model):
    _name = 'atr.connect'
    _description = 'Conexion ATR'

    name = fields.Char('Nombre', required=True)
    server = fields.Char('Servidor', required=True)
    name_bd = fields.Char('Base de datos', required=True)
    user = fields.Char('Usuario', required=True)
    password = fields.Char(required=True)
    port = fields.Char('Puerto')
    type = fields.Selection([('odoo', 'Odoo'), ('atr', 'ATR')], 'Tipo', required=True)
    company_id = fields.Many2one('res.company', 'Alcaldía', required=True)
    logo = fields.Binary('Logo', related='company_id.logo')
    active = fields.Boolean('Activo', default=True)

    @api.constrains('active')
    def check_records(self):
        """Chequear que solo exista una credencial activa"""

    def credentials_odoo(self):
        """Obtener sesion xmlrpc"""
        url = self.server
        name_bd = self.name_bd
        username = self.user
        password = self.password
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(name_bd, username, password, {})
        session = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        return session, name_bd, uid, password

    def credentials_atr(self):
        """Credenciales ATR"""
        return psycopg2.connect(dbname=self.name_bd, user=self.user, host=self.server, password=self.password, port=self.port)
