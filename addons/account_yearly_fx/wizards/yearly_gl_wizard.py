# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class YearlyGlWizard(models.TransientModel):
    _name = "yearly.gl.wizard"
    _description = "General Ledger (Daily vs Yearly FX)"

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    account_ids = fields.Many2many("account.account", string="Accounts")
    only_flagged = fields.Boolean(string="Only Accounts using Yearly FX", default=True)
    show_yearly = fields.Boolean(string="Show Yearly Column", default=True)
    show_daily = fields.Boolean(string="Show Daily Column", default=True)

    def action_print(self):
        self.ensure_one()
        if not self.show_daily and not self.show_yearly:
            raise UserError(_("Please enable at least one column (Daily/Yearly)."))
        return self.env.ref("account_yearly_fx.report_yearly_gl").report_action(self)
