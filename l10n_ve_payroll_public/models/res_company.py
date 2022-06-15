from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    salary_min = fields.Float(string='Salario Mínimo', digits=(12, 2))
    employer_contribution_risk = fields.Integer(string='% Riesgo Aporte Patronal')
    employee_contribution_risk = fields.Integer(string='% Riesgo Aporte Empleado')
    daily_food_bonus = fields.Float(string='Bono de Alimentación', digits=(12, 2))
    incentive_antiquity_ids = fields.One2many('hr.incentives.antiquity', 'company_id', string='Prima de Antigüedad')
    incentive_professionalization_ids = fields.One2many('hr.incentives.professionalization', 'company_id', string='Prima de Profesionalización')
    incentive_child = fields.Float(string='Prima por Hijo', digits=(12, 2))
    bonus_transportation = fields.Float(string='Bono de Transporte', digits=(12, 2))
    cesta_ticket = fields.Float(string='Cesta Ticket', digits=(12, 2))
    bonus_vacational = fields.Integer(string='Vacacional')
    bonus_year_end = fields.Integer(string='Fin de Año')
    bonus_marriage = fields.Float(string='Matrimonio', digits=(12, 2))
    bonus_death = fields.Float(string='Defunción', digits=(12, 2))
    bonus_school_supplies = fields.Float(string='Útiles Escolares', digits=(12, 2))
    bonus_toys = fields.Float(string='Juguetes', digits=(12, 2))
    bonus_secretary = fields.Float(string='Secretary', digits=(12, 2))
    days_utilities_annual = fields.Integer(string='Utilidades Anuales')
    days_vacation_annual = fields.Integer(string='Vacacionales Anuales')
    days_bonus_vacations = fields.Integer(string='Bonos Vacacionales')
