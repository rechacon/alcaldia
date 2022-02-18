from odoo import models, fields

LIST_TYPE_PERSON = [
    ('JURIDICO', 'Jurídico'),
    ('NATURAL', 'Natural'),
]


class Partner(models.Model):
    _inherit = 'res.partner'

    type_person = fields.Selection(LIST_TYPE_PERSON, 'Tipo de contribuyente')
    email_second = fields.Char('Correo electrónico 2°', help='Correo electrónico secundario')
