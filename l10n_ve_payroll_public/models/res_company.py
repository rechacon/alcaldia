from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    salary_min = fields.Float(string='Salario Mínimo', digits=(12, 2))
    employer_contribution_risk = fields.Integer(string='% Riesgo Aporte Patronal')
    employee_contribution_risk = fields.Integer(string='% Riesgo Aporte Empleado')
    daily_food_bonus = fields.Float(string='Bono de Alimentación Diario', digits=(12, 2), default=1.50)
