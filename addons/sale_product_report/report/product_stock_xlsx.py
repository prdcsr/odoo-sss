# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class OpenItemsXslx(models.AbstractModel):
    _name = "report.s_p_s_r.report_product_stock_xlsx"
    _description = "Open Items XLSX Report"
    _inherit = "report.sale_product_report.abstract_report_xlsx"

    def _get_report_name(self, report, data=False):
        company_id = data.get("company_id", False)
        report_name = "Sale Stock Report"
        if company_id:
            company = self.env["res.company"].browse(company_id)
            suffix = " - {} - {}".format(company.name, company.currency_id.name)
            report_name = report_name + suffix
        return report_name

    def _get_report_columns(self, report):
        res = {
            0: {"header": _("Kode Group"), "field": "date", "width": 11},
            1: {"header": _("No Part"), "field": "move_name", "width": 18},
            2: {"header": _("Nama Barang"), "field": "journal", "width": 8},
            3: {"header": _("Lokasi"), "field": "account", "width": 9},
            4: {"header": _("Jumlah"), "field": "partner_name", "width": 25},
            5: {"header": _("Satuan"), "field": "ref_label", "width": 40},
        }

        return res

    def _get_report_filters(self, report):
        return [
            [_("Date at filter"), report.date_at.strftime("%d/%m/%Y")],
            [
                _("Target moves filter"),
                _("All posted entries")
                if report.target_move == "posted"
                else _("All entries"),
            ],
            [
                _("Account balance at 0 filter"),
                _("Hide") if report.hide_account_at_0 else _("Show"),
            ],
            [
                _("Show foreign currency"),
                _("Yes") if report.foreign_currency else _("No"),
            ],
        ]

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 2

    def _get_col_count_final_balance_name(self):
        return 5

    def _get_col_pos_final_balance_label(self):
        return 5

    def _generate_report_content(self, workbook, report, data):
        res_data = self.env[
            "report.sale_product_report.product_stock"
        ]._get_report_values(report, data)
        # For each account
        stock_quants = res_data["stock_quants"]
        location_ids = res_data["location_ids"]

        for stock_id in stock_quants.keys():
            # Write account title
            self.write_array_title(
                location_ids[stock_id]["complete_name"]
            )

            # For each partner
            # if stock_quants[stock_id]:
            #     if show_partner_details:
            #         for partner_id in Open_items[account_id]:
            #             type_object = "partner"
            #             # Write partner title
            #             self.write_array_title(partners_data[partner_id]["name"])
            #
            #             # Display array header for move lines
            #             self.write_array_header()
            #
            #             # Display account move lines
            #             for line in Open_items[account_id][partner_id]:
            #                 line.update(
            #                     {
            #                         "account": accounts_data[account_id]["code"],
            #                         "journal": journals_data[line["journal_id"]][
            #                             "code"
            #                         ],
            #                     }
            #                 )
            #                 self.write_line_from_dict(line)
            #
            #             # Display ending balance line for partner
            #             partners_data[partner_id].update(
            #                 {
            #                     "currency_id": accounts_data[account_id]["currency_id"],
            #                     "currency_name": accounts_data[account_id][
            #                         "currency_name"
            #                     ],
            #                 }
            #             )
            #             self.write_ending_balance_from_dict(
            #                 partners_data[partner_id],
            #                 type_object,
            #                 total_amount,
            #                 account_id,
            #                 partner_id,
            #             )
            #
            #             # Line break
            #             self.row_pos += 1
            #     else:
            #         # Display array header for move lines
            #         self.write_array_header()
            #
            #         # Display account move lines
            #         for line in Open_items[account_id]:
            #             line.update(
            #                 {
            #                     "account": accounts_data[account_id]["code"],
            #                     "journal": journals_data[line["journal_id"]]["code"],
            #                 }
            #             )
            #             self.write_line_from_dict(line)
            #
            #     # Display ending balance line for account
            #     type_object = "account"
            #     self.write_ending_balance_from_dict(
            #         accounts_data[account_id], type_object, total_amount, account_id
            #     )
            #
            #     # 2 lines break
            #     self.row_pos += 2

    def write_ending_balance_from_dict(
        self, my_object, type_object, total_amount, account_id=False, partner_id=False
    ):
        """Specific function to write ending balance for Open Items"""
        if type_object == "partner":
            name = my_object["name"]
            my_object["residual"] = total_amount[account_id][partner_id]["residual"]
            label = _("Partner ending balance")
        elif type_object == "account":
            name = my_object["code"] + " - " + my_object["name"]
            my_object["residual"] = total_amount[account_id]["residual"]
            label = _("Ending balance")
        super(OpenItemsXslx, self).write_ending_balance_from_dict(
            my_object, name, label
        )
