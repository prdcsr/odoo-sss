# See LICENSE file for full copyright and licensing details.

import ast
import base64
from odoo import fields, models, _, sql_db, api
from odoo.tools.mimetypes import guess_mimetype
from odoo.exceptions import Warning, UserError
import datetime
import html2text
import threading
import requests
import json
import logging
import os
import pdfkit
import uuid

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = 'mail.message'

    message_type = fields.Selection(selection_add=[('whatsapp', 'Whatsapp')])
    whatsapp_server_id = fields.Many2one('ir.green_whatsapp_server', string='Whatsapp Server')
    whatsapp_method = fields.Char('Method', default='sendMessage')
    whatsapp_status = fields.Selection([('pending', 'Pending'), ('send', 'Sent'), ('error', 'Error')],
                                       default='pending', string='Status')
    whatsapp_response = fields.Text('Response', readonly=True)
    whatsapp_data = fields.Text('Data', readonly=False)
    whatsapp_chat_id = fields.Char(string='ChatId')

    def _prepare_mail_message(self, author_id, chat_id, record, model, body, data, subject, partner_ids, attachment_ids,
                              response, status, method='sendMessage'):
        # MailMessage = self.env['mail.message']
        # for active_id in active_ids:
        values = {
            'author_id': author_id,
            'model': model or 'res.partner',
            'res_id': record,  # model and self.ids[0] or False,
            'body': body,
            'whatsapp_data': data,
            'subject': subject or False,
            'message_type': 'whatsapp',
            'record_name': subject,
            'partner_ids': [(4, pid) for pid in partner_ids],
            'attachment_ids': attachment_ids and [(6, 0, attachment_ids.ids)],
            'whatsapp_method': method,
            'whatsapp_chat_id': chat_id,
            'whatsapp_response': response,
            'whatsapp_status': status,
        }
        # print ('---_prepare_mail_message---',values)
        # MailMessage += MailMessage.sudo().create(values)
        return values  # MailMessage.sudo().create(values)

    @api.model
    def _resend_whatsapp_message_resend(self, GreenApi):
        try:
            new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
            uid, context = self.env.uid, self.env.context
            with api.Environment.manage():
                self.env = api.Environment(new_cr, uid, context)
                MailMessage = self.env['mail.message'].search(
                    [('message_type', '=', 'whatsapp'), ('whatsapp_status', '=', 'pending')], limit=50)
                get_version = self.env["ir.module.module"].sudo().search([('name', '=', 'base')],
                                                                         limit=1).latest_version
                for mail in MailMessage:
                    data = json.loads(str(mail.whatsapp_data.replace("'", '"')))
                    message_data = {
                        'chatId': mail.whatsapp_chat_id,
                        'body': html2text.html2text(mail.body),
                        'phone': data['phone'],
                        'origin': data['origin'],
                        'link': data['link'],
                        'get_version': get_version,
                    }
                    if mail.whatsapp_method == 'sendFile' and mail.attachment_ids:
                        attach = [att for att in mail.attachment_ids][0]  # .datas
                        mimetype = guess_mimetype(base64.b64decode(attach.datas))
                        if mimetype == 'application/octet-stream':
                            mimetype = 'video/mp4'
                        str_mimetype = 'data:' + mimetype + ';base64,'
                        attachment = str_mimetype + str(attach.datas.decode("utf-8"))
                        message_data.update(
                            {'body': attachment, 'filename': [att for att in mail.attachment_ids][0].name})
                    data_message = json.dumps(message_data)
                    send_message = GreenApi.post_request(method=mail.whatsapp_method, data=data_message)
                    # print ('====',send_message)
                    if send_message.get('message')['sent']:
                        mail.whatsapp_status = 'send'
                        mail.whatsapp_response = send_message
                        _logger.warning('Success send Message to WhatsApp number %s', data['phone'])
                    else:
                        mail.whatsapp_status = 'error'
                        mail.whatsapp_response = send_message
                        _logger.warning('Failed send Message to WhatsApp number %s', data['phone'])
                    new_cr.commit()
        finally:
            self.env.cr.close()

    @api.model
    def resend_whatsapp_mail_message(self):
        """Resend whatsapp error message via threding."""
        WhatsappServer = self.env['ir.green_whatsapp_server']
        whatsapp_ids = WhatsappServer.search([('status', '=', 'authenticated')])
        # if len(whatsapp_ids) == 1:
        for wserver in whatsapp_ids.filtered(lambda ws: not ast.literal_eval(str(ws.message_response))['block']):
            # company_id = self.env.user.company_id
            if wserver.status != 'authenticated':
                _logger.warning('Whatsapp Authentication Failed!\nConfigure Whatsapp Configuration in General Setting.')
            GreenApi = wserver.greenapi()
            GreenApi.auth()
            thread_start = threading.Thread(target=self._resend_whatsapp_message_resend(GreenApi))
            thread_start.start()
        return True

    def pdf_to_byte_array(self, pdf_path):
        """
        This function takes a path to a PDF file and returns its contents as a byte array.

        Parameters:
        pdf_path (str): The path to the PDF file

        Returns:
        bytes: The contents of the PDF file as a byte array
        """
        try:
            # Open the PDF file in binary mode
            with open(pdf_path, "rb") as f:
                # Read the contents of the file into memory
                encoded = base64.b64encode(f.read())
                return base64.b64decode(encoded)
        except Exception as e:
            # Log the error
            print(f"Error: {e}")
            return None

    @api.model
    def send_invoice_message_action(self, GreenApi, operating_unit_id):
        try:
            base_path = '/var/lib/odoo/.local/share/Odoo/filestore'  # production
            # base_path = 'D:\green_api_whatsapp'

            new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
            uid, context = self.env.uid, self.env.context
            with (api.Environment.manage()):
                self.env = api.Environment(new_cr, uid, context)
                MailMessage = self.env['mail.message']
                # customer = self.env['res.partner'].search([('is_company', '=', True)]) # Development
                customer = self.env['res.partner'].search(['&', ('is_company','=', True), ('ref', '!=', False)])  # Production
                today = datetime.date.today()
                t_test = 0

                if customer:
                    for cust in customer:
                        # development
                        # if cust.whatsapp and cust.whatsapp != '0' and '000000' not in cust.whatsapp and cust.company_type == 'company':
                        # production
                        if cust.whatsapp and cust.whatsapp != '0' and '000000' not in cust.whatsapp and cust.company_type == 'company' and (cust.ref[
                                                                                                                                           :2] == 'CU' or cust.ref[:2] == 'CT') and cust.id != 583 and cust.id != 653 and cust.id != 670 and cust.id != 1050 and cust.id != 587 and cust.id != 714:

                            data = {
                                "wizard_id": cust.id,
                                "date_at": today.strftime("%Y-%m-%d"),
                                "date_from": False,
                                "only_posted_moves": True,
                                "hide_account_at_0": True,
                                "foreign_currency": True,
                                "show_partner_details": True,
                                "company_id": 1,
                                "target_move": 'posted',
                                # "account_ids": [33, 6],  # change with receivable accounts' id, development
                                "account_ids": [11, 710],  # change with receivable accounts' id, production
                                "partner_ids": [cust.id],
                                "account_financial_report_lang": cust.lang,
                            }
                            res_data = self.env["report.account_financial_report.open_items"]._get_report_values(cust,
                                                                                                                 data)
                            Open_items = res_data["Open_Items"]
                            accounts_data = res_data["accounts_data"]
                            show_partner_details = res_data["show_partner_details"]

                            mail_content = "Dear " + str(cust.name) + '-' + str(
                                cust.city) + ',' + '\n\nDengan Hormat \n\n' + \
                                           "Dengan ini kami perincikan nota pembelian Bapak/Ibu sebagai berikut: \n" + \
                                           "\nUntuk pembayaran tersebut diatas kami mohon dapat ditransfer ke rekening kami : " + \
                                           "\nBCA            : 702-0310868 " + \
                                           "\nMandiri      : 155-00-9873660-9" + \
                                           "\nDanamon   : 0088-000-70156" + \
                                           "\nBRI             : 0399-01-000365-30-6" + \
                                           "\nAtas Nama : PT. SAMA SAMA SUKSES" + \
                                           "\n\nTangerang, " + str(today.strftime("%d-%b-%y")) + \
                                           "\nHormat Kami " + \
                                           "\n\n\nPT. SAMA SAMA SUKSES"

                            table = "<!DOCTYPE html><html><body style='display:flex; flex-direction: row; justify-content: center; border-spacing:5px;'>" + \
                                    "PT SAMA SAMA SUKSES <br\><br\>" + \
                                    "<table style='color: black; border-color: black; background-color:white; border: 2px solid black;'>" + \
                                    "<thead><tr>" + \
                                    "<th style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>Faktur NO</strong></th>" + \
                                    "<th style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>Customer</strong></th>" + \
                                    "<th style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>Tanggal Faktur</strong></th>" + \
                                    "<th style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>Tanggal Jatuh Tempo</strong></th>" + \
                                    "<th style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>Jumlah</strong></th>" + \
                                    "<th style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>Keterangan</strong></th>" + "</tr></thead><tbody>"

                            next_month = today.replace(day=28) + datetime.timedelta(days=4)
                            next_month = next_month.replace(day=28) + datetime.timedelta(days=4)
                            next_month = next_month.replace(day=28) + datetime.timedelta(days=4)
                            res = next_month - datetime.timedelta(days=next_month.day)
                            t_jumlah = 0
                            t_acc_count = 0
                            t_cust_count = 0
                            t_cust = 0
                            t_acc = 0
                            check_cust = False
                            check_acc = False
                            curr_month = today.month
                            txt_warn = ""
                            # GreenApi = False

                            for account_id in Open_items.keys():
                                if t_cust > 0 and t_cust_count > 0:
                                    due_check = curr_month - check_cust
                                    """if due_check >= 2:
                                        txt_warn = "Jatuh Tempo"
                                    else:
                                        txt_warn = "Pengingat" """

                                    table = table + "<tr bgcolor='grey' style='padding:3px;'><td colspan='4' style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>SubTotal " + "</strong></td>"
                                    table = table + "<td style='border: 1px solid black;border-collapse: collapse;text-align:right;padding:3px;'><strong>Rp " + "{:,.2f}".format(
                                        t_cust) + "</strong></td>"
                                    table = table + "<td style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>" + txt_warn + "</strong></td></tr>"

                                if check_acc and t_acc > 0:
                                    table = table + "<tr bgcolor='grey' style='padding:3px;'><td colspan='4' style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>SubTotal " + \
                                            accounts_data[check_acc]["name"] + "</strong></td>"
                                    table = table + "<td style='border: 1px solid black;border-collapse: collapse;text-align:right;padding:3px;'><strong>Rp " + "{:,.2f}".format(
                                        t_acc) + "</strong></td></tr>"

                                    t_cust = 0
                                    t_acc = 0
                                    check_cust = False
                                    t_acc_count += 1
                                    t_cust_count = 0

                                else:
                                    check_acc = account_id

                                if Open_items[account_id]:
                                    if show_partner_details:
                                        for partner_id in Open_items[account_id]:
                                            for line in Open_items[account_id][partner_id]:
                                                move = self.env['account.move'].search(
                                                    [('id', '=', line['move_id'][0]),
                                                     ('operating_unit_id', '=', operating_unit_id)])
                                                # for wserver in whatsapp_servers:
                                                #     if wserver.operating_unit_id == move.operating_unit_id:
                                                #         GreenApi = wserver.greenapi()

                                                if move.invoice_date_due == False or move.invoice_date_due <= res:
                                                    due_60 = line['date'] + datetime.timedelta(days=60)
                                                    if move.partner_id:
                                                        partner_txt = move.partner_id.name
                                                    else:
                                                        partner_txt = line['partner_name']
                                                    if move.invoice_date_due:
                                                        if move.invoice_date_due < due_60:
                                                            due_txt = move.invoice_date_due.strftime("%d-%b-%y")
                                                        else:
                                                            due_txt = due_60.strftime("%d-%b-%y")
                                                    else:
                                                        due_txt = ""
                                                    if move.invoice_payment_term_id.name == False:
                                                        term_txt = ""
                                                    else:
                                                        term_txt = move.invoice_payment_term_id.name
                                                    if move.journal_id.type == 'sale':
                                                        name_txt = line['move_name']
                                                    else:
                                                        name_txt = accounts_data[account_id]["name"]
                                                    if check_cust and check_cust != line['date'].month:
                                                        due_check = curr_month - check_cust
                                                        """if due_check >= 2:
                                                            txt_warn = "Jatuh Tempo"
                                                        else:
                                                            txt_warn = "Pengingat" """

                                                        table = table + "<tr bgcolor='grey' style='padding:3px;'><td colspan='4' style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>SubTotal </strong></td>"
                                                        table = table + "<td style='border: 1px solid black;border-collapse: collapse;text-align:right;padding:3px;'><strong>Rp " + "{:,.2f}".format(
                                                            t_cust) + "</strong></td>"

                                                        table = table + "<td style='border: 1px solid black;border-collapse: collapse;'><strong>" + txt_warn + "</strong></td></tr>"

                                                        t_cust = 0
                                                        check_cust = line['date'].month
                                                        t_cust_count += 1
                                                    else:
                                                        if move.journal_id.type == 'sale':
                                                            check_cust = line['date'].month

                                                    table_det = "<tr>"
                                                    table_det = table_det + "<td style='border: 1px solid black;border-collapse: collapse;padding:3px;'>" + name_txt + "</td>"
                                                    table_det = table_det + "<td style='border: 1px solid black;border-collapse: collapse;padding:3px;'>" + partner_txt + "</td>"
                                                    table_det = table_det + "<td style='border: 1px solid black;border-collapse: collapse;text-align:center;padding:3px;'>" + \
                                                                line['date'].strftime("%d-%b-%y") + "</td>"
                                                    table_det = table_det + "<td style='border: 1px solid black;border-collapse: collapse;text-align:center;padding:3px;'>" + due_txt + "</td>"
                                                    table_det = table_det + "<td style='border: 1px solid black;border-collapse: collapse;text-align:right;padding:3px;'>Rp " + "{:,.2f}".format(
                                                        line['amount_residual']) + "</td>"
                                                    if move.invoice_payment_term_id.id == 92:
                                                        table_det = table_det + "<td style='border: 1px solid black;border-collapse: collapse;text-align:center;padding:3px;'/>"
                                                    else:
                                                        table_det = table_det + "<td style='border: 1px solid black;border-collapse: collapse;text-align:center;padding:3px;'>" + term_txt + "</td>"
                                                    table_det = table_det + "</tr>"

                                                    t_jumlah += line['amount_residual']
                                                    t_cust += line['amount_residual']
                                                    t_acc += line['amount_residual']

                                                    table = table + table_det

                            if t_cust > 0 and t_cust_count > 0:
                                due_check = curr_month - check_cust
                                """if due_check >= 2:
                                    txt_warn = 'Jatuh Tempo'
                                else:
                                    txt_warn = 'Pengingat' """

                                table = table + "<tr bgcolor='grey' style='padding:3px;'><td colspan='4' style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>SubTotal " + "</strong></td>"
                                table = table + "<td style='border: 1px solid black;border-collapse: collapse;text-align:right;padding:3px;'><strong>Rp " + "{:,.2f}".format(
                                    t_cust) + "</strong></td>"
                                table = table + "<td style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>" + txt_warn + "</strong></td></tr>"

                            if t_acc > 0 and t_acc_count > 0:
                                table = table + "<tr bgcolor='grey' style='padding:3px;'><td colspan='4' style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>SubTotal " + \
                                        accounts_data[account_id]["name"] + "</strong></td>"
                                table = table + "<td style='border: 1px solid black;border-collapse: collapse;text-align:right;padding:3px;'><strong>Rp " + "{:,.2f}".format(
                                    t_acc) + "</strong></td></tr>"

                            table = table + "<tr bgcolor='orange' style='padding:3px;'><td colspan='4' style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>Total</strong></td>"
                            table = table + "<td style='border: 1px solid black;border-collapse: collapse;text-align:right;padding:3px;'><strong>Rp" + "{:,.2f}".format(
                                t_jumlah) + "</strong></td></tr>"
                            table = table + "</tbody></table>"
                            table = table + '</body></html>'

                            if t_jumlah > 0:
                                t_test += 1

                                whatsapp = cust.whatsapp
                                sales_whatsapp = '00000000'
                                if cust.user_id:
                                    sales_whatsapp = cust.user_id.whatsapp

                                try:
                                    filename = 'invoice-' + cust.name + '-' + str(uuid.uuid4()) + '.pdf'
                                    # pdfkit.from_string(table, base_path + filename)
                                    # decoded_file = self.pdf_to_byte_array(filename)

                                    # Production
                                    _logger.info('Path ' + base_path + " : " + str(os.path.exists(base_path)))
                                    pdfkit.from_string(table, base_path + '/' + filename)
                                    decoded_file = self.pdf_to_byte_array(base_path + '/' + filename)

                                    attachment = self.env['ir.attachment'].create({
                                        'name': filename,
                                        'type': 'binary',
                                        'res_id': cust.ids[0],
                                        'res_model': 'res.partner',
                                        'datas': base64.b64encode(decoded_file),
                                        'mimetype': 'image/png',
                                        # 'datas_fname': filename
                                    })

                                    if whatsapp and whatsapp != '0' and '000000' not in whatsapp:

                                        green_api_post = {
                                            "chatId": whatsapp + '@c.us',
                                            'caption': mail_content,
                                            'fileName': filename,
                                        }

                                        res = GreenApi.send_message_file(data=green_api_post,
                                                                         files={'file': decoded_file})
                                        chatID = cust.chat_id if cust.chat_id else whatsapp
                                        send_attach = {}

                                        if res.get('idMessage'):
                                            status = 'send'
                                            # partner.chat_id = chatID
                                            chatID = res.get('idMessage')
                                            send_attach.update(res)
                                            _logger.warning('Success to send Message to WhatsApp number %s',
                                                            whatsapp)
                                        else:
                                            status = 'error'
                                            send_attach.update(res)
                                            _logger.warning('Failed to send Message to WhatsApp number %s',
                                                            whatsapp)

                                        vals = self._prepare_mail_message(self.env.user.partner_id.id, chatID,
                                                                          '', 'account.move', '',
                                                                          green_api_post, 'Invoice Outstanding',
                                                                          [cust.id],
                                                                          attachment, send_attach, status,
                                                                          'sendFile')
                                        MailMessage.sudo().create(vals)
                                        new_cr.commit()

                                        if sales_whatsapp and sales_whatsapp != '0' and '000000' not in sales_whatsapp:
                                            green_api_post = {
                                                "chatId": sales_whatsapp + '@c.us',
                                                'caption': mail_content,
                                                'fileName': filename,
                                            }

                                            res = GreenApi.send_message_file(data=green_api_post,
                                                                             files={'file': decoded_file})
                                            chatID = cust.chat_id if cust.chat_id else sales_whatsapp
                                            send_attach = {}

                                            if res.get('idMessage'):
                                                status = 'send'
                                                # partner.chat_id = chatID
                                                chatID = res.get('idMessage')
                                                send_attach.update(res)
                                                _logger.warning('Success to send Message to WhatsApp number %s',
                                                                sales_whatsapp)
                                            else:
                                                status = 'error'
                                                send_attach.update(res)
                                                _logger.warning('Failed to send Message to WhatsApp number %s',
                                                                sales_whatsapp)

                                            vals = self._prepare_mail_message(self.env.user.partner_id.id, chatID,
                                                                              '', 'account.move', '',
                                                                              green_api_post,
                                                                              'Invoice Outstanding WA cc Sales',
                                                                              [cust.id],
                                                                              attachment, send_attach, status,
                                                                              'sendFile')
                                            MailMessage.sudo().create(vals)
                                            new_cr.commit()

                                        os.remove(base_path + "/" + filename)  # Production
                                        # os.remove('D:/green_api_whatsapp/' + filename) # Development
                                    else:
                                        vals = self._prepare_mail_message(self.env.user.partner_id.id, '', '',
                                                                          'account.move', '', {}, 'Invoice Outstanding',
                                                                          [cust.id],
                                                                          attachment, {
                                                                              'Warning': 'Customer ' + cust.name + ' belum melakukan setup nomor whatsapp'},
                                                                          'pending', 'sendFile')
                                        MailMessage.sudo().create(vals)
                                        new_cr.commit()
                                except Exception as e:
                                    raise UserError(str(e))

        finally:
            self.env.cr.close()

    @api.model
    def send_whatsapp_bulk(self):
        WhatsappServer = self.env['ir.green_whatsapp_server']
        whatsapp_ids = WhatsappServer.sudo().search(
            [('status', '=', 'authorized'), ('whatsapp_action', '=', 'invoice_paid'), ('operating_unit_id', '=', 1)])
        for wserver in whatsapp_ids:
            # for wserver in whatsapp_ids.filtered(lambda ws: ast.literal_eval(str(ws.message_response))['limit_qty'] >= int(ws.message_counts)):
            if wserver.status != 'authorized':
                _logger.warning('Whatsapp Authentication Failed!\nConfigure Whatsapp Configuration in General Setting.')
            GreenApi = wserver.greenapi()
            GreenApi.auth()
            thread_start = threading.Thread(target=self.send_invoice_message_action(GreenApi, 1))
            thread_start.start()

            break
        return True

    @api.model
    def send_invoice_message_action_sparepart(self, GreenApi, operating_unit_id):
        try:
            base_path = '/var/lib/odoo/.local/share/Odoo/filestore'  # production
            # base_path = 'D:\green_api_whatsapp'

            new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
            uid, context = self.env.uid, self.env.context
            with (api.Environment.manage()):
                self.env = api.Environment(new_cr, uid, context)
                MailMessage = self.env['mail.message']
                # customer = self.env['res.partner'].search([('is_company', '=', True)]) # Development
                customer = self.env['res.partner'].search([('company_type', '=', 'company')])  # Production
                today = datetime.date.today()
                t_test = 0

                if customer:
                    for cust in customer:
                        # development
                        # if cust.whatsapp and cust.whatsapp != '0' and '000000' not in cust.whatsapp and cust.company_type == 'company':
                        # production
                        if cust.whatsapp and cust.whatsapp != '0' and '000000' not in cust.whatsapp and cust.company_type == 'company' and cust.display_name[
                                                                                                                                           :2] == 'CS':

                            data = {
                                "wizard_id": cust.id,
                                "date_at": today.strftime("%Y-%m-%d"),
                                "date_from": False,
                                "only_posted_moves": True,
                                "hide_account_at_0": True,
                                "foreign_currency": True,
                                "show_partner_details": True,
                                "company_id": 1,
                                "target_move": 'posted',
                                # "account_ids": [33, 6],  # change with receivable accounts' id, development
                                "account_ids": [11, 710],  # change with receivable accounts' id, production
                                "partner_ids": [cust.id],
                                "account_financial_report_lang": cust.lang,
                            }
                            res_data = self.env["report.account_financial_report.open_items"]._get_report_values(cust,
                                                                                                                 data)
                            Open_items = res_data["Open_Items"]
                            accounts_data = res_data["accounts_data"]
                            show_partner_details = res_data["show_partner_details"]

                            mail_content = "Dear " + str(cust.name) + '-' + str(
                                cust.city) + ',' + '\n\nDengan Hormat \n\n' + \
                                           "Dengan ini kami perincikan nota pembelian Bapak/Ibu sebagai berikut: \n" + \
                                           "\nUntuk pembayaran tersebut diatas kami mohon dapat ditransfer ke rekening kami : " + \
                                           "\nBCA            : 702-0656888 " + \
                                           "\nAtas Nama : PT. SAMA SAMA SUKSES" + \
                                           "\n\nTangerang, " + str(today.strftime("%d-%b-%y")) + \
                                           "\nHormat Kami " + \
                                           "\n\n\nPT. SAMA SAMA SUKSES"

                            table = "<!DOCTYPE html><html><body style='display:flex; flex-direction: row; justify-content: center; border-spacing:5px;'>" + \
                                    "PT SAMA SAMA SUKSES <br\><br\>" + \
                                    "<table style='color: black; border-color: black; background-color:white; border: 2px solid black;'>" + \
                                    "<thead><tr>" + \
                                    "<th style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>Faktur NO</strong></th>" + \
                                    "<th style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>Customer</strong></th>" + \
                                    "<th style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>Tanggal Faktur</strong></th>" + \
                                    "<th style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>Tanggal Jatuh Tempo</strong></th>" + \
                                    "<th style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>Jumlah</strong></th>" + \
                                    "<th style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>Keterangan</strong></th>" + "</tr></thead><tbody>"

                            next_month = today.replace(day=28) + datetime.timedelta(days=4)
                            next_month = next_month.replace(day=28) + datetime.timedelta(days=4)
                            next_month = next_month.replace(day=28) + datetime.timedelta(days=4)
                            res = next_month - datetime.timedelta(days=next_month.day)
                            t_jumlah = 0
                            t_acc_count = 0
                            t_cust_count = 0
                            t_cust = 0
                            t_acc = 0
                            check_cust = False
                            check_acc = False
                            curr_month = today.month
                            txt_warn = ""
                            # GreenApi = False

                            for account_id in Open_items.keys():
                                if t_cust > 0 and t_cust_count > 0:
                                    due_check = curr_month - check_cust
                                    """if due_check >= 2:
                                        txt_warn = "Jatuh Tempo"
                                    else:
                                        txt_warn = "Pengingat" """

                                    table = table + "<tr bgcolor='grey' style='padding:3px;'><td colspan='4' style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>SubTotal " + "</strong></td>"
                                    table = table + "<td style='border: 1px solid black;border-collapse: collapse;text-align:right;padding:3px;'><strong>Rp " + "{:,.2f}".format(
                                        t_cust) + "</strong></td>"
                                    table = table + "<td style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>" + txt_warn + "</strong></td></tr>"

                                if check_acc and t_acc > 0:
                                    table = table + "<tr bgcolor='grey' style='padding:3px;'><td colspan='4' style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>SubTotal " + \
                                            accounts_data[check_acc]["name"] + "</strong></td>"
                                    table = table + "<td style='border: 1px solid black;border-collapse: collapse;text-align:right;padding:3px;'><strong>Rp " + "{:,.2f}".format(
                                        t_acc) + "</strong></td></tr>"

                                    t_cust = 0
                                    t_acc = 0
                                    check_cust = False
                                    t_acc_count += 1
                                    t_cust_count = 0

                                else:
                                    check_acc = account_id

                                if Open_items[account_id]:
                                    if show_partner_details:
                                        for partner_id in Open_items[account_id]:
                                            for line in Open_items[account_id][partner_id]:
                                                move = self.env['account.move'].search(
                                                    [('id', '=', line['move_id'][0]),
                                                     ('operating_unit_id', '=', operating_unit_id)])
                                                # for wserver in whatsapp_servers:
                                                #     if wserver.operating_unit_id == move.operating_unit_id:
                                                #         GreenApi = wserver.greenapi()

                                                if move.invoice_date_due == False or move.invoice_date_due <= res:
                                                    due_60 = line['date'] + datetime.timedelta(days=60)
                                                    if move.partner_id:
                                                        partner_txt = move.partner_id.name
                                                    else:
                                                        partner_txt = line['partner_name']
                                                    if move.invoice_date_due:
                                                        if move.invoice_date_due < due_60:
                                                            due_txt = move.invoice_date_due.strftime("%d-%b-%y")
                                                        else:
                                                            due_txt = due_60.strftime("%d-%b-%y")
                                                    else:
                                                        due_txt = ""
                                                    if move.invoice_payment_term_id.name == False:
                                                        term_txt = ""
                                                    else:
                                                        term_txt = move.invoice_payment_term_id.name
                                                    if move.journal_id.type == 'sale':
                                                        name_txt = line['move_name']
                                                    else:
                                                        name_txt = accounts_data[account_id]["name"]
                                                    if check_cust and check_cust != line['date'].month:
                                                        due_check = curr_month - check_cust
                                                        """if due_check >= 2:
                                                            txt_warn = "Jatuh Tempo"
                                                        else:
                                                            txt_warn = "Pengingat" """

                                                        table = table + "<tr bgcolor='grey' style='padding:3px;'><td colspan='4' style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>SubTotal </strong></td>"
                                                        table = table + "<td style='border: 1px solid black;border-collapse: collapse;text-align:right;padding:3px;'><strong>Rp " + "{:,.2f}".format(
                                                            t_cust) + "</strong></td>"

                                                        table = table + "<td style='border: 1px solid black;border-collapse: collapse;'><strong>" + txt_warn + "</strong></td></tr>"

                                                        t_cust = 0
                                                        check_cust = line['date'].month
                                                        t_cust_count += 1
                                                    else:
                                                        if move.journal_id.type == 'sale':
                                                            check_cust = line['date'].month

                                                    table_det = "<tr>"
                                                    table_det = table_det + "<td style='border: 1px solid black;border-collapse: collapse;padding:3px;'>" + name_txt + "</td>"
                                                    table_det = table_det + "<td style='border: 1px solid black;border-collapse: collapse;padding:3px;'>" + partner_txt + "</td>"
                                                    table_det = table_det + "<td style='border: 1px solid black;border-collapse: collapse;text-align:center;padding:3px;'>" + \
                                                                line['date'].strftime("%d-%b-%y") + "</td>"
                                                    table_det = table_det + "<td style='border: 1px solid black;border-collapse: collapse;text-align:center;padding:3px;'>" + due_txt + "</td>"
                                                    table_det = table_det + "<td style='border: 1px solid black;border-collapse: collapse;text-align:right;padding:3px;'>Rp " + "{:,.2f}".format(
                                                        line['amount_residual']) + "</td>"
                                                    if move.invoice_payment_term_id.id == 92:
                                                        table_det = table_det + "<td style='border: 1px solid black;border-collapse: collapse;text-align:center;padding:3px;'/>"
                                                    else:
                                                        table_det = table_det + "<td style='border: 1px solid black;border-collapse: collapse;text-align:center;padding:3px;'>" + term_txt + "</td>"
                                                    table_det = table_det + "</tr>"

                                                    t_jumlah += line['amount_residual']
                                                    t_cust += line['amount_residual']
                                                    t_acc += line['amount_residual']

                                                    table = table + table_det

                            if t_cust > 0 and t_cust_count > 0:
                                due_check = curr_month - check_cust
                                """if due_check >= 2:
                                    txt_warn = 'Jatuh Tempo'
                                else:
                                    txt_warn = 'Pengingat' """

                                table = table + "<tr bgcolor='grey' style='padding:3px;'><td colspan='4' style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>SubTotal " + "</strong></td>"
                                table = table + "<td style='border: 1px solid black;border-collapse: collapse;text-align:right;padding:3px;'><strong>Rp " + "{:,.2f}".format(
                                    t_cust) + "</strong></td>"
                                table = table + "<td style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>" + txt_warn + "</strong></td></tr>"

                            if t_acc > 0 and t_acc_count > 0:
                                table = table + "<tr bgcolor='grey' style='padding:3px;'><td colspan='4' style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>SubTotal " + \
                                        accounts_data[account_id]["name"] + "</strong></td>"
                                table = table + "<td style='border: 1px solid black;border-collapse: collapse;text-align:right;padding:3px;'><strong>Rp " + "{:,.2f}".format(
                                    t_acc) + "</strong></td></tr>"

                            table = table + "<tr bgcolor='orange' style='padding:3px;'><td colspan='4' style='border: 1px solid black;border-collapse: collapse;padding:3px;'><strong>Total</strong></td>"
                            table = table + "<td style='border: 1px solid black;border-collapse: collapse;text-align:right;padding:3px;'><strong>Rp" + "{:,.2f}".format(
                                t_jumlah) + "</strong></td></tr>"
                            table = table + "</tbody></table>"
                            table = table + '</body></html>'

                            if t_jumlah > 0:
                                t_test += 1

                                whatsapp = cust.whatsapp
                                sales_whatsapp = '00000000'
                                if cust.user_id:
                                    sales_whatsapp = cust.user_id.whatsapp

                                try:
                                    filename = 'invoice-' + cust.name + '-' + str(uuid.uuid4()) + '.pdf'
                                    # pdfkit.from_string(table, base_path + filename)
                                    # decoded_file = self.pdf_to_byte_array(filename)

                                    # Production
                                    _logger.info('Path ' + base_path + " : " + str(os.path.exists(base_path)))
                                    pdfkit.from_string(table, base_path + '/' + filename)
                                    decoded_file = self.pdf_to_byte_array(base_path + '/' + filename)

                                    attachment = self.env['ir.attachment'].create({
                                        'name': filename,
                                        'type': 'binary',
                                        'res_id': cust.ids[0],
                                        'res_model': 'res.partner',
                                        'datas': base64.b64encode(decoded_file),
                                        'mimetype': 'image/png',
                                        # 'datas_fname': filename
                                    })

                                    if whatsapp and whatsapp != '0' and '000000' not in whatsapp:

                                        # green_api_post = {
                                        #     "chatId": whatsapp + '@c.us',
                                        #     'caption': mail_content,
                                        #     'fileName': filename,
                                        # }
                                        #
                                        # res = GreenApi.send_message_file(data=green_api_post,
                                        #                                  files={'file': decoded_file})
                                        # chatID = cust.chat_id if cust.chat_id else whatsapp
                                        # send_attach = {}
                                        #
                                        # if res.get('idMessage'):
                                        #     status = 'send'
                                        #     # partner.chat_id = chatID
                                        #     chatID = res.get('idMessage')
                                        #     send_attach.update(res)
                                        #     _logger.warning('Success to send Message to WhatsApp number %s',
                                        #                     whatsapp)
                                        # else:
                                        #     status = 'error'
                                        #     send_attach.update(res)
                                        #     _logger.warning('Failed to send Message to WhatsApp number %s',
                                        #                     whatsapp)
                                        #
                                        # vals = self._prepare_mail_message(self.env.user.partner_id.id, chatID,
                                        #                                   '', 'account.move', '',
                                        #                                   green_api_post, 'Invoice Outstanding',
                                        #                                   [cust.id],
                                        #                                   attachment, send_attach, status,
                                        #                                   'sendFile')
                                        # MailMessage.sudo().create(vals)
                                        # new_cr.commit()

                                        if sales_whatsapp and sales_whatsapp != '0' and '000000' not in sales_whatsapp:
                                            green_api_post = {
                                                "chatId": sales_whatsapp + '@c.us',
                                                'caption': mail_content,
                                                'fileName': filename,
                                            }

                                            res = GreenApi.send_message_file(data=green_api_post,
                                                                             files={'file': decoded_file})
                                            chatID = cust.chat_id if cust.chat_id else sales_whatsapp
                                            send_attach = {}

                                            if res.get('idMessage'):
                                                status = 'send'
                                                # partner.chat_id = chatID
                                                chatID = res.get('idMessage')
                                                send_attach.update(res)
                                                _logger.warning('Success to send Message to WhatsApp number %s',
                                                                sales_whatsapp)
                                            else:
                                                status = 'error'
                                                send_attach.update(res)
                                                _logger.warning('Failed to send Message to WhatsApp number %s',
                                                                sales_whatsapp)

                                            vals = self._prepare_mail_message(self.env.user.partner_id.id, chatID,
                                                                              '', 'account.move', '',
                                                                              green_api_post,
                                                                              'Invoice Outstanding WA cc Sales',
                                                                              [cust.id],
                                                                              attachment, send_attach, status,
                                                                              'sendFile')
                                            MailMessage.sudo().create(vals)
                                            new_cr.commit()

                                        os.remove(base_path + "/" + filename)  # Production
                                        # os.remove('D:/green_api_whatsapp/' + filename) # Development
                                    else:
                                        vals = self._prepare_mail_message(self.env.user.partner_id.id, '', '',
                                                                          'account.move', '', {}, 'Invoice Outstanding',
                                                                          [cust.id],
                                                                          attachment, {
                                                                              'Warning': 'Customer ' + cust.name + ' belum melakukan setup nomor whatsapp'},
                                                                          'pending', 'sendFile')
                                        MailMessage.sudo().create(vals)
                                        new_cr.commit()
                                except Exception as e:
                                    raise UserError(str(e))

        finally:
            self.env.cr.close()

    @api.model
    def send_whatsapp_bulk_sparepart(self):
        WhatsappServer = self.env['ir.green_whatsapp_server']
        whatsapp_ids = WhatsappServer.sudo().search(
            [('status', '=', 'authorized'), ('whatsapp_action', '=', 'invoice_paid'), ('operating_unit_id', '=', 2)])
        for wserver in whatsapp_ids:
            # for wserver in whatsapp_ids.filtered(lambda ws: ast.literal_eval(str(ws.message_response))['limit_qty'] >= int(ws.message_counts)):
            if wserver.status != 'authorized':
                _logger.warning('Whatsapp Authentication Failed!\nConfigure Whatsapp Configuration in General Setting.')
            GreenApi = wserver.greenapi()
            GreenApi.auth()
            thread_start = threading.Thread(target=self.send_invoice_message_action_sparepart(GreenApi, 2))
            thread_start.start()

            break
        return True
