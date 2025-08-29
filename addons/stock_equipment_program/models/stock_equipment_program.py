
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


class SaleCouponProgram(models.Model):
    _name = 'stock.equipment.program'
    _description = "Stock Equipment Program"
    # _inherits = {'stock.equipment.rule': 'rule_id', 'stock.equipment.product': 'reward_id'}

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean('Active', default=True, help="A program is available for the customers when active")
    # rule_id = fields.Many2one('stock.equipment.rule', string="Stocking Rule", ondelete='restrict', required=True)
    # reward_id = fields.Many2one('stock.equipment.product', string="Stock Equipment", ondelete='restrict', required=True, copy=False)
    sequence = fields.Integer(copy=False,
                              help="Coupon program will be applied based on given sequence if multiple programs are " +
                                   "defined on same condition(For minimum amount)")
    maximum_use_number = fields.Integer(help="Maximum number of sales orders in which reward can be provided")
    program_type = fields.Selection([
        ('promotion_program', 'Promotional Program'),
        ('coupon_program', 'Coupon Program'),
    ],
        help="""A promotional program can be either a limited promotional offer without code (applied automatically)
                    or with a code (displayed on a magazine for example) that may generate a discount on the current
                    order or create a coupon for a next order.

                    A coupon program generates coupons with a code that can be used to generate a discount on the current
                    order or create a coupon for a next order.""")
    promo_code_usage = fields.Selection([
        ('no_code_needed', 'Automatically Applied'),
        ('code_needed', 'Use a code')],
        default='no_code_needed',
        help="Automatically Applied - No code is required, if the program rules are met, the reward is applied (Except the global discount or the free shipping rewards which are not cumulative)\n" +
             "Use a code - If the program rules are met, a valid code is mandatory for the reward to be applied\n")
    promo_code = fields.Char('Promotion Code', copy=False,
                             help="A promotion code is a code that is associated with a marketing discount. For example, a retailer might tell frequent customers to enter the promotion code 'THX001' to receive a 10%% discount on their whole order.")
    promo_applicability = fields.Selection([
        ('on_current_order', 'Apply On Current Order'),
        ('on_next_order', 'Apply On Next Order')],
        default='on_current_order', string="Applicability")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    validity_duration = fields.Integer(default=1,
                                       help="Validity duration for a coupon after its generation")
    order_count = fields.Integer(compute='_compute_order_count')

    rule_date_from = fields.Datetime(string="Start Date", help="Coupon program start date")
    rule_date_to = fields.Datetime(string="End Date", help="Coupon program end date")
    rule_partners_domain = fields.Char(string="Based on Customers",
                                       help="Coupon program will work for selected customers only")
    rule_products_domain = fields.Char(string="Based on Products", default=[['purchase_ok', '=', True]],
                                       help="On Purchase of selected product, reward will be given")
    rule_min_quantity = fields.Integer(string="Minimum Quantity", default=1,
                                       help="Minimum required product quantity to get the reward")

    reward_description = fields.Char('Reward Description')
    reward_type = fields.Selection([
        # ('discount', 'Discount'),
        ('product', 'Free Product'),
    ], string='Reward Type', default='product',
        help="Discount - Reward will be provided as discount.\n" +
             "Free Product - Free product will be provide as reward \n" +
             "Free Shipping - Free shipping will be provided as reward (Need delivery module)")
    # Product Reward
    reward_product_id = fields.Many2one('product.product', string="Package Product",
                                        help="Package Product")
    reward_product_quantity = fields.Integer(string="Quantity", default=1, help="Reward product quantity")
    # Discount Reward
    discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount')], default="percentage",
        help="Percentage - Entered percentage discount will be provided\n" +
             "Amount - Entered fixed amount discount will be provided")
    discount_percentage = fields.Float(string="Discount", default=10,
                                       help='The discount in percentage, between 1 to 100')
    discount_apply_on = fields.Selection([
        ('on_order', 'On Order'),
        ('cheapest_product', 'On Cheapest Product'),
        ('specific_products', 'On Specific Products')], default="on_order",
        help="On Order - Discount on whole order\n" +
             "Cheapest product - Discount on cheapest product of the order\n" +
             "Specific products - Discount on selected specific products")
    discount_specific_product_ids = fields.Many2many('product.product', string="Products",
                                                     help="Products that will be discounted if the discount is applied on specific products")
    discount_max_amount = fields.Float(default=0,
                                       help="Maximum amount of discount that can be provided")
    discount_fixed_amount = fields.Float(string="Fixed Amount", help='The discount in fixed amount')
    reward_product_uom_id = fields.Many2one(related='reward_product_id.product_tmpl_id.uom_id',
                                            string='Unit of Measure', readonly=True)
    discount_line_product_id = fields.Many2one('product.product', string='Reward Line Product', copy=False,
                                               help="Product used in the sales order to apply the discount. Each coupon program has its own reward product for reporting purpose")

    rule_minimum_amount = fields.Float(default=0.0, help="Minimum required amount to get the reward")
    rule_minimum_amount_tax_inclusion = fields.Selection([
        ('tax_included', 'Tax Included'),
        ('tax_excluded', 'Tax Excluded')], default="tax_excluded")

    @api.constrains('rule_date_to', 'rule_date_from')
    def _check_rule_date_from(self):
        if any(applicability for applicability in self
               if applicability.rule_date_to and applicability.rule_date_from
                  and applicability.rule_date_to < applicability.rule_date_from):
            raise ValidationError(_('The start date must be before the end date'))

    # @api.constrains('rule_minimum_amount')
    # def _check_rule_minimum_amount(self):
    #     if self.filtered(lambda applicability: applicability.rule_minimum_amount < 0):
    #         raise ValidationError(_('Minimum purchased amount should be greater than 0'))

    @api.constrains('rule_min_quantity')
    def _check_rule_min_quantity(self):
        if not self.rule_min_quantity > 0:
            raise ValidationError(_('Minimum quantity should be greater than 0'))

    @api.constrains('discount_percentage')
    def _check_discount_percentage(self):
        if self.filtered(lambda reward: reward.discount_type == 'percentage' and (
                reward.discount_percentage < 0 or reward.discount_percentage > 100)):
            raise ValidationError(_('Discount percentage should be between 1-100'))

    def name_get(self):
        """
        Returns a complete description of the reward
        """
        result = []
        for reward in self:
            reward_string = ""
            if reward.reward_type == 'product':
                reward_string = _("Free Product - %s" % (reward.reward_product_id.name))
            # elif reward.reward_type == 'discount':
            #     if reward.discount_type == 'percentage':
            #         reward_percentage = str(reward.discount_percentage)
            #         if reward.discount_apply_on == 'on_order':
            #             reward_string = _("%s%% discount on total amount" % (reward_percentage))
            #         elif reward.discount_apply_on == 'specific_products':
            #             if len(reward.discount_specific_product_ids) > 1:
            #                 reward_string = _("%s%% discount on products" % (reward_percentage))
            #             else:
            #                 reward_string = _("%s%% discount on %s" % (reward_percentage, reward.discount_specific_product_ids.name))
            #         elif reward.discount_apply_on == 'cheapest_product':
            #             reward_string = _("%s%% discount on cheapest product" % (reward_percentage))
            #     elif reward.discount_type == 'fixed_amount':
            #         program = self.env['sale.coupon.program'].search([('reward_id', '=', reward.id)])
            #         reward_string = _("%s %s discount on total amount" % (str(reward.discount_fixed_amount), program.currency_id.name))
            result.append((reward.id, reward_string))
        return result

    @api.constrains('promo_code')
    def _check_promo_code_constraint(self):
        """ Program code must be unique """
        for program in self.filtered(lambda p: p.promo_code):
            domain = [('id', '!=', program.id), ('promo_code', '=', program.promo_code)]
            if self.search(domain):
                raise ValidationError(_('The program code must be unique!'))

    # The api.depends is handled in `def modified` of `sale_coupon/models/sale_order.py`
    def _compute_order_count(self):
        product_data = self.env['stock.move'].read_group(
            [('product_id', 'in', self.mapped('discount_line_product_id').ids)], ['product_id'], ['product_id'])
        mapped_data = dict([(m['product_id'][0], m['product_id_count']) for m in product_data])
        for program in self:
            program.order_count = mapped_data.get(program.discount_line_product_id.id, 0)

    @api.depends('coupon_ids')
    def _compute_coupon_count(self):
        coupon_data = self.env['stock.equipment'].read_group([('program_id', 'in', self.ids)], ['program_id'],
                                                         ['program_id'])
        mapped_data = dict([(m['program_id'][0], m['program_id_count']) for m in coupon_data])
        for program in self:
            program.coupon_count = mapped_data.get(program.id, 0)

    @api.onchange('promo_code_usage')
    def _onchange_promo_code_usage(self):
        if self.promo_code_usage == 'no_code_needed':
            self.promo_code = False

    @api.onchange('reward_product_id')
    def _onchange_reward_product_id(self):
        if self.reward_product_id:
            self.reward_product_uom_id = self.reward_product_id.uom_id

    @api.onchange('discount_type')
    def _onchange_discount_type(self):
        if self.discount_type == 'fixed_amount':
            self.discount_apply_on = 'on_order'

    @api.model
    def create(self, vals):
        program = super(SaleCouponProgram, self).create(vals)
        if not vals.get('discount_line_product_id', False):
            # discount_line_product_id = self.env['product.product'].create({
            #     'name': program.display_name,
            #     'type': 'service',
            #     'taxes_id': False,
            #     'supplier_taxes_id': False,
            #     'sale_ok': False,
            #     'purchase_ok': False,
            #     'invoice_policy': 'order',
            #     'lst_price': 0,  # Do not set a high value to avoid issue with coupon code
            # })
            program.write({'discount_line_product_id': vals['reward_product_id']})
        return program

    def write(self, vals):
        res = super(SaleCouponProgram, self).write(vals)
        reward_fields = [
            'reward_type', 'reward_product_id', 'discount_type', 'discount_percentage',
            'discount_apply_on', 'discount_specific_product_ids', 'discount_fixed_amount'
        ]
        if any(field in reward_fields for field in vals):
            self.mapped('discount_line_product_id').write({'name': self[0].reward_product_id.display_name})
        return res

    def unlink(self):
        for program in self.filtered(lambda x: x.active):
            raise UserError(_('You can not delete a program in active state'))
        return super(SaleCouponProgram, self).unlink()

    def toggle_active(self):
        super(SaleCouponProgram, self).toggle_active()
        for program in self:
            program.discount_line_product_id.active = program.active
        # coupons = self.filtered(lambda p: not p.active and p.promo_code_usage == 'code_needed').mapped('coupon_ids')
        # coupons.filtered(lambda x: x.state != 'used').write({'state': 'expired'})

    # def action_view_sales_orders(self):
    #     self.ensure_one()
    #     orders = self.env['sale.order.line'].search([('product_id', '=', self.discount_line_product_id.id)]).mapped(
    #         'order_id')
    #     return {
    #         'name': _('Sales Orders'),
    #         'view_mode': 'tree,form',
    #         'res_model': 'sale.order',
    #         'search_view_id': [self.env.ref('sale.sale_order_view_search_inherit_quotation').id],
    #         'type': 'ir.actions.act_window',
    #         'domain': [('id', 'in', orders.ids)],
    #         'context': dict(self._context, create=False)
    #     }

    def _is_global_discount_program(self):
        self.ensure_one()
        return self.promo_applicability == 'on_current_order' and \
            self.reward_type == 'discount' and \
            self.discount_type == 'percentage' and \
            self.discount_apply_on == 'on_order'

    def _keep_only_most_interesting_auto_applied_global_discount_program(self):
        '''Given a record set of programs, remove the less interesting auto
        applied global discount to keep only the most interesting one.
        We should not take promo code programs into account as a 10% auto
        applied is considered better than a 50% promo code, as the user might
        not know about the promo code.
        '''
        programs = self.filtered(lambda p: p._is_global_discount_program() and p.promo_code_usage == 'no_code_needed')
        if not programs: return self
        most_interesting_program = max(programs, key=lambda p: p.discount_percentage)
        # remove least interesting programs
        return self - (programs - most_interesting_program)

    def _check_promo_code(self, order, coupon_code):
        message = {}
        if self.maximum_use_number != 0 and self.order_count >= self.maximum_use_number:
            message = {'error': _('Promo code %s has been expired.') % (coupon_code)}
        elif not self._filter_on_mimimum_amount(order):
            message = {'error': _('A minimum of %s %s should be purchased to get the reward') % (
            self.rule_minimum_amount, self.currency_id.name)}
        elif self.promo_code and self.promo_code == order.promo_code:
            message = {'error': _('The promo code is already applied on this order')}
        elif self in order.no_code_promo_program_ids:
            message = {'error': _('The promotional offer is already applied on this order')}
        elif not self.active:
            message = {'error': _('Promo code is invalid')}
        elif self.rule_date_from and self.rule_date_from > fields.Datetime.now() or self.rule_date_to and fields.Datetime.now() > self.rule_date_to:
            message = {'error': _('Promo code is expired')}
        elif order.promo_code and self.promo_code_usage == 'code_needed':
            message = {'error': _('Promotionals codes are not cumulative.')}
        elif self.reward_type == 'free_shipping' and order.applied_coupon_ids.filtered(
                lambda c: c.program_id.reward_type == 'free_shipping'):
            message = {'error': _('Free shipping has already been applied.')}
        elif self._is_global_discount_program() and order._is_global_discount_already_applied():
            message = {'error': _('Global discounts are not cumulative.')}
        elif self.promo_applicability == 'on_current_order' and self.reward_type == 'product' and not order._is_reward_in_order_lines(
                self):
            message = {'error': _('The reward products should be in the sales order lines to apply the discount.')}
        elif not self._is_valid_partner(order.partner_id):
            message = {'error': _("The customer doesn't have access to this reward.")}
        elif not self._filter_programs_on_products(order):
            message = {'error': _(
                "You don't have the required product quantities on your sales order. If the reward is same product quantity, please make sure that all the products are recorded on the sales order (Example: You need to have 3 T-shirts on your sales order if the promotion is 'Buy 2, Get 1 Free'.")}
        elif self.promo_applicability == 'on_current_order' and not self.env.context.get('applicable_coupon'):
            applicable_programs = order._get_applicable_programs()
            if self not in applicable_programs:
                message = {'error': _('At least one of the required conditions is not met to get the reward!')}
        return message

    def _compute_program_amount(self, field, currency_to):
        self.ensure_one()
        return self.currency_id._convert(getattr(self, field), currency_to, self.company_id, fields.Date.today())

    @api.model
    def _filter_on_mimimum_amount(self, order):
        no_effect_lines = order._get_no_effect_on_threshold_lines()
        order_amount = {
            'amount_untaxed': order.amount_untaxed - sum(line.price_subtotal for line in no_effect_lines),
            'amount_tax': order.amount_tax - sum(line.price_tax for line in no_effect_lines)
        }
        program_ids = list()
        for program in self:
            if program.reward_type != 'discount':
                # avoid the filtered
                lines = self.env['stock.move']
            else:
                lines = order.move_ids_without_package.filtered(lambda line:
                                                  line.product_id == program.discount_line_product_id or
                                                  # line.product_id == program.reward_id.discount_line_product_id or
                                                  (program.program_type == 'promotion_program' and line.is_reward_line)
                                                  )
            untaxed_amount = order_amount['amount_untaxed'] - sum(line.price_subtotal for line in lines)
            tax_amount = order_amount['amount_tax'] - sum(line.price_tax for line in lines)
            program_amount = program._compute_program_amount('rule_minimum_amount', order.currency_id)
            if program.rule_minimum_amount_tax_inclusion == 'tax_included' and program_amount <= (
                    untaxed_amount + tax_amount) or program_amount <= untaxed_amount:
                program_ids.append(program.id)

        return self.env['stock.equipment.program'].browse(program_ids)

    @api.model
    def _filter_on_validity_dates(self, order):
        return self.filtered(lambda program:
                             (not program.rule_date_from or program.rule_date_from <= fields.Datetime.now())
                             and
                             (not program.rule_date_to or program.rule_date_to >= fields.Datetime.now())
                             )

    @api.model
    def _filter_promo_programs_with_code(self, order):
        '''Filter Promo program with code with a different promo_code if a promo_code is already ordered'''
        return self.filtered(
            lambda program: program.promo_code_usage == 'code_needed' and program.promo_code != order.promo_code)

    def _filter_unexpired_programs(self, order):
        return self.filtered(
            lambda program: program.maximum_use_number == 0
                            or program.order_count < program.maximum_use_number
                            or program
                            in (order.code_promo_program_id + order.no_code_promo_program_ids)
        )

    def _filter_programs_on_partners(self, order):
        return self.filtered(lambda program: program._is_valid_partner(order.partner_id))

    def _filter_programs_on_products(self, order):
        """
        To get valid programs according to product list.
        i.e Buy 1 imac + get 1 ipad mini free then check 1 imac is on cart or not
        or  Buy 1 coke + get 1 coke free then check 2 cokes are on cart or not
        """
        order_lines = order.move_ids_without_package.filtered(lambda line: line.product_id) - order._get_reward_lines()
        products = order_lines.mapped('product_id')
        products_qties = dict.fromkeys(products, 0)
        for line in order_lines:
            products_qties[line.product_id] += line.product_uom_qty
        valid_program_ids = list()
        for program in self:
            if not program.rule_products_domain:
                valid_program_ids.append(program.id)
                continue
            valid_products = program._get_valid_products(products)
            if not valid_products:
                # The program can be directly discarded
                continue
            ordered_rule_products_qty = sum(products_qties[product] for product in valid_products)
            # Avoid program if 1 ordered foo on a program '1 foo, 1 free foo'
            if program.promo_applicability == 'on_current_order' and \
                    program.reward_type == 'product' and program._get_valid_products(program.reward_product_id):
                ordered_rule_products_qty -= program.reward_product_quantity
            if ordered_rule_products_qty >= program.rule_min_quantity:
                valid_program_ids.append(program.id)
        return self.browse(valid_program_ids)

    def _filter_not_ordered_reward_programs(self, order):
        """
        Returns the programs when the reward is actually in the order lines
        """
        programs = self.env['stock.equipment.program']
        for program in self:
            if program.reward_type == 'product' and \
                    not order.move_ids_without_package.filtered(lambda line: line.product_id == program.reward_product_id):
                continue
            elif program.reward_type == 'discount' and program.discount_apply_on == 'specific_products' and \
                    not order.move_ids_without_package.filtered(
                        lambda line: line.product_id in program.discount_specific_product_ids):
                continue
            programs |= program
        return programs

    @api.model
    def _filter_programs_from_common_rules(self, order, next_order=False):
        """ Return the programs if every conditions is met
            :param bool next_order: is the reward given from a previous order
        """
        programs = self
        # Minimum requirement should not be checked if the coupon got generated by a promotion program (the requirement should have only be checked to generate the coupon)
        if not next_order:
            programs = programs and programs._filter_on_mimimum_amount(order)
        if not self.env.context.get("no_outdated_coupons"):
            programs = programs and programs._filter_on_validity_dates(order)
        # programs = programs and programs.filtered(
        #     lambda program: program.maximum_use_number == 0
        #                     or program.order_count < program.maximum_use_number
        #                     or program
        #                     in (order.code_promo_program_id + order.no_code_promo_program_ids)
        # )
        # programs = programs and programs._filter_programs_on_partners(order)
        # Product requirement should not be checked if the coupon got generated by a promotion program (the requirement should have only be checked to generate the coupon)
        if not next_order:
            programs = programs and programs._filter_programs_on_products(order)

        # programs_curr_order = programs.filtered(lambda p: p.promo_applicability == 'on_current_order')
        # programs = programs.filtered(lambda p: p.promo_applicability == 'on_next_order')
        # if programs_curr_order:
        #     # Checking if rewards are in the SO should not be performed for rewards on_next_order
        #     programs += programs_curr_order._filter_not_ordered_reward_programs(order)
        return programs

    def _is_valid_partner(self, partner):
        if self.rule_partners_domain and self.rule_partners_domain != '[]':
            domain = safe_eval(self.rule_partners_domain) + [('id', '=', partner.id)]
            return bool(self.env['res.partner'].search_count(domain))
        else:
            return True

    def _is_valid_product(self, product):
        # VFE TODO remove in master
        # NOTE: if you override this method, think of also overriding _get_valid_products
        # we also encourage the use of _get_valid_products as its execution is faster
        if self.rule_products_domain:
            domain = safe_eval(self.rule_products_domain) + [('id', '=', product.id)]
            return bool(self.env['product.product'].search_count(domain))
        else:
            return True

    def _get_valid_products(self, products):
        if self.rule_products_domain:
            domain = safe_eval(self.rule_products_domain)
            return products.filtered_domain(domain)
        return products