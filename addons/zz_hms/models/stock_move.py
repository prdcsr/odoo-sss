from odoo import models, fields,api

class StockMove(models.Model):
    _inherit = 'stock.move'

    product_categ_id = fields.Many2one(
        'product.category',
        related='product_id.categ_id',
        string='Product Category',
        store=True
    )

    depleted = fields.Boolean(string="Habis")
    # actual_cost = fields.Float(
    #     string='Total',
    #     compute='_compute_actual_cost',
    # )
    picking_type_name = fields.Char(related="picking_id.picking_type_id.name", store=True,readonly=True)

    # @api.depends('product_id', 'product_uom_qty')
    # def _compute_actual_cost(self):
    #     for move in self:
    #         if move.product_id and move.product_uom_qty:
    #             move.actual_cost = move.product_uom_qty * move.product_id.standard_price
    #         else:
    #             move.actual_cost = 0.0
