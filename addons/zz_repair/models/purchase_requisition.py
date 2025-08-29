

from datetime import datetime, timedelta,time
from collections import defaultdict

from odoo import api, fields, models,tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError

class PurchaseRequisition(models.Model):
	_inherit = "purchase.requisition"

	port_of_loading = fields.Char(string='Port Of Loading')
	port_of_destination = fields.Char(string='Port OF Destination')

	
	@api.model
	def create(self, vals):
		# Check for duplicate product codes in the purchase requisition lines
		product_codes = {}
		duplicates = []

		for line in vals.get('line_ids', []):
			product_id = line[2].get('product_id', False)
			if product_id:
				product = self.env['product.product'].browse(product_id)
				product_code = product.default_code or ''
				product_name = product.name

				if product_code in product_codes:
					if product_code not in duplicates:
						duplicates.append(product_code)
				else:
					product_codes[product_code] = product_name

		if duplicates:
			error_message = _("Duplicate product codes detected in purchase requisition lines:\n")
			for product_code in duplicates:
				product_name = product_codes.get(product_code, '')
				error_message += f"- Product Code: {product_code}, Product Name: {product_name}\n"

			raise UserError(error_message)

		return super(PurchaseRequisition, self).create(vals)

	def action_in_progress(self):
		self.ensure_one()
		super(PurchaseRequisition, self).action_in_progress()
		users = self.env['res.users'].search([('groups_id', 'in', self.env.ref('zz_repair.group_user_import').id)])
		recipient_emails = users.mapped('partner_id.email')
		mail_template = self.env.ref('zz_repair.email_template_purchase_requisition_notification')
		for email in recipient_emails:
			mail_template.sudo().send_mail(
				self.id,
				email_values={
					'email_to': email,
				},
				force_send=True
			)

class PurchaseRequisitionLine(models.Model):
	_inherit = "purchase.requisition.line"

	product_description_variants = fields.Text('Custom Description')

