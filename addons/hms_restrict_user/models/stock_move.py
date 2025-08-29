from datetime import timedelta, datetime

from odoo.exceptions import ValidationError
from odoo.osv.expression import expression
from . import constant
from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    ALLOWED_PICKING_TYPE_NAMES = [constant.STOCK_OUT_GUDANG_UTAMA, constant.RECEIPTS, constant.SO_KITCHEN_HARIAN, constant.PRODUCTION, constant.WASTE,constant.STOCK_OPNAME_ECER]

    # is_returned = fields.Boolean(string="Is Returned", compute='_compute_is_returned', store=True)

    @api.model
    def create(self, vals):
        move = super(StockMove, self).create(vals)

        if move.picking_type_id.name in self.ALLOWED_PICKING_TYPE_NAMES:
            qty = move.product_uom_qty
            if move.move_line_ids:
                move.move_line_ids.write({
                    'qty_done': qty,
                })
            else:
                move.quantity_done = qty
                move.reserved_availability = qty

        return move
        # picking_type = self.env['stock.picking.type'].search([('id', '=', vals.get('picking_type_id'))])
        # if picking_type and picking_type.name in self.ALLOWED_PICKING_TYPE_NAMES and 'product_uom_qty' in vals:
        #     vals['quantity_done'] = vals['product_uom_qty']
        #     vals['reserved_availability'] = vals['product_uom_qty']
        # return super(StockMove, self).create(vals)

    def write(self, vals):
        for move in self:
            if move.picking_type_id and move.picking_type_id.name in self.ALLOWED_PICKING_TYPE_NAMES:
                if 'product_uom_qty' in vals:
                    vals['quantity_done'] = vals.get('product_uom_qty', move.product_uom_qty)
                    vals['reserved_availability'] = vals.get('product_uom_qty', move.product_uom_qty)

                if move.has_move_lines and move.move_line_ids.ids and move.picking_id.id:
                    for line in move.move_line_ids:
                        if not line.picking_id:
                            line.write({
                                'picking_id': move.picking_id
                            })

        return super(StockMove, self).write(vals)

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):

        if self.picking_type_id and self.picking_type_id.name == constant.SO_KITCHEN_HARIAN:
            current_picking = self.picking_id
            restock_picking_type = self.env['stock.picking.type'].search([
                ('name', '=', constant.RESTOCK),
                ('warehouse_id', '=', current_picking.picking_type_id.warehouse_id.id)
            ], limit=1)
            date = current_picking.scheduled_date
            # ytd_sok_move = ytd_sok_picking.move_lines

            sog_picking_type = self.env['stock.picking.type'].search([
                ('name', '=', constant.STOCK_OUT_GUDANG_UTAMA),
                ('warehouse_id', '=', current_picking.picking_type_id.warehouse_id.id)
            ])

            start = datetime(date.year, date.month, date.day, 0, 0, 0).strftime(
                '%Y-%m-%d %H:%M:%S')
            end = datetime(date.year, date.month, date.day, 23, 59, 59).strftime(
                '%Y-%m-%d %H:%M:%S')

            today_sog_move = self.env['stock.move'].search([
                ('picking_type_id', '=', sog_picking_type.id),
                ("product_id", "=", self.product_id.id),
                ('date_expected', '>=', start),
                ('date_expected', '<=', end)
            ], order="date_expected desc")

            today_restock = self.env['stock.move'].search([
                ('picking_type_id', '=', restock_picking_type.id),
                ('product_id', '=', self.product_id.id),
                ('date_expected', '>=', start),
                ('date_expected', '<=', end)
            ], order="date_expected desc", limit=1)

            # today_sog_move = today_sog_picking.move_lines

            validation_qty = 0
            today_restock_qty = 0
            today_sog_qty = 0
            for restock_move in today_restock:
                validation_qty += restock_move.product_uom_qty
                today_restock_qty += restock_move.product_uom_qty
                # if self.product_id == sok_move.product_id:

            for sog_move in today_sog_move:
                validation_qty += sog_move.product_uom_qty
                today_sog_qty += sog_move.product_uom_qty
                # if self.product_id == sog_move.product_id:

            food_cost = validation_qty - self.product_uom_qty
            if self.product_uom_qty > validation_qty:
                if not self.picking_id.note:
                    raise ValidationError(
                        'Qty stock opname kitchen hari ini tidak boleh lebih besar dari Stock Opname Kitchen kemarin + Stock Out Gudang Utama hari ini, ref: ' + self.product_id.name + f'\nStock Opname Kitchen hari ini: {self.product_uom_qty} {self.product_uom.name}\n'
                                                                                                                                                                f'Stock Opname Kitchen kemarin: {today_restock_qty} {self.product_uom.name}\n'
                                                                                                                                                                f'Stock Out Gudang Utama hari ini: {today_sog_qty} {self.product_uom.name}\n'
                                                                                                                                                                f'Food Cost hari ini: {food_cost} {self.product_uom.name}\n'
                                                                                                                                                                                  f'Silahkan mengisi note untuk melanjutkan')

        if self.picking_type_id and self.picking_type_id.name in self.ALLOWED_PICKING_TYPE_NAMES:
            self.quantity_done = self.product_uom_qty
            self.reserved_availability = self.product_uom_qty


    def _push_apply(self):
        for move in self:
            # if the move is already chained, there is no need to check push rules
            if move.move_dest_ids:
                continue
            # if the move is a returned move, we don't want to check push rules, as returning a returned move is the only decent way
            # to receive goods without triggering the push rules again (which would duplicate chained operations)

            domain = [('location_src_id', '=', move.location_dest_id.id), ('action', 'in', ('push', 'pull_push'))]

            # first priority goes to the preferred routes defined on the move itself (e.g. coming from a SO line)
            warehouse_id = move.warehouse_id or move.picking_id.picking_type_id.warehouse_id
            if not self.env.context.get('force_company', False) and move.location_dest_id.company_id == self.env.user.company_id:
                rules = self.env['procurement.group']._search_rule(move.route_ids, move.product_id, warehouse_id, domain)
            else:
                rules = self.sudo().env['procurement.group']._search_rule(move.route_ids, move.product_id, warehouse_id, domain)
            # Make sure it is not returning the return

            available_product = False
            for rule in rules:
                route = rule.route_id
                if route.product_selectable:
                    if move.product_id.id in route.product_ids.ids:
                        available_product = True
                if route.product_categ_selectable:
                    if move.product_id.categ_id.id in route.categ_ids.ids:
                        available_product = True

            if rules and (not move.origin_returned_move_id or move.origin_returned_move_id.location_dest_id.id != rules.location_id.id) and available_product:
                rules._run_push(move)

    # def _compute_is_returned(self):
    #     for move in self:
    #         move.is_returned = self.env['stock.move'].search_count([
    #             ('origin_returned_move_id', '=', move.id)
    #         ]) > 0
