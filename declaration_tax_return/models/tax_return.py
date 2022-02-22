from odoo import api, fields, models


class AccountTaxReturn(models.Model):
    _name = 'account.tax.return'
    _description = 'Declaracion de impuesto'

    partner_id = fields.Many2one('res.partner', 'Contribuyente')
    name = fields.Char('Planilla')
    amount = fields.Float('Monto')
    date = fields.Date('Emisión')
    date_due = fields.Date('Vencimiento')
    account = fields.Char('Cuenta')
    template_id = fields.Many2one('account.template.type', 'Tipo de planilla')
    tax_id = fields.Many2one('account.declaration.tax.type', 'Tipo de impuesto')
    state = fields.Selection([('pending', 'Pendiente'), ('payment', 'Pagada')], 'Estatus')


class AccountTemplateType(models.Model):
    _name = 'account.template.type'
    _description = 'Tipo de planilla'

    sequence = fields.Integer()
    name = fields.Char('Tipo')


class AccountTaxType(models.Model):
    _name = 'account.declaration.tax.type'
    _description = 'Tipo de impuesto'

    sequence = fields.Integer()
    name = fields.Char('Tipo')
