# -*- coding: utf-8 -*-
from collections import defaultdict
from typing import Set, Tuple
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
            ('date', '=', today - timedelta(days=0)),
            ('product_id', '!=', False),
            ('analytic_account_id', '=', analytic_id),
            ('account_id', 'in', [221, 91]),
            ('move_id.state', '=', 'posted'),
        ])

        # === Build SOK Picking Map ===
        sok_picking_map = {}

        for lne in lines:
            name = (lne.name or '').upper()
            if '/SOK/' not in name:
                continue

            try:
                picking_code = name.split(' - ')[0].strip()  # 'ALSUT/SOK/00481'
                warehouse_code = picking_code.split('/')[0].strip().upper()  # 'ALSUT'
            except (IndexError, AttributeError, ValueError):
                continue
        # === Fetch pickings and their depleted moves ===
        sok_picking_names = list(sok_picking_map.values())
        pickings = self.env['stock.picking'].search([
            ('name', 'in', sok_picking_names)
        ])
        moves = self.env['stock.move'].search([
            ('picking_id', 'in', pickings.ids),
            ('depleted', '=', True),
            ('product_id', '!=', False),
        ])

        # === Build (warehouse_code, product_code) pairs that were marked depleted ===
        depleted_keys: Set[Tuple[str, str]] = set()
        for move in moves:
            picking = move.picking_id
            if not picking or not picking.picking_type_id.warehouse_id:
                continue

            warehouse_code = picking.picking_type_id.warehouse_id.code.strip().upper()
            product_code = (move.product_id.default_code or '').strip().upper()
            depleted_keys.add((warehouse_code, product_code))

        income_data = defaultdict(lambda: {
            'default_code': '',
            'product': '',
            'qty': 0.0,
            'price': 0.0
        })
        cost_data = defaultdict(lambda: {
            'category': '',
            'uom': '',
            'qty': 0.0,
            'value': 0.0,
            'products': defaultdict(lambda: {
                'default_code': '',
                'name': '',
                'uom': '',
                'qty': 0.0,
                'value': 0.0,
                'percent_cost': 0.0,
                'percent_income': 0.0,
                'highlighted': False,
            })
        })
        excluded_data = defaultdict(lambda: {
            'category': '',
            'uom': '',
            'qty': 0.0,
            'value': 0.0,
            'products': defaultdict(lambda: {
                'default_code': '',
                'name': '',
                'uom': '',
                'qty': 0.0,
                'value': 0.0,
                'percent_cost': 0.0,
                'percent_income': 0.0})
        })

        excluded_categories = ['MISC', 'PACKAGING MATERIAL']
        color_plate_names = ['YELLOW', 'RED', 'BLUE']
        grouped_income_rows = {
            'Color Plate': {
                'lines': [],
                'total_qty': 0,
                'total_price': 0,
                'total_percentage_income': 0.0,
            },
            'Ala Carte': {
                'lines': [],
                'total_qty': 0,
                'total_price': 0,
                'total_percentage_income': 0.0,
            }
        }
        total_income = 0.0
        total_cost = 0.0

        for line in lines:
            product = line.product_id
            category = product.categ_id.name
            uom = product.uom_id.name or ''
            qty = line.quantity
            amount = line.balance
            default_code = product.default_code
            highlighted = product.product_tmpl_id.is_highlighted
            is_income = line.account_id.user_type_id.internal_group == 'income'
            is_expense = line.account_id.user_type_id.internal_group != 'income'

            if is_income:
                key = product.id
                income_data[key]['default_code'] = default_code
                income_data[key]['product_name'] = product.name
                income_data[key]['product'] = product.display_name
                income_data[key]['qty'] += qty
                income_data[key]['highlighted'] = highlighted
                income_data[key]['price'] += abs(amount)
                total_income += abs(amount)

            if is_expense:
                target = excluded_data if category in excluded_categories else cost_data
                qty *= -1
                # amount *= -1
                if category not in target:
                    target[category]['category'] = category
                    target[category]['uom'] = uom

                key = product.id
                target[category]['qty'] += qty
                target[category]['value'] += amount

                target[category]['products'][key]['default_code'] = default_code
                target[category]['products'][key]['name'] = product.display_name
                target[category]['products'][key]['uom'] = uom
                target[category]['products'][key]['qty'] += qty
                target[category]['products'][key]['highlighted'] = highlighted
                target[category]['products'][key]['value'] += amount
                target[category]['products'][key]['percent_cost'] = round((amount / total_cost * 100) if total_cost else 0.0, 2)
                target[category]['products'][key]['percent_income'] = round((amount / total_income * 100) if total_income else 0.0, 2)
                # target[category]['products'].append({
                #     'default_code': default_code,
                #     'name': product.display_name,
                #     'uom': uom,
                #     'qty': qty,
                #     'value': amount,
                #     'percent_cost': round((amount / total_cost * 100) if total_cost else 0.0, 2),
                #     'percent_income': round((amount / total_income * 100) if total_income else 0.0, 2),
                # })
                if category not in excluded_categories:
                    total_cost += amount

        income_rows = []
        for val in income_data.values():
            percent = (val['price'] / total_income * 100) if total_income else 0.0
            income_rows.append({
                'default_code': val['default_code'],
                'product': val['product'],
                'product_name': val['product_name'],
                'qty': val['qty'],
                'price': val['price'],
                #'highlighted': val['highlighted'],
                'percent': round(percent, 2)
            })

        for row in income_rows:
            if row['product_name'] in color_plate_names:
                category = 'Color Plate'
            else:
                category = 'Ala Carte'
            grouped_income_rows[category]['lines'].append(row)
            grouped_income_rows[category]['total_qty'] += row['qty']
            grouped_income_rows[category]['total_price'] += row['price']
            grouped_income_rows[category]['total_percentage_income'] += row['percent']

        def format_product_cost_val(dict_data):
            rows = []
            for val in dict_data.values():
                percent_income = (val['value'] / total_income * 100) if total_income else 0.0
                percent_cost = (val['value'] / total_cost * 100) if total_cost else 0.0
                is_highlighted = val.get('highlighted', False)
                product_code = val.get('default_code', '').strip().upper()

                warehouse_code = None

                # Find the first line for this product that contains a SOK code, and get warehouse
                for lne in lines:
                    if not lne.product_id:
                        continue
                    if (lne.product_id.default_code or '').strip().upper() != product_code:
                        continue
                    name = (lne.name or '').upper()
                    if '/SOK/' in name:
                        try:
                            picking_code = name.split(' - ')[0].strip()
                            warehouse_code = picking_code.split('/')[0].strip().upper()
                            break  # found one, break
                        except Exception:
                            continue

                missing_sok = is_highlighted and not any(
                    '/SOK/' in (lne.name or '').upper()
                    for lne in lines
                    if lne.product_id and (lne.product_id.default_code or '').strip().upper() == product_code
                )

                depleted_confirmed = missing_sok and warehouse_code and (warehouse_code, product_code) in depleted_keys

                rows.append({
                    'default_code': val['default_code'],
                    'name': val['name'],
                    'uom': val['uom'],
                    'qty': val['qty'],
                    'value': val['value'],
                    'percent_cost': round(percent_cost, 2),
                    'percent_income': round(percent_income, 2),
                    'highlighted': is_highlighted,
                    'missing_sok': missing_sok,
                    'depleted_confirmed': depleted_confirmed,
                })
            return rows

            # percent_income = (data['value'] / total_income * 100) if total_income else 0.0
            # percent_cost = (data['value'] / total_cost * 100) if total_cost else 0.0
            # data['percent_income'] = round(percent_income, 2)
            # data['percent_cost'] = round(percent_cost, 2)
            # return data

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
                    # 'products': list(map(format_product_cost_val, val['products'])),
                    'products': format_product_cost_val(val['products']),
                })
            return rows

        cost_rows = format_cost_rows(cost_data)
        excluded_rows = format_cost_rows(excluded_data)

        overall_percent = (total_cost / total_income * 100) if total_income else 0.0

        val = {
            'analytic': analytic,
            'report_date': today - timedelta(days=0),
            'income_rows': income_rows,
            'cost_rows': cost_rows,
            'excluded_rows': excluded_rows,
            'total_income': round(total_income, 2),
            'total_cost': round(total_cost, 2),
            'overall_percent': round(overall_percent, 2),
            'grouped_income_rows': grouped_income_rows,
            'cost_data': cost_data
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
            ('date', '=', today - timedelta(days=0)),
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
            recipient_emails = users.mapped('partner_id.email')
            recipient_emails += ['verentantry@gmail.com' ,'hmoffice08@gmail.com','fegenwilliam@gmail.com']
            # recipient_emails = filter(lambda email: email in ['calvintantry888@gmail.com', 'sssidodoo@gmail.com'], users.mapped('partner_id.email'))

            # Generate report with context
            pdf = report.with_context(analytic_id=analytic_id, currency_id=self.env.company.currency_id).render_qweb_pdf([])[0]

            # Send email per user
            mail_template = self.env.ref('daily_food_cost_report.email_template_food_cost_report')
            for email in recipient_emails:
                mail_template.sudo().send_mail(
                    self.id,
                    email_values={
                        'email_to': email,
                        #'email_cc': 'verentantry@gmail.com,youlasartika19@gmail.com',
                        # 'email_cc': 'calvintantri888@gmail.com,verentantry@gmail.com,youlasartika19@gmail.com',
                        # 'email_cc': 'calvintantri888@gmail.com',
                        'attachment_ids': [(0, 0, {
                            'name': f'{analytic_name}_food_cost_report_{today}.pdf',
                            'datas': base64.b64encode(pdf),
                            # 'datas_fname': f'{analytic_name}_food_cost_report.pdf',
                            'res_model': 'daily.food.cost.report.sender',
                        })]
                    },
                    force_send=True
                )