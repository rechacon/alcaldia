from odoo import models, fields


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    sector_laboral_id = fields.Many2one('hr.employee.sector.laboral', string='Tabla Salarial', related="employee_id.department_id.sector_laboral_id", store=True)
