from odoo import models, fields, api
from datetime import datetime

PURCHASE_REQUISITION_STATES = [
    ('draft', 'Draft'),
    ('ongoing', 'Ongoing'),
    ('in_progress', 'Confirmed'),
    ('open', 'Bid Selection'),
    ('done', 'Closed'),
    ('cancel', 'Cancelled')
]

class PurchaseRequisitionHistory(models.Model):
    _name = 'purchase.requisition.history'
    _description = 'Purchase Requisition Status & Qty History'
    _order = 'date desc'

    requisition_id = fields.Many2one('purchase.requisition', string='Requisition', required=True)
    line_id = fields.Many2one('purchase.requisition.line', string='Line')
    date = fields.Datetime(string='Change Date', required=True, default=fields.Datetime.now)
    old_status = fields.Selection(PURCHASE_REQUISITION_STATES, string='Old Status')
    new_status = fields.Selection(PURCHASE_REQUISITION_STATES, string='New Status')
    old_ordered_qty = fields.Float(string='Old Ordered Qty')
    new_ordered_qty = fields.Float(string='New Ordered Qty')
    changed_by = fields.Many2one('res.users', string='Changed By', default=lambda self: self.env.user)


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    def write(self, vals):
        for rec in self:
            if 'state' in vals and vals['state'] != rec.state:
                self.env['purchase.requisition.history'].create({
                    'requisition_id': rec.id,
                    'date': fields.Datetime.now(),
                    'old_status': rec.state,
                    'new_status': vals['state'],
                    'changed_by': self.env.user.id
                })
        return super(PurchaseRequisition, self).write(vals)


class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    def write(self, vals):
        for line in self:
            if 'product_qty' in vals and vals['product_qty'] != line.product_qty:
                self.env['purchase.requisition.history'].create({
                    'requisition_id': line.requisition_id.id,
                    'line_id': line.id,
                    'date': fields.Datetime.now(),
                    'old_ordered_qty': line.product_qty,
                    'new_ordered_qty': vals['product_qty'],
                    'changed_by': self.env.user.id
                })
            if 'qty_done' in vals and hasattr(line, 'qty_done') and vals['qty_done'] != line.qty_done:
                self.env['purchase.requisition.history'].create({
                    'requisition_id': line.requisition_id.id,
                    'line_id': line.id,
                    'date': fields.Datetime.now(),
                    'old_ordered_qty': line.qty_done,
                    'new_ordered_qty': vals['qty_done'],
                    'changed_by': self.env.user.id
                })
        return super(PurchaseRequisitionLine, self).write(vals)
