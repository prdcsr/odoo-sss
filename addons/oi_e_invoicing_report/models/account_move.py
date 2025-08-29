import datetime
import base64
from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    invoice_qr_code = fields.Text(compute="_get_qr_text", store=False)

    @api.model    
    def _get_hex(self, tag, value):
        to_hex = lambda i : '%02x' % i
        value = value.encode('utf8')
        
        res = to_hex(int(tag)) + to_hex(len(value))
        for t in value:
            res += to_hex(t)
        return res       

    @api.onchange('company_id', 'amount_tax', 'amount_total')
    def _get_qr_text(self):
        for record in self:
            vendor_name = ""
            vat = ""
            date = ""
            
            #if record.company_id.x_parent_company_id:
            #    vendor_name = str(record.company_id.x_parent_company_id.name)
            #else:
            vendor_name = str(record.company_id.name)+'-'+str(record.partner_id.name)+'-'+str(record.name)
                
            vendor_name_hex = self._get_hex("01",vendor_name)
            
            if record.company_id.vat:
                vat = str(record.company_id.vat)
            else:
                vat = " "
            vat_hex = self._get_hex("02",vat) 
            
            #if record.x_issue_date:
            #    date = str(record.x_issue_date.strftime("%m-%d-%YT%H:%M:%S"))
            #elif record.create_date and not record.x_issue_date:
            date = str(record.create_date.strftime("%m-%d-%YT%H:%M:%S"))
            #else:
            #   date = " "
            date_hex = self._get_hex("03",date)
            
            total_amount = str(record.currency_id._convert(record.amount_total, self.env.ref("base.SAR"), record.company_id, datetime.date.today()))
            total_amount_hex = self._get_hex("04",total_amount)
            
            tax_amount = str(record.currency_id._convert(record.amount_tax, self.env.ref("base.SAR"), record.company_id, datetime.date.today()))
            tax_amount_hex = self._get_hex("05",tax_amount)     
                   
            #qr_val = vendor_name_hex + vat_hex + date_hex + total_amount_hex + tax_amount_hex
            #encoded_base64_bytes = base64.b64encode(bytes.fromhex(qr_val)).decode()
            #record.invoice_qr_code = encoded_base64_bytes
            record.invoice_qr_code = vendor_name