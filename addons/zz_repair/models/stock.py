from collections import defaultdict
from datetime import datetime
from dateutil import relativedelta
from itertools import groupby
from operator import itemgetter
from re import findall as regex_findall, split as regex_split

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_round, float_is_zero

class Repair(models.Model):
    _inherit = 'repair.order'

    operations = fields.One2many(
        'repair.line', 'repair_id', 'Parts',
        copy=True, readonly=True, states={'draft': [('readonly', False)], 'under_repair': [('readonly', False)], 'confirmed': [('readonly', False)]})
        # copy=True)

    fees_lines = fields.One2many(
        'repair.fee', 'repair_id', 'Operations',
        copy=True, readonly=True, states={'draft': [('readonly', False)], 'under_repair': [('readonly', False)]})

    cust_name =  fields.Text('customer Name',readonly=True, states={'draft': [('readonly', False)]})
    is_garansi = fields.Boolean('Ada Kartu Garansi',readonly=True,states={'draft': [('readonly', False)]})
    is_complete = fields.Boolean('Kartu garansi diisi dengan lengkap dan ada stamp Toko/Dealer',readonly=True, states={'draft': [('readonly', False)]})
    is_damage_delivery = fields.Boolean('Tidak terjadi kerusakan karena kelalaian pemakaian, kesalahan penyimpanan atau kesalahan pengangkutan'
    ,readonly=True,states={'draft': [('readonly', False)]})
    is_damage_self = fields.Boolean('Sistem unit tidak dirubah atau direparasi pihak ketiga',readonly=True,states={'draft': [('readonly', False)]})
    is_damage_nature = fields.Boolean('Kerusakan tidak disebabkan oleh bencana alam',readonly=True,states={'draft': [('readonly', False)]})
    is_consumables = fields.Boolean('Komponen kategori barang habis pakai',readonly=True,states={'draft': [('readonly', False)]})
    is_delivery_cost = fields.Boolean('Biaya pengembalian produk dari service center ditanggung oleh Dealer/Customer',readonly=True,states={'draft': [('readonly', False)]})
    origin_id = fields.Many2one(comodel_name='rma', string='Source Document')
    spbr_no = fields.Char(string='SPBR No')
    salesman_id = fields.Many2one(
        'res.users', string='Salesperson', index=True, tracking=2)

    technician_id = fields.Many2one(
        "res.users", string="Teknisi"
    )

    sales_id = fields.Many2one(
        "res.users", String="Sales"
    )
    is_garansi_selection=fields.Selection(
        [('garansi', 'Garansi'), ('no_garansi', 'Tidak Garansi')]
    )
    form_number=fields.Text("Nomor Form Analisa dan Validasi Produk")
    reason = fields.Text("Keluhan pada mesin dan penyebab kerusakan")
    is_card_gone = fields.Boolean("Telah lewat garansi")
    is_modified = fields.Boolean("Sistem unit telah dirubah atau direparasi pihak ketiga")
    is_garansi_passed = fields.Boolean("Telah lewat garansi")
    is_paid_by_customer = fields.Boolean("Seluruh biaya pengembalian barang menjadi tanggung jawab pembeli")


    @api.model
    def create(self, vals):
        # To avoid consuming a sequence number when clicking on 'Create', we preprend it if the
        # the name starts with '/'.
        vals['name'] = vals.get('name') or '/'
        vals['location_id'] = vals.get('location_id')
        location = self.env['stock.location'].search([("id", "=", vals['location_id'])])
        if vals['name'].startswith('/'):
            if location and location.repair_sequence:
                seq = location.repair_sequence
                vals['name'] = (self.env['ir.sequence'].next_by_code(seq.code) or '/') + vals['name']
                vals['name'] = vals['name'][:-1] if vals['name'].endswith('/') and vals['name'] != '/' else vals['name']
            else:
                vals['name'] = (self.env['ir.sequence'].next_by_code('repair.order') or '/') + vals['name']
                vals['name'] = vals['name'][:-1] if vals['name'].endswith('/') and vals['name'] != '/' else vals['name']
        return super(Repair, self).create(vals)
    
