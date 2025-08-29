# Copyright 2017-19 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import _, models
from odoo.exceptions import CacheMiss
from odoo.tools import float_round
from . import cell_constants as constant
from .cell_constants import ROW_START_COL

_logger = logging.getLogger(__name__)


class BomStructureXlsx(models.AbstractModel):
    _name = "report.mrp_bom_structure_xlsx.bom_structure_xlsx"
    _description = "BOM Structure XLSX Report"
    _inherit = "report.report_xlsx.abstract"

    # def print_bom_children(self, ch, sheet, row, level):
    #     i, j = row, level
    #     j += 1
    #     sheet.write(i, 1, "> " * j)
    #     sheet.write(i, 2, ch.product_id.default_code or "")
    #     sheet.write(i, 3, ch.product_id.display_name or "")
    #     sheet.write(
    #         i,
    #         4,
    #         ch.product_uom_id._compute_quantity(ch.product_qty, ch.product_id.uom_id)
    #         or "",
    #     )
    #     sheet.write(i, 5, ch.product_id.uom_id.name or "")
    #     sheet.write(i, 6, ch.bom_id.code or "")
    #     i += 1
    #     # self.env.cache.invalidate()
    #     try:
    #         for child in ch.child_line_ids:
    #             i = self.print_bom_children(child, sheet, i, j)
    #
    #     except CacheMiss:
    #         # The Bom has no childs, thus it is the last level.
    #         # When a BoM has no childs, chlid_line_ids is None, this creates a
    #         # CacheMiss Error. However, this is expected because there really
    #         # cannot be child_line_ids.
    #         pass
    #
    #     j -= 1
    #     return i

    def _get_operation_line(self, routing, qty, level):
        operations = []
        total = 0.0
        for operation in routing.operation_ids:
            operation_cycle = float_round(qty / operation.workcenter_id.capacity, precision_rounding=1, rounding_method='UP')
            duration_expected = operation_cycle * operation.time_cycle + operation.workcenter_id.time_stop + operation.workcenter_id.time_start

            total = ((duration_expected / 60.0) * operation.workcenter_id.costs_hour)
            total += operation.workcenter_id.costs_by_product
            operations.append({
                'level': level or 0,
                'operation': operation,
                'name': operation.name + ' - ' + operation.workcenter_id.name,
                'duration_expected': duration_expected,
                'total': self.env.company.currency_id.round(total),
            })
        return operations

    def _get_price(self, bom, factor, product):
        price = 0
        if bom.routing_id:
            # routing are defined on a BoM and don't have a concept of quantity.
            # It means that the operation time are defined for the quantity on
            # the BoM (the user produces a batch of products). E.g the user
            # product a batch of 10 units with a 5 minutes operation, the time
            # will be the 5 for a quantity between 1-10, then doubled for
            # 11-20,...
            operation_cycle = float_round(factor, precision_rounding=1, rounding_method='UP')
            operations = self._get_operation_line(bom.routing_id, operation_cycle, 0)
            price += sum([op['total'] for op in operations])

        for line in bom.bom_line_ids:
            if line._skip_bom_line(product):
                continue
            if line.child_bom_id:
                qty = line.product_uom_id._compute_quantity(line.product_qty * factor, line.child_bom_id.product_uom_id) / line.child_bom_id.product_qty
                sub_price = self._get_price(line.child_bom_id, qty, line.product_id)
                price += sub_price
            else:
                prod_qty = line.product_qty * factor
                company = bom.company_id or self.env.company
                not_rounded_price = line.product_id.uom_id._compute_price(line.product_id.with_context(force_company=company.id).standard_price, line.product_uom_id) * prod_qty
                price += company.currency_id.round(not_rounded_price)
        return price

    def _get_bom_lines(self, bom, bom_quantity, product, line_id, level):
        components = []
        total = 0
        for line in bom.bom_line_ids:
            line_quantity = (bom_quantity / (bom.product_qty or 1.0)) * line.product_qty
            if line._skip_bom_line(product):
                continue
            company = bom.company_id or self.env.company
            price = line.product_id.uom_id._compute_price(line.product_id.with_context(force_company=company.id).standard_price, line.product_uom_id) * line_quantity
            if line.child_bom_id:
                factor = line.product_uom_id._compute_quantity(line_quantity, line.child_bom_id.product_uom_id) / line.child_bom_id.product_qty
                sub_total = self._get_price(line.child_bom_id, factor, line.product_id)
            else:
                sub_total = price
            sub_total = self.env.company.currency_id.round(sub_total)
            components.append({
                'prod_id': line.product_id.id,
                'prod_name': line.product_id.display_name,
                'code': line.child_bom_id and line.child_bom_id.display_name or '',
                'prod_qty': line_quantity,
                'prod_uom': line.product_uom_id.name,
                'prod_cost': company.currency_id.round(price),
                'parent_id': bom.id,
                'line_id': line.id,
                'level': level or 0,
                'total': sub_total,
                'child_bom': line.child_bom_id.id,
                'location': line.location_id.complete_name or "",
                'phantom_bom': line.child_bom_id and line.child_bom_id.type == 'phantom' or False,
                'attachments': self.env['mrp.document'].search(['|', '&',
                    ('res_model', '=', 'product.product'), ('res_id', '=', line.product_id.id), '&', ('res_model', '=', 'product.template'), ('res_id', '=', line.product_id.product_tmpl_id.id)]),

            })
            total += sub_total
        return components, total

    def get_product_bom(self, bom_id = False, product_id = False, line_qty=False, line_id=False, level=False):
        bom = self.env['mrp.bom'].browse(bom_id)
        company = bom.company_id or self.env.company
        bom_quantity = line_qty

        if line_id:
            current_line = self.env['mrp.bom.line'].browse(int(line_id))
            bom_quantity = current_line.product_uom_id._compute_quantity(line_qty, bom.product_uom_id) or 0

        if product_id:
            product = self.env['product.product'].browse(int(product_id))
        else:
            product = bom.product_id or bom.product_tmpl_id.product_variant_id
        if product:
            price = product.uom_id._compute_price(product.with_context(force_company=company.id).standard_price, bom.product_uom_id) * bom_quantity
            attachments = self.env['mrp.document'].search(['|', '&', ('res_model', '=', 'product.product'),
            ('res_id', '=', product.id), '&', ('res_model', '=', 'product.template'), ('res_id', '=', product.product_tmpl_id.id)])
        else:
            # Use the product template instead of the variant
            price = bom.product_tmpl_id.uom_id._compute_price(bom.product_tmpl_id.with_context(force_company=company.id).standard_price, bom.product_uom_id) * bom_quantity
            attachments = self.env['mrp.document'].search([('res_model', '=', 'product.template'), ('res_id', '=', bom.product_tmpl_id.id)])

        operations = []
        if bom.product_qty > 0:
            operations = self._get_operation_line(bom.routing_id,
                                                  float_round(bom_quantity / bom.product_qty, precision_rounding=1,
                                                              rounding_method='UP'), 0)
        lines = {
            'bom': bom,
            'bom_qty': bom_quantity,
            'bom_prod_name': product.display_name,
            'currency': company.currency_id,
            'product': product,
            'code': bom and bom.display_name or '',
            'price': price,
            'total': sum([op['total'] for op in operations]),
            'level': level or 0,
            'operations': operations,
            'operations_cost': sum([op['total'] for op in operations]),
            'attachments': attachments,
            'operations_time': sum([op['duration_expected'] for op in operations]),
            'location': bom.location_id.complete_name or ""
        }
        components, total = self._get_bom_lines(bom, bom_quantity, product, line_id, level)
        lines['components'] = components
        lines['total'] += total
        return lines

    def generate_xlsx_report(self, workbook, ctx, bom_list):

        def get_sub_lines(bom, product_id, line_qty, line_id, level, child_bom_ids=[]):
            data = self.get_product_bom(bom_id=bom.id, product_id=product_id, line_qty=line_qty, line_id=line_id, level=level)
            bom_lines = data['components']
            lines = []
            for bom_line in bom_lines:
                lines.append({
                    'name': bom_line['prod_name'],
                    'type': 'bom',
                    'quantity': bom_line['prod_qty'],
                    'uom': bom_line['prod_uom'],
                    'prod_cost': bom_line['prod_cost'],
                    'bom_cost': bom_line['total'],
                    'level': bom_line['level'],
                    'code': bom_line['code'],
                    'child_bom': bom_line['child_bom'],
                    'prod_id': bom_line['prod_id'],
                    'location': bom_line['location']
                })
                if bom_line['child_bom'] and (bom_line['child_bom'] in child_bom_ids):
                    line = self.env['mrp.bom.line'].browse(bom_line['line_id'])
                    lines += (
                        get_sub_lines(line.child_bom_id, line.product_id.id, bom_line['prod_qty'], line, level + 1, line.child_bom_id.bom_line_ids.child_bom_id.ids))
            if data['operations']:
                lines.append({
                    'name': _('Operations'),
                    'type': 'operation',
                    'quantity': data['operations_time'],
                    'uom': _('minutes'),
                    'bom_cost': data['operations_cost'],
                    'level': level,
                })
                for operation in data['operations']:
                    # if 'operation-' + str(bom.id) in child_bom_ids:
                    lines.append({
                        'name': operation['name'],
                        'type': 'operation',
                        'quantity': operation['duration_expected'],
                        'uom': _('minutes'),
                        'bom_cost': operation['total'],
                        'level': level + 1,
                    })
            return lines

        self._define_formats(workbook)
        currency = self.env.company.currency_id
        bold_only = workbook.add_format({
            'bold': 1,
            'font_size': 12,
        })
        bold_left = workbook.add_format({
            'bold': 1,
            'font_size': 14,
            'valign': 'vcenter', 'text_wrap': True
        })

        styled_currency = workbook.add_format({
            'num_format': f'{currency.symbol} #,##0.00',
            'valign': 'vcenter', 'text_wrap': True
        })

        bold_currency = workbook.add_format({
            'bold': 1,
            'num_format': f'{currency.symbol} #,##0.00',
            'valign': 'vcenter', 'text_wrap': True
        })

        for bom in bom_list:
            product_id = bom.product_id.id or bom.product_tmpl_id.product_variant_id.id
            data = self.get_product_bom(bom_id=bom.id, product_id=product_id, line_qty=bom.product_qty)
            pdf_lines = get_sub_lines(bom, product_id, bom.product_qty, False, 1, bom.bom_line_ids.child_bom_id.ids)
            data['components'] = []
            data['lines'] = pdf_lines

            sheet = workbook.add_worksheet(_(data['bom_prod_name']))
            sheet.merge_range('A1:F2', 'BoM Structure & Cost', bold_left)
            sheet.merge_range('A4:Z5', data['bom_prod_name'], bold_left)

            sheet.set_column(constant.COL_PRODUCT, constant.COL_PRODUCT, 60)
            sheet.set_column(constant.COL_BOM, constant.COL_BOM, 60)
            sheet.set_column(constant.COL_QTY, constant.COL_QTY, 5)
            sheet.set_column(constant.COL_UOM, constant.COL_UOM, 5)
            sheet.set_column(constant.COL_PRODUCT_COST, constant.COL_PRODUCT_COST, 15)
            sheet.set_column(constant.COL_BOM_COST, constant.COL_BOM_COST, 15)
            sheet.set_column(constant.COL_LOCATION, constant.COL_LOCATION, 10)

            sheet.write(constant.ROW_START_COL, constant.COL_PRODUCT, 'Products', bold_only)
            sheet.write(constant.ROW_START_COL, constant.COL_BOM, 'BOM', bold_only)
            sheet.write(constant.ROW_START_COL, constant.COL_QTY, 'Qty', bold_only)
            sheet.write(constant.ROW_START_COL, constant.COL_UOM, 'UoM', bold_only)
            sheet.write(constant.ROW_START_COL, constant.COL_PRODUCT_COST, 'Product Cost', bold_only)
            sheet.write(constant.ROW_START_COL, constant.COL_BOM_COST, 'BoM Cost', bold_only)
            sheet.write(constant.ROW_START_COL, constant.COL_LOCATION, 'Location', bold_only)

            row_start = ROW_START_COL + 1

            # Write the main product and its BOM
            sheet.write(row_start, constant.COL_PRODUCT, data['bom_prod_name'], bold_only)
            sheet.write(row_start, constant.COL_BOM, data.get('code'), bold_only)
            sheet.write(row_start, constant.COL_QTY, bom.product_qty, bold_only)
            sheet.write(row_start, constant.COL_UOM, bom.product_id.uom_id.name or bom.product_tmpl_id.product_variant_id.uom_id.name, bold_only)

            if 'price' in data:
                # sheet.merge_range('J8:K8', data['price'])
                sheet.write(row_start, constant.COL_PRODUCT_COST, data['price'], bold_currency)
            if 'total' in data:
                # sheet.merge_range('L8:M8', data['total'])
                sheet.write(row_start, constant.COL_BOM_COST, data['total'], bold_currency)
            if 'location' in data:
                location_name = data['location']
                sheet.write(row_start, constant.COL_LOCATION, location_name, bold_only)

            row_start += 1
            for index, product in enumerate(data.get('lines', [])):
                current_row = index + row_start
                space_td = '    ' * product['level']

                sheet.write(current_row, constant.COL_PRODUCT, space_td + product['name'])

                if 'code' in product:
                    sheet.write(current_row, constant.COL_BOM, product['code'])

                sheet.write(current_row, constant.COL_QTY, product['quantity'])

                if 'uom' in product:
                    sheet.write(current_row, constant.COL_UOM, product['uom'])

                if 'prod_cost' in product:
                    sheet.write(current_row, constant.COL_PRODUCT_COST, product['prod_cost'], styled_currency)

                if 'bom_cost' in product:
                    sheet.write(current_row, constant.COL_BOM_COST, product['bom_cost'], styled_currency)

                if 'location' in product:
                    sheet.write(current_row, constant.COL_LOCATION, product['location'])

            # Add the Unit Cost row at the end
            last_row = row_start + len(data.get('lines', []))
            sheet.merge_range(f'A{last_row+1}:D{last_row+1}', 'Unit Cost', bold_only)
            if 'price' in data:
                sheet.write(last_row, constant.COL_PRODUCT_COST, data['price'], bold_currency)

            if 'total' in data:
                sheet.write(last_row, constant.COL_BOM_COST, data['total'], bold_currency)



        workbook.close()


    # def generate_xlsx_report(self, workbook, data, objects):
    #     workbook.set_properties(
    #         {"comments": "Created with Python and XlsxWriter from Odoo 11.0"}
    #     )
    #     sheet = workbook.add_worksheet(_("BOM Structure"))
    #     sheet.set_landscape()
    #     sheet.fit_to_pages(1, 0)
    #     sheet.set_zoom(80)
    #     sheet.set_column(0, 0, 40)
    #     sheet.set_column(1, 2, 20)
    #     sheet.set_column(3, 3, 40)
    #     sheet.set_column(4, 6, 20)
    #     bold = workbook.add_format({"bold": True})
    #     title_style = workbook.add_format(
    #         {"bold": True, "bg_color": "#FFFFCC", "bottom": 1}
    #     )
    #     sheet_title = [
    #         _("BOM Name"),
    #         _("Level"),
    #         _("Product Reference"),
    #         _("Product Name"),
    #         _("Quantity"),
    #         _("Unit of Measure"),
    #         _("Reference"),
    #     ]
    #     sheet.set_row(0, None, None, {"collapsed": 1})
    #     sheet.write_row(1, 0, sheet_title, title_style)
    #     sheet.freeze_panes(2, 0)
    #     i = 2
    #     for o in objects:
    #         sheet.write(i, 0, o.product_tmpl_id.name or "", bold)
    #         sheet.write(i, 1, "", bold)
    #         sheet.write(i, 2, o.product_id.default_code or "", bold)
    #         sheet.write(i, 3, o.product_id.name or "", bold)
    #         sheet.write(i, 4, o.product_qty, bold)
    #         sheet.write(i, 5, o.product_uom_id.name or "", bold)
    #         sheet.write(i, 6, o.code or "", bold)
    #         i += 1
    #         j = 0
    #         for ch in o.bom_line_ids:
    #             i = self.print_bom_children(ch, sheet, i, j)
