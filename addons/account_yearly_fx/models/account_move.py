# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    use_yearly_rate = fields.Boolean(
        string="Use Yearly FX (Override)",
        help="If enabled, this JE uses Yearly FX for foreign-currency lines."
    )

    @api.onchange("use_yearly_rate")
    def _onchange_use_yearly_rate_recompute(self):
        helper = self.env["yearly.fx.mixin"]
        for move in self:
            company = move.company_id
            date = move.date or fields.Date.context_today(self)
            for line in move.line_ids:
                currency = line.currency_id
                if not currency or currency == company.currency_id:
                    continue
                use_yearly = bool(move.use_yearly_rate or (line.account_id and line.account_id.use_yearly_rate))
                if line.amount_currency:
                    amt = (helper._convert_amount_yearly(line.amount_currency, currency, company, date)
                           if use_yearly else
                           helper._convert_amount_daily(line.amount_currency, currency, company, date))
                    line.debit = amt if amt >= 0 else 0.0
                    line.credit = -amt if amt < 0 else 0.0

    def post(self):
        helper = self.env["yearly.fx.mixin"]
        for move in self:
            company = move.company_id
            date = move.date or fields.Date.context_today(self)
            for line in move.line_ids:
                currency = line.currency_id
                if not currency or currency == company.currency_id:
                    continue
                use_yearly = bool(move.use_yearly_rate or (line.account_id and line.account_id.use_yearly_rate))
                if use_yearly:
                    helper._get_yearly_rate(currency, company, date)
                if line.amount_currency:
                    amt = (helper._convert_amount_yearly(line.amount_currency, currency, company, date)
                           if use_yearly else
                           helper._convert_amount_daily(line.amount_currency, currency, company, date))
                    line.debit = amt if amt >= 0 else 0.0
                    line.credit = -amt if amt < 0 else 0.0
        return super(AccountMove, self).post()
