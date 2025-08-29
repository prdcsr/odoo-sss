from odoo import api, models

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id', 'price_unit')
    def _check_last_price(self):
        if self.product_id and self.price_unit:
            # Get last purchase order for same vendor & product
            last_order = self.env['purchase.order'].search([
                ('partner_id', '=', self.order_id.partner_id.id),
                ('order_line.product_id', '=', self.product_id.id),
                ('state', 'in', ['purchase', 'done'])
            ], order='date_order desc', limit=1)

            last_line = False
            if last_order:
                last_line = last_order.order_line.filtered(
                    lambda l: l.product_id.id == self.product_id.id
                )[:1]

            if last_line:
                last_price = last_line.price_unit
                price_diff = abs(self.price_unit - last_price)
                if last_price > 0:
                    diff_percent = (price_diff / last_price) * 100
                    if diff_percent > 10:
                        return {
                            'warning': {
                                'title': "Price Difference Warning",
                                'message': (
                                    f"Pembelian Terakhir untuk '{self.product_id.display_name}' "
                                    f"Dari Vendor {self.order_id.partner_id.name} Adalah {last_price:.2f}.\n"
                                    f"Hasil Input Adalah {self.price_unit:.2f} "
                                )
                            }
                        }
