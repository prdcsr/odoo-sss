from odoo import models, fields, api


class InventoryValuationLine(models.TransientModel):
    _name = 'fifo.inventory.valuation.line'
    _description = 'FIFO Inventory Valuation Line'

    wizard_id = fields.Many2one('fifo.inventory.valuation.wizard', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    quantity = fields.Float(string='Quantity')
    cost = fields.Float(string='Unit Cost')
    total_value = fields.Float(string='Total Value', compute='_compute_total_value', store=True)

    @api.depends('quantity', 'cost')
    def _compute_total_value(self):
        for line in self:
            line.total_value = line.quantity * line.cost
