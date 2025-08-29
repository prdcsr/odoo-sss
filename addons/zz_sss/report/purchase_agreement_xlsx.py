import base64,math
from io import BytesIO
from odoo import _, models
from . import cell_constants as constants
from .cell_constants import COL_SPECIFICATION


class PurchaseAgreementXlsx(models.AbstractModel):
    _name = "report.zz_sss.purchase_agreement_xlsx"
    _description = "Purchase Agreement XLSX Report"
    _inherit = "report.report_xlsx.abstract"

    def estimate_row_height(self,text, col_width, default_font_char_width=1.1, line_height=15):
        """
        Rough estimate of how many lines text will wrap into given column width.
        default_font_char_width is average pixel width of a character, adjust as needed.
        line_height is the pixel height per line.
        """
        if not text:
            return line_height

        lines = text.split('\n')
        chars_per_line = int(col_width / default_font_char_width)

        total_lines = 0
        for line in lines:
            if not line:
                total_lines += 1
            else:
                total_lines += math.ceil(len(line) / chars_per_line)

        return total_lines * line_height

    def print_table(self, data, sheet, row, col_idx, workbook,o):
        #formats
        currency = o.currency_id
        style = workbook.add_format({
            'border': 1,
            'border_color': 'black',
            'valign': 'vcenter',
            'align': "left",
            'text_wrap': True,
            'font_size':12
        })
        style_center = workbook.add_format({
            'border': 1,
            'border_color': 'black',
            'valign': 'vcenter',
            'align': "center",
            'text_wrap': True,
            'font_size': 12
        })

        currency_style = workbook.add_format({
            'border': 1,
            'border_color': 'black',
            'valign': 'vcenter',
            'text_wrap': True,
            'font_size': 12,
            'num_format': f'{currency.symbol} #,##0.00'
        })
        col_widths = {
            constants.COL_NO: 5,
            constants.COL_NAME: 16,
            constants.COL_SPECIFICATION: 30,
            constants.COL_DESCRIPTION: 22,
            constants.COL_BRAND: 12,
            constants.COL_HSCODE: 12,
            constants.COL_QTY: 13,
            constants.COL_UOM: 6,
            constants.COL_UNIT_PRICE: 12,
            constants.COL_AMOUNT: 15,
        }

        max_height = 15  # minimum height in pixels
        if data.product_id.type == "product":
            seller = data.product_id._select_seller(
                partner_id=o.vendor_id,
                quantity=data.product_qty
            )

            product_code = seller.product_code or data.product_id.default_code or ""
            specification = seller.product_specification or ""
            variant = data.product_description_variants or ""

            if variant:
                if specification != product_code:
                    description = f"{variant} - {specification}"
                else:
                    description = variant
            else:
                description = specification if specification != product_code else ""

            # if o.operating_unit_id.id == 2:
            #     for idx, line in enumerate(o.line_ids):
            #         image_data = line.product_id.image_1920
            #         if image_data:
            #             image_bytes = base64.b64decode(image_data)
            #             image_stream = BytesIO(image_bytes)
            #             sheet.insert_image(row, COL_SPECIFICATION, 'image.png',
            #                                {'image_data': image_stream, 'x_scale': 0.5, 'y_scale': 0.5})
            custom_desc = seller.product_name or ""
            brand = ""
            if o.operating_unit_id.id != 2 and data.product_id.categ_id.parent_id.name == "UNITS":
                brand = data.product_id.brand_id.name or ""

            hs_code = data.product_id.hs_code_id.local_code or ""
            qty = data.product_qty
            uom = data.product_uom_id.name or ""
            unit_price = data.price_unit
            amount = qty * unit_price

            max_height = max(max_height, self.estimate_row_height(description, col_widths[constants.COL_SPECIFICATION]))
            max_height = max(max_height, self.estimate_row_height(custom_desc, col_widths[constants.COL_DESCRIPTION]))

            sheet.write(row,constants.COL_NO,col_idx +1,style)
            sheet.write(row,constants.COL_NAME,product_code,style)
            sheet.write(row, constants.COL_SPECIFICATION, description, style)
            sheet.write(row, constants.COL_DESCRIPTION, custom_desc, style)
            sheet.write(row, constants.COL_BRAND, brand, style)
            sheet.write(row, constants.COL_HSCODE, hs_code, style)
            sheet.write(row, constants.COL_QTY, qty, style_center)
            sheet.write(row, constants.COL_UOM, uom, style)
            sheet.write(row, constants.COL_UNIT_PRICE, unit_price, currency_style)
            sheet.write(row, constants.COL_AMOUNT, amount, currency_style)

            sheet.set_row(row, max_height)

            row +=1
        return row
    def generate_workbook(self, workbook, data, objects):
        sheet = workbook.add_worksheet(_("Purchase Agreement"))
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)

        #formats here
        bold_left_border = workbook.add_format({
            'bold': 1,
            'font_size': 12,
            'border': 1,
            'border_color': 'black',
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True
        })
        currency_style = workbook.add_format({
            'valign': 'vcenter',
            'text_wrap': True,
            'font_size': 12,
            'num_format': f'{objects.currency_id.symbol} #,##0.00'

        })
        small_wrap_format = workbook.add_format({
            'font_size': 12,
            'text_wrap': True,
            'valign': 'top',
            'align': 'left'
        })
        wrap_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'align': 'center',
            'font_size': 12,
        })
        large_wrap_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'align': 'center',
            'font_size': 16,
        })
        wrap_left_center_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'vcenter',
            'font_size': 12,
            'align': 'left'

        })
        bold_large_left = workbook.add_format({
            'bold': 1,
            'font_size': 26,
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True
        })
        bold_center = workbook.add_format({
            'bold': 1,
            'font_size': 12,
            'border':1,
            'border_color': 'black', 'align': 'center', 'valign': 'top', 'text_wrap': True
        })
        bold_large_center_orange = workbook.add_format({
            'bold': True,
            'font_size': 21,
            'align': 'left',
            'valign': 'vcenter',
            'font_color': 'orange',
            'text_wrap': True
        })
        date_format = workbook.add_format({'num_format': 'dd mmmm yyyy','font_size': 12,})
        sheet.set_column(constants.COL_NO, constants.COL_NO, 5)
        sheet.set_column(constants.COL_NAME, constants.COL_NAME, 16)
        sheet.set_column(constants.COL_SPECIFICATION, constants.COL_SPECIFICATION, 30)
        sheet.set_column(constants.COL_DESCRIPTION, constants.COL_DESCRIPTION, 22)
        sheet.set_column(constants.COL_BRAND, constants.COL_BRAND, 12)
        sheet.set_column(constants.COL_HSCODE, constants.COL_HSCODE, 12)
        sheet.set_column(constants.COL_QTY, constants.COL_QTY, 13)
        sheet.set_column(constants.COL_UOM, constants.COL_UOM, 6)
        sheet.set_column(constants.COL_UNIT_PRICE, constants.COL_UNIT_PRICE, 12)
        sheet.set_column(constants.COL_AMOUNT, constants.COL_AMOUNT, 15)

        sheet.set_row(constants.ROW_COMPANY_NAME,110)

        for o in objects:
            company = o.env.company
            vendor = o.vendor_id

            company_data = f"{company.display_name or ''}\n {company.street or ''}\n{company.city or ''} {company.state_id.name or ''} {company.zip or ''} {company.country_id.name or ''} \nTelp. {company.phone or ''}, NPWP: {company.vat16 or ''}"
            vendor_data = f"{vendor._display_address()}\n{vendor.phone or ''}"
            vendor_row_height = self.estimate_row_height(vendor_data, 73)
            sheet.set_row(constants.ROW_VENDOR_NAME,vendor_row_height)
            if company.logo:
                image_data = base64.b64decode(company.logo)
                image_stream = BytesIO(image_data)
                sheet.insert_image('A1', 'logo.png', {'image_data': image_stream,'x_scale': 1.2,'y_scale':1.2})
            sheet.merge_range('C{row}:I{row}'.format(row=constants.ROW_COMPANY_NAME + 1),
                               company_data or "",large_wrap_format)
            sheet.merge_range('A{row}:C{row}'.format(row=constants.ROW_TITLE+1),
                               "Purchase Agreement",bold_large_left)
            sheet.write(constants.ROW_TITLE,constants.COL_AMOUNT,o.ordering_date,date_format)
            sheet.merge_range('A{row}:C{row}'.format(row=constants.ROW_CODE + 1),
                               o.name or "",bold_large_center_orange)
            sheet.merge_range('A{row}:D{row}'.format(row=constants.ROW_VENDOR_NAME + 1),
                               vendor_data or "",small_wrap_format)

            curr_row = constants.ROW_VENDOR_BANKS
            for idx,bank in enumerate(vendor.bank_ids):
                bank_data = f"Bank: {bank.bank_id.name or ''}\nAddress: {bank.bank_id.street or ''}\nAccount Number: {bank.acc_number or ''}\nSwift: {bank.bank_id.bic or ''}"
                bank_row_height = self.estimate_row_height(bank_data,73)
                sheet.set_row(curr_row, bank_row_height)
                sheet.merge_range('A{row}:D{row}'.format(row=curr_row+1),
                                  bank_data,small_wrap_format)
                curr_row = curr_row + 2

            sheet.set_row(curr_row, 46)
            sheet.merge_range('A{row}:B{row}'.format(row=curr_row + 1),
                               f"SC Reference:\n{o.origin or ''}",wrap_format)
            sheet.write(curr_row,constants.COL_SPECIFICATION,f"Shipment Date:\n{o.schedule_date or ''}",wrap_format)
            sheet.write(curr_row, constants.COL_DESCRIPTION,
                                f"Incoterm:\n{o.incoterm_id.code or ''}", wrap_format)
            sheet.merge_range('E{row}:F{row}'.format(row=curr_row + 1),
                              f"Payment Term:\n{o.payment_term_id.name or ''}", wrap_format)
            sheet.write(curr_row,constants.COL_QTY,f"QTY Container:\n{o.qty_container or ''}",wrap_format)
            sheet.merge_range('H{row}:J{row}'.format(row=curr_row + 1),
                               f"Port Of Destination:\n{o.port_of_destination or ''}",wrap_format)
            curr_row+=2
            table_head = [
                "NO",
                "NAME OF PRODUCT",
                "SPECIFICATION",
                "DESCRIPTION OF GOODS ON CUSTOM",
                "BRAND",
                "HS CODE",
                "QTY",
                "UOM",
                "UNIT PRICE",
                "AMOUNT"]
            for i, head in enumerate(table_head):
                sheet.write(curr_row, i, head,bold_left_border)
            total = 0
            curr_row +=1
            table_head_number = curr_row
            for idx, ch in enumerate(o.line_ids):
                curr_row = self.print_table(ch, sheet, curr_row, idx, workbook,o)
                if ch.product_id.type == 'product':
                    total += ch.product_qty * ch.price_unit
            curr_row+=1
            sheet.merge_range('G{row}:I{row}'.format(row=curr_row + 2),
                               "Total ")
            sheet.write_formula(curr_row+1, constants.COL_AMOUNT,
                                '=SUM(J{start}:J{end})'.format(start=table_head_number+1, end=curr_row+1),currency_style)
            curr_row +=2
            amount_in_words = o.currency_id.with_context(lang='en_US').amount_to_text(total)
            sheet.merge_range('A{row}:J{row}'.format(row=curr_row+1),
                               f"Amount: {amount_in_words} ")
            curr_row +=1
            max_height = self.estimate_row_height(f"Note:\n {o.description or ''}",143)
            sheet.set_row(curr_row,max_height)
            sheet.merge_range('A{row}:J{row}'.format(row=curr_row+1),
                               f"Note:\n {o.description or ''}" ,wrap_left_center_format)
            curr_row +=1
            po_names = []
            for purchase in o.purchase_ids:
                if purchase.state != 'cancel':
                    po_names.append(f"{purchase.name} ")
            sheet.merge_range('A{row}:J{row}'.format(row=curr_row+1),
                               f"Purchase Order For Your Reference : {' '.join(po_names)}")
            curr_row +=1
            sheet.set_row(curr_row,82)
            sheet.merge_range('A{row}:D{row}'.format(row=curr_row+1),
                               'Confirmed by Vendor',bold_center)
            sheet.merge_range('E{row}:J{row}'.format(row=curr_row+1),
                               'PT.SAMA SAMA SUKSES',bold_center)
            sheet.set_paper(9)
            sheet.set_portrait()


    def generate_xlsx_report(self, workbook, data, objects):
        self.generate_workbook(workbook,data,objects)
