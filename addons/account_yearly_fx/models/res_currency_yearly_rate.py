# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ResCurrencyYearlyRate(models.Model):
    _name = "res.currency.yearly.rate"
    _description = "Yearly Currency Rate"
    _order = "currency_id, company_id, year desc"
    _rec_name = "display_name"

    currency_id = fields.Many2one("res.currency", required=True, ondelete="cascade")
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    year = fields.Integer(required=True, help="Fiscal year (e.g., 2025)")
    rate = fields.Float(required=True, digits=(16, 6),
                        help="Company currency per 1 foreign unit (e.g., 1 USD = 15800 IDR)")

    display_name = fields.Char(compute="_compute_display_name", store=False)

    @api.depends("currency_id", "company_id", "year", "rate")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s | %s | %s: %s" % (
                rec.company_id.name,
                rec.currency_id.name,
                rec.year,
                rec.rate,
            )

    _sql_constraints = [
        ("uniq_year_currency_company",
         "unique(currency_id, company_id, year)",
         "Yearly rate per Currency/Company/Year must be unique."),
    ]

    @api.constrains("year")
    def _check_year(self):
        for rec in self:
            if rec.year < 1900 or rec.year > 2100:
                raise ValidationError(_("Year must be between 1900 and 2100."))
