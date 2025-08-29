# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import models, fields, api
from datetime import date, timedelta
import base64

from odoo.exceptions import UserError


class DailyFoodCostReport(models.AbstractModel):
    _name = 'report.daily_food_cost_report.report_template'
    _description = 'Daily Food Cost Report'

    def _get_report_values(self, docids, data=None):
        analytic_id = self.env.context.get('analytic_id')
        analytic = self.env['account.analytic.account'].browse(analytic_id)
        today = fields.Date.today()

        # Fetch all related move lines
        lines = self.env['account.move.line'].search([
            ('date', '=', today - timedelta(days=2)),
            ('product_id', '!=', False),
            ('analytic_account_id', '=', analytic_id),
            ('account_id', 'in', [221, 91]),
            ('move_id.state', '=', 'posted'),
        ])

        income_data = defaultdict(lambda: {'default_code': '', 'product': '', 'qty': 0.0, 'price': 0.0})
        cost_data = defaultdict(lambda: {'category': '', 'uom': '', 'qty': 0.0, 'value': 0.0, 'products': []})
        excluded_data = defaultdict(lambda: {'category': '', 'uom': '', 'qty': 0.0, 'value': 0.0, 'products': []})

        excluded_categories = ['MISC', 'PACKAGING MATERIAL']
        total_income = 0.0
        total_cost = 0.0

        for line in lines:
            product = line.product_id
            category = product.categ_id.name
            uom = product.uom_id.name or ''
            qty = line.quantity
            amount = line.debit - line.credit
            default_code = product.default_code

            is_income = line.account_id.user_type_id.internal_group == 'income'
            is_expense = line.account_id.user_type_id.internal_group != 'income'

            if is_income:
                key = product.id
                income_data[key]['default_code'] = default_code
                income_data[key]['product'] = product.name
                income_data[key]['qty'] += qty
                income_data[key]['price'] += abs(amount)
                total_income += abs(amount)

            if is_expense:
                target = excluded_data if category in excluded_categories else cost_data
                if category not in target:
                    target[category]['category'] = category
                    target[category]['uom'] = uom
                target[category]['qty'] += qty
                target[category]['value'] += amount
                target[category]['products'].append({
                    'default_code': default_code,
                    'name': product.name,
                    'uom': uom,
                    'qty': qty,
                    'value': amount,
                    'percent_cost': round((amount / total_cost * 100) if total_cost else 0.0, 2),
                    'percent_income': round((amount / total_income * 100) if total_income else 0.0, 2),
                })
                if category not in excluded_categories:
                    total_cost += amount

        income_rows = []
        for val in income_data.values():
            percent = (val['price'] / total_income * 100) if total_income else 0.0
            income_rows.append({
                'default_code': val['default_code'],
                'product': val['product'],
                'qty': val['qty'],
                'price': val['price'],
                'percent': round(percent, 2)
            })

        def format_product_cost_val(data):
            percent_income = (data['value'] / total_income * 100) if total_income else 0.0
            percent_cost = (data['value'] / total_cost * 100) if total_cost else 0.0
            data['percent_income'] = round(percent_income)
            data['percent_cost'] = round(percent_cost)
            return data

        def format_cost_rows(data_dict):
            rows = []
            for val in data_dict.values():
                percent_cost = (val['value'] / total_cost * 100) if total_cost else 0.0
                percent_income = (val['value'] / total_income * 100) if total_income else 0.0
                rows.append({
                    'category': val['category'],
                    'uom': val['uom'],
                    'qty': val['qty'],
                    'value': val['value'],
                    'percent_cost': round(percent_cost, 2),
                    'percent_income': round(percent_income, 2),
                    'products': list(map(format_product_cost_val, val['products'])),
                })
            return rows

        cost_rows = format_cost_rows(cost_data)
        excluded_rows = format_cost_rows(excluded_data)

        overall_percent = (total_cost / total_income * 100) if total_income else 0.0

        val = {
            'analytic': analytic,
            'report_date': today - timedelta(days=2),
            'income_rows': income_rows,
            'cost_rows': cost_rows,
            'excluded_rows': excluded_rows,
            'total_income': round(total_income, 2),
            'total_cost': round(total_cost, 2),
            'overall_percent': round(overall_percent, 2),
        }

        return val


class DailyFoodCostReportSender(models.TransientModel):
    _name = 'daily.food.cost.report.sender'
    _description = 'Send Daily Food Cost Report'

    @api.model
    def send_daily_food_cost_report(self):
        today = fields.Date.today()
        report = self.env.ref('daily_food_cost_report.action_daily_food_cost_report')
        aml_obj = self.env['account.move.line']

        # Target mapping
        target_map = {
            'MAS': 'hms_restrict_user.group_inventory_alsut_manager',
            'MBO': 'hms_restrict_user.group_inventory_btr_manager',
            'MGS': 'hms_restrict_user.group_inventory_gs_manager',
        }

        # Filter move lines
        lines = (aml_obj.search([
            ('date', '=', today - timedelta(days=2)),
            ('product_id', '!=', False),
            ('account_id', 'in', [221, 91]),
            ('analytic_account_id', '!=', False),
        ]))
                 # .filtered(lambda line: line['account_id'].user_type_id.type in ['income', 'expense']))

        # Group by analytic
        analytics = {}
        for line in lines:
            analytic = line.analytic_account_id
            if not analytic:
                continue
            analytics.setdefault(analytic.id, []).append(line)

        for analytic_id, lines in analytics.items():
            analytic = self.env['account.analytic.account'].browse(analytic_id)
            analytic_name = analytic.code or analytic.name

            # Skip if not in mapping
            if analytic_name not in target_map:
                continue

            # Get group users
            group = self.env.ref(target_map[analytic_name])
            users = self.env['res.users'].search([('groups_id', 'in', [group.id])])
            # recipient_emails = users.mapped('partner_id.email')
            recipient_emails = filter(lambda email: email in ['calvintantry888@gmail.com', 'sssidodoo@gmail.com'], users.mapped('partner_id.email'))

            # Generate report with context
            pdf = report.with_context(analytic_id=analytic_id, currency_id=self.env.company.currency_id).render_qweb_pdf([])[0]

            # Send email per user
            mail_template = self.env.ref('daily_food_cost_report.email_template_food_cost_report')
            for email in recipient_emails:
                mail_template.sudo().send_mail(
                    self.id,
                    email_values={
                        'email_to': email,
                        # 'email_cc': 'verentantry@gmail.com,youlasartika19@gmail.com',
                        'email_cc': 'calvintantri888@gmail.com',
                        'attachment_ids': [(0, 0, {
                            'name': f'{analytic_name}_food_cost_report.pdf',
                            'datas': base64.b64encode(pdf),
                            # 'datas_fname': f'{analytic_name}_food_cost_report.pdf',
                            'res_model': 'daily.food.cost.report.sender',
                        })]
                    },
                    force_send=True
                )