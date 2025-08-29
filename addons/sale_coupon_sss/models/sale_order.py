# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime

from duckdb import limit

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # def _get_reward_values_percentage_amount(self, program):
    #     values = super(SaleOrder, self)._get_reward_values_percentage_amount(program)
    #     for value in values:
    #         if program.is_incentive and program.discount_max_amount > 1:
    #             disc_amount = value['price_unit'] * -1 if value['price_unit'] < 0 else value['price_unit']
    #             if disc_amount >= program.discount_max_amount:
    #                 program.write({
    #                     'discount_max_amount': 1
    #                 })
    #                 value['price_unit'] = disc_amount
    #             else:
    #                 program.write({
    #                     'discount_max_amount': program.discount_max_amount - disc_amount
    #                 })
    #
    #     return values

    def _create_new_no_code_promo_reward_lines(self):
        '''Apply new programs that are applicable'''
        self.ensure_one()
        super(SaleOrder, self)._create_new_no_code_promo_reward_lines()
        order = self
        programs = order._get_applicable_no_code_promo_program()
        programs = programs._keep_only_most_interesting_auto_applied_global_discount_program()
        for program in programs:
            for value in self._get_reward_line_values(program):
                if program.is_incentive and program.discount_max_amount > 1:
                    disc_amount = value['price_unit'] * -1 if value['price_unit'] < 0 else value['price_unit']
                    disc_inc_tax = disc_amount + round(11/100*disc_amount)
                    if disc_inc_tax >= program.discount_max_amount:

                        for line in self.order_line.filtered(lambda x: x.product_id == program.discount_line_product_id):
                            line.write({
                                'price_unit': round(program.discount_max_amount / 1.11) * -1
                            })

                        program.write({
                            'discount_max_amount': 1,
                            'rule_date_to': fields.Datetime.now()
                        })
                    else:
                        program.write({
                            'discount_max_amount': program.discount_max_amount - disc_amount
                        })

    def action_cancel(self):
        super(SaleOrder, self).action_cancel()
        start_date = datetime.date(self.date_order.year, 1,1)
        end_date = datetime.date(self.date_order.year, 12,31)
        for line in self.order_line:
            if line.is_reward_line:
                prog = self.env['sale.coupon.program'].search([
                    ('discount_line_product_id', '=', line.product_id.id),
                    ('rule_date_to', '<=', end_date),
                    ('rule_date_to', '>=', start_date)
                ], order = 'rule_date_to desc', limit = 1)

                amount = abs(line.price_unit + (line.price_unit * 11/100))
                prog.write({
                    'discount_max_amount': prog.discount_max_amount + amount if prog.discount_max_amount > 1 else prog.discount_max_amount + amount - 1,
                    'rule_date_to': end_date
                })
                line.unlink()

    # def _get_reward_values_product(self):
    #     line =  super(SaleOrder, self)._get_reward_values_product()
    #     logging_model = self.env['ir.logging']
    #     logging_model.create({
    #         'type': 'client',  # Or 'server'
    #         'name': 'sale oder coupon Log',
    #         'path': 'D:\odoo-yasuka\addons\sale_coupon_sss\models\sale_order.py',
    #         'line': 82,  # Or the relevant line number
    #         'func': '_get_reward_values_product',
    #         'message': line
    #     })
    #     return line


    # def _update_existing_reward_lines(self):
    #     self.ensure_one()
    #     order = self
    #     super(SaleOrder, self)._update_existing_reward_lines()
    #     applied_programs = order._get_applied_programs_with_rewards_on_current_order()
    #
    #     for program in applied_programs.sorted(lambda ap: (ap.discount_type == 'fixed_amount', ap.discount_apply_on == 'on_order')):
    #         # values = order._get_reward_line_values(program)
    #         for value in self._get_reward_line_values(program):
    #             if program.is_incentive and program.discount_max_amount > 1:
    #                 disc_amount = value['price_unit'] * -1 if value['price_unit'] < 0 else value['price_unit']
    #                 if disc_amount >= program.discount_max_amount:
    #                     program.write({
    #                         'discount_max_amount': 1,
    #                         'rule_date_to': fields.Datetime.now()
    #                     })
    #                 else:
    #                     program.write({
    #                         'discount_max_amount': program.discount_max_amount - disc_amount
    #                     })
