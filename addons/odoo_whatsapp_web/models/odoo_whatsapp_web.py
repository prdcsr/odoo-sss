from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import html2text


class OdooWhatsappWeb(models.TransientModel):
    _inherit = 'mail.compose.message'

    # ===== Declare Functions =====

    def action_share_whatsapp(self):
        if not self.partner_ids.mobile:
            raise ValidationError(_("[%s] doesn't have phone number") % self.partner_ids.name)
        local = self.env['ir.config_parameter'].search([('key', '=', 'web.base.url')]).value
        # msg = self.env["ir.fields.converter"].text_from_html(self.body, 100)
        msg = html2text.html2text(self.body)

        for attachment_id in self.attachment_ids:
            local2 = '/web/image/ir.attachment/%s/datas' % str(attachment_id.id)
            msg += ' ' + local + local2
        print('msg', msg)
        whatsapp_api_url = 'https://api.whatsapp.com/send?phone=%s&text=%s' % (self.partner_ids.mobile, msg)
        print('self.body', msg)
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': whatsapp_api_url
        }


class InvoiceOdooWhatsappWeb(models.TransientModel):
    _inherit = 'account.invoice.send'

    # ===== Declare Functions =====

    def action_share_whatsapp_Invoice(self):
        if not self.partner_ids.mobile:
            raise ValidationError(_("[%s] doesn't have phone number") % self.partner_ids.name)
        local = self.env['ir.config_parameter'].search([('key', '=', 'web.base.url')]).value
        msg = html2text.html2text(self.body)
        for attachment_id in self.attachment_ids:
            local2 = '/web/image/ir.attachment/%s/datas' % str(attachment_id.id)
            msg += ' ' + local + local2
        print('msg', msg)
        whatsapp_api_url = 'https://api.whatsapp.com/send?phone=%s&text=%s' % (self.partner_ids.mobile, msg)
        print('self.body', msg)
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': whatsapp_api_url
        }
