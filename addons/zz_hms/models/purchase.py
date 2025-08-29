
from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
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

    bl_no = fields.Char(string='B/L No')
    bl_date = fields.Date(string="B/L Date")
    fp_no = fields.Char(string='FP No')
    pib_no = fields.Char(string='PIB No')
    pib_date = fields.Date(string="PIB Date")
    vendor_inv_no = fields.Char(string='Vendor Invoice No')

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
    
    
    # def button_ontheway(self):
    #    self.write({'state': 'ontheway'})

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'      
    
    def unlink(self):
        for line in self:
            if line.is_deposit:
                raise UserError(_('Cannot delete down payment purchase order line'))
        return super(PurchaseOrderLine, self).unlink() 