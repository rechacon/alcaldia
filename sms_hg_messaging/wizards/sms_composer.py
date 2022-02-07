from ast import literal_eval
from suds.client import Client

from odoo import fields, models, _
from odoo.exceptions import ValidationError

STATUS_CODE = {
    0: {'name': 'Mensaje aceptado por la plataforma', 'action': '-'},
    -100: {'name': 'Error de infraestructura', 'action': 'Intente más tarde'},
    -101: {'name': 'Error interno', 'action': 'Intente más tarde'},
    -102: {'name': 'Operador fuera de línea', 'action': 'Intente más tarde'},
    -103: {'name': 'Receptor no disponible', 'action': 'Notifique a Tedexis'},
    -104: {'name': 'Destino no aceptado por el operador', 'action': 'Verifique país, operadora y número'},
    -105: {'name': 'No autenticado', 'action': 'Verifique su pasaporte y password'},
    -106: {'name': 'Servicio no disponible', 'action': 'Intente más tarde'},
    -107: {'name': 'Destino no aceptado', 'action': 'Verifique país, operadora y número'},
    -201: {'name': 'Recepción en proceso', 'action': '-'},
    -202: {'name': 'Recepción no estaba en proceso', 'action': '-'},
    -203: {'name': 'No configurado', 'action': 'Notifique a Tedexis'},
    -204: {'name': 'Código de país no soportado', 'action': 'Verifique el código de país'},
    -205: {'name': 'Código de área no soportado', 'action': 'Verifique el código de área'},
    -206: {'name': 'Número no soportado', 'action': 'Verifique el número'},
    -207: {'name': 'Mensaje rechazado', 'action': 'Verifique país, operadora y número'},
    -208: {'name': 'Error en número suministrado', 'action': 'Verifique el número'},
    -209: {'name': 'Pasaporte existente', 'action': 'Utilice otro pasaporte'},
    -300: {'name': 'Pasaporte o password nulo', 'action': 'Verifique el pasaporte y password'},
    -301: {'name': 'Sin saldo suficiente', 'action': 'Notifique a Tedexis'},
    -302: {'name': 'Anti flood activado', 'action': 'Verifique que no esté enviando mensajes al mismo número'},
    -601: {'name': 'Id mensaje no válido', 'action': 'Está respondiendo un mensaje usando un ID incorrecto'},
    -602: {'name': 'Destino de respuesta no coincide', 'action': 'Está respondiendo a un número diferente al MO'},
    -603: {'name': 'MO ya contestado', 'action': 'Está contestando un MO ya respondido'},
}


class SendSMS(models.TransientModel):
    _inherit = 'sms.composer'

    method = fields.Selection([('HgMessaging', 'Hg Messaging'), ('none', 'Ninguno')], string="Método")

    # ------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------

    def _action_send_sms(self):
        records = self._get_records()
        if self.method == 'HgMessaging':
            return self.send_hg_messaging(records)
        res = super()._action_send_sms()
        return res

    def send_hg_messaging(self, records):
        """Enviar sms por hg messaging"""
        records = records if records is not None else self._get_records()

        sms_record_values = self._prepare_mass_sms_values(records)
        sms_all = self._prepare_mass_sms(records, sms_record_values)

        hg_messaging = self.env['sms.hg.messaging'].search([], limit=1)
        if not hg_messaging:
            raise ValidationError(_("Debe configurar alguna credencial de Hg Messaging antes de proceder"))

        client = Client(hg_messaging.wsdl, cache=None, timeout=600)

        for sms in sms_all:
            number = sms.number.replace('+', '')
            body = sms.body

            result = client.service.sendSMS(hg_messaging.passport, hg_messaging.password, number, body)
            if result == 0:
                sms.state = 'sent'
            else:
                sms.state = 'error'
                result = STATUS_CODE.get(result, False)
                msg = f"""{result['name']} / Por favor, {result['action']}\n\nNúmero: {number}"""
                raise ValidationError(msg)

    def _get_records(self):
        if not self.res_model:
            return None
        if self.use_active_domain:
            active_domain = literal_eval(self.active_domain or '[]')
            records = self.env[self.res_model].search(active_domain)
        elif self.res_ids:
            records = self.env[self.res_model].browse(literal_eval(self.res_ids))
        elif self.res_id:
            records = self.env[self.res_model].browse(self.res_id)
        else:
            records = self.env[self.res_model]

        records = records.with_context(mail_notify_author=True)
        # Verificar si existe un campo de partner_id en el modelo
        fields_model = self.env['ir.model'].search([('model', '=', self.res_model)]).field_id.mapped('name')
        if 'partner_id' in fields_model and self.res_model != 'res.partner':
            ids = []
            for record in records:
                if record.partner_id:
                    ids.append(record.partner_id.id)
            # Retorna los partners asociados al modelo
            records = self.env['res.partner'].browse(ids)
        return records

    def _prepare_body_values(self, records):
        if self.template_id and self.body == self.template_id.body:
            # Evitar conflictos de records.ids
            all_bodies = self.template_id._render_field('body', literal_eval(self.res_ids), compute_lang=True)
        else:
            all_bodies = self.env['mail.render.mixin']._render_template(self.body, records._name, records.ids)
        return all_bodies

    def _prepare_mass_sms_values(self, records):
        all_bodies = self._prepare_body_values(records)
        all_recipients = self._prepare_recipient_values(records)
        blacklist_ids = self._get_blacklist_record_ids(records, all_recipients)
        done_ids = self._get_done_record_ids(records, all_recipients)

        # Evitar conflictos de id
        if self.res_ids != records.ids and not self.comment_single_recipient and self.res_model != 'res.partner':
            for record in records:
                fix_ids = self.env[self.res_model].search([('partner_id', '=', record.id)]).filtered(lambda x: x.id in literal_eval(self.res_ids))
                for fix in fix_ids:
                    all_bodies[record.id] = all_bodies.get(fix.id)

        result = {}
        for record in records:
            recipients = all_recipients[record.id]
            sanitized = recipients['sanitized']
            if sanitized and record.id in blacklist_ids:
                state = 'canceled'
                failure_type = 'sms_blacklist'
            elif sanitized and record.id in done_ids:
                state = 'canceled'
                failure_type = 'sms_duplicate'
            elif not sanitized:
                state = 'error'
                failure_type = 'sms_number_format' if recipients['number'] else 'sms_number_missing'
            else:
                state = 'outgoing'
                failure_type = ''

            result[record.id] = {
                'body': all_bodies[record.id],
                'partner_id': recipients['partner'].id,
                'number': sanitized if sanitized else recipients['number'],
                'state': state,
                'failure_type': failure_type,
            }
        return result

    def _prepare_mass_sms(self, records, sms_record_values):
        sms_create_vals = [sms_record_values[record.id] for record in records]

        # Evita que el sms sea duplicado cuando es el mismo partner
        if self.res_model != 'res.partner' and not self.comment_single_recipient:
            exclude_ids = []
            vals_ids = []
            all_bodies = self._prepare_body_values(records)
            for sms in sms_create_vals:
                fix_ids = self.env[self.res_model].search([('partner_id', '=', sms['partner_id'])]).filtered(lambda x: x.id in literal_eval(self.res_ids) and x.id not in exclude_ids)
                for fix in fix_ids:
                    body = all_bodies.get(fix.id)
                    sms['body'] = body
                    sms_create = self.env['sms.sms'].sudo().create(sms)
                    vals_ids.append(sms_create.id)
                    exclude_ids.append(fix.id)
                    break
            return self.env['sms.sms'].sudo().browse(vals_ids)

        return self.env['sms.sms'].sudo().create(sms_create_vals)
