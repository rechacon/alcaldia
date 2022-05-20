from odoo import fields, models
from matplotlib import pyplot as plt

import base64
import io
import numpy as np


class WizardReports(models.TransientModel):
    _name = 'wizard.reports'
    _description = 'Wizard de Reportes Estadisticos'

    date_start = fields.Date('Fecha Inicio', required=True)
    date_end = fields.Date('Fecha Fin', required=True)
    tax_ids = fields.Many2many('account.tax.return', string="Declaraciones")
    # payment_ids = fields.Many2many('account.tax.return', string="Planillas de pagos")

    def get_graphic(self):
        ypoints = np.array([3, 8, 1, 10])
        plt.plot(ypoints, linestyle='solid')

        ypoints = np.array([6, 2, 3, 12])
        plt.plot(ypoints, linestyle='solid', color="red")

        plt.grid(True, axis='y')
        figure = plt.gca()
        x_axis = figure.axes.get_xaxis()
        x_axis.set_visible(False)

        plt.legend(loc="upper left",
                   mode='expand',
                   ncol=1,
                   )

        plt.grid(True, axis='y')

        img = io.BytesIO()
        plt.savefig(img, dpi=100, format='png')
        plt.close()

        return base64.b64encode(img.getvalue())

    def create_report_municipal_comparison_graphic(self):
        """Crear reporte del comparativo municipal"""
        tax_ids = self.env['account.tax.return'].search(
            [('date', '>=', self.date_start), ('date', '<=', self.date_end),
             ('type_tax', '=', 'tax')])
        if tax_ids:
            self.tax_ids = [(6, 0, tax_ids.ids)]
            action = self.env.ref(
                'declaration_tax_return.report_municipal_comparison_action').sudo().report_action(self)
            return action
