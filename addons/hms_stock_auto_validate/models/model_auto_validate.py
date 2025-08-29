from odoo import models, fields, api
from datetime import datetime, timedelta
import pytz
import logging

_logger = logging.getLogger(__name__)


class StockPickingAutoValidate(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def auto_validate_transfers(self):
        """
        Auto validate ready transfers for specific operation types
        """
        try:
            # Operation types to search for
            operation_types = ['STOCK OUT GUDANG UTAMA', 'SO KITCHEN HARIAN']

            # Get current date in Jakarta timezone
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            now_jakarta = datetime.now(jakarta_tz)
            today_date = now_jakarta.date()

            _logger.info(f"Auto validate transfers running for date: {today_date}")

            # Create start and end datetime in Jakarta timezone, then convert to UTC
            start_jakarta = jakarta_tz.localize(datetime.combine(today_date, datetime.min.time()))
            end_jakarta = jakarta_tz.localize(datetime.combine(today_date, datetime.max.time()))

            start_utc = start_jakarta.astimezone(pytz.UTC)
            end_utc = end_jakarta.astimezone(pytz.UTC)

            _logger.info(f"Searching transfers between {start_utc} and {end_utc} (UTC)")

            # Find matching picking types first
            picking_types = self.env['stock.picking.type'].search([
                ('name', 'in', operation_types)
            ])

            if not picking_types:
                _logger.warning(f"No picking types found with names: {operation_types}")
                return

            _logger.info(f"Found picking types: {picking_types.mapped('name')}")

            # Find all matching transfers that are "Ready" (assigned) and scheduled for today
            domain = [
                ('scheduled_date', '>=', start_utc.strftime('%Y-%m-%d %H:%M:%S')),
                ('scheduled_date', '<=', end_utc.strftime('%Y-%m-%d %H:%M:%S')),
                ('state', '=', 'assigned'),
                ('picking_type_id', 'in', picking_types.ids)
            ]

            transfers = self.search(domain)

            _logger.info(f"Found {len(transfers)} transfers to validate")

            if not transfers:
                _logger.info("No transfers found for auto-validation.")
                return

            # Log details of transfers found
            for transfer in transfers:
                _logger.info(
                    f"Transfer {transfer.name} - Type: {transfer.picking_type_id.name} - Scheduled: {transfer.scheduled_date}")

            # Validate each transfer individually to handle errors gracefully
            validated_count = 0
            failed_count = 0

            for transfer in transfers:
                try:
                    # Check if transfer is still in assigned state (might have changed)
                    if transfer.state != 'assigned':
                        _logger.info(f"Transfer {transfer.name} is no longer in assigned state, skipping")
                        continue

                    # Validate the transfer with context to bypass the foodcost wizard
                    transfer.with_context(skip_foodcost_check=True).button_validate()
                    validated_count += 1
                    _logger.info(f"Successfully validated transfer: {transfer.name}")

                except Exception as e:
                    failed_count += 1
                    _logger.error(f"Failed to validate transfer {transfer.name}: {str(e)}")
                    # Log the full traceback for debugging
                    import traceback
                    _logger.error(f"Full traceback for {transfer.name}: {traceback.format_exc()}")

            _logger.info(f"Auto validation completed: {validated_count} validated, {failed_count} failed")

        except Exception as e:
            _logger.error(f"Error in auto_validate_transfers: {str(e)}")
            # Re-raise the exception if you want the cron job to show as failed
            # raise