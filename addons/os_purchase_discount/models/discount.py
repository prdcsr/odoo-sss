# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Float(string='DiscInPrice', )
    discount_in_percentage = fields.Float(string='DiscIn(%)')
    price_subtotal = fields.Monetary(string="Subtotal", readonly=True, compute='_get_price')
    product_qty = fields.Float(string='Quantity')
    price_unit = fields.Float(string='Unit Price')
    discs_price = fields.Float(string='Disc(%)EqlRps', compute='_get_price')

    @api.depends('discount', 'discount_in_percentage', 'discs_price', 'price_unit', 'product_qty')
    def _get_price(self):
        for rec in self:
            rec.discs_price = ((rec.price_unit * rec.product_qty) * (rec.discount_in_percentage / 100))
            rec.price_subtotal = (rec.price_unit * rec.product_qty) - rec.discs_price - rec.discount


class PurchaseMonetaryInherit(models.Model):
    _inherit = 'purchase.order'

    discounts = fields.Monetary(string='Total Product Discount Fixed Amount', readonly=True)
    discount_in_percentage = fields.Monetary(string='DiscIn(%) ', readonly=True)
    discs_price = fields.Float(string='Total Product Discount Percentage Equal Price', readonly=True)
    amount_total = fields.Float(String='Total', compute='_get_sum')
    discounted_price = fields.Float(string='Discounted Price')
    amount_untaxed = fields.Monetary(string='Untaxed_Amount')
    amount_tax = fields.Monetary(string='Taxes')
    extra_discount_in_price = fields.Monetary(string='Order Discount Fixed Amount')
    extra_discount_percentage = fields.Float(string='Order Discount Fixed Percentage', readonly=False)
    ex_disc_price = fields.Monetary(string='Order Discount Fixed Amount', compute='get_extra')
    ex_disc_perc = fields.Monetary(string='Order Discount Fixed percentage', compute='get_extra')
    ex_dis_perc_eql_price = fields.Monetary(string='Order Discount Fixed Percentage Equal Amount',
                                            compute='_set_extra_disc')

    def _get_sum(self):
        for disc in self:
            disc.discounted_price = disc.amount_untaxed * (disc.discount_in_percentage / 100) * 100

        for rec in self:
            rec.amount_total = rec.amount_untaxed + rec.amount_tax - rec.discounts - rec.discs_price - rec.ex_disc_price - rec.ex_dis_perc_eql_price

    @api.depends('order_line.discount', 'order_line.discount_in_percentage', 'order_line')
    @api.onchange('order_line')
    def set_discount(self):
        self.discounts = 0
        self.discount_in_percentage = 0
        self.discs_price = 0

        for rec in self.order_line:
            self.discounts += rec.discount
            self.discount_in_percentage += rec.discount_in_percentage / 100
            self.discs_price += rec.discs_price

    def get_extra(self):
        for rec in self:
            rec.ex_disc_perc = rec.extra_discount_percentage / 100
            rec.ex_disc_price = rec.extra_discount_in_price

    def _set_extra_disc(self):
        for ext in self:
            ext.ex_dis_perc_eql_price = (ext.amount_untaxed - ext.discs_price - ext.discounts) * (
                    ext.extra_discount_percentage / 100)
