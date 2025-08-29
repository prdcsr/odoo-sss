from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    _sql_constraints = [('order_product_uniq', 'unique (order_id,product_id)',     
                 'Duplicate products in order line not allowed !')]


