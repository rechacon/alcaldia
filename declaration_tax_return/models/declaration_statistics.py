from odoo import fields, models


class AccountDeclarationStatistics(models.Model):
    _name = 'account.declaration.statistics'
    _description = 'Estadisticas de declaraciones por cliente'

    partner_id = fields.Many2one('res.partner', 'Contribuyente')
    total_tax = fields.Integer('Total de Declaraciones')
    total_payment = fields.Integer('Total de Plantillas de Pago')
    template_statistics_ids = fields.One2many('account.template.type.statistics', 'statistics_id', 'Estadística por Plantilla')
    type_statistics_ids = fields.One2many('account.declaration.tax.type.statistics', 'statistics_id', 'Estadística por Impuesto')


class AccountTemplateTypeStatistics(models.Model):
    _name = 'account.template.type.statistics'
    _description = 'Estadisticas de tipo de planilla'

    name = fields.Many2one('account.template.type', 'Tipo')
    total = fields.Float('Total')
    statistics_id = fields.Many2one('account.declaration.statistics', 'Estadística')


class AccountTaxTypeStatistics(models.Model):
    _name = 'account.declaration.tax.type.statistics'
    _description = 'Estadisticas de tipo de impuesto'

    name = fields.Many2one('account.template.type', 'Tipo')
    total = fields.Float('Total')
    statistics_id = fields.Many2one('account.declaration.statistics', 'Estadística')
