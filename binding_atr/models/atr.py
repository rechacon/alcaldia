import psycopg2
from odoo import api, models, fields


TYPE_ATR = [('partner', 'Contactos'), ('payment', 'Declaraciones de Impuestos')]


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

    def get_last_log(self, cursor):
        """Obtener último log"""
        # Obtener número total de registros
        cursor.execute(self.sql_count)
        total = cursor.fetchall()[0][0]
        atr_obj = self.env['atr.log']
        if self.log_ids:
            date = max(self.log_ids.mapped('create_date')).strftime('%Y-%m-%d')
            date_now = fields.Datetime.now().strftime('%Y-%m-%d')
            log_id = self.log_ids.filtered(lambda x: x.create_date.strftime('%Y-%m-%d') == date)
            if log_id.total != log_id.flag and date == date_now:
                return log_id
            if log_id.total == log_id.flag and date == date_now:
                return False
        new_log = atr_obj.create({
            'date_start': fields.Datetime.now(),
            'atr_id': self.id,
            'flag': 0,
            'total': total,
        })
        return new_log

    def connect_atr(self):
        """Conectar con ATR"""
        if self.type_atr == 'partner':
            self.create_partner()
        elif self.type_atr == 'payment':
            self.create_payment()

    def create_partner(self):
        """Crear Partner"""
        cursor = self.env['atr.connect'].search([], limit=1)
        cursor = cursor.credentials_atr().cursor()
        # Obtener log
        log_id = self.get_last_log(cursor)
        if not log_id:
            return False
        # Consulta SQL
        cursor.execute(self.sql.replace('{offset}', str(log_id.flag)).replace('{limit}', str(self.lote)))
        records = cursor.fetchall()
        # Objeto
        partner_id = self.env['res.partner']
        for rec in records:
            vat = rec[0].strip().replace(',', '').replace(' ', '')
            name = rec[1].strip().replace(',', '') if rec[1] else 'S/N'
            type_person = rec[2].strip().replace(',', '').replace(' ', '')
            active = True if rec[3].strip().replace(',', '').replace(' ', '') == 'ACTIVO' else False
            email = rec[4].strip().replace(',', '').replace(' ', '') if rec[4] else ''
            email_second = rec[5].strip().replace(',', '').replace(' ', '') if rec[5] else ''
            mobile = rec[6].strip().replace(',', '').replace(' ', '') if rec[6] else ''
            phone = rec[7].strip().replace(',', '').replace(' ', '') if rec[7] else ''
            values = {
                'vat': vat,
                'name': name,
                'type_person': type_person,
                'is_company': True if type_person == 'JURIDICO' else False,
                'active': active,
                'email': email,
                'email_second': email_second,
                'mobile': mobile,
                'phone': phone,
            }
            print(f'\n{values}\n')
            if partner_id.search(['&', ('active', '=', 'False'), ('vat', '=', vat)]) and not active:
                log_id.ignore += 1
            elif partner_id.search([('vat', '=', vat)]):
                partner_id = partner_id.search([('vat', '=', vat)])
                del values['vat']
                del values['name']
                partner_id.write(values)
                log_id.upd += 1
            else:
                partner_id = partner_id.create(values)
                log_id.qty += 1
            log_id.flag += 1
            log_id.date_end = fields.Datetime.now()
            self.env.cr.commit()
        if log_id.flag == log_id.total:
            # Aquí enviar correo
            log_id.send = True
            self.env.cr.commit()
        else:
            self.create_partner()

    def create_payment(self):
        """Crear Partner"""
        cursor = self.env['atr.connect'].search([], limit=1)
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
            }
            print(f'\n{values}\n')

            if declaration_id.search(['&', ('name', '=', name), ('state', '=', 'payment')]):
                log_id.ignore += 1
            elif declaration_id.search([('name', '=', name)]):
                declaration_id = declaration_id.search([('name', '=', name)])
                del values['partner_id']
                del values['name']
                del values['account']
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

    def _compute_get_name(self):
        """Obtener nombre"""
        for rec in self:
            type_atr = {
                'partner': 'Contactos',
                'payment': 'Pagos',
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
    active = fields.Boolean('Activo', default=True)

    @api.constrains('active')
    def check_records(self):
        """Chequear que solo exista una credencial activa"""

    def credentials_atr(self):
        """Credenciales ATR"""
        return psycopg2.connect(dbname=self.name_bd, user=self.user, host=self.server, password=self.password, port=self.port)
