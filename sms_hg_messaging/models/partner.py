from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    sms_ids = fields.One2many('sms.sms', 'partner_id', string='SMS')
