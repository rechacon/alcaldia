from odoo import models, fields, api

LIST_TYPE_PERSON = [
    ('JURIDICO', 'Jurídico'),
    ('NATURAL', 'Natural'),
]


class Partner(models.Model):
    _inherit = 'res.partner'

    type_person = fields.Selection(LIST_TYPE_PERSON, 'Tipo de contribuyente')
    email_second = fields.Char('Correo electrónico 2°', help='Correo electrónico secundario')
    count_declaration = fields.Integer(compute='_compute_count_declaration')
    municipality_id = fields.Many2one('res.country.state.municipality', 'Municipio')
    parish_id = fields.Many2one('res.country.state.municipality.parish', 'Parroquia')

    @api.model
    def _address_fields(self):
        address_fields = set(super()._address_fields())
        address_fields.add('municipality_id')
        address_fields.add('parish_id')
        return list(address_fields)

    def _compute_count_declaration(self):
        """Contar el total de declaraciones"""
        for rec in self:
            rec.count_declaration = self.env['account.tax.return'].search_count([('partner_id', '=', rec.id), ('type_tax', '=', 'tax')])

    def view_declarations(self):
        """Ver declaraciones"""
        for rec in self:
            action = self.env["ir.actions.act_window"]._for_xml_id('declaration_tax_return.action_account_tax_return_tax')
            ctx = eval(action['context'])
            ctx.update({'default_partner_id': rec.id, 'default_type_tax': 'tax'})
            action['domain'] = [('partner_id', '=', rec.id), ('type_tax', '=', 'tax')]
            action['context'] = ctx
            return action
