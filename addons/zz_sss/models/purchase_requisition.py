from datetime import datetime, timedelta, time
from collections import defaultdict

from odoo import api, fields, models, tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    purchase_ids = fields.Many2many('purchase.order', compute='_compute_order', string='Purchase Orders',
                                    states={'done': [('readonly', True)]})
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Terms',
                                      domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                      compute='_compute_payment_term', inverse='_inverse_payment_term', store=True)
    incoterm_id = fields.Many2one('account.incoterms', 'Incoterm', states={'done': [('readonly', True)]},
                                  help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")
    qty_container = fields.Char(string='Qty Container')
    port_of_loading = fields.Char(string='Port Of Loading')
    port_of_destination = fields.Char(string='Port OF Destination')
    rfq_bld_date = fields.Date(comodel_name='purchase.order', related='purchase_ids.bl_date', readonly=True,
                               string='BL Date')
    rfq_bld_date_txt = fields.Char(readonly=True, string='BL Date')

    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_total')

    @api.depends('line_ids.price_unit', 'line_ids.product_qty')
    def _amount_total(self):
        for order in self:
            total = 0
            for line in order.line_ids:
                subtotal = line.product_qty * line.price_unit
                total += subtotal
            currency = order.currency_id or order.partner_id.property_purchase_currency_id or self.env.company.currency_id
            order.update({
                'amount_total': currency.round(total)
            })

    @api.depends('vendor_id')
    def _compute_payment_term(self):
        self.payment_term_id = self.vendor_id.property_supplier_payment_term_id if self.vendor_id else False

    def _inverse_payment_term(self):
        pass

    @api.depends('line_ids.purchase_line_ids.order_id')
    def _compute_order(self):
        for order in self:
            orders = self.env['purchase.order']
            for line in order.line_ids:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                moves = line.purchase_line_ids
                orders |= moves.mapped('order_id')
            order.purchase_ids = orders
            order.order_count = len(orders)

    @api.depends('purchase_ids')
    def _compute_orders_number(self):
        for requisition in self:
            requisition.order_count = len(requisition.purchase_ids)
            bl_date = ''
            # if line.rfq_bld_date_txt:
            #    bl_date = line.rfq_bld_date_txt
            # else:

            for po in requisition.purchase_ids.filtered(
                    lambda purchase_order: purchase_order.state in ['purchase', 'pib', 'onport', 'done']):
                if po.bl_date:
                    bl_date += ', ' + datetime.strftime(po.bl_date, '%d/%b/%Y')

            requisition.rfq_bld_date_txt = bl_date

    @api.model
    def create(self, vals):
        # Check for duplicate product codes in the purchase requisition lines
        product_codes = {}
        duplicates = []

        for line in vals.get('line_ids', []):
            product_id = line[2].get('product_id', False)
            if product_id and product_id.default_code != 'PDisc':
                product = self.env['product.product'].browse(product_id)
                product_code = product.default_code or ''
                product_name = product.name

                if product_code in product_codes:
                    if product_code not in duplicates:
                        duplicates.append(product_code)
                else:
                    product_codes[product_code] = product_name

        if duplicates:
            error_message = _("Duplicate product codes detected in purchase requisition lines:\n")
            for product_code in duplicates:
                product_name = product_codes.get(product_code, '')
                error_message += f"- Product Code: {product_code}, Product Name: {product_name}\n"

            raise UserError(error_message)

        purchase_req = super(PurchaseRequisition, self).create(vals)

        if purchase_req.name == 'New':
            if purchase_req.is_quantity_copy != 'none':
                # self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.purchase.tender')
                if purchase_req.vendor_id.pa_sequence_id:
                    seq = purchase_req.vendor_id.pa_sequence_id
                    purchase_req.name = self.env['ir.sequence'].next_by_code(seq.code)
                else:
                    purchase_req.name = self.env['ir.sequence'].next_by_code('purchase.requisition.purchase.tender')
            else:
                purchase_req.name = self.env['ir.sequence'].next_by_code('purchase.requisition.blanket.order')

        return purchase_req

    def action_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})

    def action_in_progress(self):
        self.ensure_one()
        if not all(obj.line_ids for obj in self):
            raise UserError(_("You cannot confirm agreement '%s' because there is no product line.") % self.name)
        if self.type_id.quantity_copy == 'none' and self.vendor_id:
            for requisition_line in self.line_ids:
                if requisition_line.price_unit <= 0.0:
                    raise UserError(_('You cannot confirm the blanket order without price.'))
                if requisition_line.product_qty <= 0.0:
                    raise UserError(_('You cannot confirm the blanket order without quantity.'))
                requisition_line.create_supplier_info()
            self.write({'state': 'ongoing'})
        else:
            self.write({'state': 'in_progress'})
        # Set the sequence number regarding the requisition type
        if self.name == 'New':
            if self.is_quantity_copy != 'none':
                # self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.purchase.tender')
                if self.vendor_id.pa_sequence_id:
                    seq = self.vendor_id.pa_sequence_id
                    self.name = self.env['ir.sequence'].next_by_code(seq.code)
                else:
                    self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.purchase.tender')
            else:
                self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.blanket.order')


