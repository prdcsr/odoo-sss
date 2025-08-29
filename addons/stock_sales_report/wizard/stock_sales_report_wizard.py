from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
from . import cell_constants
import xlsxwriter
import json
from odoo.tools import date_utils
import io
import time
import datetime
from dateutil.rrule import rrule, MONTHLY
from . import cell_constants as constants


class StockCardReportWizard(models.TransientModel):
    _name = "stock.sales.report.wizard"
    start_date = fields.Date(string="Start Date", default=time.strftime('%Y-%m-01'), required=True)
    end_date = fields.Date(string="End Date", default=datetime.datetime.now(), required=True)

    def button_export_stock_sales_report(self):
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
        }

        return self.env.ref('stock_sales_report.action_stock_sales_report_xlsx').report_action(self, data=data)

        # return {
        #     'type': 'ir_actions_xlsx_download',
        #     'data': {'model': 'stock.xlsx.report.wizard',
        #              'options': json.dumps(data, default=date_utils.json_default),
        #              'output_format': 'xlsx',
        #              'report_name': 'Excel Report',
        #              }
        # }


class StockCardXlsxReport(models.AbstractModel):
    _name = 'report.stock_sales_report.stock_sales_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def month_iter(self, start_month, start_year, end_month, end_year):
        start = datetime.datetime(start_year, start_month, 1)
        end = datetime.datetime(end_year, end_month, 1)

        return ((d.month, d.year) for d in rrule(MONTHLY, dtstart=start, until=end))

    def generate_monthly_sales_subheader(self, table_head, table_sub_head, table_subheader_str, start_month, start_year,
                                         end_month, end_year):
        table_head.append("")
        table_head.append(table_subheader_str)
        for m, y in self.month_iter(start_month, start_year, end_month, end_year):
            month_year = datetime.datetime(y, m, 1).strftime("%b/%y")
            table_sub_head.append(month_year)
            table_head.append("")
        table_sub_head.append('Total')
        table_sub_head.append('Rata2 12 bln')

        return table_head, table_sub_head

    def generate_xlsx_report(self, workbook, data, objects):
        sheet = workbook.add_worksheet("Sales & Stock")
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

        start_date = datetime.datetime.strptime(data['start_date'], "%Y-%m-%d")
        end_date = datetime.datetime.strptime(data['end_date'], "%Y-%m-%d")

        start_month = start_date.month
        end_month = end_date.month
        start_year = start_date.year
        end_year = end_date.year

        sheet.set_row(constants.ROW_HEADER, 16.5)
        sheet.set_row(constants.ROW_DATE, 24)
        sheet.set_row(constants.ROW_TABLE_HEADER, 30)
        sheet.set_row(constants.ROW_TABLE_SUB_HEADER, 29.25)

        sheet.set_column(constants.COL_NAMA_BARANG, constants.COL_NAMA_BARANG, 28)
        sheet.set_column(constants.COL_SC, constants.COL_SC, 3)
        sheet.set_column(constants.COL_LAST_PBL, constants.COL_LAST_PBL, 10.15)
        sheet.set_column(constants.COL_LAST_KD_ORDER, constants.COL_LAST_KD_ORDER, 8.30)
        sheet.set_column(constants.COL_LAST_QTY_BL, constants.COL_LAST_QTY_BL, 6.15)
        sheet.set_column(constants.COL_LAST_HRG_BRG, constants.COL_LAST_HRG_BRG, 6.15)
        sheet.set_column(constants.COL_CURRENCY, constants.COL_CURRENCY, 4.5)

        for o in objects:
            table_head = [
                "",
                "",
                "",
                "",
                "",
                "IF SC Y, HG SC*104%",
                "",
                "",
                "STOCK PER",
                "",
                "",
                "",
                "",
                "ON THE WAY",
                "",
                "",
                "Sc Balance",
                "",
                "",
                "Total Stock",
                "PO",
                "",
                "Sales Rata2 / bln",
                "",
                "",
                "Jlh Kebutuhan Stock",
                "",
                "",
                "Jlh yang perlu di order",
                "",
                "",
                "",
            ]
            table_sub_head = [
                "F_KOGRUP + F_NOPART",
                "SC",
                "Last Pbl",
                "Last KD Order",
                "last qty BL/SC",
                "last hrg BL/SC",
                "CURR",
                "",
                # STOCK PER
                "JKT",
                "SBY",
                "MDN",
                "LAIN2",
                "TOTAL",
                # ON THE WAY
                "JKT",
                "SBY",
                "MDN",
                # SC BALANCE
                "JKT",
                "SBY",
                "MDN",
                # TOTAL STOCK
                "",
                # PO
                "JKT",
                "SBY",
                "MDN",
                # SALES RATA2 /BLN
                "JKT",
                "SBY",
                "MDN",
                # JLH KEBUTUHAN STOCK
                "JKT",
                "MDN",
                "SBY",
                # JLH YG PERLU DIORDER
                "JKT",
                "SBY",
                "MDN",
                "",
            ]

            table_head, table_sub_head = self.generate_monthly_sales_subheader(table_head=table_head,
                                                                               table_sub_head=table_sub_head,
                                                                               table_subheader_str='SALES JAKARTA',
                                                                               start_month=start_month,
                                                                               start_year=start_year,
                                                                               end_month=end_month, end_year=end_year)
            table_head, table_sub_head = self.generate_monthly_sales_subheader(table_head=table_head,
                                                                               table_sub_head=table_sub_head,
                                                                               table_subheader_str='SALES SURABAYA',
                                                                               start_month=start_month,
                                                                               start_year=start_year,
                                                                               end_month=end_month, end_year=end_year)
            table_head, table_sub_head = self.generate_monthly_sales_subheader(table_head=table_head,
                                                                               table_sub_head=table_sub_head,
                                                                               table_subheader_str='SALES MEDAN',
                                                                               start_month=start_month,
                                                                               start_year=start_year,
                                                                               end_month=end_month, end_year=end_year)

            # table_head.append("SALES JAKARTA")
            # for m, y in self.month_iter(start_month, start_year, end_month, end_year):
            #     month_year = datetime.datetime(y, m, 1).strftime("%b/%y")
            #     table_sub_head.append(month_year)
            #     table_head.append("")
            # table_sub_head.append('Total')
            # table_sub_head.append('Rata2 12 bln')

            table_head.append('')
            table_head.append('last 12 months Sales Rata2 / bln')
            table_head.append('')
            table_head.append('')
            table_head.append('')
            table_sub_head.append('JKT')
            table_sub_head.append('SBY')
            table_sub_head.append('MDN')
            table_sub_head.append('TOTAL')

            table_head.append('')
            table_sub_head.append('')
            table_head.append('')
            table_sub_head.append('')

            table_head.append('Stock On Hand')
            table_head.append('On the Way')
            table_head.append('SC Balance')
            table_head.append('Total Stock')


            for i, head in enumerate(table_head):
                sheet.write(constants.ROW_TABLE_HEADER, i, head, border_bold_center)

            for i, head in enumerate(table_sub_head):
                sheet.write(constants.ROW_TABLE_SUB_HEADER, i, head, border_bold_center)
