from odoo import fields, models


class AccountDeclarationStatistics(models.Model):
    _name = 'account.declaration.statistics'
    _description = 'Estadisticas de declaraciones por cliente'


class AccountTemplateTypeStatistics(models.Model):
    _name = 'account.template.type.statistics'
    _description = 'Estadisticas de tipo de planilla'
    
    name_id = fields.Many2one('account.template.type', 'Tipo')
    total = fields.float('Total')
    statistics_id = fields.Many2one('account.declaration.statistics', 'Estadística')


class AccountTaxTypeStatistics(models.Model):
    _name = 'account.declaration.tax.type.statistics'
    _description = 'Estadisticas de tipo de impuesto'
    
    name_id = fields.Many2one('account.template.type', 'Tipo')
    total = fields.float('Total')
    statistics_id = fields.Many2one('account.declaration.statistics', 'Estadística')
