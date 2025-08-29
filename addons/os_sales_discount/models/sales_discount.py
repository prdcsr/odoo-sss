# -*-coding: utf-8 -*-
from odoo import fields, api, models


class SalesOrderInherit(models.Model):
    _inherit = 'sale.order.line'

    discount = fields.Float(string='DiscPrice')
    discount_in_percentage = fields.Float(string='Disc(%)')
    discs_price = fields.Float(string='Disc(%)EqlRps', readonly=True, compute='_get_subtotal')
    product_uom_qty = fields.Float(string='Quantity')
    price_subtotal = fields.Float(string='Subtotal', compute='_get_subtotal')
    price_unit = fields.Float(string='Unit Price')
    discount_price_calculation = fields.Float(string="discount price calculation")
    cal_balance_discount_percentage = fields.Float(string="cal balance_discount_percentage",
                                                   compute='_set_discount_price_calculation')

    balance_discount_percentage = fields.Float(string="balance_discount_percentage",
                                               compute='_set_discount_price_calculation')

    def _set_discount_price_calculation(self):
        for rec in self:
            self.cal_balance_discount_percentage = 0
            self.balance_discount_percentage = 0

            if ((rec.price_unit > 0) & (rec.product_uom_qty > 0)):
                rec.cal_balance_discount_percentage = (rec.discount / (rec.price_unit * rec.product_uom_qty)) * 100
                rec.balance_discount_percentage = (100 - rec.cal_balance_discount_percentage)

    @api.onchange('discount_in_percentage')
    def _get_perce_calculation(self):
        for rec in self:
            if (rec.discount_in_percentage + rec.cal_balance_discount_percentage) > 100:
                rec.discount_in_percentage = rec.balance_discount_percentage

    @api.onchange('discount')
    def _get_price_calculation(self):
        for rec in self:
            if (rec.discs_price + rec.discount) > (rec.product_uom_qty * rec.price_unit):
                rec.discount = (rec.price_unit * rec.product_uom_qty) - rec.discs_price

    @api.depends('discount', 'discount_in_percentage', 'discs_price', 'price_unit', 'product_uom_qty')
    def _get_subtotal(self):
        for rec in self:
            rec.discs_price = ((rec.price_unit * rec.product_uom_qty) * (rec.discount_in_percentage / 100))
            rec.price_subtotal = (rec.price_unit * rec.product_uom_qty) - rec.discs_price - rec.discount

    @api.onchange('discount_in_percentage')
    def _get_discount_in_percentage(self):
        for rec in self:
            if rec.discount_in_percentage > 100:
                rec.discount_in_percentage = 100

    @api.onchange('discount')
    def _get_discount(self):
        for rec in self:
            if rec.discount > rec.product_uom_qty * rec.price_unit:
                rec.discount = rec.product_uom_qty * rec.price_unit


