from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        for account in self:
            super(AccountMove, self).action_post()
            if account.invoice_line_ids:
                if account.invoice_line_ids[0].sale_line_ids:
                    sales_order = account.invoice_line_ids[0].sale_line_ids[0].order_id
                    customer = account.partner_id
                    if sales_order.loyalty_id:
                        vals = {
                            'point': sales_order.loyalty_points,
                            'ref_code': sales_order.name,
                            'partner_id': customer.id,
                            'loyalty_id': sales_order.loyalty_id.id
                        }
                        customer.write({
                            'loyalty_points': customer.loyalty_points + sales_order.loyalty_points
                        })
                        self.env['partner.point.history'].create(vals)
