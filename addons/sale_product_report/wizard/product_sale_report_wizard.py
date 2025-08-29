# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class OpenItemsReportWizard(models.TransientModel):
    """Open items report wizard."""

    _name = "product.sale.report.wizard"
    _description = "Product Stock Report Wizard"
    # internal_code = fields.Char(string="Kode Grup")
    # part_no = fields.Char(string="Nomor Part")
    product_name = fields.Char(string="Nama Produk", required=False,)
    partner_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Partner",
        # required=True,
        # domain=lambda self: [("user_id", "=", self.env.user.id)],
    )
    operating_unit_ids = fields.Many2many(
        comodel_name="operating.unit",
        default=lambda self: self.env.user.operating_unit_ids.ids or self.env.user.default_operating_unit_id.ids,
        required=True,
        string="Operating Unit",
        domain=lambda self: [("id", "in", self.env.user.operating_unit_ids.ids)],
    )
    date_from = fields.Date(string="Tanggal Awal", required=True)
    date_to = fields.Date(string="Tanggal Akhir", default=fields.Date.today)

    # def filter_partner(self):
    #     domain = []
    #     if self.operating_unit_ids.ids.length == 1 and 1 in self.operating_unit_ids.ids:
    #         domain.append(("ref", "like", 'CU'))
    #     elif self.operating_unit_ids.ids.length == 1 and 2 in self.operating_unit_ids.ids:
    #         domain.append(("ref", "like", 'CS'))

    def _print_report(self, report_type):
        self.ensure_one()
        data = self._prepare_report_open_items()
        if report_type == "xlsx":
            report_name = "s_p_s_r.report_product_sale_xlsx"
        else:
            report_name = "sale_product_report.product_sale"
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
            "partner_ids": self.partner_ids.ids or [],
            # "internal_code": self.internal_code,
            # "part_no": self.part_no,
            "product_name": self.product_name,
            "sale_product_stock_report_lang": self.env.lang,
            "date_from": self.date_from,
            "date_to": self.date_to,
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
