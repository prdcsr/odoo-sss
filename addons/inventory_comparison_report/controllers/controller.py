from odoo import http
from odoo.http import request
import io
import xlsxwriter


class InventoryComparisonReportController(http.Controller):

    @http.route('/web/binary/download_inventory_excel_report', type='http', auth="user")
    def download_inventory_excel_report(self, wizard_id, **kwargs):
        wizard = request.env['inventory.comparison.wizard'].browse(int(wizard_id))
        data = wizard._get_inventory_comparison()

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        worksheet = workbook.add_worksheet("Inventory Report")

        bold = workbook.add_format({'bold': True})
        num_format = workbook.add_format({'num_format': '#,##0.00'})

        # Write header
        headers = ['BU','Code','Product','Cost' ,'On Hand', 'Counted','Uom', 'Difference', 'Unit Cost', 'Value Difference']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, bold)

        # Write data rows
        for row, item in enumerate(data, start=1):
            on_hand = item['on_hand']
            counted = item['counted']
            cost = item['cost']
            uom = item['uom']
            difference = counted - on_hand
            value_diff = difference * cost

            worksheet.write(row, 0, item['account'])
            worksheet.write(row, 1, item['code'])
            worksheet.write(row, 2, item['product'])
            worksheet.write(row, 3, cost, num_format)
            worksheet.write(row, 4, on_hand)
            worksheet.write(row, 5, counted)
            worksheet.write(row, 6, uom)
            worksheet.write(row, 7, difference)
            worksheet.write(row, 8, value_diff, num_format)

        workbook.close()
        buffer.seek(0)

        filename = f"Inventory_Comparison {wizard.report_date.strftime('%B')} {wizard.report_date.year}.xlsx"
        return request.make_response(
            buffer.read(),
            headers=[
                ('Content-Disposition', f'attachment; filename={filename}'),
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            ]
        )