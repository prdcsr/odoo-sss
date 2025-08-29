import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, RedirectWarning, ValidationError, UserError

_logger = logging.getLogger(__name__)

class Rma(models.Model):
    _inherit = "rma"

    line_ids = fields.One2many(
        "rma.line",
        "rma_id",
        string="RMA Lines",
        copy=True,
    )

    @api.depends("state")
    def _compute_can_be_replaced(self):
        """ Compute 'can_be_replaced'. This field controls the visibility
        of 'Replace' button in the rma form
        view and determinates if an rma can be replaced.
        This field is used in:
        rma._compute_can_be_split
        rma._ensure_can_be_replaced.
        """
        for r in self:
            r.can_be_replaced = r.state in [
                "confirmed",
                "received",
                "waiting_replacement",
                "replaced",
            ]

class RmaLine(models.Model):
    _name = "rma.line"
    _description = "RMA Damaged Part Line"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)

    rma_id = fields.Many2one(
        comodel_name="rma",  # Change if your base RMA model differs
        string="RMA",
        required=True,
        ondelete="cascade",
        index=True,
    )

    product_id = fields.Many2one(
        "product.product",
        string="Part",
        domain="[('type', 'in', ['product','consu'])]",
        required=True,
    )
    name = fields.Char(string="Description")
    product_uom = fields.Many2one("uom.uom", string="UoM")
    quantity = fields.Float(string="Quantity", default=1.0)
    requisition_id = fields.Many2one(comodel_name="purchase.requisition", string='Purchase Agreement', readonly=True)
    purchase_id = fields.Many2one(comodel_name="purchase.order", string='Purchase Order', readonly=True)

    damage_type = fields.Selection(
        [
            ("broken", "Broken"),
            ("missing", "Missing"),
            ("defect", "Manufacturing Defect"),
            ("other", "Other"),
        ],
        string="Damage Type",
    )
    severity = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        string="Severity",
        default="medium",
    )
    note = fields.Text(string="Notes")

    # Helper/UX fields
    company_id = fields.Many2one(
        related="rma_id.company_id", store=True, readonly=True
    )
    state = fields.Selection(
        related="rma_id.state", store=False, readonly=True
    )

    @api.onchange("product_id")
    def _onchange_product_id_set_uom_and_name(self):
        for rec in self:
            if rec.product_id:
                # Default to the product’s UoM
                rec.product_uom = rec.product_id.uom_id.id
                # If description empty, use product display name
                if not rec.name:
                    rec.name = rec.product_id.display_name

    @api.constrains("quantity")
    def _check_quantity_positive(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError(_("Quantity must be positive."))
            
            
    def action_order_stock(self):
        PurchaseRequisition = self.env['purchase.requisition']
        RequisitionLine = self.env['purchase.requisition.line']

        for line in self:
            if not line.product_id or not line.quantity:
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
                'origin': line.rma_id.name,
                'schedule_date': fields.Date.today(),
                'line_ids': [(0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom.id,
                    'product_qty': line.quantity,
                })]
            })

            # Link it to repair line
            line.requisition_id = requisition.id

            # TODO: SEND EMAIL TO IMPORT DIV

            # users = self.env['res.users'].search([('groups_id', 'in', self.env.ref('zz_repair.group_user_import').id)])
            # recipient_emails = users.mapped('partner_id.email')
            # mail_template = self.env.ref('zz_repair.email_template_purchase_requisition_notification')
            # for email in recipient_emails:
            #     mail_template.sudo().send_mail(
            #         requisition.id,
            #         email_values={
            #             'email_to': email,
            #         },
            #         force_send=True
            #     )

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
            if not line.product_id or not line.quantity:
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
                'origin': line.rma_id.name,
                'date_order': fields.Date.today(),
                'partner_id': partner.id,
                'order_line': [(0, 0, {
                    'name': line.product_id.display_name,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom.id,
                    'product_qty': line.quantity,
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


