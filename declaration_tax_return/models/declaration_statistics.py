from odoo import fields, models, api


class AccountDeclarationStatistics(models.Model):
    _name = 'account.declaration.statistics'
    _description = 'Estadisticas de declaraciones por cliente'
    _rec_name = 'partner_id'

    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)
        # Creando lineas por planilla
        template_ids = self.env['account.template.type'].search([])
        values_template = []
        for template in template_ids:
            values_template.append((0, 0, {'name': template.id}))
        if values_template:
            result['template_statistics_ids'] = values_template
        # Creando lineas por impuestos
        tax_ids = self.env['account.declaration.tax.type'].search([])
        values_tax = []
        for tax in tax_ids:
            values_tax.append((0, 0, {'name': tax.id}))
        if values_tax:
            result['type_statistics_ids'] = values_tax
        return result

    partner_id = fields.Many2one('res.partner', 'Contribuyente')
    total_tax = fields.Integer('Declaraciones', compute='_compute_total_tax')
    total_payment = fields.Integer('Planillas de Pago', compute='_compute_total_payment')
    template_statistics_ids = fields.One2many('account.template.type.statistics', 'statistics_id', 'Estadística por Plantilla')
    type_statistics_ids = fields.One2many('account.declaration.tax.type.statistics', 'statistics_id', 'Estadística por Impuesto')
    status_payment_payment = fields.Integer('Pagado (Pagos)', compute='_compute_status_payment_payment')
    status_payment_pending = fields.Integer('Pendiente (Pagos)', compute='_compute_status_payment_pending')
    status_tax_payment = fields.Integer('Pagado (Declaración)', compute='_compute_status_tax_payment')
    status_tax_pending = fields.Integer('Pendiente (Declaración)', compute='_compute_status_tax_pending')

    def _compute_total_tax(self):
        """Obtiene el total de todas las declaraciones del contribuyente"""
        for rec in self:
            rec.total_tax = 0
            if rec.partner_id:
                rec.total_tax = self.env['account.tax.return'].search_count([('partner_id', '=', rec.partner_id.id), ('type_tax', '=', 'tax')])

    def _compute_total_payment(self):
        """Obtiene el total de todos los pagos del contribuyente"""
        for rec in self:
            rec.total_payment = 0
            if rec.partner_id:
                rec.total_payment = self.env['account.tax.return'].search_count([('partner_id', '=', rec.partner_id.id), ('type_tax', '!=', 'tax')])

    def _compute_status_payment_payment(self):
        """Obtiene el total de estatus de pagos del contribuyente por planillas de pago"""
        for rec in self:
            rec.status_payment_payment = 0
            if rec.partner_id:
                rec.status_payment_payment = self.env['account.tax.return'].search_count([('partner_id', '=', rec.partner_id.id), ('type_tax', '!=', 'tax'), ('state', '=', 'payment')])

    def _compute_status_payment_pending(self):
        """Obtiene el total de estatus de pagos pendientes del contribuyente por planillas de pago"""
        for rec in self:
            rec.status_payment_pending = 0
            if rec.partner_id:
                rec.status_payment_pending = self.env['account.tax.return'].search_count([('partner_id', '=', rec.partner_id.id), ('type_tax', '!=', 'tax'), ('state', '=', 'pending')])

    def _compute_status_tax_payment(self):
        """Obtiene el total de estatus de pagos del contribuyente por declaraciones"""
        for rec in self:
            rec.status_tax_payment = 0
            if rec.partner_id:
                rec.status_tax_payment = self.env['account.tax.return'].search_count([('partner_id', '=', rec.partner_id.id), ('type_tax', '=', 'tax'), ('state', '=', 'payment')])

    def _compute_status_tax_pending(self):
        """Obtiene el total de estatus de pagos pendientes del contribuyente por declaraciones"""
        for rec in self:
            rec.status_tax_pending = 0
            if rec.partner_id:
                rec.status_tax_pending = self.env['account.tax.return'].search_count([('partner_id', '=', rec.partner_id.id), ('type_tax', '=', 'tax'), ('state', '=', 'pending')])

    def _cron_create_statistics(self):
        """Cron para crear estadísticas de todos los contribuyentes"""
        statistics = self.env['account.declaration.statistics']
        partners_ids = set(statistics.search([]).mapped('partner_id').ids)
        partner_exists = set(self.env['res.partner'].search([('vat', '!=', False)]).ids)
        ids = partners_ids ^ partner_exists  # Obtener solo los valores distintos entre los 2 conjuntos
        count = 1
        for rec in ids:
            if rec not in partners_ids:
                statistics.create({'partner_id': rec})
                count += 1
            if count == 100:
                self.env.cr.commit()
                count = 1


class AccountTemplateTypeStatistics(models.Model):
    _name = 'account.template.type.statistics'
    _description = 'Estadisticas de tipo de planilla'

    name = fields.Many2one('account.template.type', 'Tipo')
    total_tax = fields.Integer('Total declaraciones', compute='_compute_total_tax')
    total_payment = fields.Integer('Total planillas de pagos', compute='_compute_total_payment')
    statistics_id = fields.Many2one('account.declaration.statistics', 'Estadística', ondelete="cascade")

    def _compute_total_tax(self):
        """Calcula el total de declaraciones por tipo de planilla"""
        for rec in self:
            rec.total_tax = 0
            if rec.statistics_id.partner_id:
                rec.total_tax = self.env['account.tax.return'].search_count([('partner_id', '=', rec.statistics_id.partner_id.id), ('type_tax', '=', 'tax'), ('template_id', '=', rec.name.id)])

    def _compute_total_payment(self):
        """Calcula el total de declaraciones por tipo de impuesto"""
        for rec in self:
            rec.total_payment = 0
            if rec.statistics_id.partner_id:
                rec.total_payment = self.env['account.tax.return'].search_count([('partner_id', '=', rec.statistics_id.partner_id.id), ('type_tax', '!=', 'tax'), ('template_id', '=', rec.name.id)])


class AccountTaxTypeStatistics(models.Model):
    _name = 'account.declaration.tax.type.statistics'
    _description = 'Estadisticas de tipo de impuesto'

    name = fields.Many2one('account.declaration.tax.type', 'Tipo')
    total_tax = fields.Integer('Total declaraciones', compute='_compute_total_tax')
    total_payment = fields.Integer('Total planillas de pagos', compute='_compute_total_payment')
    statistics_id = fields.Many2one('account.declaration.statistics', 'Estadística', ondelete="cascade")

    def _compute_total_tax(self):
        """Calcula el total de declaraciones por tipo de planilla"""
        for rec in self:
            rec.total_tax = 0
            if rec.statistics_id.partner_id:
                rec.total_tax = self.env['account.tax.return'].search_count([('partner_id', '=', rec.statistics_id.partner_id.id), ('type_tax', '=', 'tax'), ('tax_id', '=', rec.name.id)])

    def _compute_total_payment(self):
        """Calcula el total de declaraciones por tipo de impuesto"""
        for rec in self:
            rec.total_payment = 0
            if rec.statistics_id.partner_id:
                rec.total_payment = self.env['account.tax.return'].search_count([('partner_id', '=', rec.statistics_id.partner_id.id), ('type_tax', '!=', 'tax'), ('tax_id', '=', rec.name.id)])
