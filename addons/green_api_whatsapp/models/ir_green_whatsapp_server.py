# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests
from email import encoders
from email.charset import Charset
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import  formataddr, formatdate, getaddresses, make_msgid
import logging
import re
import smtplib
import json
import threading
from ..greenapi import GreenApi

import html2text

from odoo import api, fields, models, tools, _, sql_db
from odoo.exceptions import except_orm, UserError
from odoo.tools import ustr, pycompat

_logger = logging.getLogger(__name__)

SMTP_TIMEOUT = 60


class WaKlikodoo(models.TransientModel):
    _name = "wa.greenapi.popup"
    _description = "Wa Klikodoo"

    qr_scan = fields.Binary("QR Scan")


class IrWhatsappServer(models.Model):
    """Represents an SMTP server, able to send outgoing emails, with SSL and TLS capabilities."""
    _name = "ir.green_whatsapp_server"
    _description = 'Whatsapp Server'

    name = fields.Char(string='Name', index=True, required=True)

    id_instance = fields.Char("ID Instance", required=True, help="Optional key for SMTP authentication")
    api_token_instance = fields.Char("API Token Secret", required=True, help="Optional secret for SMTP authentication")
    qr_scan = fields.Binary("QR Scan")
    whatsapp_number = fields.Char('Whatsapp Number')
    status = fields.Selection([('notAuthorized', 'Not Authorized'),
                               ('authorized', 'Authenticated')], default='notAuthorized', string="Status")
    whatsapp_action = fields.Selection(
        [('invoice', 'Invoice'), ('invoice_paid', 'Invoice Paid')], required=True
    )
    operating_unit_id = fields.Many2one('operating.unit', string='Operating Unit')

    def greenapi(self):
        self.ensure_one()
        return GreenApi(self.id_instance, self.api_token_instance)

    def get_instance_status(self):
        for was in self:

            GreenApi = was.greenapi()
            GreenApi.auth()
            res = GreenApi.get_instance_status()

            if isinstance(res, str):
                raise Exception(res)

            was.status = res.get('stateInstance')

            if was.status == 'authorized':
                setting = GreenApi.get_instance_setting()
                whatsapp_number = setting.get('wid')
                idx = whatsapp_number.index('@')
                was.whatsapp_number = whatsapp_number[:idx]
            else:
                was.whatsapp_number = ""
                was.qr_scan = ''

    def send_message_text(self, data):
        for was in self:
            GreenApi = was.greenapi()
            GreenApi.auth()
            res = GreenApi.send_message_text(data=data)
            return res

    def _get_instance_setting(self):
        for was in self:
            GreenApi = was.greenapi()
            GreenApi.auth()
            setting = GreenApi.get_instance_setting()
            was.whatsapp_number = setting.get('wid')

    def _formatting_mobile_number(self, number):
        for rec in self:
            module_rec = self.env['ir.module.module'].sudo().search_count([
                ('name', '=', 'crm_phone_validation'),
                ('state', '=', 'installed')])
            return module_rec and re.sub("[^0-9]", '', number) or \
                str(rec.partner_id.country_id.phone_code
                    ) + number

    def greenapi(self):
        return GreenApi(self.id_instance, self.api_token_instance)

    #     def greenapi_status(self):
    #         # WhatsApp is open on another computer or browser. Click “Use Here” to use WhatsApp in this window.
    #         data = {}
    #         GreenApi = self.greenapi()
    #         GreenApi.auth()
    #         # INJECT START == WHATSAPP NUMBER ON SERVER
    #         number_data = {
    #             'whatsapp_number': self.whatsapp_number,
    #         }
    #         data_number = json.dumps(number_data)
    #         GreenApi.post_request(method='number', data=data_number)
    #         # =======================================================================
    #         data = GreenApi.get_request(method='status', data=data)
    #         # print ('---data---',data)
    #         if data.get('accountStatus') == 'loading':
    #             self.hint = 'Auth status is Loading! Please click QR Code/Use here again'
    #             self.status = 'loading'
    #             self.notes = ''
    #         elif data.get('accountStatus') == 'authenticated':
    #             # ALREADY SCANNED
    #             self.hint = 'Auth status Authenticated'
    #             self.status = 'authenticated'
    #             self.notes = ''
    #         elif data.get('qrCode'):
    #             # FIRST SCANNED OR RELOAD QR
    #             # print('33333')
    #             qrCode = data.get('qrCode').split(',')[1]
    #             self.qr_scan = qrCode
    #             self.status = 'got qr code'
    #             self.hint = 'To send messages, you have to authorise like for WhatsApp Web'
    #             self.notes = """1. Open the WhatsApp app on your phone
    # 2. Press Settings->WhatsApp WEB and then plus
    # 3. Scan a code and wait a minute
    # 4. Keep your phone turned on and connected to the Internet
    # A QR code is valid only for 45 seconds. Message sennding will be available right after authorization."""
    #         else:
    #             # print('44444')
    #             # ERROR GET QR
    #             self.qr_scan = False
    #             self.status = 'init'
    #             self.hint = data.get('error')
    #             self.notes = ''

    def load_qr_code(self):
        GreenApi = self.greenapi()
        GreenApi.auth()
        for was in self:
            qr_code = GreenApi.get_instance_qr_code().get('message')
            was.qr_scan = qr_code

    def instance_logout(self):
        GreenApi = self.greenapi()
        GreenApi.auth()
        for was in self:
            logout_status = GreenApi.instance_logout().get('isLogout')
            if logout_status:
                was.qr_scan = ""
                was.whatsapp_number = ""
                was.status = "notAuthorized"

    def instance_send_text_message(self, data):
        GreenApi = self.greenapi()
        GreenApi.auth()
        return GreenApi.send_message_text(data)

    def instance_send_file_message(self, file, data):
        GreenApi = self.greenapi()
        GreenApi.auth()
        return GreenApi.send_message_file(data, file)

    @api.model
    def _send_whatsapp(self, numbers, message):
        """ Send whatsapp """
        GreenApi = self.greenapi()
        GreenApi.auth()
        new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
        for number in numbers:
            whatsapp = self._formatting_mobile_number(number)
            message_data = {
                'phone': whatsapp,
                'body': html2text.html2text(message),
            }
            data_message = json.dumps(message_data)
            send_message = GreenApi.post_request(method='sendMessage', data=data_message)
            if send_message.get('message')['sent']:
                _logger.warning('Success to send Message to WhatsApp number %s', whatsapp)
            else:
                _logger.warning('Failed to send Message to WhatsApp number %s', whatsapp)
            new_cr.commit()
        return True
