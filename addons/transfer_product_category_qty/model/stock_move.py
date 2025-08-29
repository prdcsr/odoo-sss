from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = "stock.move"

    product_categ_id = fields.Many2one(
        'product.category',
        related='product_id.categ_id',
        string='Product Category',
        store=True
    )
