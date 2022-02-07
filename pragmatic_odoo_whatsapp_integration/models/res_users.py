import logging
from odoo import api, fields, models, _
import requests
import json

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    mobile = fields.Char()
    country_id = fields.Many2one('res.country', 'Country')
    whatsapp_endpoint = fields.Char('Whatsapp Endpoint', help="Whatsapp api endpoint url with instance id")
    whatsapp_token = fields.Char('Whatsapp Token')
    qr_code_image = fields.Binary("QR code")
    whatsapp_authenticate = fields.Boolean('Authenticate', default=False)

    def action_get_qr_code(self):
        return {
            'name': _("Scan WhatsApp QR Code"),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'whatsapp.scan.qr',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_logout_from_whatsapp(self):
        url =  self.whatsapp_endpoint + '/logout?token=' + self.whatsapp_token
        headers = {"Content-Type": "application/json"}
        tmp_dict = {"accountStatus": "Logout request sent to WhatsApp" }
        response = requests.post(url, json.dumps(tmp_dict), headers=headers)
        if response.status_code == 201 or response.status_code == 200:
            _logger.info("\nWhatsapp logout successfully")
            self.write({'whatsapp_authenticate': False})


    @api.model
    def signup(self, values, token=None):
        values.update({'email': values.get('email') or values.get('login')})
        if token:
            # signup with a token: find the corresponding partner id
            partner = self.env['res.partner']._signup_retrieve_partner(token, check_validity=True, raise_exception=True)
            # invalidate signup token
            partner.write({'signup_token': False, 'signup_type': False, 'signup_expiration': False})
            partner_user = partner.user_ids and partner.user_ids[0] or False
            # avoid overwriting existing (presumably correct) values with geolocation data
            if partner.country_id or partner.zip or partner.city:
                values.pop('city', None)
                values.pop('country_id', None)
            if partner.lang:
                values.pop('lang', None)
            if partner_user:
                # user exists, modify it according to values
                values.pop('login', None)
                values.pop('name', None)
                partner_user.write(values)
                if not partner_user.login_date:
                    partner_user._notify_inviter()
                return (self.env.cr.dbname, partner_user.login, values.get('password'))
            else:
                # user does not exist: sign up invited user
                values.update({
                    'name': partner.name,
                    'partner_id': partner.id,
                    'email': values.get('email') or values.get('login'),
                })
                if partner.company_id:
                    values['company_id'] = partner.company_id.id
                    values['company_ids'] = [(6, 0, [partner.company_id.id])]
                partner_user = self._signup_create_user(values)
                partner_user._notify_inviter()

        else:
            values['mobile'] = values.get('mobile')
            values['country_id'] = values.get('country_id')
            user_id = self._signup_create_user(values)
            if values['mobile']:
                user_id.partner_id.mobile = values['mobile']
            if values['country_id']:
                user_id.partner_id.country_id = int(values['country_id'])
            if values.get('country_id'):
                country_id = self.env['res.country'].sudo().search([('id', '=', values.get('country_id'))])
                msg = ''
                try:
                    if values.get('mobile') and country_id:
                        whatsapp_number = "+" + str(country_id.phone_code) + "" + values.get('mobile')
                        res_user_id = self.env['res.users'].sudo().search([('name', '=', 'Administrator')])
                        if res_user_id:
                            url = res_user_id.whatsapp_endpoint + '/sendMessage?token=' + res_user_id.whatsapp_token
                            headers = {"Content-Type": "application/json"}
                            tmp_dict = {
                                "phone": "+" + whatsapp_number,
                                "body": 'Hello ' + values.get('name') + ',' + '\nYou have successfully registered and logged in' + '\n*Your Email:* ' + values.get('login'),
                            }
                            response = requests.post(url, json.dumps(tmp_dict), headers=headers)
                            if response.status_code == 201 or response.status_code == 200:
                                _logger.info("\nSend Message successfully")
                        else:
                            user_ids = self.env.ref('base.group_system').users
                            for user_id in user_ids:
                                if not user_id.whatsapp_endpoint or not user_id.whatsapp_token:
                                    continue
                                if user_id.whatsapp_endpoint and user_id.whatsapp_token:
                                    url = user_id.whatsapp_endpoint + '/sendMessage?token=' + user_id.whatsapp_token
                                    headers = { "Content-Type": "application/json" }
                                    tmp_dict = {
                                        "phone": "+" + whatsapp_number,
                                        "body": 'Hello ' + values.get('name') + ',' + '\nYou have successfully registered and logged in' + '\n*Your Email:* ' + values.get('login'),
                                    }
                                    response = requests.post(url, json.dumps(tmp_dict), headers=headers)
                                    if response.status_code == 201 or response.status_code == 200:
                                        _logger.info("\nSend Message successfully")
                                        break
                except Exception as e_log:
                    _logger.exception("Exception in send message to user %s:\n", str(e_log))
        return (self.env.cr.dbname, values.get('login'), values.get('password'))


    # admin_users = self.filtered(lambda u:u.has_group('base.group_system'))