from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    loyalty_points = fields.Float(string='Loyalty Points',
                                  help='The amount of Loyalty points awarded '
                                       'to the customer with this order',
                                  compute='_compute_loyalty_point',
                                  store=True
                                  )

    loyalty_id = fields.Many2one(comodel_name='sale.loyalty.program',
                                 string='Sale Loyalty Program',
                                 help='The loyalty program used by this sale')

    @api.depends('loyalty_id', 'order_line')
    def _compute_loyalty_point(self):
        for dat in self:
            loyalty_program = dat.loyalty_id
            product_points = 0
            currency_points = 0

            if dat.order_line:

                for line in dat.order_line:
                    product = line.product_id
                    for rule in loyalty_program.rule_ids:
                        if rule.type == 'category' and rule.category_id == product.categ_id:
                            product_points = rule.pp_product * line.product_uom_qty
                            currency_points = rule.pp_currency * line.price_subtotal
                        elif rule.type == 'product' and rule.product_id == product:
                            product_points = rule.pp_product * line.product_uom_qty
                            currency_points = rule.pp_currency * line.price_subtotal

            loyalty_points = product_points + currency_points
            dat.write({
                'loyalty_points': loyalty_points
            })
