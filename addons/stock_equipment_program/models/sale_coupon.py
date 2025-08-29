import random
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _


class SaleCoupon(models.Model):
    _inherit = 'sale.coupon'
    _description = "Stock Equipment"

    picking_id = fields.Many2one('stock.picking', 'Order Reference', readonly=True,
                                 help="The sales order from which coupon is generated")
    stock_picking_id = fields.Many2one('stock.picking', 'Applied on order', readonly=True,
                                       help="The sales order on which the coupon is applied")