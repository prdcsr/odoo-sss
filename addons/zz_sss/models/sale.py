from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import ValidationError,UserError



#from odoo import api, fields, models, _
from odoo.tools.misc import formatLang


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.constrains('order_line')
    def _check_exist_product_in_line(self):
      for sale in self:
          exist_product_list = []
          for line in sale.order_line:
             if line.product_id.id in exist_product_list:
                raise ValidationError(_("Duplicate product '%s' in the sale order.") % line.product_id.default_code if line.product_id.default_code else line.product_id.name)
             if line.product_id.id:
                exist_product_list.append(line.product_id.id)


    cv_hascreated = fields.Boolean('Is CV Transaction Has Created')

