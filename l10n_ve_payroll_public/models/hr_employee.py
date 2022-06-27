from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    childs_ids = fields.One2many('hr.employee.child', 'employee_id', string='Hijos(a)')
    children = fields.Integer(compute='get_number_children', store=True)
    academic_degree_id = fields.Many2one('hr.employee.academic.degree', string='Grado Académico')
    sector_laboral_id = fields.Many2one('hr.employee.sector.laboral', string='Sector Laboral')
    scale_administrative_id = fields.Many2one('hr.pay.scale.administrative', string='Escala Administrativa')
    description = fields.Char(string='Descripción', related='sector_laboral_id.description')

    @api.model
    def get_active(self):
        return self.env['hr.employee.category'].search([('name', '=', 'Activo')])

    category_ids = fields.Many2many('hr.employee.category', 'employee_category_rel', 'emp_id', 'category_id', groups="hr.group_hr_manager", string='Tags', default=get_active)
    years_worked = fields.Integer(string='Años Laborados')
    month_worked = fields.Integer(string='Meses Laborados')
    month_accumulated_worked = fields.Integer(string='Meses Acumulados Laborados')
    wage = fields.Float(related='job_id.wage', store=True)
    wage_compensate = fields.Float(string='Salario Compensatorio', digits=(12, 2), related='job_id.wage_compensate', store=True)
    years_worked_previous = fields.Integer(string='Años Servicios Anteriores', default=0)

    @api.model
    def _cron_update_years_month_worked(self):
        employees = self.env['hr.employee'].search([])
        for emp in employees:
            contract = self.env['hr.contract'].search([('employee_id', '=', emp.id)])
            if contract:
                emp.years_worked = relativedelta(datetime.now(), contract[0].date_start).years + emp.years_worked_previous
                emp.month_worked = relativedelta(datetime.now(), contract[0].date_start).months
                emp.month_accumulated_worked = ((relativedelta(datetime.now(), contract[0].date_start).years + emp.years_worked_previous) * 12) + relativedelta(datetime.now(), contract[0].date_start).months

    @api.depends('childs_ids.age')
    def get_number_children(self):
        if len(self.childs_ids) >= 1:
            childs = 0
            for child in self.childs_ids:
                if child.age <= 17:
                    childs += 1
            self.children = childs
        else:
            self.children = 0

    def get_annio_mes(self):
        contract = self.env['hr.contract'].search([('employee_id', '=', self.id)])
        if contract:
            self.years_worked = relativedelta(datetime.now(), contract[0].date_start).years + self.years_worked_previous
            self.month_worked = relativedelta(datetime.now(), contract[0].date_start).months
            self.month_accumulated_worked = ((relativedelta(datetime.now(), contract[0].date_start).years + self.years_worked_previous) * 12) + relativedelta(datetime.now(), contract[0].date_start).months


class HrEmployeeChild(models.Model):
    _name = 'hr.employee.child'
    _description = 'Hijos(a) de los Empleados'

    name = fields.Char(string='Nombre y Apellido', required=True)
    birth_date = fields.Date(string='Fecha de Nacimiento', required=True)
    age = fields.Integer(string='Edad', compute='get_age', store=True)
    academic_degree_id = fields.Many2one('hr.employee.academic.degree', string='Grado Académico')
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    certificate = fields.Binary(string='Partida Nacimiento')
    constancy = fields.Binary(string='Constancia')

    @api.depends('birth_date')
    def get_age(self):
        for child in self:
            if child.birth_date:
                child.age = relativedelta(datetime.now(), child.birth_date).years

    @api.model
    def _cron_update_annio_children(self):
        children = self.env['hr.employee.child'].search([])
        employees = self.env['hr.employee'].search([])
        for child in children:
            child.age = relativedelta(datetime.now(), child.birth_date).years
        for employee in employees:
            if len(employee.childs_ids) > 1:
                childs = 0
                for child in employee.childs_ids:
                    if child.age < 17:
                        childs += 1
                employee.children = childs
            else:
                employee.children = 0


class HrEmployeeAcademicDegree(models.Model):
    _name = 'hr.employee.academic.degree'
    _description = 'Grado Académico de los Empleados'
    _rec_name = 'description'

    description = fields.Char(string='Descripción', required=True)


class HrEmployeeSectorLaboral(models.Model):
    _name = 'hr.employee.sector.laboral'
    _description = 'Tabla Salarial de los Empleados'
    _rec_name = 'description'

    description = fields.Char(string='Descripción', required=True)
