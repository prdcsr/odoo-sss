from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta, datetime


class ValidationConfirmationWizard(models.TransientModel):
    _name = 'stock.picking.validation.confirmation.wizard'
    _description = 'One-Time Picking Warning Wizard'

    picking_id = fields.Many2one('stock.picking', required=True)
    line_ids = fields.One2many('stock.picking.validation.confirmation.wizard.line', 'wizard_id', readonly=True)

    def action_confirm(self):
        # Check if there are any lines that exceed the max food cost
        if self.line_ids:
            error_message = "Silahkan betulkan hasil SOK."
            raise UserError(error_message)

        # If we reach here, no lines exist (nothing exceeded), so validation is allowed
        self.picking_id.with_context(from_validation_wizard=True).button_validate()
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def default_get(self, data_fields):
        res = super().default_get(data_fields)
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        lines = []
        date = picking.scheduled_date
        restock_picking_type = self.env['stock.picking.type'].search([
            ('name', '=', 'RESTOCK KITCHEN'),
            ('warehouse_id', '=', picking.picking_type_id.warehouse_id.id)
        ], limit=1)
        sog_picking_type = self.env['stock.picking.type'].search([
            ('name', '=', 'STOCK OUT GUDANG UTAMA'),
            ('warehouse_id', '=', picking.picking_type_id.warehouse_id.id)
        ])

        start = datetime(date.year, date.month, date.day, 0, 0, 0).strftime(
            '%Y-%m-%d %H:%M:%S')
        end = datetime(date.year, date.month, date.day, 23, 59, 59).strftime(
            '%Y-%m-%d %H:%M:%S')

        today_sog_move = self.env['stock.move'].search([
            ('picking_type_id', '=', sog_picking_type.id),
            ("product_id", "=", picking.product_id.id),
            ('date_expected', '>=', start),
            ('date_expected', '<=', end)
        ], order="date_expected desc")

        today_restock = self.env['stock.move'].search([
            ('picking_type_id', '=', restock_picking_type.id),
            ('product_id', '=', picking.product_id.id),
            ('date_expected', '>=', start),
            ('date_expected', '<=', end)
        ], order="date_expected desc", limit=1)

        validation_qty = 0

        for restock_move in today_restock:
            validation_qty += restock_move.product_uom_qty

        for sog_move in today_sog_move:
            validation_qty += sog_move.product_uom_qty

        for move in picking.move_ids_without_package:
            tmpl = move.product_id.product_tmpl_id
            location = move.location_dest_id

            # Get food cost configuration for this product and location
            food_cost = self.env['product.food.cost'].search([
                ('product_tmpl_id', '=', tmpl.id),
                ('name', '=', location.id)
            ], limit=1)

            if not food_cost:
                continue

            today_food_cost = validation_qty - move.quantity_done

            # Get base max food cost
            max_allowed = food_cost.max_food_cost

            # Check if it's weekend or holiday
            date = picking.scheduled_date
            day = date.isoweekday()  # Monday=1, Sunday=7
            is_holiday = self.env['fnb.holiday.schedule'].is_holiday(date)
            is_weekend = day > 5  # Saturday=6, Sunday=7

            # Check if there's an active promotion using the updated model method
            active_promos = self.env['fnb.promo.schedule'].get_active_promotions(date)
            has_promotion = bool(active_promos)

            # Check if this specific product is in any active promotion for this location and get the promo quantity
            promo_max_qty = 0.0
            product_in_promo = False
            if has_promotion:
                # Updated search to include location matching
                promo_lines = self.env['fnb.promo.line'].search([
                    ('promo_id', 'in', active_promos),
                    ('location_id', '=', location.id),  # Match the destination location
                    '|',
                    ('product_id', '=', move.product_id.id),
                    ('product_tmplt_id', '=', tmpl.id)
                ])
                if promo_lines:
                    product_in_promo = True
                    # Take the max_qty from the first matching promo line
                    promo_max_qty = promo_lines[0].max_qty

            # Determine the appropriate max food cost based on conditions
            # Priority: Promo (location-specific) > Weekend/Holiday > Normal
            if product_in_promo:
                max_food_cost = promo_max_qty
            elif is_weekend or is_holiday:
                max_food_cost = food_cost.weekend_food_cost
            else:
                max_food_cost = max_allowed

            # Debug logging to help troubleshoot
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info(f"Product: {move.product_id.name}")
            _logger.info(f"Location: {location.name}")
            _logger.info(
                f"Base max: {max_allowed}, Weekend: {food_cost.weekend_food_cost}, Promo max_qty: {promo_max_qty}")
            _logger.info(
                f"Is weekend: {is_weekend}, Is holiday: {is_holiday}, Has promotion: {has_promotion}, Product in promo: {product_in_promo}")
            _logger.info(f"Final max_food_cost: {max_food_cost}, Today's Food Cost: {today_food_cost}")

            # Add to lines if quantity exceeds the determined max
            if today_food_cost > max_food_cost:
                lines.append((0, 0, {
                    'product_id': move.product_id.id,
                    'food_cost': today_food_cost,
                    'max_food_cost': max_food_cost,
                }))

        res.update({
            'picking_id': picking.id,
            'line_ids': lines,
        })
        return res


class ValidationConfirmationWizardLine(models.TransientModel):
    _name = 'stock.picking.validation.confirmation.wizard.line'
    _description = 'Exceeded Quantity Line (No Cost Shown)'

    wizard_id = fields.Many2one('stock.picking.validation.confirmation.wizard', required=True)
    product_id = fields.Many2one('product.product', readonly=True)
    food_cost = fields.Float("Food Cost hari ini", readonly=True)
    max_food_cost = fields.Float("Maximum Quantity Normal", readonly=True)