from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    product_specification = fields.Char(
        name='Vendor Product Specification',
    )

