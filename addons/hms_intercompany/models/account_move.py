from odoo import models

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super().action_post()

        for move in self:
            if move.type not in ('out_invoice', 'out_refund'):
                continue

            sale_order = self.env['sale.order'].search([('name', '=', move.invoice_origin)], limit=1)
            if not sale_order or not sale_order.intercompany_toggle:
                continue

            for line in move.line_ids:
                if line.product_id and line.debit > 0:
                    category = line.product_id.categ_id
                    interco_account = category.intercompany_account
                    if interco_account:
                        line.account_id = interco_account.id

        return res
