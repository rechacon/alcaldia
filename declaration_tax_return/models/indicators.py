from odoo import fields, models, api

class AccountMacroeconomicIndicators(models.Model):
    _name = 'account.macroeconomic.indicators'
    _description = 'Indicadores MacroEconomicos'
    
    name = fields.Many2one('account.indicators', 'Indicador', required=True)
    date = fields.Date('Fecha')
    total = fields.Float('Total')
        
class AccountIndicators(models.Model):
    _name = 'account.indicators'
    _description = 'Indicadores'
    
    name = fields.Char('Indicador', required=True)
    logo = fields.Binary('Logo')