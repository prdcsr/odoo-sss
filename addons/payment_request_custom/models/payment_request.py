from odoo import api, fields, models, tools,_
from odoo.exceptions import ValidationError, UserError
import math

class PaymentRequest(models.Model):
    _name = 'payment.request'
    _inherit = 'mail.thread'

    name = fields.Char('Sequence', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'),
                       track_visibility="onchange")
    lpo_num = fields.Many2one('purchase.order', string="RFQ",required=True)
    fp_no = fields.Char(string='FP No',readonly=True)
    ntpn_no = fields.Char(string='NTPN No')
    skb_no = fields.Char(string='SKB No')
    pib_no = fields.Char(string='PIB No',readonly=True)
    pib_date = fields.Date(string="PIB Date",readonly=True)
    company = fields.Many2one('res.partner', string="Vendor",readonly=True)
    payment_term = fields.Many2one('account.payment.term', string="Payment Term",readonly=True)
    currency_id= fields.Many2one('res.currency', 'Currency')
    amount = fields.Float('Amount')
    amount_exch = fields.Float("Exchange Rate")
    amount_dpp = fields.Float('DPP')
    amount_tax_vat = fields.Float('PPN')
    amount_tax_income = fields.Float('PPH')    
    amount_duty = fields.Float("Bea Masuk")
    prepared = fields.Many2one('res.users', string="Prepared By")
    approved = fields.Many2one('res.users', string="Approved By")
    account_approve = fields.Many2one('res.users', string="Accounts Approved By")
    project = fields.Many2one('account.analytic.account', string="Projects")
    department_manager_comment = fields.Text(string="Department Manager Comment")
    account_comment = fields.Text(string="Accounts Comment")
    purchase_comment = fields.Text(string="Purchase Comment")
    state = fields.Selection([
        ('Draft', 'Draft'),
        ('Department Approval', 'Department Manager Approval'),
        ('Accounts Approval', 'Accounts Approval'),
        ('Department Reject', 'Department Manager Rejected'),
        ('Accounts Reject', 'Accounts Rejected'),
        ('Approved', 'Posted'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='Draft')
    move_id = fields.Many2one('account.move', string='Journal Entry')
    amount_total = fields.Float('Total Payment')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('payment.request') or 'New'
        return super(PaymentRequest, self).create(vals)

    def unlink(self):
        for order in self:
            if not order.state == 'Draft':
                raise UserError(_('Cannot Delete non Draft State Payment Request'))
        return super(PaymentRequest, self).unlink()

    @api.onchange('lpo_num')
    def _get_data(self):
        for rec in self:
            rec.company = rec.lpo_num.partner_id.id
            rec.payment_term = rec.lpo_num.payment_term_id.id
            rec.amount = rec.lpo_num.amount_total
            rec.fp_no = rec.lpo_num.fp_no
            rec.pib_no = rec.lpo_num.pib_no
            rec.pib_date = rec.lpo_num.pib_date
            #rec.project = rec.lpo_num.analytic_id.id

    @api.onchange("amount_dpp","amount_duty")
    def _onchange_amount_dpp(self):      

        #round up to the nearest 1.000
        #raise UserWarning(_("test aja"))
        for rec in self:
            vat = int(math.ceil(((rec.amount_dpp + rec.amount_duty)  * 0.11)/1000)) * 1000 
            rec.amount_tax_vat = float(vat)
            pph = int(math.ceil(((rec.amount_dpp + rec.amount_duty) * 0.025)/1000)) * 1000
            rec.amount_tax_income = float(pph)   
            #rec.amount_total = rec.amount_duty + rec.amount_tax_vat + rec.amount_tax_income

    @api.onchange("amount_tax_vat","amount_tax_income","amount_duty")
    def _onchange_amount_total(self):      

        #round up to the nearest 1.000
        #raise Use Warning(_("test aja"))
        for rec in self: 
            if not rec.skb_no :                        
                rec.amount_total = rec.amount_duty + rec.amount_tax_vat + rec.amount_tax_income
            else:
                rec.amount_total = rec.amount_duty + rec.amount_tax_vat

   # @api.multi
    def action_confirm(self):

        if not self.fp_no or not self.pib_no or not self.pib_date:
            raise UserError(_('Customs Data is not set yet'))

        self.write({'state': 'Department Approval', 'prepared': self.env.user.id})
        channel_all_employees = self.env.ref('payment_request_custom.channel_all_payment_request').read()[0]
        template_new_employee = self.env.ref('payment_request_custom.email_template_data_payment_request').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            body = """Hello, Payment Request with number %s Sending to purchase department approval""" % (self.name)
            channel_id.message_post(body=body, subject='Payment Request', subtype='mail.mt_comment')

   # @api.multi
    def action_department_approve(self):
        self.write({'state': 'Accounts Approval', 'approved': self.env.user.id})
        channel_all_employees = self.env.ref('payment_request_custom.channel_all_to_approve_payment_request').read()[0]
        template_new_employee = self.env.ref('payment_request_custom.email_template_data_to_approve_payment_request').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            body = """This payment request %s waiting for accounts approval""" % (self.name)
            channel_id.message_post(body=body, subject='Payment Request', subtype='mail.mt_comment')

   # @api.multi
    def action_department_reject(self):
        self.write({'state': 'Department Reject'})
        channel_all_employees = self.env.ref('payment_request_custom.channel_all_payment_request').read()[0]
        template_new_employee = self.env.ref('payment_request_custom.email_template_data_payment_request').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            body = """This payment request %s get rejected by the purchase department manager""" % (self.name)
            channel_id.message_post(body=body, subject='Payment Request', subtype='mail.mt_comment')

   # @api.multi
    def action_accounts_approve(self):
        self.write({'state': 'Approved', 'account_approve': self.env.user.id})
        self._create_invoice()
        channel_all_employees = self.env.ref('payment_request_custom.channel_all_payment_request').read()[0]
        template_new_employee = self.env.ref('payment_request_custom.email_template_data_payment_request').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            body = """This payment request %s is approved by the accounts team""" % (self.name)
            channel_id.message_post(body=body, subject='Payment Request', subtype='mail.mt_comment')

   # @api.multi
    def action_accounts_reject(self):
        self.write({'state': 'Accounts Reject'})
        channel_all_employees = self.env.ref('payment_request_custom.channel_all_payment_request').read()[0]
        template_new_employee = self.env.ref('payment_request_custom.email_template_data_payment_request').read()[0]
        # raise ValidationError(_(template_new_employee))
        if template_new_employee:
            # MailTemplate = self.env['mail.template']
            body_html = template_new_employee['body_html']
            subject = template_new_employee['subject']
            # raise ValidationError(_('%s %s ') % (body_html,subject))
            ids = channel_all_employees['id']
            channel_id = self.env['mail.channel'].search([('id', '=', ids)])
            body = """This payment request %s is rejected by the accounts team""" % (self.name)
            channel_id.message_post(body=body, subject='Payment Request', subtype='mail.mt_comment')

    #@api.multi
    def set_to_draft(self):
        self.write({'state':'Draft','account_approve':False,'approved':False})
    
    def _create_invoice(self):
        Invoice = self.env["account.move"]
        #domain
        #order = 
        
        if self.amount_total <= 0:
            raise UserError(_("The value of the payment must be positive."))
        

        #context = {"lang": order.partner_id.lang}
        amount_pph = self.amount_tax_income
        if self.skb_no :
            amount_pph = 0
        name = self.name+_("; customs payment ") + self.lpo_num.name
        pph_account = self.env['ir.config_parameter'].sudo().get_param('payment_request_custom.payment_tax_account_id')
        import_tax_account = self.env['ir.config_parameter'].sudo().get_param('payment_request_custom.import_tax_account_id')
        import_duty_account = self.env['ir.config_parameter'].sudo().get_param('payment_request_custom.import_duty_account_id')
        account_payable = self.env['ir.config_parameter'].sudo().get_param('payment_request_custom.account_payable_id')
        payment_request_journal = self.env['ir.config_parameter'].sudo().get_param('payment_request_custom.payment_request_journal_id')

        invoice = Invoice.create(
            {
                "invoice_origin": self.name,
                "ref" : name,
                "type": "entry",
                "partner_id": self.company.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": name,
                            "account_id": int(pph_account),
                            'debit': amount_pph,
                            'credit': 0,
                            'journal_id' : int(payment_request_journal),
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": name,
                            "account_id": int(import_duty_account),
                            'debit': self.amount_duty,
                            'credit': 0,
                            'journal_id' : int(payment_request_journal),
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": name,
                            "account_id": int(import_tax_account),
                            'debit': self.amount_tax_vat,
                            'credit': 0,
                            'journal_id' : int(payment_request_journal),
                        },
                    ),
                       (
                        0,
                        0,
                        {
                            "name": name,
                            "account_id": int(account_payable),
                            'debit': 0,
                            'credit': self.amount_total,
                            'journal_id' : int(payment_request_journal),
                        },
                    ),
                ],
                "journal_id" : int(payment_request_journal),
                "purchase_id" : self.lpo_num.id,
                #"currency_id": self.currency_id.id,
                "date" : self.pib_date,      
                "narration": self.department_manager_comment +" "+ self.account_comment,
                #"state" : 'posted',
            }
        )
        invoice.message_post_with_view(
            "mail.message_origin_link",
            values={"self": invoice, "origin": self},
            subtype_id=self.env.ref("mail.mt_note").id,
        )
        return invoice