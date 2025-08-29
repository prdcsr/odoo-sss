from odoo import models, fields, api

class Highlight(models.AbstractModel):
    _inherit = "product.template"

    is_highlighted = fields.Boolean(string="Highlight in Report")