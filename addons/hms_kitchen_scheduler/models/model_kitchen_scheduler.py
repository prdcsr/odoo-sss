from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class Picking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def auto_schedule_return_transfer(self):
        """Automatically moves products from 'Restock' back to warehouse stock (lot_stock_id)."""

        #now = fields.Datetime.now()


        warehouses = self.env['stock.warehouse'].search([('name', 'in', ['ALAM SUTRA', 'GADING SERPONG', 'BINTARO'])])
        for warehouse in warehouses:
            restock_picking_type = self.env['stock.picking.type'].search([
                ('name', 'in', ['RESTOCK KITCHEN','RESTOCK SUSHI']),
                ('warehouse_id', '=', warehouse.id)
            ])
            for picking_type in restock_picking_type:

                source_location = picking_type.default_location_src_id
                destination_location = picking_type.default_location_dest_id
                stock_quant = self.env['stock.quant'].search([
                    ('location_id', '=', source_location.id),
                    ('quantity', '>', 0)
                ])

                if not stock_quant:
                    _logger.info(f"Skipping {warehouse.name}: No stock available in source location.")
                    continue

                transfer = self.env['stock.picking'].create({
                    'picking_type_id': picking_type.id,
                    'location_id': source_location.id,
                    'location_dest_id': destination_location.id,
                    'move_type': 'direct',
                    'state': 'draft',
                })

                for quant in stock_quant:
                    product = quant.product_id
                    quantity = quant.quantity

                    self.env['stock.move'].create({
                        'product_id': product.id,
                        'name': quant.product_id.name,
                        'product_uom': product.uom_id.id,
                        'location_id': source_location.id,
                        'location_dest_id': destination_location.id,
                        'product_uom_qty': quantity,
                        'quantity_done': quantity,
                        'picking_id': transfer.id,
                    })

                transfer.action_confirm()
                transfer.action_assign()
                transfer.button_validate()













            # restock_pickings = self.env['stock.picking'].search([
            #     ('picking_type_id.name', 'ilike', 'RESTOCK'),
            #     ('state', '=', 'done'),
            #     ('location_dest_id', 'child_of', warehouse.lot_stock_id.id),
            #     ('origin','not ilike','Return%'),
            #     #('date_done', '>=', evening_start.strftime('%Y-%m-%d %H:%M:%S')),
            #     #('date_done', '<=', evening_end.strftime('%Y-%m-%d %H:%M:%S')),
            # ],order='date_done DESC', limit=1)


            # for picking in restock_pickings:
            #     new_picking = self.env['stock.picking'].create({
            #         'picking_type_id': picking.picking_type_id.id,  # Keep same operation type
            #         'location_id': picking.location_id.id,  # Where it was restocked
            #         'location_dest_id': picking.location_dest_id.id,  # Move back to warehouse stock
            #         'origin': f"Restock Return of {picking.name}",
            #         'scheduled_date': now.replace(hour=7, minute=0, second=0, microsecond=0) + timedelta(days=1),
            #         'move_type': 'direct',
            #     })
            #
            #
            #     for move in picking.move_lines:
            #         packaging = move.product_packaging
            #         packaging_qty = move.product_packaging_qty
            #         stock_move_vals = {
            #             'name': f"Restock: {move.product_id.id}",
            #             'picking_id': new_picking.id,
            #             'product_id': move.product_id.id,
            #             'product_uom_qty': move.product_uom_qty,
            #             'product_uom': move.product_uom.id,
            #             'location_id': new_picking.location_id.id,
            #             'location_dest_id': new_picking.location_dest_id.id,
            #             'quantity_done': move.product_uom_qty,
            #         }
            #         if packaging and packaging_qty:
            #             stock_move_vals.update({
            #                 'product_packaging': packaging.id,
            #                 'product_packaging_qty': packaging_qty,
            #             })
            #         self.env['stock.move'].create(stock_move_vals)
            #     new_picking.action_confirm()
            #     new_picking.action_assign()
            #     new_picking.button_validate()

        #         _logger.info(f"Scheduled restock transfer: {new_picking.name} for 7 AM in {warehouse.name}")
        #
        # _logger.info("Auto-restock job completed.")
