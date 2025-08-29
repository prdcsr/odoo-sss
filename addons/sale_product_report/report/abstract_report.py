# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class AgedPartnerBalanceReport(models.AbstractModel):
    _name = "report.sale_product_report.abstract_report"
    _description = "Abstract Report"

    @api.model
    def _get_stock_quant_domain(
            self, location_ids, product_ids
    ):
        domain = []
        if location_ids:
            domain += [('location_id', 'in', location_ids)]
        if product_ids:
            domain += [('product_id', 'in', product_ids)]
        return domain

    @api.model
    def _get_products_domain(
            self, operating_unit_ids, name
    ):
        domain = [('type', 'like', 'product'), ('sale_ok', '=', True)]
        if operating_unit_ids:
            domain += ['|', ('operating_unit_ids', 'in', operating_unit_ids), ('operating_unit_ids', '=', False)]
        if name:
            domain += ['|', ('default_code', 'ilike', name.upper()),
                       ('name', 'ilike', name.upper())]
        # if internal_code:
        #     domain += [('default_code', 'in', internal_code)]
        # if used_for:
        #     domain += [('used_for', 'in', used_for)]

        return domain

    @api.model
    def _get_sale_products_domain(
            self, operating_unit_ids, name
    ):
        domain = [('sale_ok', '=', True)]
        if operating_unit_ids:
            domain += ['|', ('operating_unit_ids', 'in', operating_unit_ids), ('operating_unit_ids', '=', False)]
        if name:
            domain += ['|', ('default_code', 'ilike', name.upper()),
                       ('name', 'ilike', name.upper()),
                       ]
        # if internal_code:
        #     domain += [('default_code', 'in', internal_code)]
        # if used_for:
        #     domain += [('used_for', 'in', used_for)]

        return domain

    @api.model
    def _get_sale_order_line_domain(self, product_variant_ids,):
        domain = [('product_id', 'in', product_variant_ids)]
        return domain

    @api.model
    def _get_new_move_lines_domain(
            self, new_ml_ids, account_ids, company_id, partner_ids, only_posted_moves
    ):
        domain = [
            ("account_id", "in", account_ids),
            ("company_id", "=", company_id),
            ("id", "in", new_ml_ids),
        ]
        if partner_ids:
            domain += [("partner_id", "in", partner_ids)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        else:
            domain += [("move_id.state", "in", ["posted", "draft"])]
        return domain

    def _recalculate_move_lines(
            self,
            move_lines,
            debit_ids,
            credit_ids,
            debit_amount,
            credit_amount,
            ml_ids,
            account_ids,
            company_id,
            partner_ids,
            only_posted_moves,
    ):
        debit_ids = set(debit_ids)
        credit_ids = set(credit_ids)
        in_credit_but_not_in_debit = credit_ids - debit_ids
        reconciled_ids = list(debit_ids) + list(in_credit_but_not_in_debit)
        reconciled_ids = set(reconciled_ids)
        ml_ids = set(ml_ids)
        new_ml_ids = reconciled_ids - ml_ids
        new_ml_ids = list(new_ml_ids)
        new_domain = self._get_new_move_lines_domain(
            new_ml_ids, account_ids, company_id, partner_ids, only_posted_moves
        )
        ml_fields = [
            "id",
            "name",
            "date",
            "move_id",
            "journal_id",
            "account_id",
            "partner_id",
            "amount_residual",
            "date_maturity",
            "ref",
            "debit",
            "credit",
            "reconciled",
            "currency_id",
            "amount_currency",
            "amount_residual_currency",
        ]
        new_move_lines = self.env["account.move.line"].search_read(
            domain=new_domain, fields=ml_fields
        )
        move_lines = move_lines + new_move_lines
        for move_line in move_lines:
            ml_id = move_line["id"]
            if ml_id in debit_ids:
                move_line["amount_residual"] += debit_amount[ml_id]
            if ml_id in credit_ids:
                move_line["amount_residual"] -= credit_amount[ml_id]
        return move_lines

    def _get_locations_data(self, location_ids):
        locations = self.env["stock.location"].browse(location_ids)
        locations_data = {}
        for location in locations:
            locations_data.update(
                {
                    location.id: {
                        "id": location.id,
                        "name": location.display_name,
                    }
                }
            )
        return locations_data

    def _get_products_data(self, product_ids):
        products = self.env["product.product"].browse(product_ids)
        products_data = {}
        for product in products:
            products_data.update({product.id: {"id": product.id, "full_name": '[{product_code}] {product_name}'.format(
                product_code=product.default_code, product_name=product.name), 'group_code': product.used_for,
                                               'product_code': product.default_code, 'name': product.name,
                                               'used_for': product.used_for}})
        return products_data

    def _get_partners_data(self, partner_ids):
        partners = self.env["res.partner"].browse(partner_ids)
        partners_data = {}
        for partner in partners:
            partners_data.update({
                partner.id: {
                    "id": partner.id,
                    "display_name": partner.display_name,
                    "parent_name": partner.parent_id.name,
                    "name": partner.name,
                    "reference": partner.ref,
                }
            })
        return partners_data
