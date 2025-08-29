from odoo import models, fields
from datetime import datetime, time

class StockQuantityHistoryInherit(models.TransientModel):
    _inherit = 'stock.quantity.history'

    inventory_datetime = fields.Datetime(
        string='Inventory at Date',
        help="Choose a date to get the inventory at that date",
        default=lambda self: datetime.combine(fields.Datetime.now().date(), time(16, 59, 59))
    )
