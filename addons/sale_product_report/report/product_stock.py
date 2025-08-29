# © 2016 Julien Coux (Camptocamp)
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import operator
from datetime import date, datetime

from odoo import api, models
from odoo.tools import float_is_zero


class OpenItemsReport(models.AbstractModel):
    _name = "report.sale_product_report.product_stock"
    _description = "Product Stock Report"
    _inherit = "report.sale_product_report.abstract_report"

    def _get_data(
            self,
            location_ids,
            product_ids,
            # date_at_object,
            # only_posted_moves,
            # company_id,
            # date_from,
    ):
        product_varian_ids = product_ids.ids
        domain = self._get_stock_quant_domain(
            location_ids, product_varian_ids
        )
        ml_fields = [
            "id",
            "product_id",
            "location_id",
            "lot_id",
            "package_id",
            "owner_id",
            # "stored_qty",
            "reserved_quantity",
            "product_uom_id",
            'quantity'
        ]
        stock_quants = self.env["stock.quant"].search_read(
            domain=domain, fields=ml_fields
        )
        products_ids = set()
        locations_ids = set()
        locations_data = {}

        stock_quant_data = {}
        for quant in stock_quants:
            products_ids.add(quant['product_id'][0])

            if quant["location_id"]:
                loc_id = quant["location_id"][0]
                loc_name = quant["location_id"][1]
            else:
                loc_id = 0
                loc_name = 'missing location'

            if loc_id in locations_ids:
                locations_data.update({
                    loc_id: {
                        'id': loc_id,
                        'name': loc_name,
                    }
                })
                locations_ids.add(loc_id)

            quant.update(
                {
                    "location_id": loc_id,
                    "location_name": loc_name,
                    "id": quant['id'],
                    "product_id": quant['product_id'][0],
                    "lot_id": quant['lot_id'],
                    "package_id": quant['package_id'],
                    # "inventory_quantity": quant['stored_qty'],
                    "reserved_quantity": quant['reserved_quantity'],
                    "product_uom_id": quant['product_uom_id'],
                    "quantity": quant['quantity'],
                }

            )

            if loc_id not in stock_quant_data.keys():
                stock_quant_data[loc_id] = [quant]
            else:
                stock_quant_data[loc_id].append(quant)

        products_data = self._get_products_data(list(products_ids))
        locations_data = self._get_locations_data(stock_quant_data.keys())

        return (locations_data, products_data, stock_quant_data)

    @api.model
    def set_quant_data(
            self, stock_quants
    ):
        new_stock_quants = {}

        for quant_id in stock_quants.keys():
            new_stock_quants[quant_id] = {}
            move_lines = []
            move_lines += stock_quants[quant_id]
            new_stock_quants[quant_id] = move_lines

        return new_stock_quants


    def _get_report_values(self, docids, data):
        wizard_id = data["wizard_id"]
        # company = self.env["res.company"].browse(data["company_id"])
        # company_id = data["company_id"]
        def_operating_unit = self.env.user.operating_unit_ids

        operating_unit_ids = data['operating_unit_ids'] or def_operating_unit
        location_ids = data["location_ids"]
        # internal_code = data["internal_code"]
        # used_for = data["part_no"]
        name = data["product_name"]

        product_domain = self._get_products_domain(
            operating_unit_ids, name
        )
        product_ids = self.env["product.product"].search(product_domain)

        (location_data, products_data, stock_quants) = self._get_data(
            location_ids,
            product_ids)

        stock_quants = self.set_quant_data(
            stock_quants
        )

        return {
            "doc_ids": [wizard_id],
            "doc_model": "product.sale.report.wizard",
            "docs": self.env["product.stock.report.wizard"].browse(wizard_id),
            "stock_quants": stock_quants,
            'location_data': location_data,
            "products_data": products_data,
        }
