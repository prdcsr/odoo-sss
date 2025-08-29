from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    helper_uom_id = fields.Many2one(
        'uom.uom', string='Helper UoM',
        help='Select another UoM to input the quantity'
    )
    helper_qty = fields.Float(
        string='Quantity in Helper UoM',
        help='Quantity in selected helper UoM',
    )

    @api.onchange('helper_uom_id', 'helper_qty', 'product_id')
    def _onchange_helper_qty(self):
        for line in self:
            if line.product_id and line.helper_uom_id and line.helper_qty:
                base_uom = line.product_uom_id
                helper_uom = line.helper_uom_id
                # Check category match
                if helper_uom.category_id.id != base_uom.category_id.id:
                    raise ValidationError(
                        f"Unit mismatch: '{helper_uom.name}' ('{helper_uom.category_id.name}') and '{base_uom.name}' ('{base_uom.category_id.name}') must be in the same category!"
                    )
                # Convert and set base UoM qty
                line.product_qty = helper_uom._compute_quantity(line.helper_qty, base_uom)
