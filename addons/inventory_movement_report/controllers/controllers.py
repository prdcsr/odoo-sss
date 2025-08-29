from odoo import http
from odoo.http import request
import io
import xlsxwriter

class InventoryReportController(http.Controller):

    @http.route('/web/binary/download_inventory_excel_report', type='http', auth="user")
    def download_inventory_excel_report(self, wizard_id, **kwargs):
        wizard = request.env['inventory.movement.wizard'].browse(int(wizard_id))
        data = wizard._get_inventory_movements()

        # Create Excel file in memory
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Inventory Report")

        # Write header
        headers = ['Product', 'UoM', 'Closing Stock (Yesterday)', 'Stock In (Today)', 'Stock Out (Today)']
        for col, h in enumerate(headers):
            worksheet.write(0, col, h)

        # Write data
        for row, line in enumerate(data, start=1):
            worksheet.write(row, 0, line['product'].display_name)
            worksheet.write(row, 1, line['product'].uom_id.name or '')
            worksheet.write(row, 2, round(line['closing'], 2))
            worksheet.write(row, 3, round(line['in'], 2))
            worksheet.write(row, 4, round(line['out'], 2))

        workbook.close()
        output.seek(0)

        filename = f"Inventory_Movement_{wizard.report_date}.xlsx"
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Disposition', f'attachment; filename={filename}'),
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            ]
        )