class SaleMonetaryInherit(models.Model):
    _inherit = 'sale.order'
    extra_discount_in_price = fields.Monetary(string='Order Discount Fixed Amount')
    extra_discount_in_percentage = fields.Float(string='Order Discount Fixed Percentage')
    discounts = fields.Monetary(string='Total Product Discount Fixed Amount', readonly=True)
    discount_in_percentage = fields.Monetary(string='DiscIn(%)')
    discs_price = fields.Float(string='Total Product Discount Equal Price', readonly=True)
    amount_total = fields.Float(string='Total', readonly=True, compute='_get_total')
    discounted_price = fields.Float(string='Discounted Price')
    amount_untaxed = fields.Monetary(string='Untaxed_Amount')
    amount_tax = fields.Monetary(string='Taxes')
    ex_disc_price = fields.Monetary(string='Order Discount Fixed Amount', readonly=True, compute='get_extra_discount')
    ex_disc_perc = fields.Monetary(string='Order Discount Fixed Percentage', readonly=True,
                                   compute='get_extra_discount')
    ex_dis_perc_eql_price = fields.Monetary(string='Order Discount Fixed Percentage Equal Amount', readonly=True,
                                            compute='_get_extra_disc')

    undisc_price = fields.Monetary(string='Untaxed_Amount', readonly=True, compute='set_untaxed_amount')

    cal_balance_extra_discount_percentage = fields.Float(string="cal balance_extra_discount_percentage",
                                                         compute='_set_extra_discount_percentage_calculation')
    balance_extra_discount_percentage = fields.Float(string="balance_extra_discount_percentage",
                                                     compute='_set_extra_discount_percentage_calculation')
    test_value = fields.Float(string='test_value', compute='_get_calculate_ex_disc')
    test_val = fields.Float(string='test_val', compute='_get_calculate_ex_disc')

    def _set_extra_discount_percentage_calculation(self):
        for rec in self:
            self.cal_balance_extra_discount_percentage = 0
            self.balance_extra_discount_percentage = 0

            if (rec.amount_untaxed > 0):
                rec.cal_balance_extra_discount_percentage = (rec.extra_discount_in_price / rec.amount_untaxed) * 100
                rec.balance_extra_discount_percentage = (100 - rec.cal_balance_extra_discount_percentage)

    @api.onchange('extra_discount_in_percentage')
    def _set_extra_disc_perce_calc(self):
        for rec in self:
            if (rec.extra_discount_in_percentage + rec.cal_balance_extra_discount_percentage) > 100:
                rec.extra_discount_in_percentage = rec.balance_extra_discount_percentage

    @api.depends('order_line.discount', 'order_line.discount_in_percentage', 'order_line')
    @api.onchange('order_line')
    def _set_discount(self):
        self.discounts = 0
        self.discount_in_percentage = 0
        self.discs_price = 0

        for rec in self.order_line:
            self.discounts += rec.discount
            self.discs_price += rec.discs_price
            self.discount_in_percentage += rec.discount_in_percentage / 100

    def get_extra_discount(self):
        for ext in self:
            ext.ex_disc_perc = ext.extra_discount_in_percentage / 100
            ext.ex_disc_price = ext.extra_discount_in_price

    @api.depends('order_line', 'order_line.product_uom_qty', 'order_line.price_unit')
    @api.onchange('undisc_price')
    def set_untaxed_amount(self):
        for uta in self:
            uta.undisc_price = 0.0

            for line in uta.order_line:
                uta.undisc_price += line.product_uom_qty * line.price_unit

    def _get_extra_disc(self):
        for disc in self:
            disc.ex_dis_perc_eql_price = (disc.undisc_price - disc.discs_price - disc.discounts) * (
                    disc.extra_discount_in_percentage / 100)

    def _get_total(self):
        for tot in self:
            tot.amount_total = tot.undisc_price + tot.amount_tax - tot.discs_price - tot.discounts - tot.extra_discount_in_price - tot.ex_dis_perc_eql_price

    @api.onchange('extra_discount_in_percentage')
    def _get_set_extra_discount_in_percentage(self):
        for disc in self:
            if disc.extra_discount_in_percentage > 100:
                disc.extra_discount_in_percentage = 100

    @api.onchange('extra_discount_in_price')
    def _cal_extra_discount_in_price(self):
        for cal in self:
            if cal.extra_discount_in_price > cal.amount_untaxed:
                cal.extra_discount_in_price = cal.amount_untaxed

    @api.depends('ex_dis_perc_eql_price', 'amount_untaxed')
    @api.onchange('extra_discount_in_price')
    def _get_calculate_ex_disc(self):

        for rec in self:

            rec.test_val = (rec.undisc_price - rec.discs_price - rec.discounts) * (rec.extra_discount_in_percentage / 100)
            rec.test_value = (rec.extra_discount_in_price + rec.test_val)

            if (rec.test_value > rec.amount_untaxed):
                rec.extra_discount_in_price = (rec.amount_untaxed - rec.test_val)
