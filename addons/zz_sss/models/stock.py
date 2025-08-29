from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError

class Inventory(models.Model):
	_name = "stock.inventory"
	_inherit = ['mail.thread', 'mail.activity.mixin','stock.inventory']

	state = fields.Selection(track_visibility='onchange')

"""class InventoryLine(models.Model):
	_inherit = "stock.inventory.line"

	def _generate_moves(self):
		vals_list = []
		for line in self:
			virtual_location = line._get_virtual_location()
			rounding = line.product_id.uom_id.rounding
			#if float_is_zero(line.difference_qty, precision_rounding=rounding):
			 #   continue
			if line.difference_qty > 0:  # found more than expected
				vals = line._get_move_values(line.difference_qty, virtual_location.id, line.location_id.id, False)
			elif line.difference_qty < 0: 
				vals = line._get_move_values(abs(line.difference_qty), line.location_id.id, virtual_location.id, True)
			else:
				vals = line._get_move_values(abs(line.theoretical_qty), line.location_id.id, line.location_id.id, True)
			vals_list.append(vals)
		return self.env['stock.move'].create(vals_list)"""

class Picking(models.Model):
	_inherit = "stock.picking"

	no_container = fields.Char(string='No Container')
	picking_qr_code = fields.Text(compute="_get_picking_qr_text", store=False)
	is_titipan = fields.Boolean(string = 'Titipan ?')

	def button_validate(self):
		self.ensure_one()
		if self.purchase_id and not self.purchase_id.order_type.is_import:
			self.purchase_id.write({
				'state': 'done'
			})
		return super(Picking, self).button_validate()


	@api.model
	def _get_hex(self, tag, value):
		to_hex = lambda i : '%02x' % i
		value = value.encode('utf8')

		res = to_hex(int(tag)) + to_hex(len(value))
		for t in value:
			res += to_hex(t)
		return res

	@api.onchange('company_id', 'partner_id')
	def _get_picking_qr_text(self):
		for record in self:
			vendor_name = ""
			vat = ""
			date = ""

			#if record.company_id.x_parent_company_id:
			#    vendor_name = str(record.company_id.x_parent_company_id.name)
			#else:
			vendor_name = str(record.company_id.name)+'-'+str(record.partner_id.name)+'-'+str(record.name)+'-'+str(record.origin)

			vendor_name_hex = self._get_hex("01",vendor_name)

			#if record.company_id.vat:
			#    vat = str(record.company_id.vat)
			#else:
			#    vat = " "
			#vat_hex = self._get_hex("02",vat)

			#if record.x_issue_date:
			#    date = str(record.x_issue_date.strftime("%m-%d-%YT%H:%M:%S"))
			#elif record.create_date and not record.x_issue_date:
			#date = str(record.create_date.strftime("%m-%d-%YT%H:%M:%S"))
			#else:
			#   date = " "
			#date_hex = self._get_hex("03",date)

			#total_amount = str(record.currency_id._convert(record.amount_total, self.env.ref("base.SAR"), record.company_id, datetime.date.today()))
			#total_amount_hex = self._get_hex("04",total_amount)

			#tax_amount = str(record.currency_id._convert(record.amount_tax, self.env.ref("base.SAR"), record.company_id, datetime.date.today()))
			#tax_amount_hex = self._get_hex("05",tax_amount)

			#qr_val = vendor_name_hex + vat_hex + date_hex + total_amount_hex + tax_amount_hex
			#encoded_base64_bytes = base64.b64encode(bytes.fromhex(qr_val)).decode()
			#record.invoice_qr_code = encoded_base64_bytes
			record.picking_qr_code = vendor_name

class StockMove(models.Model):
	_inherit = 'stock.move'

	# def _action_confirm(self, merge=True, merge_into=False):
	#
	# 	move = super(StockMove, self)._action_confirm(merge=merge, merge_into=merge_into)
	#
	# 	if move.location_dest_id != move.picking_id.location_dest_id:
	# 		move.write({
	# 			'location_dest_id': move.picking_id.location_dest_id
	# 		})
	# 		# move._push_apply()
	# 		# move._check_company()
	# 		# if merge:
	# 		# 	return move._merge_moves(merge_into=merge_into)
	#
	# 	return move


class InventoryAdjustmentLine(models.Model):
	_inherit = "stock.inventory.line"

	remark = fields.Text(string='Remark')

