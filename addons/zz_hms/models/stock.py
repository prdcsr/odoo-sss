from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError

# class Picking(models.Model):
#     _inherit = "stock.picking"
#
#     no_container = fields.Char(string='No Container')
#
# class Inventory(models.Model):
# 	_name = "stock.inventory"
# 	_inherit = ['mail.thread', 'mail.activity.mixin','stock.inventory']
#
# 	state = fields.Selection(track_visibility='onchange')
# 	note = fields.Text('Description',readonly=True,states={'draft': [('readonly', False)]},)

class StockValuationLayer(models.Model):
	_inherit = 'stock.valuation.layer'
	location_id = fields.Many2one('stock.location', 'Source Location', related='stock_move_id.location_id', store=True)
	location_dest_id = fields.Many2one('stock.location', 'Location Destination', related='stock_move_id.location_dest_id', store=True)

	analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', compute="_compute_analytic_account", store=True)

	@api.depends('account_move_id')
	def _compute_analytic_account(self):
		for svl in self:
			if svl.account_move_id and svl.account_move_id.line_ids:
				for line in svl.account_move_id.line_ids:
					if line.analytic_account_id:
						svl.analytic_account_id = line.analytic_account_id
