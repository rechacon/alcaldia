from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class Contract(models.Model):
    _inherit = 'hr.contract'

    years_worked = fields.Integer(string='Años Laborados', compute='_compute_get_years_worked', store=True)
    month_worked = fields.Integer(string='Meses Laborados', compute='_compute_get_month_worked', store=True)
    month_accumulated_worked = fields.Integer(string='Meses Acumulados Laborados', compute='_compute_get_month_accumulated_worked', store=True)
    wage = fields.Float(related='job_id.wage', store=True)
    wage_compensate = fields.Float(string='Salario Compensatorio', digits=(12, 2), related='job_id.wage_compensate', store=True)

    @api.depends('date_start')
    def _compute_get_years_worked(self):
        if self.date_start:
            self.years_worked = relativedelta(datetime.now(), self.date_start).years

    @api.depends('date_start')
    def _compute_get_month_worked(self):
        if self.date_start:
            self.month_worked = relativedelta(datetime.now(), self.date_start).months

    @api.depends('date_start')
    def _compute_get_month_accumulated_worked(self):
        if self.date_start:
            self.month_accumulated_worked = (relativedelta(datetime.now(), self.date_start).years * 12) + relativedelta(datetime.now(), self.date_start).months

    @api.model
    def _cron_update_years_month_worked(self):
        contracts = self.env['hr.contract'].search([])
        for contract in contracts:
            if contract.date_start:
                contract.years_worked = relativedelta(datetime.now(), contract.date_start).years
                contract.month_worked = relativedelta(datetime.now(), contract.date_start).months
                contract.month_accumulated_worked = (relativedelta(datetime.now(), contract.date_start).years * 12) + relativedelta(datetime.now(), contract.date_start).months
