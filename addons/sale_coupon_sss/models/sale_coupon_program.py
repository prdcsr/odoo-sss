# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


class SaleCouponProgram(models.Model):
    _inherit = 'sale.coupon.program'

    is_incentive = fields.Boolean("Insentif")
    incentive_total = fields.Float("Total Insentif")