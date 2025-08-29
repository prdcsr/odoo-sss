from odoo import api, models, fields


class IrActionsReport(models.Model):
    _inherit = "stock.quant"

    stored_qty = fields.Float(compute='_compute_stored_qty', store=True)

    @api.depends('inventory_quantity')
    def _compute_stored_qty(self):
        for rec in self:
            rec.stored_qty = rec.inventory_quantity