class RepairOrderLine(models.Model):
    _inherit = "repair.line"

    insufficient_qty = fields.Boolean(
        string='Insufficient Stock',
        compute='_compute_insufficient_qty',
        store=False
    )

    requisition_id = fields.Many2one('purchase.requisition', string='Purchase Agreement', copy=False)
    purchase_id = fields.Many2one('purchase.order', string="Purchase Order", copy=False)
    vendor_id = fields.Many2one('res.partner', string='Vendor to Purchase')

    @api.depends('product_id', 'product_uom_qty')
    def _compute_insufficient_qty(self):
        for line in self:
            if not line.product_id or not line.product_uom_qty:
                line.insufficient_qty = False
                continue
            # Specify the location (or make it dynamic based on your flow)
            stock_location = line.repair_id.location_id

            quant = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('location_id', '=', stock_location.id)
            ], limit=1)

            line.insufficient_qty = quant.quantity < line.product_uom_qty if quant else True

    def action_order_stock(self):
        PurchaseRequisition = self.env['purchase.requisition']
        RequisitionLine = self.env['purchase.requisition.line']

        for line in self:
            if not line.product_id or not line.product_uom_qty:
                raise UserError(_('Product or quantity missing on the repair line.'))

            if line.requisition_id:
                # Already created
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Purchase Requisition',
                    'res_model': 'purchase.requisition',
                    'view_mode': 'form',
                    'res_id': line.requisition_id.id,
                    'target': 'current',
                }

            # Create Purchase Requisition
            requisition = PurchaseRequisition.create({
                'origin': line.repair_id.name,
                'schedule_date': fields.Date.today(),
                'line_ids': [(0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom.id,
                    'product_qty': line.product_uom_qty,
                })]
            })

            # Link it to repair line
            line.requisition_id = requisition.id

            # TODO: SEND EMAIL TO IMPORT DIV

            return {
                'type': 'ir.actions.act_window',
                'name': 'Purchase Requisition',
                'res_model': 'purchase.requisition',
                'view_mode': 'form',
                'res_id': requisition.id,
                'target': 'current',
            }

    def action_purchase_stock(self):
        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']

        for line in self:
            if not line.product_id or not line.product_uom_qty:
                raise UserError(_('Product or quantity missing on the repair line.'))

            if line.purchase_id:
                # Already created
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Purchase Order',
                    'res_model': 'purchase.order',
                    'view_mode': 'form',
                    'res_id': line.purchase_id.id,
                    'target': 'current',
                }

            # Create Purchase Order
            partner = line.product_id.last_purchase_supplier_id
            if not partner:
                partner = line.vendor_id
            order = PurchaseOrder.create({
                'origin': line.repair_id.name,
                'date_order': fields.Date.today(),
                'partner_id': partner.id,
                'order_line': [(0, 0, {
                    'name': line.product_id.display_name,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom.id,
                    'product_qty': line.product_uom_qty,
                    'price_unit': line.product_id.standard_price,
                    'display_type': False,
                    'date_planned': fields.Date.today()
                })]
            })

            # Link it to repair line
            line.purchase_id = order.id

            # TODO: SEND EMAIL TO IMPORT DIV

            # users = self.env['res.users'].search(
            #     [('groups_id', 'in', self.env.ref('zz_repair.group_user_import').id)])
            # recipient_emails = users.mapped('partner_id.email')
            # mail_template = self.env.ref('zz_repair.email_template_purchase_order_notification')
            # for email in recipient_emails:
            #     mail_template.sudo().send_mail(
            #         order.id,
            #         email_values={
            #             'email_to': email,
            #         },
            #         force_send=True
            #     )

            return {
                'type': 'ir.actions.act_window',
                'name': 'Purchase Order',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'res_id': order.id,
                'target': 'current',
            }

class StockMove(models.Model):
    _inherit = "stock.move"

    invoice_method = fields.Selection([
        ('none', 'No Invoice'),
        ('b4repair', 'Before Repair'),
        ('after_repair', 'After Repair'),],string='Invoice Method', copy=False, default='none')

    cost = fields.Float("Cost",
        related='product_id.standard_price'
    )
    total_cost = fields.Float(
        "Total Cost",
        compute="_compute_total_cost"
    )

    @api.depends('product_id', 'product_uom_qty')
    def _compute_total_cost(self):
        for line in self:
            line.total_cost = line.product_id.standard_price * line.product_uom_qty


class InventoryAdjustmentLine(models.Model):
	_inherit = "stock.inventory.line"

	remark = fields.Text(string='Remark')
    