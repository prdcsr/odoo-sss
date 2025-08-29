# -*- coding: utf-8 -*-
from odoo import api, fields, models

class AccountAccount(models.Model):
    _inherit = "account.account"

    use_yearly_rate = fields.Boolean(
        string="Use Yearly FX",
        help="If enabled, move lines posted to this account will convert foreign currency using Yearly FX."
    )

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _should_use_yearly(self):
        self.ensure_one()
        return bool(self.account_id.use_yearly_rate or (self.move_id and self.move_id.use_yearly_rate))

    @api.onchange("amount_currency", "currency_id", "account_id", "debit", "credit")
    def _onchange_amount_currency_yearly_fx(self):
        for line in self:
            company = line.company_id or (line.move_id and line.move_id.company_id)
            currency = line.currency_id
            if not company or not currency or currency == company.currency_id:
                continue
            if not line._should_use_yearly():
                continue
            if not line.amount_currency and not line.debit and not line.credit:
                continue

            date = line.date or (line.move_id and line.move_id.date) or fields.Date.context_today(self)
            amount_company = self.env["yearly.fx.mixin"]._convert_amount_yearly(
                line.amount_currency, currency, company, date
            )
            if amount_company >= 0:
                line.debit = amount_company
                line.credit = 0.0
            else:
                line.debit = 0.0
                line.credit = -amount_company

    def _get_fields_onchange_balance_model(self, quantity, discount, balance, move_type, currency, taxes, price_subtotal, force_computation=False):
        res = super(AccountMoveLine, self)._get_fields_onchange_balance_model(quantity, discount, balance, move_type, currency, taxes, price_subtotal, force_computation)
        for line in self:
            company = line.company_id or (line.move_id and line.move_id.company_id)
            currency = line.currency_id
            if not company or not currency or currency == company.currency_id:
                continue
            if not line._should_use_yearly():
                continue
            date = line.date or (line.move_id and line.move_id.date) or fields.Date.context_today(self)
            amount_company = self.env["yearly.fx.mixin"]._convert_amount_yearly(
                line.amount_currency, currency, company, date
            )
            if amount_company >= 0:
                line.debit = amount_company
                line.credit = 0.0
            else:
                line.debit = 0.0
                line.credit = -amount_company
        return res
