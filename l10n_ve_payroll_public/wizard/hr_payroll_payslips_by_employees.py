from odoo import models, fields, api


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    sector_laboral_id = fields.Many2one('hr.employee.sector.laboral', string='Sector Laboral')
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees', compute='set_employees')
    description = fields.Char(string='Descripción', related='sector_laboral_id.description')
    # department_id = fields.Many2one('hr.department')

    @api.depends('sector_laboral_id', 'department_id')
    def set_employees(self):
        if self.sector_laboral_id and self.department_id:
            employees = self.env['hr.employee'].search([('sector_laboral_id', '=', self.sector_laboral_id.id), ('department_id', '=', self.department_id.id)])
            self.employee_ids = employees
        else:
            employees = self.env['hr.employee'].search([('sector_laboral_id', '=', self.sector_laboral_id.id)])
            self.employee_ids = employees
