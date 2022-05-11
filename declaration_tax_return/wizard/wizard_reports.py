from odoo import fields, models


class WizardReports(models.TransientModel):
    _name = 'wizard.reports'
    _description = 'Wizard de Reportes Estadisticos'

    date_start = fields.Date('Fecha Inicio', required=True)
    date_end = fields.Date('Fecha Fin', required=True)
    tax_ids = fields.Many2many('account.tax.return', string="Declaraciones")
    # payment_ids = fields.Many2many('account.tax.return', string="Planillas de pagos")

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
