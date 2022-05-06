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
    company_id = fields.Many2one('res.company', 'Alcaldía')
    currency_id = fields.Many2one('res.currency', 'VES', default=_set_currency_id)
    currency_usd_id = fields.Many2one('res.currency', 'USD', default=_set_currency_usd_id)
    type_tax = fields.Selection([('payment', 'Pagos'), ('tax', 'Impuesto')], 'Tipo de registro')
    id_tax = fields.Integer('ID del impuesto')
    concept = fields.Char('Concepto')
    name = fields.Char('Planilla')
    amount = fields.Float('Monto Bs.')
    amount_usd = fields.Float('Monto USD')
    sell_rate = fields.Float('Tasa del día', compute='_compute_get_rate')
    date = fields.Date('Emisión')
    date_due = fields.Date('Vencimiento')
    account = fields.Char('Cuenta')
    template_id = fields.Many2one('account.template.type', 'Tipo de planilla')
    tax_id = fields.Many2one('account.declaration.tax.type', 'Tipo de impuesto')
    state = fields.Selection([('pending', 'Pendiente'), ('payment', 'Pagada')], 'Estatus')

    def name_get(self):
        result = []
        for record in self:
            if record.type_tax == 'tax':
                result.append((record.id, record.account))
                return result
        result.append((record.id, record.name))
        return result

    def _compute_get_rate(self):
        """Obtener tasa de cambio"""
        for rec in self:
            rate_usd = self.env['res.currency.rate'].search([('name', '=', rec.date),
                                                             ('currency_id', '=', self.currency_usd_id.id)])
            if rate_usd:
                rec.amount_usd = rec.amount / rate_usd.sell_rate
                rec.sell_rate = rate_usd.sell_rate
            else:
                rec.amount_usd = 0.0
                rec.sell_rate = 0.0


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
