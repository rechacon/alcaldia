# -*- coding: utf-8 -*-

from odoo import api, models, fields


class HgMessaging(models.Model):
    _name = 'sms.hg.messaging'
    _description = 'Integracion Hg Messaging'

    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)
        result['wsdl'] = 'http://api.tedexis.com:8086/m4.in.wsint/services/M4WSIntSR?wsdl'
        return result

    name = fields.Char('Nombre', required=True)
    wsdl = fields.Char('WSDL', required=True)
    passport = fields.Char(required=True)
    password = fields.Char(required=True)
    active = fields.Boolean('Activo', default=True)
