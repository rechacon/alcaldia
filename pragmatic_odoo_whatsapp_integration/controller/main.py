import requests
from odoo import http, _, models, api
import logging
import json
from odoo.exceptions import UserError
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.main import ensure_db, Home, SIGN_UP_REQUEST_PARAMS
from odoo.http import request
import phonenumbers
import datetime
import time
import pytz
from odoo.tools import ustr
import requests
import base64
_logger = logging.getLogger(__name__)
from odoo.addons.phone_validation.tools import phone_validation


class SendMessage(http.Controller):
    _name = 'send.message.controller'

    def format_amount(self, amount, currency):
        fmt = "%.{0}f".format(currency.decimal_places)
        lang = http.request.env['res.lang']._lang_get(http.request.env.context.get('lang') or 'en_US')

        formatted_amount = lang.format(fmt, currency.round(amount), grouping=True, monetary=True)\
            .replace(r' ', u'\N{NO-BREAK SPACE}').replace(r'-', u'-\N{ZERO WIDTH NO-BREAK SPACE}')
        pre = post = u''
        if currency.position == 'before':
            pre = u'{symbol}\N{NO-BREAK SPACE}'.format(symbol=currency.symbol or '')
        else:
            post = u'\N{NO-BREAK SPACE}{symbol}'.format(symbol=currency.symbol or '')
        return u'{pre}{0}{post}'.format(formatted_amount, pre=pre, post=post)

    @http.route('/whatsapp/send/message', type='http', auth='public', website=True, csrf=False)
    def sale_order_paid_status(self, **post):
        pos_order = http.request.env['pos.order'].sudo().search([('pos_reference', '=', post.get('order'))])
        if pos_order.partner_id:
            if pos_order.partner_id.mobile and pos_order.partner_id.country_id.phone_code:
                doc_name = 'POS'
                msg = _("Hello") + " " + pos_order.partner_id.name
                if pos_order.partner_id.parent_id:
                    msg += "(" + pos_order.partner_id.parent_id.name + ")"
                msg += "\n\n" + _("Your")+ " "
                msg += doc_name + " *" + pos_order.name + "* "
                msg += " " + _("with Total Amount") + " " + self.format_amount(pos_order.amount_total, pos_order.pricelist_id.currency_id) + "."
                msg += "\n\n" + _("Following is your order details.")
                for line_id in pos_order.lines:
                    msg += "\n\n*" + _("Product") + ":* " + line_id.product_id.name + "\n*" + _("Qty") + ":* " + str(line_id.qty) + " " + "\n*" + _("Unit Price") + ":* " + str(
                        line_id.price_unit) + "\n*" + _("Subtotal")+ ":* " + str(line_id.price_subtotal)
                    msg += "\n------------------"
                Param = http.request.env['res.config.settings'].sudo().get_values()
                str_msg = ''
                whatsapp_number = pos_order.partner_id.mobile
                whatsapp_msg_number_without_space = whatsapp_number.replace(" ", "")
                whatsapp_msg_number_without_code = whatsapp_msg_number_without_space.replace('+' + str(pos_order.partner_id.country_id.phone_code), "")
                phone_exists_url = http.request.env.user.whatsapp_endpoint + '/checkPhone?token=' + http.request.env.user.whatsapp_token + '&phone=' + str(pos_order.partner_id.country_id.phone_code) + "" + whatsapp_msg_number_without_code
                phone_exists_response = requests.get(phone_exists_url)
                json_response_phone_exists = json.loads(phone_exists_response.text)
                if (phone_exists_response.status_code == 200 or phone_exists_response.status_code == 201) and json_response_phone_exists['result'] == 'exists':
                    url = http.request.env.user.whatsapp_endpoint + '/sendMessage?token=' + http.request.env.user.whatsapp_token
                    headers = {"Content-Type": "application/json"}

                    tmp_dict = {
                        "phone": "+" + str(pos_order.partner_id.country_id.phone_code) + "" +whatsapp_msg_number_without_code,
                        "body": msg}
                    response = requests.post(url, json.dumps(tmp_dict), headers=headers)
                    if response.status_code == 201 or response.status_code == 200:
                        _logger.info("\nSend Message successfully")
                        return "Send Message successfully"
                elif json_response_phone_exists.get('result') == 'not exists':
                    str_msg = 'Phone not exists on whatsapp'
                    return str_msg
                else:
                    return json_response_phone_exists.get('error')


