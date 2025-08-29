

from datetime import datetime, timedelta,time
from collections import defaultdict

from odoo import api, fields, models,tools
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError

class PurchaseRequisition(models.Model):
	_inherit = "purchase.requisition"

	payment_term_id = fields.Many2one('account.payment.term', 'Payment Terms', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
	incoterm_id = fields.Many2one('account.incoterms', 'Incoterm', states={'done': [('readonly', True)]}, help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")
	qty_container = fields.Char(string='Qty Container')
	port_of_loading = fields.Char(string='Port Of Loading')
	port_of_destination = fields.Char(string='Port OF Destination')

class PurchaseRequisitionLine(models.Model):
    _name = "purchase.requisition.line"
    _inherit = "purchase.requisition.line"
    _order = 'requisition_id, sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    qty_ordered = fields.Float(compute='_compute_ordered_qty', string='Ordered Quantities',store=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', related='requisition_id.vendor_id',store = True)

    @api.depends('requisition_id.purchase_ids.state')
    def _compute_ordered_qty(self):
        for line in self:
            total = 0.0
            for po in line.requisition_id.purchase_ids.filtered(lambda purchase_order: purchase_order.state in ['purchase', 'done']):
                for po_line in po.order_line.filtered(lambda order_line: order_line.product_id == line.product_id):
                    if po_line.product_uom != line.product_uom_id:
                        total += po_line.product_uom._compute_quantity(po_line.product_qty, line.product_uom_id)
                    else:
                        total += po_line.product_qty
            line.qty_ordered = total



class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
	
    def npwp_string(self,string):
        if len(string) == 15:
            val=string[:2]+'.' +string[2:5]+'.' +string[5:8]+'.' +string[8:9]+'-'+string[9:12]+'.'+string[12:15]
        else: 
            val=string
        return val	

