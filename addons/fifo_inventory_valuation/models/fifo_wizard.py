from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_round
from odoo.http import request
from datetime import datetime
import base64
import io
import xlsxwriter


class FifoInventoryValuationWizard(models.TransientModel):
    _name = 'fifo.valuation.wizard'
    _description = 'FIFO Inventory Valuation Report Wizard'

    date = fields.Date(required=True, default=fields.Date.context_today)
    location_id = fields.Many2one('stock.location', string='Location')
    include_child_locations = fields.Boolean(string='Include Child Locations', default=True)
    show_detailed = fields.Boolean(string='Show Detailed Valuation', default=False)

    def action_generate_report(self):
        report_lines = self._get_valuation_lines()

        return self.env.ref('fifo_inventory_valuation.action_fifo_inventory_valuation_report').report_action(self,
                                                                                                             data={
                                                                                                                 'report_lines': report_lines,
                                                                                                                 'date': self.date.strftime(
                                                                                                                     '%Y-%m-%d'),
                                                                                                                 'location_id': self.location_id.id,
                                                                                                                 'include_child_locations': self.include_child_locations,
                                                                                                             })

    def action_export_excel(self):
        report_lines = self._get_valuation_lines()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("FIFO Valuation")

        bold = workbook.add_format({'bold': True})
        sheet.write('A1', 'Code', bold)
        sheet.write('B1', 'Product', bold)
        sheet.write('C1', 'UoM', bold)
        sheet.write('D1', 'Quantity', bold)
        sheet.write('E1', 'Value', bold)

        if self.show_detailed:
            sheet.write('F1', 'Move Date', bold)
            sheet.write('G1', 'Price Unit', bold)
            sheet.write('H1', 'Movement Source', bold)
            sheet.write('I1', 'Location', bold)
        else:
            sheet.write('F1', 'Date', bold)
            sheet.write('G1', 'Location', bold)

        row = 1
        for line in report_lines:
            if line['product_id'].type == 'product':
                sheet.write(row, 0, line['product_id'].default_code)
                sheet.write(row, 1, line['product_id'].name)
                sheet.write(row, 2, line['uom'])
                sheet.write(row, 3, line['quantity'])
                sheet.write(row, 4, line['value'])
                # sheet.write(row, 5, line['date'])
                sheet.write(row, 5, line['date'])
                if self.show_detailed and line['name']:
                    sheet.write(row, 6, line['price_unit'])
                    sheet.write(row, 7, line['name'])
                    sheet.write(row, 8, line['location'])
                else:
                    sheet.write(row, 6, line['location'])
                row += 1

        workbook.close()
        output.seek(0)

        filename = f"FIFO_Inventory_Valuation_{self.date.strftime('%Y%m%d')}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}?download=true",
            'target': 'self',
        }

    def _get_valuation_lines(self):
        products = self.env['product.product'].search([('type', '=', 'product'), ('categ_id', '!=', 22)])
        report_lines = []
        date = datetime(self.date.year, self.date.month, self.date.day, 23, 59, 59).strftime(
            '%Y-%m-%d %H:%M:%S')

        location = self.location_id.complete_name
        if location == 'ALSUT':
            location = 'MAS'
        if location == 'BTR':
            location = 'MBO'
        if location == 'GS':
            location = 'MGS'

        for product in products:
            qty_available = self._get_fifo_qty(product, date, self.location_id, self.include_child_locations)
            fifo_value, move_details = self._compute_fifo_value(product, qty_available, date, self.location_id,
                                                                self.include_child_locations)
            # if qty_available:
            if self.show_detailed and move_details:
                for md in move_details:
                    report_lines.append({
                        'product_id': product,
                        'uom': product.uom_id.name,
                        'quantity': round(md['qty'], 2),
                        'value': round(md['qty'] * md['price_unit'], 2),
                        'price_unit': round(md['price_unit'], 2),
                        'date': md['date'].strftime('%Y-%m-%d'),
                        'location': location,
                        'name': md['name']
                    })
            else:
                report_lines.append({
                    'product_id': product,
                    'uom': product.uom_id.name,
                    'quantity': round(qty_available, 2),
                    'value': round(fifo_value, 2),
                    'price_unit': 0,
                    'date': self.date.strftime('%Y-%m-%d'),
                    'location': location,
                    'name': "test"
                })
        return report_lines

    def _get_fifo_qty(self, product, date, location, include_child):
        domain_in = [('product_id', '=', product.id),
                     ('date', '<=', date), ('state', '=', 'done')]

        domain_out = [('product_id', '=', product.id),
                      ('date', '<=', date), ('state', '=', 'done')]
        if location:
            loc_domain = 'child_of' if include_child else '='
            domain_in.append(('location_dest_id', loc_domain, location.id))
            domain_out.append(('location_id', loc_domain, location.id))
        else:
            # All locations, so exclude internal moves by filtering only external ones
            domain_in.append(('location_id.usage', '!=', 'internal'))
            domain_out.append(('location_dest_id.usage', '!=', 'internal'))

            # domain_in = [('product_id', '=', product.id), ('location_dest_id', loc_domain, location.id),
            #          ('date', '<=', date), ('state', '=', 'done')]
            # domain_out = [('product_id', '=', product.id), ('location_id', loc_domain, location.id),
            #               ('date', '<=', date), ('state', '=', 'done')]

        qty_in = 0
        qty_out = 0
        for move in self.env['stock.move'].search(domain_in):
            try:
                if product.uom_id.category_id.id == move.product_uom.category_id.id:
                    qty_in += move.product_uom._compute_quantity(move.product_qty, product.uom_id)
            except Exception as e:
                raise UserError(f'{e}, ref: {move.name}, {move.picking_id.name}')

        for move in self.env['stock.move'].search(domain_out):
            try:
                if product.uom_id.category_id.id == move.product_uom.category_id.id:
                    qty_out += move.product_uom._compute_quantity(move.product_qty, product.uom_id)
            except Exception as e:
                raise UserError(f'{e}, ref: {move.name}, {move.picking_id.name}')

        # try:
        #     qty_in = sum(move.product_uom._compute_quantity(move.product_qty, product.uom_id) for move in self.env['stock.move'].search(domain_in))
        #     qty_out = sum(move.product_uom._compute_quantity(move.product_qty, product.uom_id) for move in self.env['stock.move'].search(domain_out))
        # except Exception as e:
        #     raise UserError(f'{e}, ref: {product.name}')

        return float_round(qty_in - qty_out, precision_rounding=product.uom_id.rounding)

    def _compute_fifo_value(self, product, qty, date, location, include_child):

        domain_in = [('product_id', '=', product.id), ('date', '<=', date), ('state', '=', 'done')]
        if location:
            loc_domain = 'child_of' if include_child else '='
            domain_in.append(('location_dest_id', loc_domain, location.id))
        else:
            domain_in.append(('location_id.usage', '!=', 'internal'))

        moves_in = self.env['stock.move'].search(domain_in, order='date asc')

        value = 0.0
        remaining_qty = qty
        details = []

        for move in moves_in:
            if remaining_qty <= 0:
                break
            if move.product_uom.category_id.id == product.uom_id.category_id.id:
                move_qty = move.product_uom._compute_quantity(move.quantity_done, product.uom_id)
                used_qty = min(move_qty, remaining_qty)
                # unit_price = move.price_unit or move.product_id.standard_price
                unit_price = move.price_unit
                value += used_qty * unit_price
                details.append({
                    'qty': used_qty,
                    'price_unit': unit_price,
                    'date': move.date,
                    'name': move.reference
                })
                remaining_qty -= used_qty

        return value, details

    # def _compute_fifo_value(self, product, qty, date, location, include_child):
    #     StockValLayer = self.env['stock.valuation.layer']
    #     StockMove = self.env['stock.move']
    #
    #     # Get all valuation layers for this product up to the selected date
    #     domain = [
    #         ('product_id', '=', product.id),
    #         ('create_date', '<=', date),
    #         ('quantity', '>', 0),  # only incoming stock
    #     ]
    #
    #     valuation_layers = StockValLayer.search(domain, order='create_date asc')
    #
    #     remaining_qty = qty
    #     total_value = 0.0
    #     details = []
    #
    #     for layer in valuation_layers:
    #         move = layer.stock_move_id
    #
    #         # Validate the move is relevant to the selected location
    #         if not move:
    #             continue
    #
    #         # Check if location matches (destination only for incoming moves)
    #         layer_location = move.location_dest_id
    #         if location:
    #             if include_child:
    #                 if not layer_location.id == location.id and not layer_location.id in location.child_ids.ids:
    #                     continue
    #             else:
    #                 if layer_location.id != location.id:
    #                     continue
    #         else:
    #             if layer_location.usage != 'internal':
    #                 continue
    #
    #         # FIFO logic
    #         used_qty = min(layer.quantity, remaining_qty)
    #         unit_cost = abs(layer.value / layer.quantity) if layer.quantity else 0.0
    #         total_value += used_qty * unit_cost
    #
    #         details.append({
    #             'qty': used_qty,
    #             'price_unit': unit_cost,
    #             'date': layer.create_date,
    #             'name': move.reference or move.picking_id.name or '',
    #         })
    #
    #         remaining_qty -= used_qty
    #         if remaining_qty <= 0:
    #             break
    #
    #     return total_value, details
