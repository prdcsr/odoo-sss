from odoo import api, fields, models


class PurchaseOrderType(models.Model):
    _inherit = "purchase.order.type"

    is_import = fields.Boolean("Import")
