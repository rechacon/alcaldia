import calendar

from datetime import timedelta
from odoo import fields, models, api


class HrPaylisp(models.Model):
    _inherit = 'hr.payslip'

    monday_of_month = fields.Integer('Lunes del mes', compute='_compute_get_monday', store=True)
    segunda_quincena = fields.Boolean(string='2da Quincena', compute='calcular_segunda_quincena', store=True)

    @api.depends('date_from', 'date_to')
    def _compute_get_monday(self):
        """Contar los lunes que tiene el periodo de nómina seleccionado"""
        for record in self:
            if record.date_from and record.date_to:
                monday = 0
                start_date = record.date_from
                end_date = record.date_to
                delta = timedelta(days=1)
                while start_date <= end_date:
                    if calendar.day_name[start_date.weekday()].lower() in ['monday', 'lunes']:
                        monday += 1
                    start_date += delta
                record.monday_of_month = monday

    @api.depends('date_from')
    def calcular_segunda_quincena(self):
        for fecha in self:
            if fecha.date_from:
                if fecha.date_from.day >= 15:
                    fecha.segunda_quincena = True
                else:
                    fecha.segunda_quincena = False
