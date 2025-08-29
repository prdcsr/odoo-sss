# -*- coding: utf-8 -*-
from odoo import models, api, _, fields
from odoo.exceptions import UserError
from datetime import datetime

class YearlyFxMixin(models.AbstractModel):
    _name = "yearly.fx.mixin"
    _description = "Helper mixin for Yearly FX"

    @api.model
    def _get_yearly_rate(self, currency, company, date):
        if not currency or not company:
            return None
        if not isinstance(date, datetime):
            date = fields.Datetime.to_datetime(date)

        Rate = self.env["res.currency.yearly.rate"]
        year = date.year
        rec = Rate.search([
            ("currency_id", "=", currency.id),
            ("company_id", "=", company.id),
            ("year", "=", year),
        ], limit=1)
        if rec:
            return rec.rate

        rec = Rate.search([
            ("currency_id", "=", currency.id),
            ("company_id", "=", company.id),
            ("year", "<=", year),
        ], order="year desc", limit=1)
        if rec:
            return rec.rate

        rec = Rate.search([
            ("currency_id", "=", currency.id),
            ("company_id", "=", company.id),
        ], order="year desc", limit=1)
        if rec:
            return rec.rate

        raise UserError(_(
            "No Yearly FX rate defined for %s in %s. "
            "Please configure it in Accounting > Configuration > Currencies > Yearly FX Rates."
        ) % (currency.name, company.name))

    @api.model
    def _convert_amount_yearly(self, amount_foreign, currency, company, date):
        if not currency or currency == company.currency_id:
            return amount_foreign
        rate = self._get_yearly_rate(currency, company, date)
        return amount_foreign * rate


    @api.model
    def _convert_amount_daily(self, amount_foreign, currency, company, date):
        if not currency or currency == company.currency_id:
            return amount_foreign
        return currency._convert(amount_foreign, company.currency_id, company, date)
