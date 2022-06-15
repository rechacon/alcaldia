from odoo import models, fields


class HrIncentivesAntiquity(models.Model):
    _name = 'hr.incentives.antiquity'
    _description = 'Primas de Antigüedad'

    year_service = fields.Integer(string='Años de Servicio', required=True)
    percentage_salary_basic = fields.Float(string='% Salario Basico', digits=(12, 2), required=True)
    percentage_compensation = fields.Integer(string='% Sobre Compensación', required=True)
    company_id = fields.Many2one('res.company', string='Compañía')


class HrIncentivesProfessionalization(models.Model):
    _name = 'hr.incentives.professionalization'
    _description = 'Primas de Profesionalización'

    academic_degree_id = fields.Many2one('hr.employee.academic.degree', string='Grado Académico')
    percentage_salary_basic = fields.Float(string='% Salario Basico', digits=(12, 2), required=True)
    percentage_compensation = fields.Integer(string='% Sobre Compensación', required=True)
    company_id = fields.Many2one('res.company', string='Compañía')
