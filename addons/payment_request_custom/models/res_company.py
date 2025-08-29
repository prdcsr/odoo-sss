# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.Model):
    _inherit = 'res.company'

    payment_tax_account_id = fields.Many2one(
        'account.account', 'Payment Tax Account')

    import_tax_account_id = fields.Many2one(
        'account.account', 'Import Tax Account')

    import_duty_account_id = fields.Many2one(
        'account.account', 'Import Duty Account')

    account_payable_id = fields.Many2one(
        'account.account', 'Account Payable')

    payment_request_journal_id = fields.Many2one(
        'account.journal', 'Payment Request Journal'
    )
