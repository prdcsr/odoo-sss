
from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'onport': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('pib', 'PIB Payment'),        
        ('onport', 'On Port'),
        ('done', 'Received'),
        ('cancel', 'Cancelled')
        ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    requisition_ids = fields.Many2many('purchase.requisition',store = True,compute='_compute_req',string='Purchase Requisitions', states={'done': [('readonly', True)]})
    bl_no = fields.Char(string='B/L No')
    bl_date = fields.Date(string="B/L Date")
    fp_no = fields.Char(string='FP No')
    pib_no = fields.Char(string='PIB No')
    pib_date = fields.Date(string="PIB Date")
    vendor_inv_no = fields.Char(string='Vendor Invoice No')
    eta_date = fields.Date(string='ETA Date')
    doc_receive_date = fields.Date(string='Document Received')
    sppb_date = fields.Date(string='SPPB Date')
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Terms',
                                      domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                      related='requisition_id.payment_term_id')
    add_rfq_no = fields.Char(string='Additional RFQ No')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            seq_date = None
            vendor_seq = None
            is_vendorseq = False
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            if 'partner_id' in vals:
                vendor_seq = self.env['res.partner'].browse(vals['partner_id']).sequence_id
                if vendor_seq:
                    is_vendorseq = True
            if is_vendorseq:
                vals['name'] = self.env['ir.sequence'].next_by_code(vendor_seq.code, sequence_date=seq_date) or '/'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order', sequence_date=seq_date) or '/'
        return super(PurchaseOrder, self).create(vals)
    
    @api.depends('order_line.requisition_line_id.requisition_id')
    def _compute_req(self):
        for order in self:
            orders = self.env['purchase.requisition']
            for line in order.order_line:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                moves = line.requisition_line_id
                orders |= moves.mapped('requisition_id')
            order.requisition_ids = orders
            #order.order_count = len(orders)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    requisition_id = fields.Many2one(related='requisition_line_id.requisition_id', string="Purchase Agreement", store=True, readonly=True)    
    requisition_line_id = fields.Many2one('purchase.requisition.line',
        'Purchase requisition Line', ondelete='set null', index=True, readonly=True)      
    
    """"@api.model
    def create(self, values):
        line = super(PurchaseOrderLine, self).create(values)
        #if 'requisition_line_id' in values:
        line.name = values
        return line"""
        
    def unlink(self):
        for line in self:
            if line.is_deposit:
                raise UserError(_('Cannot delete down payment purchase order line'))
        return super(PurchaseOrderLine, self).unlink()

    # @api.model
    # def create(self, vals):
    #     product_id = vals.get('product_id')
    #     order_id = vals.get('order_id')

    #     # Cek product double input
    #     existing_line = self.env['purchase.order.line'].search([
    #         ('product_id', '=', product_id),
    #         ('order_id', '=', order_id)
    #     ])

    #     if existing_line:
    #         product_name = existing_line.product_id.name
    #         raise UserError(_("Product '%s' is already added to the purchase order.") % product_name)

    #     return super(PurchaseOrderLine, self).create(vals)