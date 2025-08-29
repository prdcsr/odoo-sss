import base64

from odoo import api, fields, models, _
from xml.dom import minidom

from odoo.exceptions import UserError, ValidationError

"""class AccountAccount(models.Model):
    _inherit = "account.account"
    tax_group_id = fields.Many2one('account.group')
    lka_group_id = fields.Many2one('account.group')"""

class Efaktur(models.Model):
    _inherit = "l10n_id_efaktur.efaktur.range"

    operating_unit_id = fields.Many2one(
        comodel_name="operating.unit",
        string="Operating Unit",
        default=lambda self: (
            self.env["res.users"].operating_unit_default_get(self.env.uid)
        ),
    )
    

class AccountMove(models.Model):
    _inherit = 'account.move'

  
    purchase_id = fields.Many2one('purchase.order', store=True, readonly=True,
        states={'draft': [('readonly', False)]},
        string='Purchase Order',
        help="purchase order.")
        
    def _get_report_base_filename(self):
        if any(not move.is_invoice(include_receipts=True) for move in self):
            raise UserError(_("Only invoices could be printed."))
        return self._get_move_display_name()
    
    def fp_string(self,string):
        if len(string) == 16:
            val=string[:3]+'.' +string[3:6]+'-'+string[6:8]+'.'+string[8:16]
        else: 
            val=string
        return val
    
    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
        
        if not self.type == 'in_invoice':
            return

        if self.purchase_vendor_bill_id.vendor_bill_id:
            self.invoice_vendor_bill_id = self.purchase_vendor_bill_id.vendor_bill_id
            self._onchange_invoice_vendor_bill()
        elif self.purchase_vendor_bill_id.purchase_order_id:
            self.purchase_id = self.purchase_vendor_bill_id.purchase_order_id
        self.purchase_vendor_bill_id = False

        
        if not self.purchase_id:
            return

        # Copy partner.
        self.partner_id = self.purchase_id.partner_id
        self.fiscal_position_id = self.purchase_id.fiscal_position_id
        self.invoice_payment_term_id = self.purchase_id.payment_term_id
        self.currency_id = self.purchase_id.currency_id

        # Copy purchase lines.
        po_lines = self.purchase_id.order_line - self.line_ids.mapped('purchase_line_id')
        new_lines = self.env['account.move.line']
        for line in po_lines.filtered(lambda l: not l.display_type):
            new_line = new_lines.new(line._prepare_account_move_line(self))
            new_line.account_id = new_line._get_computed_account()
            new_line._onchange_price_subtotal()
            new_lines += new_line
        new_lines._onchange_mark_recompute_taxes()

        # Compute invoice_origin.
        origins = set(self.line_ids.mapped('purchase_line_id.order_id.name'))
        self.invoice_origin = ','.join(list(origins))

        # Compute ref.
        refs = set(self.line_ids.mapped('purchase_line_id.order_id.partner_ref'))
        refs = [ref for ref in refs if ref]
        self.ref = ','.join(refs)

        # Compute invoice_payment_ref.
        if len(refs) == 1:
            self.invoice_payment_ref = refs[0]

        self.purchase_id = False
        self._onchange_currency()
        self.invoice_partner_bank_id = self.bank_partner_id.bank_ids and self.bank_partner_id.bank_ids[0]

    def _generate_coretax_invoice(self):

        for move in self.filtered(lambda m: m.state == 'posted'):
            root = minidom.Document()

            nik = str(move.partner_id.l10n_id_nik) if not move.partner_id.vat else ''

            if move.l10n_id_replace_invoice_id:
                number_ref = str(move.l10n_id_replace_invoice_id.name) + " replaced by " + str(move.name) + " " + nik
            else:
                number_ref = str(move.name) + " " + nik

            street = ', '.join([x for x in (move.partner_id.street, move.partner_id.street2) if x])

            invoice_npwp = '000000000000000'
            if move.partner_id.vat and len(move.partner_id.vat) >= 12:
                invoice_npwp = move.partner_id.vat
            elif (not move.partner_id.vat or len(move.partner_id.vat) < 12) and move.partner_id.l10n_id_nik:
                invoice_npwp = move.partner_id.l10n_id_nik
            invoice_npwp = invoice_npwp.replace('.', '').replace('-', '')

            xml = root.createElement('TaxInvoiceBulk')
            xml.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
            xml.setAttribute("xsi:noNamespaceSchemaLocation", "TaxInvoice.xsd")
            root.appendChild(xml)

            tin = root.createElement('TIN')
            tin.appendChild(root.createTextNode(move.company_id.vat))
            xml.appendChild(tin)

            listOfTaxInvoice = root.createElement('ListOfTaxInvoice')
            taxInvoice = root.createElement('TaxInvoice')

            taxInvoiceDate = root.createElement('TaxInvoiceDate')
            taxInvoiceDate.appendChild(root.createTextNode(
                '{0}-{1}-{2}'.format(move.invoice_date.year, move.invoice_date.month, move.invoice_date.day)))

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
            refDesc = root.createElement('RefDesc')

            facilityStamp = root.createElement('FacilityStamp')
            if move.l10n_id_kode_transaksi == '07' or move.l10n_id_kode_transaksi == '08':
                facilityStamp.appendChild(
                    root.createTextNode("Diisi dengan cap Fasilitas, isian terkait dengan isian AddInfo"))

            sellerIDTKU = root.createElement('SellerIDTKU')
            sellerIdTkuString = move.company_id.vat + ""
            sellerIDTKU.appendChild(root.createTextNode(sellerIdTkuString))

            buyerTin = root.createElement('BuyerTin')
            buyerTin.appendChild(root.createTextNode(invoice_npwp))

            buyerDocument = root.createElement('BuyerDocument')
            buyerDocument.appendChild(root.createTextNode("Diisi dengan : TIN, NIK, Passport, Other"))

            buyerCountry = root.createElement('BuyerCountry')
            buyerCountry.appendChild(root.createTextNode(move.partner_id.country_id.code))

            buyerDocumentNumber = root.createElement('BuyerDocumentNumber')

            buyerName = root.createElement('BuyerName')
            buyerName.appendChild(root.createTextNode(
                move.partner_id.name if invoice_npwp == '000000000000000' else move.partner_id.l10n_id_tax_name or move.partner_id.name))

            buyerAddress = root.createElement('BuyerAddress')
            buyerAddress.appendChild(root.createTextNode(move.partner_id.contact_address.replace('\n',
                                                                                                 '') if invoice_npwp == '000000000000000' else move.partner_id.l10n_id_tax_address or street))

            buyerEmail = root.createElement('BuyerEmail')
            buyerEmail.appendChild(root.createTextNode(move.partner_id.email))

            buyerIDTKU = root.createElement('BuyerIDTKU')
            buyerIDTKU.appendChild(root.createTextNode(invoice_npwp))

            listOfGoodService = root.createElement('ListOfGoodService')

            for line in move.invoice_line_ids:
                goodService = root.createElement('GoodService')
                product = line.product_id

                type = 'A'
                if product.type == 'service':
                    type = 'B'
                opt = root.createElement('Opt')
                opt.appendChild(root.createTextNode(type))

                code = root.createElement('Code')
                code.appendChild(root.createTextNode(str(product.default_code)))

                productName = root.createElement('Name')
                productName.appendChild(root.createTextNode(str(product.name)))

                unit = root.createElement('Unit')
                unit.appendChild(root.createTextNode(str(line.product_uom_id.name)))

                price = root.createElement('Price')
                price.appendChild(root.createTextNode(str(line.price_unit)))

                qty = root.createElement('Qty')
                qty.appendChild(root.createTextNode(str(line.quantity)))

                totalDiscount = root.createElement('TotalDiscount')
                totalDiscValue = line.discount / 100 * line.price_subtotal
                totalDiscount.appendChild(root.createTextNode(str(totalDiscValue)))

                taxBase = root.createElement('TaxBase')
                taxBaseValue = line.price_subtotal - totalDiscValue
                taxBase.appendChild(root.createTextNode(str(taxBaseValue)))

                otherTaxBase = root.createElement('OtherTaxBase')
                otherTaxBase.appendChild(root.createTextNode(str(taxBaseValue)))

                goodService.appendChild(opt)
                goodService.appendChild(code)
                goodService.appendChild(productName)
                goodService.appendChild(unit)
                goodService.appendChild(price)
                goodService.appendChild(qty)
                goodService.appendChild(totalDiscount)
                goodService.appendChild(taxBase)
                goodService.appendChild(otherTaxBase)

                vatTotal = 0
                for tax in line.tax_ids:
                    vatRate = root.createElement('VATRate')
                    vatRate.appendChild(root.createTextNode(str(tax.amount)))
                    goodService.appendChild(vatRate)
                    vatTotal += tax.amount / 100 * taxBaseValue

                vat = root.createElement('VAT')
                vat.appendChild(root.createTextNode(str(vatTotal)))

                stlgRate = root.createElement('STLGRate')
                stlg = root.createElement('STLG')

                goodService.appendChild(vat)
                goodService.appendChild(stlgRate)
                goodService.appendChild(stlg)
                listOfGoodService.appendChild(goodService)

            taxInvoice.appendChild(taxInvoiceDate)
            taxInvoice.appendChild(taxInvoiceOpt)
            taxInvoice.appendChild(trxCode)
            taxInvoice.appendChild(addInfo)
            taxInvoice.appendChild(refDesc)
            taxInvoice.appendChild(facilityStamp)
            taxInvoice.appendChild(sellerIDTKU)
            taxInvoice.appendChild(buyerTin)
            taxInvoice.appendChild(buyerDocument)
            taxInvoice.appendChild(buyerCountry)
            taxInvoice.appendChild(buyerDocumentNumber)
            taxInvoice.appendChild(buyerName)
            taxInvoice.appendChild(buyerAddress)
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
        if self.filtered(lambda x: not x.l10n_id_kode_transaksi):
            raise UserError(_('Some documents don\'t have a transaction code'))
        if self.filtered(lambda x: x.type != 'out_invoice'):
            raise UserError(_('Some documents are not Customer Invoices'))

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