class AuthSignupHomeDerived(AuthSignupHome):

    def get_auth_signup_config(self):
        """retrieve the module config (which features are enabled) for the login page"""
        get_param = request.env['ir.config_parameter'].sudo().get_param
        countries = request.env['res.country'].sudo().search([])
        return {
            'signup_enabled': request.env['res.users']._get_signup_invitation_scope() == 'b2c',
            'reset_password_enabled': get_param('auth_signup.reset_password') == 'True',
            'countries': countries
        }

    def get_auth_signup_qcontext(self):
        SIGN_UP_REQUEST_PARAMS.add('mobile')
        qcontext = super().get_auth_signup_qcontext()
        return qcontext

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = { key: qcontext.get(key) for key in ('login', 'name', 'password', 'mobile', 'country_id') }
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        supported_langs = [lang['code'] for lang in request.env['res.lang'].sudo().search_read([], ['code'])]
        if request.lang in supported_langs:
            values['lang'] = request.lang
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()


class Whatsapp(http.Controller):

    def convert_epoch_to_unix_timestamp(self, msg_time):
        formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg_time))
        date_time_obj = datetime.datetime.strptime(formatted_time, '%Y-%m-%d %H:%M:%S')
        dt = False
        if date_time_obj:
            timezone = pytz.timezone(request.env['res.users'].sudo().browse([int(2)]).tz or 'UTC')
        dt = pytz.UTC.localize(date_time_obj)
        dt = dt.astimezone(timezone)
        dt = ustr(dt).split('+')[0]
        return date_time_obj

    @http.route(['/whatsapp/response/message'], type='json', auth='public')
    def whatsapp_responce(self):
        _logger.info("In whatsapp integration controller")
        data = json.loads(request.httprequest.data)
        _logger.info("data %s: ", str(data))
        _request = data
        if 'messages' in data and data['messages']:
            msg_list=[]
            msg_dict={}
            res_partner_obj = request.env['res.partner']
            whatapp_msg = request.env['whatsapp.messages']
            mail_channel_obj = request.env['mail.channel']
            mail_message_obj = request.env['mail.message']
            project_task_user_rel_obj = request.env['project.task.user.rel']

            for msg in data['messages']:
                if 'quotedMsgId' in msg and msg['quotedMsgId']:
                    project_task_user_rel_id = project_task_user_rel_obj.sudo().search([('whatsapp_msg_id', 'like', msg['quotedMsgId'][-9:])])
                    if 'chatId' in msg and msg['chatId']:
                        chat_id = msg['chatId']
                        chatid_split = chat_id.split('@')
                        mobile = '+' + chatid_split[0]
                        mobile_coutry_code = phonenumbers.parse(mobile, None)
                        mobile_number = mobile_coutry_code.national_number
                        country_code = mobile_coutry_code.country_code
                        res_country_id = request.env['res.country'].sudo().search([('phone_code', '=', country_code)], limit=1)
                        reg_sanitized_number = phone_validation.phone_format(str(mobile_number), res_country_id.code, country_code)
                        res_partner_obj = res_partner_obj.sudo().search([('mobile', '=', reg_sanitized_number)], limit=1)
                        mail_message_id = mail_message_obj.sudo().search([('whatsapp_message_id', '=', msg['quotedMsgId'])], limit=1)
                        if mail_message_id.model == 'mail.channel' and mail_message_id.res_id:
                            channel_id = mail_channel_obj.sudo().search([('id', '=', mail_message_id.res_id)])
                            channel_id.with_context(from_odoobot=True).message_post(body=msg['body'],
                                                                                    message_type="notification",
                                                                                    subtype_xmlid="mail.mt_comment",
                                                                                    author_id=res_partner_obj.id)
                            mail_message_id.with_context(from_odoobot=True)
                    if project_task_user_rel_id:
                        if msg.get('body') == 'done' or msg.get('body') == 'Done':
                            task_type_done_id = project_task_user_rel_id.task_id.env['project.task.type'].search([('name', '=', 'Done')], limit=1)
                            if task_type_done_id:
                                stage_id = project_task_user_rel_id.task_id.write({'stage_id': task_type_done_id.id})

                elif 'chatId' in msg and msg['chatId']:
                    if '@c.us' in msg['chatId']:    #@c.us is for contacts & @g.us is for group
                        res_partner_obj = res_partner_obj.sudo().search([('chatId','=',msg['chatId'])], limit=1)
                        if res_partner_obj:
                            if msg['type'] == 'image' and res_partner_obj:
                                url = msg['body']
                                image_data = base64.b64encode(requests.get(url.strip()).content).replace(b'\n', b'')
                                msg_dict = {
                                    'name': msg['body'],
                                    'message_body': msg['caption'],
                                    'message_id': msg['id'],
                                    'fromMe': msg['fromMe'],
                                    'to': msg['chatName'] if msg['fromMe']==True else 'To Me',
                                    'chatId': msg['chatId'],
                                    'type': msg['type'],
                                    'senderName': msg['senderName'],
                                    'chatName': msg['chatName'],
                                    'author': msg['author'],
                                    'time': self.convert_epoch_to_unix_timestamp(msg['time']),
                                    'partner_id': res_partner_obj.id,
                                    'state': 'sent' if msg['fromMe'] == True else 'received',
                                    'msg_image':image_data
                                }
                            if res_partner_obj and msg['type'] == 'chat':
                                msg_dict = {
                                    'name':msg['body'],
                                    'message_body':msg['body'],
                                    'message_id':msg['id'],
                                    'fromMe':msg['fromMe'],
                                    'to':msg['chatName'] if msg['fromMe']==True else 'To Me',
                                    'chatId':msg['chatId'],
                                    'type':msg['type'],
                                    'senderName':msg['senderName'],
                                    'chatName':msg['chatName'],
                                    'author':msg['author'],
                                    'time':self.convert_epoch_to_unix_timestamp(msg['time']),
                                    'partner_id':res_partner_obj.id,
                                    'state':'sent' if msg['fromMe'] == True else 'received',
                                }
                            if msg['type'] == 'document' and res_partner_obj:
                                msg_dict = {
                                    'name': msg['body'],
                                    'message_body': msg['caption'],
                                    'message_id': msg['id'],
                                    'fromMe': msg['fromMe'],
                                    'to': msg['chatName'] if msg['fromMe']==True else 'To Me',
                                    'chatId': msg['chatId'],
                                    'type': msg['type'],
                                    'senderName': msg['senderName'],
                                    'chatName': msg['chatName'],
                                    'author': msg['author'],
                                    'time': self.convert_epoch_to_unix_timestamp(msg['time']),
                                    'partner_id': res_partner_obj.id,
                                    'state': 'sent' if msg['fromMe'] == True else 'received'
                                }
                        else:
                            chat_id = msg['chatId']
                            chatid_split = chat_id.split('@')
                            mobile = '+'+chatid_split[0]
                            mobile_coutry_code = phonenumbers.parse(mobile,None)
                            mobile_number = mobile_coutry_code.national_number
                            res_partner_obj = res_partner_obj.sudo().search([('mobile','=',mobile_number)], limit=1)
                            if not res_partner_obj:
                                mobile_coutry_code = phonenumbers.parse(mobile, None)
                                mobile_number = mobile_coutry_code.national_number
                                country_code = mobile_coutry_code.country_code
                                mobile = '+'+str(country_code)+' '+str(mobile_number)
                                res_partner_obj = res_partner_obj.sudo().search([('mobile', '=', mobile)], limit=1)
                            if not res_partner_obj:
                                mobile_coutry_code = phonenumbers.parse(mobile, None)
                                mobile_number = mobile_coutry_code.national_number
                                country_code = mobile_coutry_code.country_code
                                res_country_id = request.env['res.country'].sudo().search([('phone_code', '=', country_code)], limit=1)
                                reg_sanitized_number = phone_validation.phone_format(str(mobile_number), res_country_id.code, country_code)
                                res_partner_obj = res_partner_obj.sudo().search([('mobile', '=', reg_sanitized_number)], limit=1)
                            if res_partner_obj:
                                res_partner_obj.chatId = chat_id
                                msg_dict = {
                                    'name': msg['body'],
                                    'message_body': msg['body'],
                                    'message_id': msg['id'],
                                    'fromMe': msg['fromMe'],
                                    'to': msg['chatName'] if msg['fromMe']==True else 'To Me',
                                    'chatId': msg['chatId'],
                                    'type': msg['type'],
                                    'senderName': msg['senderName'],
                                    'chatName': msg['chatName'],
                                    'author': msg['author'],
                                    'time': self.convert_epoch_to_unix_timestamp(msg['time']),
                                    'partner_id': res_partner_obj.id,
                                    'state': 'sent' if msg['fromMe'] == True else 'received'
                                }
                            else:
                                res_partner_dict = {}
                                mobile_number = msg['chatId'].replace('@c.us','')
                                res_partner_dict['name'] = mobile_number
                                chatid_split = msg['chatId'].split('@')
                                mobile = '+' + chatid_split[0]
                                mobile_coutry_code = phonenumbers.parse(mobile, None)
                                country_code = mobile_coutry_code.country_code
                                res_country_id = request.env['res.country'].sudo().search([('phone_code', '=', country_code)], limit=1)
                                res_partner_dict['country_id'] = res_country_id.id
                                res_partner_dict['mobile'] = mobile
                                res_partner_dict['chatId'] = msg['chatId']
                                res_partner_id = request.env['res.partner'].sudo().create(res_partner_dict)
                                if res_partner_id:
                                    msg_dict = {
                                        'name': msg['body'],
                                        'message_body': msg['body'],
                                        'message_id': msg['id'],
                                        'fromMe': msg['fromMe'],
                                        'to': msg['chatName'] if msg['fromMe'] == True else 'To Me',
                                        'chatId': msg['chatId'],
                                        'type': msg['type'],
                                        'senderName': msg['senderName'],
                                        'chatName': msg['chatName'],
                                        'author': msg['author'],
                                        'time': self.convert_epoch_to_unix_timestamp(msg['time']),
                                        'partner_id': res_partner_id.id,
                                        'state': 'sent' if msg['fromMe'] == True else 'received'
                                    }
                        _logger.info("msg_dict %s: ", str(msg_dict))
                        if len(msg_dict) > 0:
                            msg_list.append(msg_dict)
            for msg in msg_list:
                res_whatsapp_msg = whatapp_msg.sudo().create(msg)
                _logger.info("res_whatsapp_msg %s: ", str(res_whatsapp_msg))
                if 'messages' in data and data['messages']:
                    for msg in data['messages']:
                        if res_whatsapp_msg and msg['type'] == 'document':
                            msg_attchment_dict = {}
                            url = msg['body']
                            data_base64 = base64.b64encode(requests.get(url.strip()).content)
                            msg_attchment_dict = {'name': msg['caption'], 'datas': data_base64, 'type': 'binary',
                                               'res_model': 'whatsapp.messages', 'res_id': res_whatsapp_msg.id}
                            attachment_id = request.env['ir.attachment'].sudo().create(msg_attchment_dict)
                            res_update_whatsapp_msg = res_whatsapp_msg.sudo().write({'attachment_id': attachment_id.id})
                            _logger.info("res_update_whatsapp_msg %s: ", str(res_update_whatsapp_msg))
        return 'OK'
