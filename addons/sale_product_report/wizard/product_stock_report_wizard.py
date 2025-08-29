# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class OpenItemsReportWizard(models.TransientModel):
    """Open items report wizard."""

    _name = "product.stock.report.wizard"
    _description = "Product Stock Report Wizard"

    location_ids = fields.Many2many(
        comodel_name="stock.location",
        string="Filter Location",
        compute="_compute_location_ids",
        inverse="_inverse_location_ids",
    )
    # internal_code = fields.Char(string="Kode Grup")
    # part_no = fields.Char(string="Nomor Part")
    product_name = fields.Char(string="Nama Produk", required=True)
    operating_unit_ids = fields.Many2many(
        comodel_name="operating.unit",
        default=lambda self: self.env.user.operating_unit_ids.ids or self.env.user.default_operating_unit_id.ids,
        required=True,
        string="Operating Unit",
        domain=lambda self: [("id", "in", self.env.user.operating_unit_ids.ids)],
    )

    # @api.onchange("company_id")
    # def onchange_company_id(self):
    #     """Handle company change."""
    #     if self.company_id and self.warehouse_ids:
    #         self.warehouse_ids = self.warehouse_ids.filtered(
    #             lambda p: p.company_id == self.company_id or not p.company_id
    #         )
    #
    #     res = {"domain": {"warehouse_ids": []}}
    #     if not self.company_id:
    #         return res
    #     else:
    #         res["domain"]["warehouse_ids"] += [("company_id", "=", self.company_id.id)]
    #     return res

    @api.depends("operating_unit_ids")
    def _compute_location_ids(self):
        self.ensure_one()
        self.location_ids = []
        if 1 in self.operating_unit_ids.ids:
            location_list = self.env['stock.location'].search([('complete_name', 'in',
                                                                ['JKT25CD/Stock', 'JKT25CD/OTWImport', 'SBYF22/Stock',
                                                                 'SBYF22/OTWImport', 'MEDAN/Stock',
                                                                 'MEDAN/OTWImport', 'TEST/Stock'])])
            self.location_ids += location_list
        if 2 in self.operating_unit_ids.ids:
            location_list = self.env['stock.location'].search(
                [('complete_name', 'in', ['JKT61/Stock', 'JKT61/OTWImport', 'JKT61/OnCheck', 'WH/Stock'])])
            self.location_ids += location_list

    def _inverse_location_ids(self):
        self.ensure_one()
        return None

    def _print_report(self, report_type):
        self.ensure_one()
        data = self._prepare_report_open_items()
        if report_type == "xlsx":
            report_name = "s_p_s_r.report_product_stock_xlsx"
        else:
            report_name = "sale_product_report.product_stock"
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(self, data=data)
        )

    def _prepare_report_open_items(self):
        self.ensure_one()
        return {
            "wizard_id": self.id,
            "operating_unit_ids": self.operating_unit_ids.ids or [],
            # "internal_code": self.internal_code,
            # "part_no": self.part_no,
            "product_name": self.product_name,
            "location_ids": self.location_ids.ids or [],
            "sale_product_stock_report_lang": self.env.lang,
        }

    def button_export_html(self):
        self.ensure_one()
        report_type = "qweb-html"
        return self._print_report(report_type)

    def button_export_pdf(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._print_report(report_type)

    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._print_report(report_type)
