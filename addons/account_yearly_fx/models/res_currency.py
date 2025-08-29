# -*- coding: utf-8 -*-
from odoo import fields, models

class ResCurrency(models.Model):
    _inherit = "res.currency"

    yearly_rate_ids = fields.One2many(
        "res.currency.yearly.rate", "currency_id",
        string="Yearly FX Rates"
    )
