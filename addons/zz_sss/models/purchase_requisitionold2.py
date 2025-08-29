

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
    rfq_bld_date =  fields.Date(comodel_name='purchase.order',related='purchase_ids.bl_date',readonly=True,string='BL Date')
    rfq_bld_date_txt = fields.Char(readonly=True,string='BL Date')


    @api.depends('purchase_ids')
    def _compute_orders_number(self):
        for requisition in self:
            requisition.order_count = len(requisition.purchase_ids)
            bl_date = ''
            #if line.rfq_bld_date_txt:
            #    bl_date = line.rfq_bld_date_txt
            #else:
            
        
            for po in requisition.purchase_ids.filtered(lambda purchase_order: purchase_order.state in ['purchase','pib','onport','done']):
                if po.bl_date:
                    bl_date += ', ' + datetime.strftime(po.bl_date,'%d/%b/%Y')

            requisition.rfq_bld_date_txt = bl_date

class PurchaseRequisitionLine(models.Model):
    _name = "purchase.requisition.line"
    _inherit = "purchase.requisition.line"
    _order = 'requisition_id, sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    qty_ordered = fields.Float(compute='_compute_ordered_qty', string='Ordered Quantities',store=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', related='requisition_id.vendor_id',store = True)
    currency_id = fields.Many2one('res.currency', string='Currency',related='requisition_id.currency_id',store = True)

    product_description_variants = fields.Text('Custom Description')

    @api.onchange('product_id')
    def onchange_product_id(self):
        hide_ref = True #ast.literal_eval(self.env["ir.config_parameter"].sudo().get_param("purchase.requisition.line.hide_ref", "False"))
        
        # Get supplier info
        supplier_info = self.product_id.seller_ids.filtered(
            lambda s: (s.name == self.requisition_id.vendor_id)
        )
        if supplier_info:
            supplier_info = supplier_info[0]

        # Set supplier product code as name
        if supplier_info.product_code and not hide_ref:
            self.product_description_variants = "[" + supplier_info.product_code + "] "
        else:
            self.product_description_variants = ""
        
        # Append purchase description to name
        if self.product_id.description_purchase:
            product = self.product_id.with_context(
                lang=self.requisition_id.vendor_id.lang
            )
            self.product_description_variants += product.description_purchase

        # If no purchase description is given set name
        elif self.product_id:
            self.product_description_variants += self.product_id.name

        # Append supplier product name
        if supplier_info.product_name:
            self.product_description_variants += '\n' + supplier_info.product_name

    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        res = super(PurchaseRequisitionLine, self)._prepare_purchase_order_line(name, product_qty, price_unit, taxes_ids)
        res['name'] = name #self.product_description_variants
        return res

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

