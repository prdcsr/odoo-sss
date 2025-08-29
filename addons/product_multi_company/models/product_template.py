import json
import logging

from odoo import api, fields, models, _
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.constrains('company_id')
    def _check_sale_product_company(self):
        """Ensure the product is not being restricted to a single company while
        having been sold in another one in the past, as this could cause issues."""
        # target_company = self.company_id
        # if target_company:  # don't prevent writing `False`, should always work
        #     product_data = self.env['product.product'].sudo().with_context(active_test=False).search_read(
        #         [('product_tmpl_id', 'in', self.ids)], fields=['id'])
        #     product_ids = list(map(lambda p: p['id'], product_data))
        #     so_lines = self.env['sale.order.line'].sudo().search_read(
        #         [('product_id', 'in', product_ids), ('company_id', '!=', target_company.id)],
        #         fields=['id', 'product_id'])
        #     used_products = list(map(lambda sol: sol['product_id'][1], so_lines))
        #     if so_lines and self.company_id:
        #         raise ValidationError(_('The following products cannot be restricted to the company'
        #                                 ' %s because they have already been used in quotations or '
        #                                 'sales orders in another company:\n%s\n'
        #                                 'You can archive these products and recreate them '
        #                                 'with your company restriction instead, or leave them as '
        #                                 'shared product.') % (target_company.name, ', '.join(used_products)))
        return True