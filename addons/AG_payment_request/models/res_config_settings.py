# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payment_tax_account_id = fields.Many2one(
        'account.account', 'Payment Tax Account', related="company_id.payment_tax_account_id")

    import_tax_account_id = fields.Many2one(
        'account.account', 'Import Tax Account', related="company_id.import_tax_account_id")

    import_duty_account_id = fields.Many2one(
        'account.account', 'Import Duty Account', related="company_id.import_duty_account_id")

    account_payable_id = fields.Many2one(
        'account.account', 'Account Payable', related="company_id.account_payable_id")

    payment_request_journal_id = fields.Many2one(
        'account.journal', 'Payment Request Journal', related="company_id.payment_request_journal_id"
    )
