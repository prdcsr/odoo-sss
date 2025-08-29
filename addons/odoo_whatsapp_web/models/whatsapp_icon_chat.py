from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WhatsAppIconChat(models.Model):
    _inherit = 'res.partner'

    def whatsapp_person_chat_mobile(self):
        if not self.mobile:
            raise ValidationError(_("[%s] doesn't have phone number") % self.name)
        msg = ''
        whatsapp_api_url = 'https://api.whatsapp.com/send?phone=%s&text=%s' % (self.mobile, msg)
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': whatsapp_api_url
        }

    def whatsapp_person_chat_phone(self):
        if not self.phone:
            raise ValidationError(_("[%s] doesn't have phone number") % self.name)
        msg = ''
        whatsapp_api_url = 'https://api.whatsapp.com/send?phone=%s&text=%s' % (self.phone, msg)
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': whatsapp_api_url
        }
