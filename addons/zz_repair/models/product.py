import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, RedirectWarning, ValidationError, UserError

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def create(self, vals):
        # Check for duplicate default_code
        default_code = vals.get('default_code')
        if default_code:
            existing_product = self.env['product.template'].search([('default_code', '=', default_code)])
            if existing_product:
                raise UserError('A product with the same Internal Reference already exists.')

        return super(ProductTemplate, self).create(vals)
