# Copyright 2017-19 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import datetime
import logging

from odoo import _, models
from . import cell_constants as constants

_logger = logging.getLogger(__name__)


class PayslipBatchesXlsx(models.AbstractModel):
    _name = "report.hr_payslip_run.payslip_batches_xlsx"
    _description = "Payslip batches XLSX Report"
    _inherit = "report.report_xlsx.abstract"

    def print_batches_children(self, data, sheet, row, col_idx, workbook, year):
        style = workbook.add_format({
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter',
            'text_wrap': True
        })

        style_center = workbook.add_format({
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter',
            'align': 'center',
            'text_wrap': True
        })

        styled_currency = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        year_mod = year % 2000
        off_info = ''
        off_total = 0
        worked_day = 0
        food_salary = 0
        outside_meal = 0
        overtime_meal = 0
        outside_info = ''
        outside_total = 0
        overtime_info = ''
        overtime_total = 0
        total = 0

        outside_code_list = [
            # 'dinasluar_' + str(year_mod),
            'dinasluarkota_' + str(year_mod),
            # 'dinas_ln'
        ]

        overtime_code_list = [
            'lembur_h' + str(year),
            'OT100',
            'OVT_OUT'
            # 'lembur_hl' + str(year),
        ]

        off_code_list = [
            'cuti_menikah',
            'cuti_anak_menikah',
            'cuti_kematian_keluarga_inti',
            'cuti_istri_melahirkan',
            'cuti_melahirkan',
            'kematian_keluarga'
            'kematian_keluarga_inti'
        ]

        for workday in data.worked_days_line_ids:
            if workday.code not in overtime_code_list and workday.code != 'WORK100' and workday.code != 'GLOBAL':
                off_info += workday.name + ' '
            if workday.code == 'WORK100':
                worked_day += workday.number_of_days
            if workday.code == 'GLOBAL':
                worked_day -= workday.number_of_days
            # if workday.code == "cuti2022" or workday.code == "cuti2023":
            if workday.code == 'cuti' + str(year) or workday.code == "skt_" + str(
                    year) or workday.code == "izin_" + str(
                year_mod) or workday.code in outside_code_list:
                off_total += workday.number_of_days
            # if workday.code == "telat2022" or workday.code == "telat2023":
            if workday.code == "telat" + str(year):
                off_total += workday.number_of_days * 0.5
            # if workday.code == "WFH" or workday.code == "izin052023":
            if workday.code == "WFH" or workday.code == "izin05" + str(year):
                off_total += workday.number_of_days * 0.5
            if workday.code in off_code_list:
                off_total += workday.number_of_days

        for other in data.input_line_ids:
            if other.code in overtime_code_list and other.number_of_days:
                overtime_total += other.number_of_days
                overtime_info += other.name + ','
                overtime_meal += other.amount
            if other.code in outside_code_list and other.number_of_days:
                outside_total += other.number_of_days
                outside_info += other.name + ','
                outside_meal += other.amount

            # # if workday.code == "skt_2022" or workday.code == "skt_2023":
            # if workday.code == "skt_" + str(year):
            #     off_total += workday.number_of_days
            # # if workday.code == "izin2022" or workday.code == "izin2023":
            # if workday.code == "izin" + str(year):
            #     off_total += workday.number_of_days
            # if workday.code == 'dinas_ln':
            #     off_total += workday.number_of_days

        for rule in data.line_ids:
            if rule.code == 'WORK100':
                food_salary += rule.amount
            # if rule.code in outside_code_list:
            #     outside_meal += rule.amount
            # if rule.code in overtime_code_list:
            #     overtime_meal += rule.amount
            if rule.code == 'CDT':
                food_salary += rule.amount
            if rule.code == 'NET':
                total += rule.amount

        sheet.write(row, constants.COL_NO, col_idx + 1, style_center)
        # sheet.write(row, constants.COL_PAID_VIA, data.contract_id.hr_responsible_id.name or "", style)
        sheet.write(row, constants.COL_NAMA, data.employee_id.name or "", style)
        # sheet.write(row, constants.COL_JABATAN, data.employee_id.job_title or "", style)
        sheet.write_number(row, constants.COL_HARI_KERJA, worked_day, style_center)
        sheet.write_number(row, constants.COL_TELAT, off_total * -1, style_center)
        sheet.write(row, constants.COL_KETERANGAN, off_info, style)
        sheet.write_formula(row, constants.COL_TOTAL_HARI, '=C{row}+D{row}'.format(row=row + 1),
                            style_center)
        sheet.write_number(row, constants.COL_UANG_MAKAN_KOTA, food_salary, styled_currency)
        sheet.write_number(row, constants.COL_TOTAL_HARI_LUAR, outside_total, style_center)
        sheet.write_number(row, constants.COL_UANG_MAKAN_LUAR, outside_meal, styled_currency)
        sheet.write(row, constants.COL_KETERANGAN_UANG_MAKAN_LUAR, outside_info, style)

        sheet.write_number(row, constants.COL_TOTAL_LEMBUR, overtime_total, style_center)
        sheet.write_number(row, constants.COL_UPAH_LEMBUR, overtime_meal, styled_currency)
        sheet.write(row, constants.COL_KETERANGAN_LEMBUR, overtime_info, style)

        sheet.write_number(row, constants.COL_TOTAL_UANG_MAKAN, total, styled_currency)
        sheet.write(row, constants.COL_TTD_1, '', style)

        # if (row + 1) % 2 == 0:
        #     sheet.write(row, constants.COL_TTD_1, col_idx + 1, style)
        #     sheet.write(row, constants.COL_TTD_2, '', style_left)
        # else:
        #     sheet.write(row, constants.COL_TTD_2, col_idx + 1, style)
        #     sheet.write(row, constants.COL_TTD_1, '', style_left)

        row += 1
        return row

    def generate_weekly(self, workbook, data, objects):
        workbook.set_properties(
            {"comments": "Created with Python and XlsxWriter "}
        )
        sheet = workbook.add_worksheet(_("PaySlip Batches"))
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)

        bold_center = workbook.add_format({
            'bold': 1,
            'font_size': 12,
            'border_color': 'orange', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        })
        bold_left = workbook.add_format({
            'bold': 1,
            'font_size': 14,
            'border_color': 'orange', 'valign': 'vcenter', 'text_wrap': True
        })
        border_bold_center = workbook.add_format({
            'bold': 1,
            'border': 1,
            'border_color': 'orange', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        })

        styled_currency = workbook.add_format({
            'bold': 1,
            'num_format': '#,##0',
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter', 'text_wrap': True, 'bg_color': '#D9D9D9'
        })

        sheet.set_column(constants.COL_NO, constants.COL_NO, 5)
        # sheet.set_column(constants.COL_PAID_VIA, constants.COL_PAID_VIA, 9)
        sheet.set_column(constants.COL_NAMA, constants.COL_NAMA, 29)
        # sheet.set_column(constants.COL_JABATAN, constants.COL_JABATAN, 12)
        sheet.set_column(constants.COL_HARI_KERJA, constants.COL_HARI_KERJA, 5)
        sheet.set_column(constants.COL_TELAT, constants.COL_TELAT, 9.5)
        sheet.set_column(constants.COL_KETERANGAN, constants.COL_KETERANGAN, 16.5)
        sheet.set_column(constants.COL_TOTAL_HARI, constants.COL_TOTAL_HARI, 5)
        sheet.set_column(constants.COL_UANG_MAKAN_KOTA, constants.COL_UANG_MAKAN_KOTA, 16)
        sheet.set_column(constants.COL_TOTAL_HARI_LUAR, constants.COL_TOTAL_HARI_LUAR, 5)
        sheet.set_column(constants.COL_UANG_MAKAN_LUAR, constants.COL_UANG_MAKAN_LUAR, 13)
        sheet.set_column(constants.COL_KETERANGAN_UANG_MAKAN_LUAR, constants.COL_KETERANGAN_UANG_MAKAN_LUAR,
                         23)
        sheet.set_column(constants.COL_TOTAL_LEMBUR, constants.COL_TOTAL_LEMBUR, 9)
        sheet.set_column(constants.COL_UPAH_LEMBUR, constants.COL_UPAH_LEMBUR, 12)
        sheet.set_column(constants.COL_KETERANGAN_LEMBUR, constants.COL_KETERANGAN_LEMBUR, 23)
        sheet.set_column(constants.COL_TOTAL_UANG_MAKAN, constants.COL_TOTAL_UANG_MAKAN, 13.30)
        sheet.set_column(constants.COL_TTD_1, constants.COL_TTD_1, 14)
        # sheet.set_column(constants.COL_TTD_2, constants.COL_TTD_2, 14)

        sheet.set_default_row(27.5)
        sheet.set_row(constants.ROW_TABLE_HEAD, 46.5)
        sheet.set_row(constants.ROW_PERIOD + 1, 10.5)

        for o in objects:
            sheet.merge_range('A{row}:C{row}'.format(row=constants.ROW_TITLE + 1), o.name or "", bold_left)
            sheet.merge_range('A{row}:C{row}'.format(row=constants.ROW_COMPANY_NAME + 1),
                              o.env.company.display_name or "", bold_left)
            sheet.merge_range('A{row}:B{row}'.format(row=constants.ROW_PERIOD + 1), 'Periode', bold_left)

            sheet.merge_range('C{row}:D{row}'.format(row=constants.ROW_PERIOD + 1),
                              o.date_start.strftime('%d-%m-%Y'),
                              bold_center)
            sheet.write(constants.ROW_PERIOD, constants.COL_PERIOD_VALUE + 2,
                        o.date_end.strftime('%d-%m-%Y'),
                        bold_center)
            year = o.date_start.year

            table_head = [
                "No",
                _("Nama"),
                _("Hari Kerja"),
                _("Potongan Hari Kerja"),
                _("Keterangan"),
                _("Total Hari"),
                _("UM Dalam Kota"),
                _("Hari Luar Kota"),
                _("UM Luar Kota"),
                _("Keterangan Luar Kota"),
                _("Jlh Lembur Hari libur"),
                _("Upah Lembur Hari Libur"),
                _("Ket Lembur Hari Libur"),
                _("Total UM"),
                _("Tanda Tangan"),
            ]

            for i, head in enumerate(table_head):
                sheet.write(constants.ROW_TABLE_HEAD, i, head, border_bold_center)

            curr_row = constants.ROW_TABLE_HEAD + 1
            for idx, ch in enumerate(o.slip_ids):
                curr_row = self.print_batches_children(ch, sheet, curr_row, idx, workbook, year)

            for idx, col in enumerate(table_head):
                sheet.write(curr_row, idx, '', styled_currency)

            sheet.write(curr_row, constants.COL_NAMA, 'Total', styled_currency)
            sheet.write_formula(curr_row, constants.COL_UANG_MAKAN_KOTA,
                                '=SUM(G{start}:G{end})'.format(start=constants.ROW_TABLE_HEAD + 2, end=curr_row),
                                styled_currency)
            sheet.write_formula(curr_row, constants.COL_UANG_MAKAN_LUAR,
                                '=SUM(I{start}:I{end})'.format(start=constants.ROW_TABLE_HEAD + 2, end=curr_row),
                                styled_currency)
            sheet.write_formula(curr_row, constants.COL_UPAH_LEMBUR,
                                '=SUM(L{start}:L{end})'.format(start=constants.ROW_TABLE_HEAD + 2, end=curr_row),
                                styled_currency)
            sheet.write_formula(curr_row, constants.COL_TOTAL_UANG_MAKAN,
                                '=SUM(N{start}:N{end})'.format(start=constants.ROW_TABLE_HEAD + 2, end=curr_row),
                                styled_currency)

            sheet.autofilter('A{start}:N{end}'.format(start=constants.ROW_TABLE_HEAD + 1, end=curr_row))
            sheet.freeze_panes('A1')
            sheet.freeze_panes('B2')
            sheet.freeze_panes('C3')
            sheet.freeze_panes('D4')
            sheet.freeze_panes('E5')
            sheet.freeze_panes('F6')
            sheet.set_landscape()
            sheet.center_horizontally()
            sheet.center_vertically()
            sheet.set_paper(5)
            sheet.set_margins(top=0, left=0, right=2)
            sheet.print_area(constants.ROW_TITLE, constants.COL_NO, curr_row, constants.COL_TTD_1)

    def print_overtime_batches_children(self, data, sheet, row, col_idx, workbook):
        style = workbook.add_format({
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter',
            'text_wrap': True
        })

        style_left = workbook.add_format({
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter',
            'align': 'left',
            'text_wrap': True
        })

        style_center = workbook.add_format({
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter',
            'align': 'center',
            'text_wrap': True
        })

        styled_currency = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        input_line_ids = data.input_line_ids
        total_amount = 0
        total_hour = 0
        for input in input_line_ids:
            if input.code == 'OVTHOUR' or input.code == 'OT100':
                total_amount += input.amount
                total_hour += input.number_of_hours

        if total_hour > 0:
            sheet.write(row, constants.COL_NO_OVERTIME, col_idx + 1, style_center)
            # sheet.write(row, constants.COL_PAID_VIA, data.contract_id.hr_responsible_id.name or "", style)
            sheet.write(row, constants.COL_NAME_OVERTIME, data.employee_id.name or "", style)
            sheet.write_number(row, constants.COL_OVERTIME_DURATION, total_hour or 0, style_center)
            sheet.write_number(row, constants.COL_OVERTIME_AMOUNT, total_amount or 0, styled_currency)

            if (col_idx + 1) % 2 != 0:
                sheet.write(row, constants.COL_SIGN_OVERTIME1, "{num}. ".format(num=col_idx + 1), style_left)
                sheet.write(row, constants.COL_SIGN_OVERTIME2, "", style_left)
            else:
                sheet.write(row, constants.COL_SIGN_OVERTIME2, "{num}. ".format(num=col_idx + 1), style_left)
                sheet.write(row, constants.COL_SIGN_OVERTIME1, "", style_left)
            row += 1
        return row

    def overtime_slip_filter(self, slip):
        hour_overtime = filter(lambda x: x.duration_type == 'hours', slip.overtime_ids)
        if hour_overtime:
            return True
        return False

    def generate_overtime_sheet(self, workbook, sheet, data, objects):
        bold_center = workbook.add_format({
            'bold': 1,
            'font_size': 12,
            'border_color': 'orange', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        })
        bold_left = workbook.add_format({
            'bold': 1,
            'font_size': 14,
            'border_color': 'orange', 'valign': 'vcenter', 'text_wrap': True
        })
        border_bold_center = workbook.add_format({
            'bold': 1,
            'border': 1,
            'border_color': 'orange', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        })

        styled_currency = workbook.add_format({
            'bold': 1,
            'num_format': '#,##0',
            'border': 1,
            'border_color': 'orange',
            'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bg_color': '#D9D9D9'
        })
        sheet.set_default_row(27.5)
        sheet.set_row(constants.ROW_TABLE_HEAD_OVERTIME, 46.5)
        sheet.set_row(constants.ROW_MONTH + 1, 10.5)

        sheet.set_column(constants.COL_NO_OVERTIME, constants.COL_NO_OVERTIME, 5)
        # sheet.set_column(constants.COL_PAID_VIA, constants.COL_PAID_VIA, 9)
        sheet.set_column(constants.COL_NAME_OVERTIME, constants.COL_NAME_OVERTIME, 29)
        sheet.set_column(constants.COL_OVERTIME_DURATION, constants.COL_OVERTIME_DURATION, 8)
        sheet.set_column(constants.COL_OVERTIME_AMOUNT, constants.COL_OVERTIME_AMOUNT, 16)
        sheet.set_column(constants.COL_SIGN_OVERTIME1, constants.COL_SIGN_OVERTIME1, 16)
        sheet.set_column(constants.COL_SIGN_OVERTIME2, constants.COL_SIGN_OVERTIME2, 16)

        curr_row = constants.ROW_TABLE_HEAD_OVERTIME + 1

        for o in objects:
            sheet.merge_range('A{row}:C{row}'.format(row=constants.ROW_TITLE_OVERTIME + 1), 'DAFTAR UANG LEMBUR',
                              bold_left)
            sheet.merge_range('A{row}:C{row}'.format(row=constants.ROW_COMPANY_NAME_OVERTIME + 1),
                              o.env.company.display_name or "", bold_left)
            sheet.merge_range('A{row}:B{row}'.format(row=constants.ROW_MONTH + 1), 'BULAN', bold_left)

            sheet.merge_range('C{row}:D{row}'.format(row=constants.ROW_MONTH + 1),
                              o.date_start.strftime('%b-%y'),
                              bold_center)

            table_head = [
                'NO',
                'Nama',
                'Durasi',
                'Total U. Lembur',
                'Tanda Tangan 1',
                'Tanda Tangan 2',
            ]

            for i, head in enumerate(table_head):
                sheet.write(constants.ROW_TABLE_HEAD_OVERTIME, i, head, border_bold_center)

            # slip_ids = filter(self.overtime_slip_filter, o.slip_ids)
            slip_ids = [slip for slip in o.slip_ids if
                        len([overtime for overtime in slip.overtime_ids if overtime.duration_type == 'hours']) > 0]
            for slip in slip_ids:
                print(slip.employee_id.name)

            for idx, ch in enumerate(slip_ids):
                curr_row = self.print_overtime_batches_children(ch, sheet, curr_row, idx, workbook)

        sheet.merge_range('A{row}:C{row}'.format(row=curr_row + 1), 'Total', border_bold_center)

        sheet.merge_range("D{row}:F{row}".format(row=curr_row + 1), "", border_bold_center)
        sheet.write_formula(curr_row, constants.COL_OVERTIME_AMOUNT,
                            '=SUM(D{start}:D{end})'.format(start=constants.ROW_TABLE_HEAD_OVERTIME + 2, end=curr_row),
                            styled_currency)
        sheet.write(curr_row, constants.COL_SIGN_OVERTIME2, "", border_bold_center)

        sheet.autofilter('A{start}:F{end}'.format(start=constants.ROW_TABLE_HEAD_OVERTIME + 1, end=curr_row - 1))
        sheet.freeze_panes('A1')
        sheet.freeze_panes('B2')
        sheet.freeze_panes('C3')
        sheet.freeze_panes('D4')
        # sheet.freeze_panes('E5')
        sheet.set_landscape()
        sheet.center_horizontally()
        sheet.center_vertically()
        sheet.set_paper(5)
        sheet.set_margins(top=0, left=0, right=2)
        sheet.print_area(constants.ROW_TITLE_OVERTIME, constants.COL_NO_OVERTIME, curr_row,
                         constants.COL_SIGN_OVERTIME2)

    def print_diligence_batch_children(self, data, sheet, row, col_idx, workbook):
        style = workbook.add_format({
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter',
            'text_wrap': True
        })

        style_left = workbook.add_format({
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter',
            'align': 'left',
            'text_wrap': True
        })

        style_center = workbook.add_format({
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter',
            'align': 'center',
            'text_wrap': True
        })

        styled_currency = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        total = 0
        for rule in data.line_ids:
            if rule.code == 'DILIGENCE':
                total += rule.amount

        sheet.write(row, constants.COL_NO_DILIGENCE, col_idx + 1, style_center)
        # sheet.write(row, constants.COL_PAID_VIA, data.contract_id.hr_responsible_id.name or "", style)
        sheet.write(row, constants.COL_NAME_DILIGENCE, data.employee_id.name or "", style)
        sheet.write_number(row, constants.COL_TOTAL_DILIGENCE, total, styled_currency)

        if (col_idx + 1) % 2 != 0:
            sheet.write(row, constants.COL_SIGN_DILIGENCE1, "{num}. ".format(num=col_idx + 1), style_left)
            sheet.write(row, constants.COL_SIGN_DILIGENCE2, "", style_left)
        else:
            sheet.write(row, constants.COL_SIGN_DILIGENCE2, "{num}. ".format(num=col_idx + 1), style_left)
            sheet.write(row, constants.COL_SIGN_DILIGENCE1, "", style_left)
        row += 1

        return row

    def generate_diligence_sheet(self, workbook, sheet, data, objects):
        bold_center = workbook.add_format({
            'bold': 1,
            'font_size': 12,
            'border_color': 'orange', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        })
        bold_left = workbook.add_format({
            'bold': 1,
            'font_size': 14,
            'border_color': 'orange', 'valign': 'vcenter', 'text_wrap': True
        })
        border_bold_center = workbook.add_format({
            'bold': 1,
            'border': 1,
            'border_color': 'orange', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        })

        styled_currency = workbook.add_format({
            'bold': 1,
            'num_format': '#,##0',
            'border': 1,
            'border_color': 'orange',
            'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bg_color': '#D9D9D9'
        })
        sheet.set_default_row(27.5)
        sheet.set_row(constants.ROW_TABLE_HEAD_DILIGENCE, 46.5)
        sheet.set_row(constants.ROW_MONTH_DILIGENCE + 1, 10.5)

        sheet.set_column(constants.COL_NO_DILIGENCE, constants.COL_NO_DILIGENCE, 5)
        # sheet.set_column(constants.COL_PAID_VIA, constants.COL_PAID_VIA, 9)
        sheet.set_column(constants.COL_NAME_DILIGENCE, constants.COL_NAME_DILIGENCE, 29)
        sheet.set_column(constants.COL_TOTAL_DILIGENCE, constants.COL_TOTAL_DILIGENCE, 16)
        sheet.set_column(constants.COL_SIGN_DILIGENCE1, constants.COL_SIGN_DILIGENCE1, 16)
        sheet.set_column(constants.COL_SIGN_DILIGENCE2, constants.COL_SIGN_DILIGENCE2, 16)

        curr_row = constants.ROW_TABLE_HEAD_OVERTIME + 1

        for o in objects:
            sheet.merge_range('A{row}:C{row}'.format(row=constants.ROW_TITLE_DILIGENCE + 1), 'DAFTAR UANG KERAJINAN',
                              bold_left)
            sheet.merge_range('A{row}:C{row}'.format(row=constants.ROW_COMPANY_NAME_DILIGENCE + 1),
                              o.env.company.display_name or "", bold_left)
            sheet.merge_range('A{row}:B{row}'.format(row=constants.ROW_MONTH_DILIGENCE + 1), 'BULAN', bold_left)

            sheet.merge_range('C{row}:D{row}'.format(row=constants.ROW_MONTH_DILIGENCE + 1),
                              o.date_start.strftime('%b-%y'),
                              bold_center)

            table_head = [
                'NO',
                'Nama',
                'Total U. Kerajinan',
                'Tanda Tangan 1',
                'Tanda Tangan 2',
            ]

            for i, head in enumerate(table_head):
                sheet.write(constants.ROW_TABLE_HEAD_DILIGENCE, i, head, border_bold_center)

            for idx, ch in enumerate(o.slip_ids):
                curr_row = self.print_diligence_batch_children(ch, sheet, curr_row, idx, workbook)

            sheet.merge_range('A{row}:B{row}'.format(row=curr_row+1), 'TOTAL', border_bold_center)
            sheet.merge_range('C{row}:E{row}'.format(row=curr_row+1), '', border_bold_center)
            sheet.write_formula(curr_row, constants.COL_TOTAL_DILIGENCE, '=SUM(C{start}:C{end})'.format(start=constants.ROW_TABLE_HEAD_DILIGENCE+1,end=curr_row),
                                styled_currency)

            sheet.autofilter('A{start}:E{end}'.format(start=constants.ROW_TABLE_HEAD_DILIGENCE + 1, end=curr_row - 1))
            sheet.freeze_panes('A1')
            sheet.freeze_panes('B2')
            sheet.freeze_panes('C3')
            sheet.set_landscape()
            sheet.center_horizontally()
            sheet.center_vertically()
            sheet.set_paper(5)
            sheet.set_margins(top=0, left=0, right=2)
            sheet.print_area(constants.ROW_TITLE_DILIGENCE, constants.COL_NO_DILIGENCE, curr_row,
                             constants.COL_SIGN_DILIGENCE2)


    def print_report_batches_children(self, data, sheet, row, col_idx, workbook):

        styled_currency_green = workbook.add_format({
            'bold': 1,
            'num_format': '#,##0',
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter', 'text_wrap': True, 'bg_color': '#E2EFDA'
        })

        style_center = workbook.add_format({
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter',
            'align': 'center',
            'text_wrap': True
        })

        styled_currency = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        payslip_ids = self.env['hr.payslip'].search(
            [("employee_id", '=', data.employee_id.id),
             ('date_from', '>=', data.date_from),
             ('date_to', '<=', data.date_to),
             ('id', '!=', data.id),
             ('state', '=', 'done')
             ])

        payslip_ids = sorted(payslip_ids, key=lambda payslip: payslip.date_from)

        sheet.write(row, constants.COL_NO_REPORT, col_idx + 1, style_center)
        sheet.write(row, constants.COL_NAMA_REPORT, data.employee_id.name, style_center)

        sheet.write_number(row, constants.COL_WEEK1, 0, styled_currency)
        sheet.write_number(row, constants.COL_WEEK2, 0, styled_currency)
        sheet.write_number(row, constants.COL_WEEK3, 0, styled_currency)
        sheet.write_number(row, constants.COL_WEEK4, 0, styled_currency)
        sheet.write_number(row, constants.COL_WEEK5, 0, styled_currency)
        sheet.write_number(row, constants.COL_UM_AN, 0, styled_currency)

        for i, payslip in enumerate(payslip_ids):
            dif = payslip.date_to - payslip.date_from
            total = 0
            if dif.days <= 8:
                for rule in payslip.line_ids:
                    if rule.code == 'NET':
                        total += rule.amount
                if i == 0:
                    sheet.write_number(row, constants.COL_WEEK1, total, styled_currency)
                elif i == 1:
                    sheet.write_number(row, constants.COL_WEEK2, total, styled_currency)
                elif i == 2:
                    sheet.write_number(row, constants.COL_WEEK3, total, styled_currency)
                elif i == 3:
                    sheet.write_number(row, constants.COL_WEEK4, total, styled_currency)
                elif i == 4:
                    sheet.write_number(row, constants.COL_WEEK5, total, styled_currency)

        sheet.write_formula(row, constants.COL_TOTAL_UM,
                            '=SUM(C{row}:H{row})'.format(row=row + 1), styled_currency_green)

        input_line_ids = data.input_line_ids
        line_ids = data.line_ids
        total_amount = 0
        diligence = 0
        for input in input_line_ids:
            if input.code == 'OVTHOUR' or input.code == 'OT100':
                total_amount += input.amount

        for rule in line_ids:
            if rule.code == 'DILIGENCE':
                diligence += rule.amount

        sheet.write_number(row, constants.COL_LEMBUR, total_amount, styled_currency)
        sheet.write_number(row, constants.COL_KERAJINAN, diligence, styled_currency)
        sheet.write_number(row, constants.COL_INSENTIF, 0, styled_currency)
        sheet.write_number(row, constants.COL_OTHERS, 0, styled_currency)
        sheet.write_formula(row, constants.COL_TOTAL, '=SUM(I{row}:M{row})'.format(row=row + 1),
                            styled_currency_green)

        return row + 1

    def generate_monthly_report(self, workbook, sheet, data, objects):
        bold_center = workbook.add_format({
            'bold': 1,
            'font_size': 12,
            'border_color': 'orange', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        })
        bold_left = workbook.add_format({
            'bold': 1,
            'font_size': 14,
            'border_color': 'orange', 'valign': 'vcenter', 'text_wrap': True
        })
        border_bold_center = workbook.add_format({
            'bold': 1,
            'border': 1,
            'border_color': 'orange', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        })

        styled_currency = workbook.add_format({
            'bold': 1,
            'num_format': '#,##0',
            'border': 1,
            'border_color': 'orange',
            'valign': 'vcenter', 'text_wrap': True, 'bg_color': '#D9D9D9'
        })
        sheet.set_default_row(27.5)
        sheet.set_row(constants.ROW_TABLE_HEAD_OVERTIME, 46.5)
        sheet.set_row(constants.ROW_MONTH + 1, 10.5)

        sheet.set_column(constants.COL_NO_REPORT, constants.COL_NO_REPORT, 5)
        sheet.set_column(constants.COL_NAMA_REPORT, constants.COL_NAMA_REPORT, 29)
        sheet.set_column(constants.COL_WEEK1, constants.COL_WEEK1, 11.5)
        sheet.set_column(constants.COL_WEEK2, constants.COL_WEEK2, 11.5)
        sheet.set_column(constants.COL_WEEK3, constants.COL_WEEK3, 11.5)
        sheet.set_column(constants.COL_WEEK4, constants.COL_WEEK4, 11.5)
        sheet.set_column(constants.COL_WEEK5, constants.COL_WEEK5, 11.5)
        sheet.set_column(constants.COL_UM_AN, constants.COL_UM_AN, 11.5)
        sheet.set_column(constants.COL_TOTAL_UM, constants.COL_TOTAL_UM, 12.4)
        sheet.set_column(constants.COL_LEMBUR, constants.COL_LEMBUR, 12.4)
        sheet.set_column(constants.COL_KERAJINAN, constants.COL_KERAJINAN, 12.4)
        sheet.set_column(constants.COL_INSENTIF, constants.COL_INSENTIF, 12.4)
        sheet.set_column(constants.COL_OTHERS, constants.COL_OTHERS, 12.4)
        sheet.set_column(constants.COL_TOTAL, constants.COL_TOTAL, 12.4)

        curr_row = constants.ROW_TABLE_HEAD_REPORT + 1

        for o in objects:
            sheet.merge_range('A{row}:C{row}'.format(row=constants.ROW_TITLE_REPORT + 1), "REKAP BULANAN", bold_left)
            sheet.merge_range('A{row}:C{row}'.format(row=constants.ROW_COMPANY_NAME_REPORT + 1),
                              o.env.company.display_name or "", bold_left)
            sheet.merge_range('A{row}:B{row}'.format(row=constants.ROW_MONTH_REPORT + 1), 'BULAN', bold_left)

            sheet.merge_range('C{row}:D{row}'.format(row=constants.ROW_MONTH_REPORT + 1),
                              o.date_start.strftime('%b-%y'),
                              bold_center)

            table_head = [
                "No",
                _("Nama"),
                _("UM WK1"),
                _("UM WK2"),
                _("UM WK3"),
                _("UM WK4"),
                _("UM WK5"),
                _("UM + AN"),
                _("TOTAL UM"),
                _("LEMBUR"),
                _("KERAJINAN"),
                _("INSENTIF"),
                _("LAIN-LAIN"),
                _("Total"),
            ]

            for i, head in enumerate(table_head):
                sheet.write(constants.ROW_TABLE_HEAD_REPORT, i, head, border_bold_center)

            for idx, ch in enumerate(o.slip_ids):
                curr_row = self.print_report_batches_children(ch, sheet, curr_row, idx, workbook)

        sheet.merge_range('A{row}:B{row}'.format(row=curr_row + 1), 'Total', border_bold_center)

        # sheet.merge_range("D{row}:F{row}".format(row=curr_row + 1), "", border_bold_center)
        sheet.write_formula(curr_row, constants.COL_WEEK1,
                            '=SUM(C{start}:C{end})'.format(start=constants.ROW_TABLE_HEAD_REPORT + 2, end=curr_row),
                            styled_currency)
        sheet.write_formula(curr_row, constants.COL_WEEK2,
                            '=SUM(D{start}:D{end})'.format(start=constants.ROW_TABLE_HEAD_REPORT + 2, end=curr_row),
                            styled_currency)
        sheet.write_formula(curr_row, constants.COL_WEEK3,
                            '=SUM(E{start}:E{end})'.format(start=constants.ROW_TABLE_HEAD_REPORT + 2, end=curr_row),
                            styled_currency)
        sheet.write_formula(curr_row, constants.COL_WEEK4,
                            '=SUM(F{start}:F{end})'.format(start=constants.ROW_TABLE_HEAD_REPORT + 2, end=curr_row),
                            styled_currency)
        sheet.write_formula(curr_row, constants.COL_WEEK5,
                            '=SUM(G{start}:G{end})'.format(start=constants.ROW_TABLE_HEAD_REPORT + 2, end=curr_row),
                            styled_currency)
        sheet.write_formula(curr_row, constants.COL_UM_AN,
                            '=SUM(H{start}:H{end})'.format(start=constants.ROW_TABLE_HEAD_REPORT + 2, end=curr_row),
                            styled_currency)
        sheet.write_formula(curr_row, constants.COL_TOTAL_UM,
                            '=SUM(I{start}:I{end})'.format(start=constants.ROW_TABLE_HEAD_REPORT + 2, end=curr_row),
                            styled_currency)
        sheet.write_formula(curr_row, constants.COL_LEMBUR,
                            '=SUM(J{start}:J{end})'.format(start=constants.ROW_TABLE_HEAD_REPORT + 2, end=curr_row),
                            styled_currency)
        sheet.write_formula(curr_row, constants.COL_KERAJINAN,
                            '=SUM(K{start}:K{end})'.format(start=constants.ROW_TABLE_HEAD_REPORT + 2, end=curr_row),
                            styled_currency)
        sheet.write_formula(curr_row, constants.COL_INSENTIF,
                            '=SUM(L{start}:L{end})'.format(start=constants.ROW_TABLE_HEAD_REPORT + 2, end=curr_row),
                            styled_currency)
        sheet.write_formula(curr_row, constants.COL_OTHERS,
                            '=SUM(M{start}:M{end})'.format(start=constants.ROW_TABLE_HEAD_REPORT + 2, end=curr_row),
                            styled_currency)
        sheet.write_formula(curr_row, constants.COL_TOTAL,
                            '=SUM(N{start}:N{end})'.format(start=constants.ROW_TABLE_HEAD_REPORT + 2, end=curr_row),
                            styled_currency)

        sheet.autofilter('A{start}:N{end}'.format(start=constants.ROW_TABLE_HEAD_REPORT + 1, end=curr_row - 1))
        sheet.freeze_panes('A1')
        sheet.freeze_panes('B2')
        sheet.freeze_panes('C3')
        sheet.freeze_panes('D4')
        sheet.freeze_panes('E5')
        sheet.set_landscape()
        sheet.center_horizontally()
        sheet.center_vertically()
        sheet.set_paper(5)
        sheet.set_margins(top=0, left=0, right=2)
        sheet.print_area(constants.ROW_TITLE_REPORT, constants.COL_NO_REPORT, curr_row, constants.COL_TOTAL)

    def generate_monthly(self, workbook, data, objects):
        workbook.set_properties(
            {"comments": "Created with Python and XlsxWriter "}
        )

        sheet = workbook.add_worksheet("LEMBUR")
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)

        sheet2 = workbook.add_worksheet("KERAJINAN")
        sheet2.set_landscape()
        sheet2.fit_to_pages(1, 0)

        sheet3 = workbook.add_worksheet("REKAP BULANAN")
        sheet3.set_landscape()
        sheet3.fit_to_pages(1, 0)

        self.generate_overtime_sheet(workbook, sheet, data, objects)
        self.generate_diligence_sheet(workbook, sheet2, data, objects)
        self.generate_monthly_report(workbook, sheet3, data, objects)

    def generate_xlsx_report(self, workbook, data, objects):
        if not objects.is_monthly:
            self.generate_weekly(workbook, data, objects)
        else:
            self.generate_monthly(workbook, data, objects)
