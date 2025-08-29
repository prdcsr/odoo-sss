from odoo import models, fields, api
from datetime import datetime

PURCHASE_STATES = [
    ('draft', 'RFQ'),
    ('sent', 'RFQ Sent'),
    ('to approve', 'To Approve'),
    ('purchase', 'Purchase Order'),
    ('pib', 'PIB Payment'),
    ('onport', 'On Port'),
    ('done', 'Received'),
    ('cancel', 'Cancelled')
]

class PurchaseOrderHistory(models.Model):
    _name = 'purchase.order.history'
    _description = 'Purchase Order Status & Qty History'
    _order = 'date desc'

    order_id = fields.Many2one('purchase.order', string='Order', required=True)
    line_id = fields.Many2one('purchase.order.line', string='Line')
    date = fields.Datetime(string='Change Date', required=True, default=fields.Datetime.now)
    old_status = fields.Selection(PURCHASE_STATES, string='Old Status')
    new_status = fields.Selection(PURCHASE_STATES, string='New Status')
    old_received_qty = fields.Float(string='Old Received Qty')
    new_received_qty = fields.Float(string='New Received Qty')
    changed_by = fields.Many2one('res.users', string='Changed By', default=lambda self: self.env.user)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def write(self, vals):
        for rec in self:
            if 'state' in vals and vals['state'] != rec.state:
                self.env['purchase.order.history'].create({
                    'order_id': rec.id,
                    'date': fields.Datetime.now(),
                    'old_status': rec.state,
                    'new_status': vals['state'],
                    'changed_by': self.env.user.id
                })
        return super(PurchaseOrder, self).write(vals)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def write(self, vals):
        for line in self:
            if 'product_qty' in vals and vals['product_qty'] != line.product_qty:
                self.env['purchase.order.history'].create({
                    'order_id': line.order_id.id,
                    'line_id': line.id,
                    'date': fields.Datetime.now(),
                    'old_received_qty': line.product_qty,
                    'new_received_qty': vals['product_qty'],
                    'changed_by': self.env.user.id
                })
            if 'qty_received' in vals and hasattr(line, 'qty_received') and vals['qty_received'] != line.qty_done:
                self.env['purchase.order.history'].create({
                    'order_id': line.order_id.id,
                    'line_id': line.id,
                    'date': fields.Datetime.now(),
                    'old_received_qty': line.qty_received,
                    'new_received_qty': vals['qty_received'],
                    'changed_by': self.env.user.id
                })
        return super(PurchaseOrderLine, self).write(vals)
