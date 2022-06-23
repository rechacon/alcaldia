from odoo import models, fields


class Department(models.Model):
    _inherit = "hr.department"

    sector_laboral_id = fields.Many2one('hr.employee.sector.laboral', string='Tabla Salarial')
