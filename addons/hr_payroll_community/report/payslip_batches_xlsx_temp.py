# Copyright 2017-19 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import _, models
from odoo.exceptions import CacheMiss

_logger = logging.getLogger(__name__)


class PayslipBatchesXlsx(models.AbstractModel):
    _name = "report.hr_payslip_run.payslip_batches_xlsx_temp"
    _description = "Payslip batches XLSX Report"
    _inherit = "report.report_xlsx.abstract"

    def print_batches_children(self, ch, sheet, row, level):
        i_dict = row
        sheet.write(i_dict[0], 0,  i_dict[0]-4)
        sheet.write(i_dict[0], 1, ch.number or "")
        sheet.write(i_dict[0], 2, ch.employee_id.display_name or "")
        #Collect Refereence
        ch_ref = ''
        for workday in ch.worked_days_line_ids:
            if workday.code != 'WORK100':
                ch_ref += workday.name + ' '
        sheet.write(i_dict[0], 3, ch_ref or "")
        k = 4
        j=1
        for line in  ch.line_ids:
            sheet.write(i_dict[0], k, line.amount or 0)
            i_dict[j] += line.amount
            k += 1
            j+=1

        #sheet.write(
        #    i,
        #    4,
        #    ch.product_uom_id._compute_quantity(ch.product_qty, ch.product_id.uom_id)
        #    or "",
       # )
       # sheet.write(i, 5, ch.product_id.uom_id.name or "")
       # sheet.write(i, 6, ch.bom_id.code or "")
        i_dict[0] += 1
        # self.env.cache.invalidate()
       # try:

       # except CacheMiss:
            # The Bom has no childs, thus it is the last level.
            # When a BoM has no childs, chlid_line_ids is None, this creates a
            # CacheMiss Error. However, this is expected because there really
            # cannot be child_line_ids.
        #    pass

       # j -= 1
        return i_dict

    def generate_xlsx_report(self, workbook, data, objects):
        workbook.set_properties(
            {"comments": "Created with Python and XlsxWriter "}
        )
        sheet = workbook.add_worksheet(_("PaySlip Batches"))
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.set_zoom(80)
        sheet.set_column(0, 0, 40)
        sheet.set_column(1, 2, 20)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 6, 20)
        bold = workbook.add_format({"bold": True})
        title_style = workbook.add_format(
            {"bold": True, "bg_color": "#FFFFCC", "bottom": 1}
        )
        sheet_title = [
            _("Batches Name"),
            _("Period"),
           # _("Product Reference"),
           # _("Product Name"),
           # _("Quantity"),
           # _("Unit of Measure"),
           # _("Reference"),
        ]
        sheet.set_row(0, None, None, {"collapsed": 1})
        sheet.write_row(1, 0, sheet_title, title_style)
        sheet.freeze_panes(2, 0)
        i = 2
        for o in objects:
            sheet.write(i, 0, o.name or "", bold)
            #sheet.write(i, 1, "", bold)
            sheet.write(i, 1, o.date_start.strftime('%d-%m-%Y') or "", bold)
            sheet.write(i, 2, o.date_end.strftime('%d-%m-%Y') or "", bold)
            #sheet.write(i, 4, o.product_qty, bold)
            #sheet.write(i, 5, o.product_uom_id.name or "", bold)
            #sheet.write(i, 6, o.code or "", bold)
            i += 2
            j = 0
            sheet_child_title = [
                _("No"),
                _("Payslip No"),
                _("Employee"),
                _("Reference"),
                _("Uang Makan"),
                _("Uang Makan LK"),
                _("Izin,Cuti Dan Telat"),
                _("Lembur DiBayar Per Jam"),
                _("Lembur DiBayar Bulat 100K"),
                _("Lembur DiBayar Bulat 120K"),
                _("Total UM + Lembur"),
                _("TTD"),
            ]
            sheet.write_row(i, 0, sheet_child_title, title_style)
            i += 1
            i_dict=[i,0,0,0,0,0,0,0]
            for ch in o.slip_ids:
                i_dict = self.print_batches_children(ch, sheet, i_dict, j)
            i=i_dict[0]
            meal,lk,deduct,jam,hk,h20k,ttl = i_dict[1],i_dict[2],i_dict[3],i_dict[4],i_dict[5],i_dict[6],i_dict[7]

            sheet.write(i, 0, "Total", title_style)
            sheet.write(i, 1, "", title_style)
            sheet.write(i, 2, "", title_style)
            sheet.write_row(i, 3, i_dict, title_style)
            #sheet.write(i, 4, meal, title_style)            
            
            #sheet.write(i, 5, lk, title_style)            
            #sheet.write(i, 6, deduct, title_style)            
            #sheet.write(i, 7, jam)            
            #sheet.write(i, 8, hk)
            #sheet.write(i, 9, h20k)
            #sheet.write(i, 10, ttl)
            