from datetime import datetime
from odoo import fields, models, api

MONTHS = [('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'), ('04', 'Abril'),
          ('05', 'Mayo'), ('06', 'Junio'), ('07', 'Julio'), ('08', 'Agosto'),
          ('09', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'),
          ('12', 'Diciembre')]


class MonthlyGoal(models.Model):
    _name = 'account.tax.return.monthly.goal'
    _description = 'Estadisticas de declaraciones por meta mensual de las alcaldias'

    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)
        # Tener por defecto todas las alcaldias seleccionadas
        company_ids = self.env['res.company'].search([])
        result['company_ids'] = [(4, company.id) for company in company_ids]
        return result

    company_ids = fields.Many2many('res.company', string="Alcaldías", required=True)
    name = fields.Char(string="Nombre")
    year = fields.Selection([(str(i), str(i)) for i in range(2020, int(datetime.now().year) + 10)], string="Año", required=True)
    line_ids = fields.One2many('account.tax.return.monthly.line', 'goal_id', string="Líneas")

    _sql_constraints = [('year_uniq', 'unique (year)', ('Este año ya está creado'))]

    @api.model
    def create(self, vals):
        vals['name'] = f'Meta del Año {vals.get("year", "")}'
        res = super().create(vals)
        values = []
        for company in res.company_ids:
            for month in MONTHS:
                values.append((0, 0, {
                    'month': month[0],
                    'year': res.year,
                    'company_id': company.id,
                }))
        res.line_ids = values
        return res


class AccountTaxReturnMonthlyGoal(models.Model):
    _name = 'account.tax.return.monthly.line'
    _description = 'Lineas de Meta Mensual'

    name = fields.Char(string="Nombre")
    month = fields.Selection(MONTHS, 'Mes', required=True)
    year = fields.Selection([(str(i), str(i)) for i in range(2020, int(datetime.now().year) + 10)], string="Año", required=True)
    company_id = fields.Many2one('res.company', string="Alcaldía", required=True)
    raised = fields.Float(string='Recaudado Bs.', compute='_compute_raised')
    pending = fields.Float(string='Pendiente Bs.', compute='_compute_pending')
    goal = fields.Float(string='Meta Bs.')
    accomplished = fields.Float(string='% Logrado', compute='_compute_accomplished')
    goal_id = fields.Many2one('account.tax.return.monthly.goal', string="Meta", ondelete='cascade')

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.name = f'Meta de {res.company_id.name} para {res.month} del {res.year}'
        return res

    def _compute_accomplished(self):
        """Obtener porcentaje de logro"""
        for rec in self:
            rec.accomplished = 0
            if rec.goal > 0:
                rec.accomplished = (rec.raised / rec.goal) * 100

    def _compute_raised(self):
        """Obtener monto recaudado"""
        for rec in self:
            rec.raised = 0
            tax_ids = self.env['account.tax.return'].search([
                '&', '&',
                ('company_id', '=', rec.company_id.id),
                ('type_tax', '=', 'tax'),
                ('state', '=', 'payment'),
            ]).filtered(lambda x: x.date.month == int(rec.month) and x.date.year == int(rec.year)).mapped('amount')
            rec.raised = sum(tax_ids)

    def _compute_pending(self):
        """Obtener monto pendiente"""
        for rec in self:
            rec.pending = 0
            tax_ids = self.env['account.tax.return'].search([
                '&', '&',
                ('company_id', '=', rec.company_id.id),
                ('type_tax', '=', 'tax'),
                ('state', '=', 'pending'),
            ]).filtered(lambda x: x.date.month == int(rec.month) and x.date.year == int(rec.year)).mapped('amount')
            rec.pending = sum(tax_ids)
