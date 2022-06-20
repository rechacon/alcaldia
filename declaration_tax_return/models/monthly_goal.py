from odoo import fields, models, api

class MonthlyGoal(models.Model):
    _name = 'account.tax.return.monthly.goal'
    _description = 'Estadisticas de declaraciones por meta mensual de las alcaldias'

    company_ids = fields.Many2many('res.company', string="Alcaldías", required=True)
    name = fields.Char(string="Nombre")
    year_records = fields.Selection([('2012', '2012'), ("2027", "2027")], string="Seleccion de años")
    line_ids = fields.One2many('account.tax.return.monthly.line', 'prueba_id', string="Líneas")

class AccountTaxReturnMonthlyGoal(models.Model):
    _name = 'account.tax.return.monthly.line'
    _description = 'Lineas de Meta Mensual'

    company_id = fields.Many2one('res.company', string="Alcaldías", required=True)
    raised = fields.Integer(string='Recaudado')
    pending = fields.Integer(string='Pendiente')
    goal = fields.Integer(string='Meta')
    accomplished = fields.Integer(string='% Logrado')
    prueba_id = fields.Many2one('account.tax.return.monthly.goal', string="Alcaldías")

