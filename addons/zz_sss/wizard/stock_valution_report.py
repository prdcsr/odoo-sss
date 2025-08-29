# -*- coding: utf-8 -*-

#import odoo.addons.decimal_precision as dp
#from odoo import api, fields, models, _
#from datetime import datetime, timedelta
#from odoo.tools import pycompat, DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
#from odoo.tools.float_utils import float_round

import logging
_logger = logging.getLogger(__name__)

try:
	import xlsxwriter
except ImportError:
	_logger.debug('Cannot `import xlsxwriter`.')
#try:
	#import base64
#except ImportError:
	#_logger.debug('Cannot `import base64`.')

from logging import INFO, warning
from typing import TextIO
from odoo import models, fields, api, _
from odoo.tools.misc import xlwt
import io
import base64
from xlwt import easyxf
import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError,Warning

class InventoryStockValuationReportWizard(models.TransientModel):
	_name = 'inventory.stock.valution.report.wizard'
	_description = 'Inventory And Stock Valuation Report'

	date_from = fields.Date('Start Date')
	date_to = fields.Date('End Date')
	warehouse_ids = fields.Many2one('stock.warehouse', string="Warehouse")
	location_ids = fields.Many2one('stock.location', string="Location",domain=[("usage", "in", ["internal", "transit"])])
	product_ids = fields.Many2many('product.product', string="Product")
	product_categ_ids = fields.Many2many('product.category', string="Category")
	filter_type = fields.Selection([('product','Product'),('category','Category')], default='product', string='Filter By')
	document = fields.Binary('File To Download')
	file = fields.Char('Report File Name', readonly=1)
	period_length = fields.Integer('Period Length (Days)', default=30)
	company_id = fields.Many2one('res.company','Company')
	#report_type = fields.Selection([('warehouse','Warehouse'),('location','Location')], default='warehouse', string='Generate Report Based on')
	report_type = fields.Selection([('national','National'),('location','Location')], default='national', string='Generate Report Based on')
	@api.onchange('filter_type')
	def _onchange_filter_type(self):
		if self.filter_type == 'product':
			self.product_categ_ids = False
		else:
			self.product_ids = False

	@api.onchange('report_type')
	def _onchange_report_type(self):
		#if self.report_type == 'warehouse':
		if self.report_type == 'national':
			self.location_ids = False
		#else:
			#self.warehouse_ids = False

	def print_pdf_report(self):
		self.ensure_one()
		[data] = self.read()
		datas = {
			 'ids': [1],
			 'model': 'inventory.stock.valution.report.wizard',
			 'form': data
		}
		return self.env.ref('stock_valuation_report_app.action_report_stock_inventory_valution').report_action(self, data=datas)

	def print_excel_report(self):
		self.ensure_one()
		file_path = 'Inventory And Stock Valuation Report' + '.xlsx'
		#workbook = xlsxwriter.Workbook('/tmp/' + file_path)
		workbook = xlwt.Workbook()
		#header_format = workbook.add_format({'bold': True,'valign':'vcenter','font_size':16,'align': 'center','bg_color':'#D8D8D8'})
		header_format = easyxf('font:height 200; align: horiz center;pattern: pattern solid, fore_color black; font: color white; font:bold True;' "borders: top thin,bottom thin")
		column_heading_style = easyxf('font:height 200;font:bold True;align: horiz center;')
		date_format = xlwt.XFStyle()
		date_format.num_format_str = 'dd/mm/yyyy'
		#worksheet = workbook.add_worksheet('Stock Mutation  Summary') 
		worksheet = workbook.add_sheet('Stock Mutation  Summary')
		
		worksheet.write_merge(2, 2, 1, 2,_('Initial Balance'), column_heading_style)
		worksheet.write_merge(2, 2, 3, 4,_('Vendor'), column_heading_style)
		worksheet.write_merge(2, 2, 5, 6,_('customer'), column_heading_style)
		worksheet.write_merge(2, 2, 7, 8,_('Inventory'), column_heading_style)
		worksheet.write_merge(2, 2, 9, 10,_('Transfer'), column_heading_style)
		worksheet.write_merge(2, 2, 11, 12,_('Value Correction'), column_heading_style)
		worksheet.write_merge(2, 2, 13, 14,_('Ending Balance'), column_heading_style)

		worksheet.write(3, 0, _('Product'), column_heading_style) 
		worksheet.write(3, 1, _('IB Qty'), column_heading_style)
		worksheet.write(3, 2, _('IB Val'), column_heading_style)
		worksheet.write(3, 3, _('PO Qty'), column_heading_style)
		worksheet.write(3, 4, _('PO Val'), column_heading_style)
		worksheet.write(3, 5, _('DO Qty'), column_heading_style)
		worksheet.write(3, 6, _('DO Val'), column_heading_style)
		worksheet.write(3, 7, _('IV Qty'), column_heading_style)
		worksheet.write(3, 8, _('IV Val'), column_heading_style)
		worksheet.write(3, 9, _('IN Qty'), column_heading_style)
		worksheet.write(3, 10, _('IN Value'), column_heading_style)
		worksheet.write(3, 11, _('HP Qty'), column_heading_style)
		worksheet.write(3, 12, _('HP Val'), column_heading_style)
		worksheet.write(3, 13, _('EB Qty'), column_heading_style)
		worksheet.write(3, 14, _('EB Val'), column_heading_style)

		#worksheet.col(0).width = 5000
		i = 1
		while i < 14 :
			worksheet.col(i).width = 5000
			i +=1

		#worksheet.col(1).width = 5000
		#worksheet.col(2).width = 5000
		#worksheet.col(3).width = 5000
		#worksheet.col(4).width = 5000
		#worksheet.col(5).width = 5000
		#worksheet.col(6).width = 5000
		#worksheet.col(7).width = 5000
		#worksheet.col(8).width = 5000
		
		row = 4
		customer_row = 2
		
		for wizard in self:
			
			ctx = dict(self.env.context) or {}
			date = wizard.date_from - datetime.timedelta(days=1) 
			date = date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
			eb_date = wizard.date_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

			x_date= datetime.datetime(2020, 12, 31)
			y_date = datetime.date(2021, 1, 3)
			start_date = wizard.date_from
			end_date = wizard.date_to
			location_id = wizard.location_ids
			heading =  'Stock Mutation Report' #+ str(wizard.currency_id.name) + ')'
			if location_id:
				heading += ' ' + location_id.complete_name
			else: 
				heading += ' National'
			#worksheet.merge_range(1, 0, 1, 11, heading, header_format)
			worksheet.write_merge(0, 0, 0, 12,heading, header_format)
			
			worksheet.write(1, 1, _('Period :'), header_format)
			worksheet.write(1, 2, start_date, date_format)
			worksheet.write(1, 3, end_date, date_format)
	

			ctx.update({'to_date': date,
						'location' : location_id.id,}) 

			if wizard.filter_type == 'category':
				if wizard.report_type == 'location' :
					product_ids = self.env['product.product'].with_context(ctx).\
						search([('categ_id', 'child_of', wizard.product_categ_ids.ids),('type','=','product')])
				else:
					product_ids = self.env['product.product'].\
						search([('categ_id', 'child_of', wizard.product_categ_ids.ids),('type','=','product')])
			else:
				if wizard.report_type == 'location' :
					product_ids = self.env['product.product'].with_context(ctx).\
						search([('id', 'in', wizard.product_ids.ids),('type','=','product')])
				else:
					product_ids = self.env['product.product'].\
						search([('id', 'in', wizard.product_ids.ids),('type','=','product')])
			
			#raise Warning ('start product')
			for product_id  in product_ids:
			
				# ============== Inital Balance ===============
				li_domain = ['|',('account_move_id', '!=', False),('stock_move_id', '!=', False),
							('create_date', '<', start_date),
							('create_date', '>', x_date),
							('product_id', '=', product_id.id),]
				
				ib_qty = 0
				ib_unit = 0
				ib_value = 0

								
				move_ids =self.env['stock.valuation.layer'].read_group(domain=li_domain,
                                                               	fields=["product_id","quantity","value",],
                                                                groupby=["product_id"],
                                                                lazy=False,
                                                               )
				if move_ids:
					for valuation in move_ids:
						ib_qty += valuation["quantity"]
						ib_value +=  valuation["value"]
				
				if ib_qty != 0:
					ib_unit = ib_value/ib_qty

				if wizard.report_type == 'location' :
					if start_date >= y_date :
						ib_qty = product_id.qty_available				
						ib_value = ib_qty*ib_unit

				po_qty = 0
				po_value = 0
				do_qty = 0
				do_value = 0
				iv_qty = 0				
				iv_value = 0
				in_qty = 0
				in_value = 0
				eb_qty = ib_qty
				eb_value = ib_value

				if wizard.report_type == 'location' :
					m_domain = ['|',('location_id','=',location_id.id),
								('location_dest_id','=',location_id.id),								
								('state', '=', 'done'),
								('date', '>=', start_date),
								('date', '<=', end_date),
								('product_id', '=', product_id.id),]
				else:
					m_domain = [('state', '=', 'done'),
								('date', '>=', start_date),
								('date', '<=', end_date),
								('product_id', '=', product_id.id),]


				move_ids =self.env['stock.move'].search(m_domain,order='date')
           
				if move_ids:
					for move in move_ids:
						#check if there is value correction at move date 

						if move.location_id.usage == 'supplier' or move.location_dest_id.usage == 'supplier':
							for valuation in move.stock_valuation_layer_ids:
								po_qty += valuation.quantity
								po_value += valuation.value
								eb_qty += valuation.quantity
								eb_value += valuation.value
							continue	
						elif move.location_id.usage == 'customer' or move.location_dest_id.usage == 'customer':
							for valuation in move.stock_valuation_layer_ids:
								do_qty += valuation.quantity
								do_value += valuation.value
								eb_qty += valuation.quantity
								eb_value += valuation.value
							continue
						elif move.location_id.usage == 'inventory' or move.location_dest_id.usage == 'inventory':
							for valuation in move.stock_valuation_layer_ids:
								iv_qty += valuation.quantity
								iv_value += valuation.value
								eb_qty += valuation.quantity
								eb_value += valuation.value
							continue
						elif move.location_id == location_id and (move.location_dest_id.usage == 'internal' or move.location_dest_id.usage == 'transit'):
							if wizard.report_type == 'location' :
								in_qty += move.quantity_done * -1
								
								date = move.date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
								ctx_nas = dict(self.env.context) or {}
								#standard_price = move._get_price_unit()
								standard_price = 0
								if eb_qty !=0 :
									standard_price = eb_value/eb_qty
								else :
									ctx_nas.update({'to_date': date})
									product_nas = self.env['product.product'].with_context(ctx_nas)	.search([('id', '=', product_id.id)])
									if product_nas:
										for product in product_nas:
											if product.quantity_svl != 0 :
												standard_price = (product.value_svl / product.quantity_svl)
								in_value += move.quantity_done * -1 * standard_price
								eb_qty += move.quantity_done * -1
								eb_value += move.quantity_done * -1 * standard_price
								continue
						else :
							if wizard.report_type == 'location' :
								in_qty += move.quantity_done
								#standard_price =move._get_price_unit()
								date = move.date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
								ctx_nas = dict(self.env.context) or {}
								standard_price = 0
								if eb_qty !=0 :
									standard_price = eb_value/eb_qty
								else :
									ctx_nas.update({'to_date': date})
									product_nas = self.env['product.product'].with_context(ctx_nas)	.search([('id', '=', product_id.id)])
									if product_nas:
										for product in product_nas:
											if product.quantity_svl != 0 :
												standard_price = (product.value_svl / product.quantity_svl)
								in_value += move.quantity_done * standard_price
								eb_qty += move.quantity_done
								eb_value += move.quantity_done  * standard_price

				# ============== Price Correction ===============
				hp_qty = 0
				hp_unit = 0
				hp_value = 0
				hp_loc_qty = 0
				hp_nas_qty = 0

				move_ids =self.env['stock.valuation.layer'].search([('account_move_id', '!=', False),
																	('stock_move_id', '=', False),
																	('create_date', '>=', start_date),
																	('create_date', '<=', end_date),
																	('product_id', '=', product_id.id),])
                                                              
				if move_ids:
					for valuation in move_ids:
						hp_qty += valuation["quantity"]
						hp_value +=  valuation["value"]
						if wizard.report_type == 'location' :
							ctx_loc = dict(self.env.context) or {}
							ctx_nas = dict(self.env.context) or {}
							date = valuation.create_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
							ctx_loc.update({'to_date': date,'location' : location_id.id,})
							ctx_nas.update({'to_date': date})
							product_loc = self.env['product.product'].with_context(ctx_loc).search([('id', '=', product_id.id)])
							if product_loc:
								for product in product_loc:
									hp_loc_qty += product.qty_available	

							product_nas = self.env['product.product'].with_context(ctx_nas)	.search([('id', '=', product_id.id)])
							if product_nas:
								for product in product_nas:
									hp_nas_qty += product.qty_available	
				
			
				
					

				if wizard.report_type == 'location' :
					if hp_qty != 0:
						hp_unit = hp_value/hp_qty
						hp_qty = hp_loc_qty
						hp_value = hp_qty*hp_unit
					else:
						if hp_nas_qty != 0:
							hp_unit = hp_value/hp_nas_qty
						hp_value = hp_loc_qty*hp_unit

				eb_qty += hp_qty
				eb_value += hp_value

				if wizard.report_type == 'location' :
					standard_price = 0
					ctx_nas = dict(self.env.context) or {}
					ctx_nas.update({'to_date': eb_date,'location' : location_id.id,})
					product_nas = self.env['product.product'].with_context(ctx_nas)	.search([('id', '=', product_id.id)])
					if product_nas:
						for product in product_nas:
							if product.quantity_svl != 0 :
								standard_price = (product.value_svl / product.quantity_svl)
							eb_qty = product.qty_available
							eb_value = eb_qty * standard_price

				worksheet.write(row, 0, product_id.display_name)
				worksheet.write(row, 1, ib_qty)
				worksheet.write(row, 2, ib_value)
				worksheet.write(row, 3, po_qty)
				worksheet.write(row, 4, po_value)
				worksheet.write(row, 5, do_qty)
				worksheet.write(row, 6, do_value)
				worksheet.write(row, 7, iv_qty)
				worksheet.write(row, 8, iv_value)
				worksheet.write(row, 9, in_qty)
				#worksheet.write(row, 10, in_value)
				worksheet.write(row, 11, hp_qty)
				worksheet.write(row, 12, hp_value)				
				worksheet.write(row, 13, eb_qty)
				worksheet.write(row, 14, eb_value)
			
				row += 1
			
			#raise Warning('end product')
			#workbook.close()
			#buf = base64.b64encode(open('/tmp/' + file_path, 'rb+').read())
			#wizard.document = buf
			#wizard.file = 'Inventory And Stock Valuation Report'+'.xlsx'
			fp = io.BytesIO()
			workbook.save(fp)
			excel_file = base64.encodestring(fp.getvalue())
			wizard.document = excel_file
			wizard.file = 'Stock Mutation Report.xls'
			#wizard.payment_report_printed = True
			fp.close()
			return {
				'view_mode': 'form',
				'res_id': wizard.id,
				'res_model': 'inventory.stock.valution.report.wizard',
				'view_type': 'form',
				'type': 'ir.actions.act_window',
				'context': self.env.context,
				'target': 'new',
				}

