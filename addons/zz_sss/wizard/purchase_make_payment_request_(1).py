
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from datetime import datetime
import math
# from typing_extensions import Required

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class PurchaseOnPort(models.TransientModel):
    _name = "purchase.onport"
    _description = "Purchase On Port"

    ntpn_no = fields.Char(string='NTPN No',Required=True)
    pib_no = fields.Char(string='PIB No',Required=True)
    pib_date = fields.Date(string="PIB Date",Required=True)

    def button_onport(self):
        Purchase = self.env["purchase.order"]        
        purchases = Purchase.browse(self._context.get("active_ids", []))
        
        for order in purchases:            
            order.pib_no = self.pib_no
            order.pib_date = self.pib_date
            order.state = 'onport'
            domain = [('lpo_num','=',order.id)]
            paymentreq = self.env['payment.request'].search(domain)
            if paymentreq:
                for rec in paymentreq:
                    rec.ntpn_no = self.ntpn_no
                    rec.pib_no = self.pib_no
                    rec.pib_date = self.pib_date


class PurchaseAdvancePaymentInv(models.TransientModel):
    _name = "purchase.payment.request.customs"
    _description = "Purchase Customs Payment Request"

    @api.model
    def default_get(self, fields):    
        active_id = self._context.get("active_id")        
        purchase = self.env["purchase.order"].browse(active_id)
        res = super().default_get(fields)
        # self.lpo_num = purchase.id
        # self.payment_term = purchase.payment_term_id
        res.update({"amount": purchase.amount_total,"currency_id": purchase.currency_id.id})
        #self.amount = purchase.amount_total
        # self.company = purchase.partner_id
        # self.prepared = purchase.user_id
    #    if purchase.state != "purchase":
    #        raise UserError(_("This action is allowed only in Purchase Order sate"))
    #    return super().view_init(fields)
        return res

    # lpo_num = fields.Many2one('purchase.order', string="RFQ",readonly=True)
    currency_id= fields.Many2one('res.currency', 'Currency')
    fp_no = fields.Char(string='AJU No',Required=True)
    ntpn_no = fields.Char(string='NTPN No',readonly=True)
    skb_no = fields.Char(string='SKB No')
    pib_no = fields.Char(string='PIB No',Required=True)
    pib_date = fields.Date(string="PIB Date",Required=True)
    # company = fields.Many2one('res.partner', string="Vendor",readonly=True)
    # payment_term = fields.Many2one('account.payment.term', string="Payment Term",readonly=True)
    amount = fields.Float('Amount')
    amount_exch = fields.Float("Exchange Rate")
    amount_dpp = fields.Float('DPP')
    amount_tax_vat = fields.Float('PPN')
    amount_tax_income = fields.Float('PPH')
    amount_duty = fields.Float("Bea Masuk")
    #prepared = fields.Many2one('res.users', string="Prepared By")

    

    @api.onchange("amount_exch")
    def _onchagne_amount_exch(self):        
        self.amount_dpp = self.amount * self.amount_exch

    @api.onchange("amount_dpp","amount_duty")
    def _onchange_amount_dpp(self):        
        #round up to the nearest 1.000
        #vat = int(math.ceil(((self.amount_dpp + self.amount_duty)  * 0.11)/1000)) * 1000
        vat = round((self.amount_dpp + self.amount_duty)* 0.11,-3) 
        self.amount_tax_vat = float(vat)       
        pph = int(math.ceil(((self.amount_dpp + self.amount_duty) * 0.025)/1000)) * 1000
        self.amount_tax_income = float(pph)
                       

    @api.onchange("amount_tax_vat","amount_tax_income","amount_duty")
    def _onchange_amount_tax(self):
        if not self.skb_no:    
            self.amount_total = self.amount_duty+self.amount_tax_vat + self.amount_tax_income
        else:  
            self.amount_total = self.amount_duty+self.amount_tax_vat
            
    def _create_payment_request(self, order):
        [data] = self.read()
        Invoice = self.env["payment.request"]
        #ir_property_obj = self.env["ir.property"]
        #vat = data.get('amount_tax_vat')
        
        #vat = int(math.ceil(((self.amount_dpp + self.amount_duty)  * 0.11)/1000)) * 1000 
        #self.amount_tax_vat = float(vat) 
        #vat = round((self.amount_dpp + self.amount_duty)* 0.11,-3)
        vat = data.get(amount_tax_vat)
        #vat = float(vat)       
        pph = data.get('amount_tax_income')
        #pph = float(pph)
        
        if not self.skb_no:
            amount_total = self.amount_duty + vat + pph
        else:
            amount_total = self.amount_duty + vat
            
        invoice = Invoice.create(
            {
                "lpo_num" : order.id,
                "fp_no" : self.fp_no,
                "pib_no" : self.pib_no,
                "pib_date" : self.pib_date,
                "skb_no" : self.skb_no,
                "company" : order.partner_id.id,
                "payment_term" : order.payment_term_id.id,
                "currency_id" : order.currency_id.id,
                "amount" : self.amount,
                "amount_exch" : self.amount_exch,
                "amount_dpp" : self.amount_dpp,
                "amount_tax_vat" : vat,
                "amount_tax_income" : pph,
                "amount_duty" : self.amount_duty,
                "amount_total" : amount_total,
                "state" : 'Department Approval',
                'prepared': self.env.user.id,
            }
        )

        invoice.message_post_with_view(
            "mail.message_origin_link",
            values={"self": invoice, "origin": order},
            subtype_id=self.env.ref("mail.mt_note").id,
        )
        return invoice

    def create_payments_request(self):
        Purchase = self.env["purchase.order"]
        # IrDefault = self.env["ir.default"].sudo()
        purchases = Purchase.browse(self._context.get("active_ids", []))
        # Create deposit product if necessary
      
        #PurchaseLine = self.env["purchase.order.line"]
        for order in purchases:
            order.fp_no = self.fp_no
            order.pib_no = self.pib_no
            order.pib_date = self.pib_date
            order.state = "pib"
            self._create_payment_request(order)
        # if self._context.get("open_invoices", False):
            #return purchases.action_view_invoice()
        return {"type": "ir.actions.act_window_close"}

    def _prepare_deposit_product(self):
        return {
            "name": "Purchase Deposit",
            "type": "service",
            "purchase_method": "purchase",
            "property_account_expense_id": self.deposit_account_id.id,
            "supplier_taxes_id": [(6, 0, self.deposit_taxes_id.ids)],
            "company_id": False,
        }
