

from odoo.exceptions import ValidationError
from . import constant
from odoo import models, api, fields
from datetime import datetime, timedelta
import pytz


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    ALLOWED_PICKING_TYPE_NAMES = [constant.STOCK_OUT_GUDANG_UTAMA, constant.SO_KITCHEN_HARIAN]
    PRODUCTION_PICKING_TYPE_NAME = [constant.PRODUCTION, constant.WASTE]

    scheduled_date_check = fields.Boolean(compute='_compute_scheduled_date_check')

    def _compute_scheduled_date_check(self):
        yesterday = (datetime.now() - timedelta(days=1)).date()
        for rec in self:
            rec.scheduled_date_check = rec.scheduled_date.date() == yesterday

    # @api.constrains('move_ids_without_package', 'picking_type_id')
    # def check_stock_move_for_production_and_waste(self):
    #     if self.picking_type_id.name == constant.PRODUCTION:
    #
    #         if self.move_ids_without_package.length > 1:
    #             raise ValidationError("Production can only contain 1 line")
    #         # if self.created_date >

    def action_revise_wizard(self):
        return {
            'name': 'Revise Picking',
            'type': 'ir.actions.act_window',
            'res_model': 'sok.revise.picking',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_picking_id': self.id},
        }

    @api.model
    def create(self, vals):
        picking_type = self.env['stock.picking.type'].search([('id', '=', vals.get('picking_type_id'))])

        user = self.env.user
        tz = user.tz or "Asia/Jakarta"
        tz_name = pytz.timezone(tz)
        now = fields.Datetime.now().astimezone(tz_name)
        # if now.hour >= 21 and now.minute >= 20 and picking_type.name == constant.PRODUCTION:
        #     raise ValidationError("Production cannot be created after 21:20")
        #
        # if now.hour < 21 and now.minute < 20 and picking_type.name == constant.WASTE:
        #     raise ValidationError("Waste cannot be created before 21:20")

        # start = datetime(now.year, now.month, now.day, 0, 0, 0).strftime(
        #     '%Y-%m-%d %H:%M:%S')
        # end = datetime(now.year, now.month, now.day, 23, 59, 59).strftime(
        #     '%Y-%m-%d %H:%M:%S')
        #
        # if picking_type and picking_type.name == constant.SO_KITCHEN_HARIAN:
        #     date = now
        #     move_lines = vals['move_lines'] if vals['move_lines'] else vals['move_ids_without_package']
        #     move_lines = []
        #     move_lines = filter(lambda l: l['product_id'] and l['product_uom_qty'], move_lines)
        #
        #     sog_picking_type = self.env['stock.picking.type'].search([
        #         ('name', '=', constant.STOCK_OUT_GUDANG_UTAMA),
        #         ('warehouse_id', '=', vals.get('warehouse_id'))
        #     ])
        #
        #     restock_picking_type = self.env['stock.picking.type'].search([
        #         ('name', '=', constant.RESTOCK),
        #         ('warehouse_id', '=', vals.get('warehouse_id'))
        #     ], limit=1)
        #
        #     today_restock_picking = self.env['stock.picking'].search([
        #         ('picking_type_id', '=', restock_picking_type.id),
        #         ('scheduled_date', '>=', start),
        #         ('scheduled_date', '<=', end),
        #     ], order="scheduled_date desc", limit=1)
        #     ytd_sok_move = today_restock_picking.move_lines
        #
        #     today_sog_picking = self.env['stock.picking'].search([
        #         ('picking_type_id', '=', sog_picking_type.id),
        #         ('scheduled_date', '>=', start),
        #         ('scheduled_date', '<=', end),
        #     ], order="scheduled_date desc", limit=1)
        #     today_sog_move = today_sog_picking.move_lines
        #
        #     for line in move_lines:
        #         validation_qty = 0
        #         ytd_sok_qty = 0
        #         today_sog_qty = 0
        #         product = self.env['stock.picking'].search([
        #             ('id', '=', line['product_id'])
        #         ])
        #         for sok_move in ytd_sok_move:
        #             if line['product_id'] == sok_move.product_id.id:
        #                 validation_qty += sok_move.product_uom_qty
        #                 ytd_sok_qty += sok_move.product_uom_qty
        #
        #         for sog_move in today_sog_move:
        #             if line['product_id'] == sog_move.product_id.id:
        #                 validation_qty += sog_move.product_uom_qty
        #                 today_sog_qty += sog_move.product_uom_qty
        #
        #         food_cost = validation_qty - line.product_uom_qty
        #
        #         if line['product_uom_qty'] > validation_qty:
        #             if not self.note:
        #                 raise ValidationError(
        #                     'Qty stock opname kitchen hari ini tidak boleh lebih besar dari Stock Out Kitchen kemarin + Stock Out Gudang Utama hari ini, ref: ' + product.name + f'\nStock Opname Kitchen hari ini: {line.product_uom_qty} {line.product_uom.name}\n'
        #                                                                                                                                                         f'Stock Opname Kitchen kemarin: {ytd_sok_qty} {line.product_uom.name}\n'
        #                                                                                                                                                         f'Stock Out Gudang Utama hari ini: {today_sog_qty} {line.product_uom.name}\n'
        #                                                                                                                                                         f'Food Cost hari ini: {food_cost} {line.product_uom.name}')

        picking = super(StockPicking, self).create(vals)

        if picking.picking_type_id and picking.picking_type_id.name in self.ALLOWED_PICKING_TYPE_NAMES:
            picking.action_confirm()
            if picking.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done')):
                picking.action_assign()


        if picking.picking_type_id and picking.picking_type_id.name in self.PRODUCTION_PICKING_TYPE_NAME:
            picking.action_confirm()

        if picking.state == 'assigned' and picking.picking_type_id and picking.picking_type_id.name in self.PRODUCTION_PICKING_TYPE_NAME:
            picking.button_validate()

        return picking

    def open_picking_form(self):
        # self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Planned Transfer',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'target': 'current',
        }

    def _set_scheduled_date(self):
        for picking in self:
            # if picking.state in ('done', 'cancel'):
            #     raise UserError(_("You cannot change the Scheduled Date on a done or cancelled transfer."))
            picking.move_lines.write({'date_expected': picking.scheduled_date})

    def write(self, vals):

        # picking_type = self.env['stock.picking.type'].search([('id', '=', vals.get('picking_type_id'))])
        #
        # if picking_type and picking_type.name == constant.SO_KITCHEN_HARIAN:
        #     date = vals['scheduled_date']
        #     move_lines = vals['move_lines'] if vals['move_lines'] else vals['move_ids_without_package']
        #     move_lines = filter(lambda l: l['product_id'] and l['product_uom_qty'], move_lines)
        #
        #     today_restock_picking = self.env['stock.picking'].search([
        #         ('picking_type_id', '=', vals.get('picking_type_id')),
        #         ('scheduled_date', '<', date),
        #     ], order="date_expected desc", limit=1)
        #     ytd_sok_move = today_restock_picking.move_lines
        #
        #     sog_picking_type = self.env['stock.picking.type'].search([
        #         ('name', '=', constant.STOCK_OUT_GUDANG_UTAMA),
        #         ('warehouse_id', '=', vals.get('warehouse_id'))
        #     ])
        #
        #     today_sog_picking = self.env['stock.picking'].search([
        #         ('picking_type_id', '=', sog_picking_type.id),
        #     ], order="scheduled_date desc", limit=1)
        #     today_sog_move = today_sog_picking.move_lines
        #
        #     for line in move_lines:
        #         validation_qty = 0
        #         ytd_sok_qty = 0
        #         today_sog_qty = 0
        #         product = self.env['stock.picking'].search([
        #             ('id', '=', line['product_id'])
        #         ])
        #         for sok_move in ytd_sok_move:
        #             if line['product_id'] == sok_move.product_id.id:
        #                 validation_qty += sok_move.product_uom_qty
        #                 ytd_sok_qty += sok_move.product_uom_qty
        #
        #         for sog_move in today_sog_move:
        #             if line['product_id'] == sog_move.product_id.id:
        #                 validation_qty += sog_move.product_uom_qty
        #                 today_sog_qty += sog_move.product_uom_qty
        #
        #         food_cost = validation_qty - line.product_uom_qty
        #
        #         if line['product_uom_qty'] > validation_qty:
        #             if not self.note:
        #                 raise ValidationError(
        #                     'Qty stock opname kitchen hari ini tidak boleh lebih besar dari Stock Out Kitchen kemarin + Stock Out Gudang Utama hari ini, ref: ' + product.name + f'\nStock Out Kitchen hari ini: {line.product_uom_qty} {line.product_uom.name}\n'
        #                                                                                                                                                                       f'Stock Out Kitchen kemarin: {ytd_sok_qty} {line.product_uom.name}\n'
        #                                                                                                                                                                       f'Stock Out Gudang Utama hari ini: {today_sog_qty} {line.product_uom.name}\n'
        #                                                                                                                                                                       f'Food Cost hari ini: {food_cost} {line.product_uom.name}')
        res = super(StockPicking, self).write(vals)

        for picking in self:
            if picking.state == 'draft' and picking.picking_type_id and picking.picking_type_id.name in self.ALLOWED_PICKING_TYPE_NAMES + self.PRODUCTION_PICKING_TYPE_NAME:
                picking.action_confirm()
                picking.action_assign()

            if picking.state == 'assigned' and picking.picking_type_id and picking.picking_type_id.name in self.PRODUCTION_PICKING_TYPE_NAME:
                picking.button_validate()

        return res
