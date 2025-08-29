import logging
from email.policy import default

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, RedirectWarning, ValidationError, UserError

_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = "product.template"
    product_location_food_cost_ids = fields.One2many('product.food.cost', 'product_tmpl_id', 'Product Location Max Usage')
    variant_location_food_cost_ids = fields.One2many('product.food.cost', 'product_tmpl_id', 'Variant Location Max Usage')


class ProductFoodCost(models.Model):
    _name = 'product.food.cost'

    name = fields.Many2one(
        'stock.location', 'Location',
        ondelete='cascade', required=True,
        help="Location of this product")

    product_id = fields.Many2one(
        'product.product', 'Product Variant',
        help="If not set, the vendor price will apply to all variants of this product.")
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product Template',
        index=True, ondelete='cascade', required = True,
    )

    max_food_cost = fields.Float("Maximum Food Cost", required=True)
    weekend_food_cost = fields.Float("Weekend Food Cost", required=True)
    promotion_food_cost = fields.Float("Promotion Food Cost", required=True)
    # uom_id = fields.Many2one('uom.uom', "Unit of Measure", compute="_compute_uom_id", inverse="_inverse_uom_id")
    uom_id = fields.Many2one('uom.uom', "Unit of Measure")

    @api.onchange('product_tmpl_id')
    def _compute_uom_id(self):
        for line in self:
            if line.product_tmpl_id:
                line.uom_id = line.product_tmpl_id.uom_id

    @api.onchange('uom_id')
    def _inverse_uom_id(self):
        for line in self:
            if line.product_tmpl_id and line.uom_id:
                if line.uom_id.measure_type != line.product_tmpl_id.uom_id.measure_type:
                    raise UserError('Cannot use different type of UoM from product')
