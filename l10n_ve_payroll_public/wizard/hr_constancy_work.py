# -*- coding: utf-8 -*-

from odoo import fields, models, api

ls_type_constancy = [('activo', 'Personal Activo Mensual'),
                     ('jubilado', 'Personal Jubilado Mensual')]


class HrConstacyWork(models.TransientModel):
    _name = 'hr_constancy_work'
    _description = 'Wizard de Constancia de Trabajo'

    type_constancy = fields.Selection(ls_type_constancy, string='Tipo de Constancia')
    employee_id = fields.Many2one('hr.employee', string='Empleado')

    def action_print_report(self):
        if self.type_constancy == 'activo':
            return self.env.ref('l10n_ve_payroll_public.hr_employee_constancy').report_action(self)

    @api.onchange('type_constancy')
    def set_employees(self):
        if self.type_constancy == 'activo':
            self.employee_id = ''
            domain = [('category_ids.name', 'in', ['Activo'])]
            return {'domain': {'employee_id': domain}}
        elif self.type_constancy == 'jubilado':
            self.employee_id = ''
            domain = [('category_ids.name', 'in', ['Jubilado'])]
            return {'domain': {'employee_id': domain}}
