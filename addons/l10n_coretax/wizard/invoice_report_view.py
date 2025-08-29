import base64
import datetime
from xml.dom import minidom

from odoo import api, fields, models


class PosDetails(models.TransientModel):
    _name = 'invoice.details.xml.wizard'
    _description = 'Point of Sale Details Report'

    attachment_id = fields.Many2one('ir.attachment', copy=False)
    start_date = fields.Date(required=True, default=fields.Date.context_today)
    end_date = fields.Date(required=True, default=fields.Date.context_today)
    operating_unit_id = fields.Many2one(
        comodel_name="operating.unit",
        string="Operating Unit",
        required=True,
    )

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            self.end_date = self.start_date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date and self.end_date < self.start_date:
            self.start_date = self.end_date

    def download_xml(self):
        action = {
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=ir.attachment&id=" + str(
                self.attachment_id.id) + "&filename_field=name&field=datas&download=true&name=" + self.attachment_id.name,
            'target': 'self'
        }
        return action

    def _generate_retail_invoice(self, line_dict, root):
        retailInvoice = root.createElement('RetailInvoice')

        trxCode = root.createElement('TrxCode')
        trxCode.appendChild(root.createTextNode(line_dict['trx_code']))

        buyerName = root.createElement('BuyerName')
        buyerName.appendChild(root.createTextNode('Cash'))

        buyerIdOpt = root.createElement('BuyerIdOpt')
        buyerIdOpt.appendChild(root.createTextNode("NIK"))

        buyerIdNumber = root.createElement('BuyerIdNumber')
        # buyerIdNumber.appendChild(root.createTextNode("9990000000999000"))
        buyerIdNumber.appendChild(root.createTextNode("0000000000000000"))

        goodServiceOpt = root.createElement('GoodServiceOpt')
        goodServiceOpt.appendChild(root.createTextNode(str(line_dict['good_service_opt'])))

        serialNo = root.createElement('SerialNo')
        serialNo.appendChild(root.createTextNode(line_dict['serial_no']))

        transactionDate = root.createElement('TransactionDate')
        transactionDate.appendChild(root.createTextNode(line_dict['transaction_date']))

        taxBaseSellingPrice = root.createElement('TaxBaseSellingPrice')
        taxBaseSellingPrice.appendChild(root.createTextNode(str(line_dict['tax_base_selling_price'])))

        otherTaxBaseSellingPrice = root.createElement('OtherTaxBaseSellingPrice')
        otherTaxBaseSellingPrice.appendChild(root.createTextNode(str(line_dict['other_tax_base_selling_price'])))

        vat = root.createElement('VAT')
        vat.appendChild(root.createTextNode(str(line_dict['vat'])))

        stlg = root.createElement('STLG')
        stlg.appendChild(root.createTextNode(str(0)))
        info = root.createElement('Info')
        info.appendChild(root.createTextNode(line_dict['info']))

        retailInvoice.appendChild(trxCode)
        retailInvoice.appendChild(buyerName)
        retailInvoice.appendChild(buyerIdOpt)
        retailInvoice.appendChild(buyerIdNumber)
        retailInvoice.appendChild(goodServiceOpt)
        retailInvoice.appendChild(serialNo)
        retailInvoice.appendChild(transactionDate)
        retailInvoice.appendChild(taxBaseSellingPrice)
        retailInvoice.appendChild(otherTaxBaseSellingPrice)
        retailInvoice.appendChild(vat)
        retailInvoice.appendChild(stlg)
        retailInvoice.appendChild(info)

        return retailInvoice

    def _generate_report_xml(self):

        root = minidom.Document()
        xml = root.createElement('RetailInvoiceBulk')
        xml.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        xml.setAttribute("xsi:noNamespaceSchemaLocation", "schema.xsd")
        root.appendChild(xml)

        company_vat = self.env.user.company_id.vat16
        tin = root.createElement('TIN')
        tin.appendChild(root.createTextNode(str(company_vat)))
        xml.appendChild(tin)

        tax_period_month = self.end_date.month
        month = root.createElement('TaxPeriodMonth')
        month.appendChild(root.createTextNode(str(tax_period_month)))
        xml.appendChild(month)

        tax_period_year = self.end_date.year
        year = root.createElement('TaxPeriodYear')
        year.appendChild(root.createTextNode(str(tax_period_year)))
        xml.appendChild(year)

        listOfRetailInvoice = root.createElement('ListOfRetailInvoice')

        date_start = self.start_date.strftime('%Y-%m-%d %H:%M:%S')
        date_end = datetime.datetime(self.end_date.year, self.end_date.month, self.end_date.day, 23, 59, 59).strftime('%Y-%m-%d %H:%M:%S')
        query = """
            SELECT 
              aml.product_id,
              SUM(aml.price_subtotal) AS tax_base,
              SUM(aml.price_subtotal) * 11/12 AS other_tax_base,
              SUM(aml.price_total) - SUM(aml.price_subtotal) AS vat
            FROM account_move_line aml
            JOIN account_move am on aml.move_id = am.id
            JOIN res_partner rp on am.partner_id = rp.id
            WHERE am.date >= %s AND am.date <= %s AND am.operating_unit_id = %s AND am.type = 'out_invoice' AND (rp.name like 'CASH' OR am.name = 'S002502081') AND aml.product_id is not null
            GROUP BY aml.product_id
        """
        self.env.cr.execute(query, (date_start, date_end, self.operating_unit_id.id))
        order_lines = self.env.cr.dictfetchall()

        tax_sum_query = """
            
            SELECT 
                SUM(amount_tax_signed) 
            FROM account_move am
            JOIN res_partner rp on am.partner_id = rp.id
            WHERE am.date >= %s AND am.date <= %s AND am.operating_unit_id = %s AND am.type = 'out_invoice' AND (rp.name like 'CASH' OR am.name = 'S002502081')
            
        """
        self.env.cr.execute(tax_sum_query, (date_start, date_end, self.operating_unit_id.id))
        tax_data = self.env.cr.dictfetchall()[0]

        refund_tax_base = 0
        tax_base_total = 0

        temp_tax_base_total = 0
        temp_other_tax_base_total = 0
        temp_vat_total = 0
        for order_line in order_lines:
            temp_tax_base_total += order_line['tax_base']
            temp_other_tax_base_total += order_line['other_tax_base']
            temp_vat_total += order_line['vat']

            if order_line['tax_base'] < 0:
                refund_tax_base += abs(order_line['tax_base'])
            else:
                tax_base_total += order_line['tax_base']

        if tax_data['sum'] is not None or tax_data['sum'] != 0:
            temp_vat_total = tax_data['sum']

        disc_percent = 0
        if refund_tax_base > 0 and tax_base_total > 0:
            disc_percent = abs(refund_tax_base / tax_base_total)
        lines = []
        tax_base_total = 0
        other_tax_base_total = 0
        vat_total = 0
        for order_line in order_lines:
            product_id = self.env['product.product'].search([('id', '=', order_line['product_id'])])

            if order_line['tax_base'] > 0:
                tax_base_disc = round(order_line['tax_base']) * disc_percent
                other_tax_base_disc = round(order_line['other_tax_base']) * disc_percent
                vat_disc = round(order_line['vat']) * disc_percent
                line_dict = {
                    'trx_code': 'Normal',
                    'good_service_opt': 'B' if product_id.type == 'service' else 'A',
                    'serial_no': str(product_id.hs_code_id.local_code[:4]) + "00" if product_id.hs_code_id else "000000",
                    # 'serial_no': order_line['name'],
                    'transaction_date': str(self.end_date.strftime('%Y-%m-%d')),
                    'tax_base_selling_price': round(order_line['tax_base'] - tax_base_disc),
                    'other_tax_base_selling_price': round(order_line['other_tax_base'] - other_tax_base_disc),
                    'vat': round(order_line['vat'] - vat_disc),
                    'info': 'ok',
                }

                tax_base_total += round(order_line['tax_base'] - tax_base_disc)
                other_tax_base_total += round(order_line['other_tax_base'] - other_tax_base_disc)
                vat_total += round(order_line['vat'] - vat_disc)

                lines.append(line_dict)

        length = len(lines)
        base_diff = temp_tax_base_total - tax_base_total
        other_base_diff = temp_other_tax_base_total - other_tax_base_total
        vat_diff = temp_vat_total - vat_total

        lines[length - 1]['tax_base_selling_price'] = round(lines[length - 1]['tax_base_selling_price'] + base_diff)
        lines[length - 1]['other_tax_base_selling_price'] = round(
            lines[length - 1]['other_tax_base_selling_price'] + other_base_diff)
        lines[length - 1]['vat'] = round(lines[length - 1]['vat'] + vat_diff)

        for line in lines:
            retail_invoice = self._generate_retail_invoice(line, root)
            listOfRetailInvoice.appendChild(retail_invoice)

        xml.appendChild(listOfRetailInvoice)

        xml_str = root.toprettyxml(indent="\t")
        return xml_str

    def _generate_report(self):
        # if self.filtered(lambda x: not x.l10n_id_kode_transaksi):
        #     raise UserError(_('Some documents don\'t have a transaction code'))
        # if self.filtered(lambda x: x.type != 'out_invoice'):
        #     raise UserError(_('Some documents are not Customer Invoices'))

        output_head = self._generate_report_xml()
        my_utf8 = output_head.encode("utf-8")
        out = base64.b64encode(my_utf8)

        attachment = self.env['ir.attachment'].create({
            'datas': out,
            'name': 'invoice_detail_%s.xml' % (fields.Datetime.to_string(fields.Datetime.now()).replace(" ", "_")),
            'type': 'binary',
        })

        self.attachment_id = attachment.id
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def download_report_xml(self):
        self._generate_report()
        return self.download_xml()