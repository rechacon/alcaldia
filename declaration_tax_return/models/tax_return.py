from odoo import api, fields, models
from datetime import datetime


class AccountTaxReturn(models.Model):
    _name = 'account.tax.return'
    _description = 'Declaracion de impuesto'

    def _set_currency_usd_id(self):
        usd = self.env.ref('base.USD')
        return usd

    def _set_currency_id(self):
        ves = self.env.ref('base.VES')
        return ves

    partner_id = fields.Many2one('res.partner', 'Contribuyente')
    currency_id = fields.Many2one('res.currency', 'VES', default=_set_currency_id)
    currency_usd_id = fields.Many2one('res.currency', 'USD', default=_set_currency_usd_id)
    name = fields.Char('Planilla')
    amount = fields.Float('Monto')
    amount_usd = fields.Float('Monto USD', compute='_compute_get_rate')
    date = fields.Date('Emisión')
    date_due = fields.Date('Vencimiento')
    account = fields.Char('Cuenta')
    template_id = fields.Many2one('account.template.type', 'Tipo de planilla')
    tax_id = fields.Many2one('account.declaration.tax.type', 'Tipo de impuesto')
    state = fields.Selection([('pending', 'Pendiente'), ('payment', 'Pagada')], 'Estatus')

    def _compute_get_rate(self):
        """Obtener tasa de cambio"""
        for rec in self:
            rate_usd = self.env['res.currency.rate'].search([('name', '=', datetime.now()),
                                                             ('currency_id', '=', self.currency_usd_id.id)])
            if rate_usd:
                rec.amount_usd = rec.amount / rate_usd.sell_rate
            else:
                rec.amount_usd = 0.0


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