class PurchaseRequisitionLine(models.Model):
    # _name = "purchase.requisition.line"
    _inherit = "purchase.requisition.line"
    _order = 'requisition_id, sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    qty_ordered = fields.Float(compute='_compute_purchase_ordered_qty', string='Ordered Quantities', store=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', related='requisition_id.vendor_id', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='requisition_id.currency_id', store=True)
    product_image = fields.Image("Image", max_width=1920, max_height=1920, related='product_id.image_1920')
    product_description_variants = fields.Text('Custom Description')
    purchase_line_ids = fields.One2many('purchase.order.line', 'requisition_line_id', string='Order Line',
                                        readonly=True, ondelete='set null', copy=False)
    qty_20ft = fields.Float(string="Qty 20 Ft", store=True, compute="compute_qty_20ft", inverse='inverse_qty_20ft', related="product_id.qty_20ft" )
    # qty_20ft = fields.Float(string="Qty 20 Ft" )

    not_ordered_total = fields.Float(
        string="N Ordered Qty",
        readonly=True,
        compute='compute_not_ordered_total'
    )

    @api.model
    def create(self, vals):
        requisition_id = vals['requisition_id']
        requisition = self.env['purchase.requisition'].search([('id', '=', requisition_id)])
        if 'qty_20ft' in vals:
            if (vals['qty_20ft'] == False or vals['qty_20ft'] == 0) and requisition.operating_unit_id.id == 1:
                raise UserError(_('You cannot create order without qty 20 ft'))
        res = super(PurchaseRequisitionLine, self).create(vals)
        return res

    @api.depends('product_id', 'product_id.qty_20ft')
    def compute_qty_20ft(self):
        for line in self:
            line.qty_20ft = line.product_id.qty_20ft

    def inverse_qty_20ft(self):
        pass

    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     super(PurchaseRequisitionLine)._onchange_product_id()
    #     if self.product_id:
    #         self.qty_20ft = self.product_id.qty_20ft

    @api.depends('product_qty', 'qty_ordered')
    def compute_not_ordered_total(self):
        for dat in self:
            dat.not_ordered_total = dat.product_qty - dat.qty_ordered

    @api.onchange('product_id')
    def onchange_product_id(self):
        hide_ref = True  # ast.literal_eval(self.env["ir.config_parameter"].sudo().get_param("purchase.requisition.line.hide_ref", "False"))

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
        res = super(PurchaseRequisitionLine, self)._prepare_purchase_order_line(name, product_qty, price_unit,
                                                                                taxes_ids)
        res['requisition_line_id'] = self.id
        return res

    @api.depends('purchase_line_ids.state')
    def _compute_purchase_ordered_qty(self):
        for line in self:
            total = 0.0
            for po in line.purchase_line_ids.filtered(
                    lambda m: m.product_id == line.product_id):  # requisition_id.purchase_ids.filtered(lambda purchase_order: purchase_order.state in ['purchase', 'done']):
                if po.state in ['purchase', 'pib', 'onport',
                                'done']:  # for po_line in po.order_line.filtered(lambda order_line: order_line.product_id == line.product_id):
                    if po.product_uom != line.product_uom_id:
                        total += po.product_uom._compute_quantity(po.product_qty, line.product_uom_id)
                    else:
                        total += po.product_qty
            line.qty_ordered = total
