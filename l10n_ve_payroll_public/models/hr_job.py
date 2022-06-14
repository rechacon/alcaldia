from odoo import models, fields


class Job(models.Model):
    _inherit = "hr.job"

    wage = fields.Float(string='Salario', digits=(12, 2))
    wage_compensate = fields.Float(string='Salario Compensatorio', digits=(12, 2))
