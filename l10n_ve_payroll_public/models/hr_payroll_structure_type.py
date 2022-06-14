from odoo import models, fields


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

    days_utilities_annual = fields.Integer(string='Días de Utilidades Anuales')
    days_vacation_annual = fields.Integer(string='Días de Vacacionales Anuales')
    days_bonus_vacations = fields.Integer(string='Dias de Bonos Vacacionales')
