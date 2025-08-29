from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round
from xml.dom import minidom
import base64


class AccountMove(models.Model):
    _inherit = "account.move"

    country_code = fields.Char(related='company_id.country_id.code', string='Country Code')
    l10n_id_tax_number = fields.Char(string="Tax Number", copy=False)
    # l10n_id_replace_invoice_id = fields.Many2one('account.move', string="Replace Invoice",
    #                                              domain="['|', '&', '&', ('state', '=', 'posted'), ('partner_id', '=', partner_id), ('reversal_move_id', '!=', False), ('state', '=', 'cancel')]",
    #                                              copy=False)
    l10n_id_attachment_id = fields.Many2one('ir.attachment', readonly=True, copy=False)
    l10n_id_xml_created = fields.Boolean('XML Created', compute='_compute_xml_created', copy=False)
    l10n_id_kode_transaksi = fields.Selection([
        ('01', '01 Kepada Pihak yang Bukan Pemungut PPN (Customer Biasa)'),
        ('02', '02 Kepada Pemungut Bendaharawan (Dinas Kepemerintahan)'),
        ('03', '03 Kepada Pemungut Selain Bendaharawan (BUMN)'),
        ('04', '04 DPP Nilai Lain (PPN 1%)'),
        ('06', '06 Penyerahan Lainnya (Turis Asing)'),
        ('07', '07 Penyerahan yang PPN-nya Tidak Dipungut (Kawasan Ekonomi Khusus/ Batam)'),
        ('08', '08 Penyerahan yang PPN-nya Dibebaskan (Impor Barang Tertentu)'),
        ('09', '09 Penyerahan Aktiva ( Pasal 16D UU PPN )'),
    ], string='Kode Transaksi', help='Dua digit pertama nomor pajak',
        readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    l10n_id_need_kode_transaksi = fields.Boolean(compute='_compute_need_kode_transaksi')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.l10n_id_kode_transaksi = self.partner_id.l10n_id_kode_transaksi
        return super(AccountMove, self)._onchange_partner_id()

    # @api.onchange('l10n_id_tax_number')
    # def _onchange_l10n_id_tax_number(self):
    #     for record in self:
    #         if record.l10n_id_tax_number and record.type not in self.get_purchase_types():
    #             raise UserError(_("You can only change the number manually for a Vendor Bills and Credit Notes"))

    @api.depends('l10n_id_attachment_id')
    def _compute_xml_created(self):
        for record in self:
            record.l10n_id_xml_created = bool(record.l10n_id_attachment_id)

    @api.depends('partner_id')
    def _compute_need_kode_transaksi(self):
        for move in self:
            # move.l10n_id_need_kode_transaksi = move.partner_id.l10n_id_pkp and not move.l10n_id_tax_number and move.type == 'out_invoice' and move.country_code == 'ID'
            move.l10n_id_need_kode_transaksi = move.partner_id.l10n_id_pkp and move.type == 'out_invoice' and move.country_code == 'ID'

    @api.constrains('l10n_id_kode_transaksi', 'line_ids')
    def _constraint_kode_ppn(self):
        ppn_tag = self.env.ref('l10n_id.ppn_tag')
        for move in self.filtered(lambda m: m.l10n_id_kode_transaksi != '08'):
            if any(ppn_tag.id in line.tag_ids.ids for line in move.line_ids if
                   line.exclude_from_invoice_tab is False and line.display_type is False) and any(
                ppn_tag.id not in line.tag_ids.ids for line in move.line_ids if
                line.exclude_from_invoice_tab is False and line.display_type is False):
                raise UserError(
                    _('Cannot mix VAT subject and Non-VAT subject items in the same invoice with this kode transaksi.'))
        for move in self.filtered(lambda m: m.l10n_id_kode_transaksi == '08'):
            if any(ppn_tag.id in line.tag_ids.ids for line in move.line_ids if line.exclude_from_invoice_tab is False):
                raise UserError('Kode transaksi 08 is only for non VAT subject items.')

    def _generate_coretax_invoice(self):

        dp_product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        root = minidom.Document()
        listOfTaxInvoice = root.createElement('ListOfTaxInvoice')
        xml = root.createElement('TaxInvoiceBulk')
        xml.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        xml.setAttribute("xsi:noNamespaceSchemaLocation", "TaxInvoice.xsd")
        root.appendChild(xml)

        tin = root.createElement('TIN')
        tin.appendChild(root.createTextNode(str(self.company_id.vat16)))
        xml.appendChild(tin)

        for move in self.filtered(lambda m: m.state == 'posted'):

            nik = str(move.partner_id.l10n_id_nik) if not move.partner_id.l10n_id_nik else ''

            if move.l10n_id_replace_invoice_id:
                number_ref = str(move.l10n_id_replace_invoice_id.name) + " replaced by " + str(move.name) + " " + nik
            else:
                number_ref = str(move.name) + " " + nik

            street = ', '.join([x for x in (move.partner_id.street, move.partner_id.street2) if x])

            invoice_npwp = '0000000000000000'
            invoice_nitku = '000000'

            company_npwp = '0000000000000000'
            company_nitku = '000000'

            if move.partner_id.vat16 == False and move.partner_id.l10n_id_nik == False:
                raise ValidationError('Customer {customerName} does not have vat or citizen number'.format(
                    customerName=move.partner_id.name))

            if move.partner_id.vat16 and len(move.partner_id.vat16) == 16:
                invoice_npwp = move.partner_id.vat16
            if invoice_npwp == '000000000000000' and move.partner_id.l10n_id_nik:
                invoice_npwp = move.partner_id.l10n_id_nik
            invoice_npwp = invoice_npwp.replace('.', '').replace('-', '')

            # if '0000000' in invoice_npwp:
            #     raise ValidationError('vat or citizen number for customer {customerName} is not valid'.format(
            #         customerName=move.partner_id.display_name))

            if move.partner_id.nitku_num == False:
                raise ValidationError(
                    'Customer {customerName} does not have NITKU number'.format(customerName=move.partner_id.name))

            if move.partner_id.nitku_num and len(move.partner_id.nitku_num) == 6:
                invoice_nitku = move.partner_id.nitku_num

            if move.company_id.vat16 == False:
                raise ValidationError(
                    'Company {companyName} does not have vat number'.format(companyName=move.company_id.name))

            if move.company_id.vat16 and len(move.company_id.vat16) >= 15:
                company_npwp = move.company_id.vat16

            if move.company_id.nitku_num == False:
                raise ValidationError(
                    'Customer {companyName} does not have NITKU number'.format(companyName=move.company_id.name))

            if move.company_id.nitku_num and len(move.company_id.nitku_num) == 6:
                company_nitku = move.company_id.nitku_num

            taxInvoice = root.createElement('TaxInvoice')

            taxInvoiceDate = root.createElement('TaxInvoiceDate')
            taxInvoiceDate.appendChild(root.createTextNode(move.invoice_date.strftime('%Y-%m-%d')))

            taxInvoiceOpt = root.createElement('TaxInvoiceOpt')
            taxInvoiceOpt.appendChild(root.createTextNode("Normal"))

            trxCode = root.createElement('TrxCode')
            trxCode.appendChild(root.createTextNode(move.l10n_id_kode_transaksi or ""))

            addInfo = root.createElement('AddInfo')
            if move.l10n_id_kode_transaksi == '07' or move.l10n_id_kode_transaksi == '08':
                addInfo.appendChild(
                    root.createTextNode("Diisi dengan kode fasilitas. Hanya diisi jika TrxCode 07 atau 08"))

            customDoc = root.createElement("CustomDoc")
            if (move.l10n_id_kode_transaksi == '07' and ['1', '2', '8', '9', '11', '12', '17', '18', '21', '25',
                                                         '26'] in move.l10n_id_kode_fasilitas) or (
                    move.l10n_id_kode_transaksi == '08' and ['5', '8', '9', '10'] in move.l10n_id_kode_fasilitas):
                customDoc.appendChild(root.createTextNode(''''
                    Hanya diisi jika AddInfo terisi dengan :
                    a. TrxCode 07 dan AddInfo : (1, 2, 8, 9, 11, 12, 17, 18, 21, 25, 26)
                    b. TrxCode 08 dan AddInfo : (5, 8, 9, 10) '''''
                                                          ))
            customDocMonthYear = root.createElement('CustomDocMonthYear')
            month = move.invoice_date.strftime('%m')
            year = move.invoice_date.strftime('%Y')
            customDocMonthYear.appendChild(root.createTextNode("{month}{year}".format(month=month, year=year)))

            refDesc = root.createElement('RefDesc')
            refDesc.appendChild(root.createTextNode(move.ref or move.name))

            facilityStamp = root.createElement('FacilityStamp')
            if move.l10n_id_kode_transaksi == '07' or move.l10n_id_kode_transaksi == '08':
                facilityStamp.appendChild(
                    root.createTextNode("Diisi dengan cap Fasilitas, isian terkait dengan isian AddInfo"))

            sellerIDTKU = root.createElement('SellerIDTKU')
            sellerIdTkuString = company_npwp + company_nitku
            sellerIDTKU.appendChild(root.createTextNode(sellerIdTkuString))

            buyerTin = root.createElement('BuyerTin')
            buyerTin.appendChild(root.createTextNode(invoice_npwp))

            buyerDocument = root.createElement('BuyerDocument')

            if move.partner_id.vat16 and '00000000000' not in move.partner_id.vat16:
                buyerDocument.appendChild(root.createTextNode("TIN"))
            elif move.partner_id.l10n_id_nik:
                buyerDocument.appendChild(root.createTextNode("NIK"))
            else:
                buyerDocument.appendChild(root.createTextNode('Other'))

            buyerCountry = root.createElement('BuyerCountry')
            buyerCountry.appendChild(root.createTextNode(move.partner_id.country_id.coretax_country_code or ""))

            buyerDocumentNumber = root.createElement('BuyerDocumentNumber')

            buyerName = root.createElement('BuyerName')
            buyerName.appendChild(root.createTextNode(
                move.partner_id.name if invoice_npwp == '000000000000000' else move.partner_id.l10n_id_tax_name or move.partner_id.name))

            BuyerAdress = root.createElement('BuyerAdress')
            BuyerAdress.appendChild(root.createTextNode(move.partner_id.contact_address.replace('\n',
                                                                                                '') if invoice_npwp == '000000000000000' else move.partner_id.l10n_id_tax_address or street))

            buyerEmail = root.createElement('BuyerEmail')
            buyerEmail.appendChild(root.createTextNode(move.partner_id.email or ""))

            buyerIDTKU = root.createElement('BuyerIDTKU')
            buyerIDTKU.appendChild(root.createTextNode(invoice_npwp + invoice_nitku))

            listOfGoodService = root.createElement('ListOfGoodService')

            product_line = []
            free_tax_line = discount_total = total_price = 0.0

            for line in move.line_ids.filtered(lambda l: not l.exclude_from_invoice_tab):

                vat_rate = 0
                if len(line.tax_ids) != 0:
                    if '12%' in line.tax_ids[0].name:
                        vat_rate = 12
                    else:
                        vat_rate = line.tax_ids[0].amount

                if line.price_subtotal < 0:
                    if line.product_id.id != int(dp_product_id):
                        for tax in line.tax_ids:
                            free_tax_line += (line.price_subtotal * (tax.amount / 100.0)) * -1.0
                    discount_total += abs(line.price_subtotal)
                elif line.price_subtotal > 0:

                    price_unit = line.price_unit
                    if len(line.tax_ids) != 0 and line.tax_ids[0].price_include:
                        price_unit = line.price_subtotal / line.quantity

                    price = line.price_unit * line.quantity
                    total_price += price
                    line_dict = {
                        'opt': 'B' if line.product_id.type == 'service' else 'A',
                        'product_code': str(line.product_id.hs_code_id.local_code[:4]) + "00" if line.product_id.hs_code_id else "000000",
                        # 'product_code': "000000",
                        'name': line.name or '',
                        # 'akong_code': line.product_id.akong_default_code or '',
                        'unit': line.product_uom_id.coretax_code,
                        'price': price_unit,
                        'qty': line.quantity,
                        'disc': 0,  # Diisi dengan nilai Diskon, maks 2 digit di belakang koma, pembulatan komersial
                        'tax_base': 0,  # Diisi dengan (Price*Qty) - TotalDiscount
                        'other_tax_base': 0,
                        'vat_rate': vat_rate,
                        # 'vat_rate': 12,
                        'vat': 0,
                        'stlg_rate': 0,
                        'stlg': 0,
                        'product_id': line.product_id.id,
                        'rounding_id': move.invoice_cash_rounding_id if move.invoice_cash_rounding_id else False,
                        'tax_id': line.tax_ids[0] if len(line.tax_ids) > 0 else None,
                    }
                    product_line.append(line_dict)

            disc_percentage = discount_total / total_price
            total_disc_temp = 0
            idx = 0
            line_length = len(product_line) - 1
            for line in product_line:
                goodService = root.createElement('GoodService')
                # line_price_total = round(line['qty']) * round(line['price'])
                line_price_total = line['qty'] * line['price']
                line_disc = round(line_price_total * disc_percentage, 2)
                total_disc_temp += line_disc
                # line_disc_tax = round(line_disc * 11/12 * line['vat_rate']/100)

                if idx == line_length and discount_total > total_disc_temp:
                    line_disc += discount_total - total_disc_temp

                line['disc'] = line_disc
                line['tax_base'] = round(line_price_total - line['disc'])

                line['other_tax_base'] = line['tax_base']
                if move.l10n_id_kode_transaksi != "01":
                    if line['tax_id'] and line['tax_id'].invoice_repartition_line_ids[1].factor_percent < 100:
                        line['other_tax_base'] = round(
                            line['tax_id'].invoice_repartition_line_ids[1].factor_percent / 100 * line['tax_base'], 2)
                    else:
                        line['other_tax_base'] = round(11 / 12 * line['tax_base'], 2)

                if line['vat_rate'] == 11:
                    line['vat'] = round(line['vat_rate'] / 100 * line['tax_base'], 2)
                else:
                    line['vat'] = round(line['vat_rate'] / 100 * line['other_tax_base'], 2)
                # line['vat'] = float_round(line['vat_rate'] / 100 * line['other_tax_base'],
                #                           precision_rounding=line['rounding_id'].rounding if line['rounding_id'] else 1,
                #                           rounding_method=line['rounding_id'].rounding_method if line[
                #                               'rounding_id'] else 'HALF-UP')
                line['stlg'] = float_round(line['stlg_rate'] * line['other_tax_base'],
                                           precision_rounding=line['rounding_id'].rounding if line[
                                               'rounding_id'] else 1,
                                           rounding_method=line['rounding_id'].rounding_method if line[
                                               'rounding_id'] else 'HALF-UP')

                opt = root.createElement('Opt')
                opt.appendChild(root.createTextNode(line['opt']))

                code = root.createElement('Code')
                code.appendChild(root.createTextNode(str(line['product_code'])))

                name = root.createElement('Name')
                name.appendChild(root.createTextNode(str(line['name'])))

                # akong_code = root.createElement('AkongCode')
                # akong_code.appendChild(root.createTextNode(str(line['akong_code'])))

                unit = root.createElement('Unit')
                unit.appendChild(root.createTextNode(str(line['unit'])))

                price = root.createElement('Price')
                price.appendChild(root.createTextNode(str(line['price'])))

                qty = root.createElement('Qty')
                qty.appendChild(root.createTextNode(str(round(line['qty']))))

                totalDiscount = root.createElement('TotalDiscount')
                totalDiscount.appendChild(root.createTextNode(str(line['disc'])))

                taxBase = root.createElement('TaxBase')
                taxBase.appendChild(root.createTextNode(str(line['tax_base'])))

                otherTaxBase = root.createElement('OtherTaxBase')
                otherTaxBase.appendChild(root.createTextNode(str(line['other_tax_base'])))

                vatRate = root.createElement('VATRate')
                vatRate.appendChild(root.createTextNode(str(line['vat_rate'])))
                # vatRate.appendChild(root.createTextNode(str(line['vat_rate']).replace(".", ",")))

                vat = root.createElement('VAT')
                vat.appendChild(root.createTextNode(str(line['vat'])))

                stlgRate = root.createElement('STLGRate')
                stlgRate.appendChild(root.createTextNode(str(line['stlg_rate'])))

                stlg = root.createElement('STLG')
                stlg.appendChild(root.createTextNode(str(line['stlg'])))

                goodService.appendChild(opt)
                goodService.appendChild(code)
                goodService.appendChild(name)
                # goodService.appendChild(akong_code)
                goodService.appendChild(unit)
                goodService.appendChild(price)
                goodService.appendChild(qty)
                goodService.appendChild(totalDiscount)
                goodService.appendChild(taxBase)
                goodService.appendChild(otherTaxBase)
                goodService.appendChild(vatRate)
                goodService.appendChild(vat)
                goodService.appendChild(stlgRate)
                goodService.appendChild(stlg)
                listOfGoodService.appendChild(goodService)
                idx += 1

            taxInvoice.appendChild(taxInvoiceDate)
            taxInvoice.appendChild(taxInvoiceOpt)
            taxInvoice.appendChild(trxCode)
            taxInvoice.appendChild(addInfo)
            taxInvoice.appendChild(customDoc)
            taxInvoice.appendChild(customDocMonthYear)
            taxInvoice.appendChild(refDesc)
            taxInvoice.appendChild(facilityStamp)
            taxInvoice.appendChild(sellerIDTKU)
            taxInvoice.appendChild(buyerTin)
            taxInvoice.appendChild(buyerDocument)
            taxInvoice.appendChild(buyerCountry)
            taxInvoice.appendChild(buyerDocumentNumber)
            taxInvoice.appendChild(buyerName)
            taxInvoice.appendChild(BuyerAdress)
            taxInvoice.appendChild(buyerEmail)
            taxInvoice.appendChild(buyerIDTKU)
            taxInvoice.appendChild(listOfGoodService)

            listOfTaxInvoice.appendChild(taxInvoice)
        xml.appendChild(listOfTaxInvoice)

        xml_str = root.toprettyxml(indent="\t")
        return xml_str

    def download_xml(self):
        action = {
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=ir.attachment&id=" + str(
                self.l10n_id_attachment_id.id) + "&filename_field=name&field=datas&download=true&name=" + self.l10n_id_attachment_id.name,
            'target': 'self'
        }
        return action

    def download_coretax_xml(self):
        """Collect the data and execute function _generate_efaktur."""
        for record in self:
            if record.state == 'draft':
                raise ValidationError(_('Could not download Coretax XML in draft state'))

            # if record.partner_id.l10n_id_pkp and not record.l10n_id_tax_number:
            #     raise ValidationError(_('Connect ') + record.name + _(' with Coretax XML to download this report'))

        self._generate_coretax()
        return self.download_xml()

    def _generate_coretax(self):
        # if self.filtered(lambda x: not x.l10n_id_kode_transaksi):
        #     raise UserError(_('Some documents don\'t have a transaction code'))
        # if self.filtered(lambda x: x.type != 'out_invoice'):
        #     raise UserError(_('Some documents are not Customer Invoices'))

        output_head = self._generate_coretax_invoice()
        my_utf8 = output_head.encode("utf-8")
        out = base64.b64encode(my_utf8)

        attachment = self.env['ir.attachment'].create({
            'datas': out,
            'name': 'coretax_%s.xml' % (fields.Datetime.to_string(fields.Datetime.now()).replace(" ", "_")),
            'type': 'binary',
        })

        for record in self:
            record.message_post(attachment_ids=[attachment.id])
        self.l10n_id_attachment_id = attachment.id
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
