# © 2016 Julien Coux (Camptocamp)
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import operator
from datetime import date, datetime

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class OpenItemsReport(models.AbstractModel):
    _name = "report.sale_product_report.product_sale"
    _description = "Product Sale Report"
    _inherit = "report.sale_product_report.abstract_report"

    def _get_data(
            self,
            product_ids,
            partner_ids,
            date_from,
            date_to
    ):
        product_variant_ids = product_ids.ids
        domain = self._get_sale_order_line_domain(
            product_variant_ids,
        )
        ml_fields = [
            "id",
            "product_id",
            "product_uom_qty",
            "qty_invoiced",
            "price_unit",
            "price_reduce",
            "price_subtotal",
            "order_id",
        ]
        sale_order_line = self.env["sale.order.line"].search(
            domain
        ).filtered(lambda line: line['order_id'].partner_id.id in partner_ids and line['order_id'].date_order >= datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S') and line['order_id'].date_order <= datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S') and line['order_id'].state not in ['cancel', 'draft'])

        products_ids = set()
        partners_ids = set()
        partners_data = {}

        product_sale_data = {}
        for order_line in sale_order_line:
            products_ids.add(order_line.product_id.id)
            order_id = order_line.order_id.id

            if order_line.product_id:
                product_id = order_line.product_id.id
                product_name = order_line.product_id.name
            else:
                product_id = 0
                product_name = 'missing product data'

            order = order_line.order_id
            if order:
                order_name = order.name
                order_date = order.date_order
                partner_id = order.partner_id.id
                partner_name = order.partner_id.name
            else:
                order_name = order.name
                partner_id = 0
                partner_name = "Missing Partner"
                order_date = "Missing Order Date"

            if partner_id in partner_ids:
                partners_data.update({
                    partner_id: {
                        'id': partner_id,
                        'name': partner_name,
                    }
                })
                partners_ids.add(partner_id)

            line = {
                    "id": order_line['id'],
                    "product_id": order_line['product_id'].id,
                    "product_uom_qty": order_line['product_uom_qty'],
                    "qty_invoiced": order_line['qty_invoiced'],
                    "price_unit": order_line['price_unit'],
                    "price_reduce": order_line['price_reduce'],
                    "price_subtotal": order_line['price_subtotal'],
                    "order_id": order_id,
                    "order_name": order_name,
                    'partner_id': partner_id,
                    'partner_name': partner_name,
                    'order_date': order_date.strftime("%d-%m-%Y"),
                }

            if partner_id not in product_sale_data.keys():
                product_sale_data[partner_id] = {product_id: [line]}
            else:
                if product_id not in product_sale_data[partner_id].keys():
                    product_sale_data[partner_id][product_id] = [line]
                else:
                    product_sale_data[partner_id][product_id].append(line)

        products_data = self._get_products_data(list(products_ids))
        partners_data = self._get_partners_data(product_sale_data.keys())

        return partners_data, products_data, product_sale_data

    # def _get_data(self, product_ids, partner_ids, date_from, date_to):
    #     product_variant_ids = product_ids.ids
    #
    #     if len(partner_ids) > 0 and len(product_variant_ids) > 0 and date_from and date_to:
    #         query = """
    #             select
    #                 product_product.id as product_id,
    #                 product_uom_qty as total_qty,
    #                 price_subtotal as total_price,
    #                 sale_order_line.price_unit as price_unit,
    #                 sale_order.date_order as date_order,
    #                 sale_order.name as so_no,
    #                 res_partner.name as partner_name,
    #                 res_partner.id as partner_id
    #             from sale_order_line
    #             join product_product on sale_order_line.product_id = product_product.id
    #             join product_template on product_product.product_tmpl_id = product_template.id
    #             join sale_order on sale_order_line.order_id = sale_order.id
    #             join res_partner on sale_order.partner_id = res_partner.id
    #             where product_template.sale_ok = true
    #                 and sale_order_line.product_id in %s
    #                 and sale_order.partner_id in %s
    #                 and sale_order.date_order >= %s
    #                 and sale_order.date_order <= %s
    #                 and sale_order.state not in ('cancel', 'draft')
    #             group by product_product.id, res_partner.id, sale_order.id, product_uom_qty
    #             order by res_partner.name
    #         """
    #         self.env.cr.execute(query, [tuple(product_variant_ids), tuple(partner_ids), (date_from), (date_to)])
    #         result = self.env.cr.dictfetchall()
    #         products_ids = set()
    #         partners_ids = set()
    #         partners_data = {}
    #
    #         product_sale_data = {}
    #         for order_line in result:
    #             products_ids.add(order_line['product_id'])
    #
    #             if order_line["partner_id"]:
    #                 partner_id = order_line["partner_id"]
    #                 partner_name = order_line["partner_name"]
    #             else:
    #                 partner_id = 0
    #                 partner_name = 'missing order data'
    #
    #
    #             if partner_id in partner_ids:
    #                 partners_data.update({
    #                     partner_id: {
    #                         'id': partner_id,
    #                         'name': partner_name,
    #                     }
    #                 })
    #                 partners_ids.add(partner_id)
    #
    #             order_line.update(
    #                 {
    #                     "product_id": order_line['product_id'],
    #                     "product_uom_qty": order_line['total_qty'],
    #                     "price_subtotal": order_line['total_price'],
    #                     "price_unit": order_line['price_unit'],
    #                     "date_order": order_line['date_order'],
    #                     "so_no": order_line['so_no'],
    #                     partner_id: partner_id,
    #                     partner_name: partner_name,
    #                 }
    #
    #             )
    #
    #             if partner_id not in product_sale_data.keys():
    #                 product_sale_data[partner_id] = [order_line]
    #             else:
    #                 product_sale_data[partner_id].append(order_line)
    #
    #         products_data = self._get_products_data(list(products_ids))
    #         partners_data = self._get_partners_data(product_sale_data.keys())
    #
    #         return partners_data, products_data, product_sale_data
    #     else:
    #         raise UserError("Data penjualan untuk produk yang diminta tidak ditemukan")

    @api.model
    def set_product_sale(
            self, product_sale
    ):
        new_product_sale = {}

        for product_sale_id in product_sale.keys():
            new_product_sale[product_sale_id] = {}
            move_lines = []
            move_lines += product_sale[product_sale_id]
            new_product_sale[product_sale_id] = move_lines

        return new_product_sale


    def _get_report_values(self, docids, data):
        wizard_id = data["wizard_id"]
        def_operating_unit = self.env.user.operating_unit_ids

        operating_unit_ids = data['operating_unit_ids'] or def_operating_unit
        partner_ids = data["partner_ids"]
        name = data["product_name"]
        date_from = data["date_from"] + ' 00:00:00'
        date_to = data["date_to"] + ' 23:59:59'

        product_domain = self._get_sale_products_domain(
            operating_unit_ids, name
        )
        product_ids = self.env["product.product"].search(product_domain)

        if len(partner_ids) == 0:
            partner_ids = self.env["res.partner"].search([('user_id', '=', self.env.user.id)]).ids

        (partners_data, products_data, product_sale_data) = self._get_data(
            product_ids, partner_ids, date_from, date_to)

        # product_sale_data = self.set_product_sale(
        #     product_sale_data
        # )

        return {
            "doc_ids": [wizard_id],
            "doc_model": "product.sale.report.wizard",
            "docs": self.env["product.stock.report.wizard"].browse(wizard_id),
            "product_sale": product_sale_data,
            'partners_data': partners_data,
             "products_data": products_data,
        }
