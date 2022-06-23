from odoo import models, fields


class Contract(models.Model):
    _inherit = 'hr.contract'

    wage = fields.Float(related='job_id.wage', store=True)
    wage_compensate = fields.Float(string='Salario Compensatorio', digits=(12, 2), related='job_id.wage_compensate', store=True)
