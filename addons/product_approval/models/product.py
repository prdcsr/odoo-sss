# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from lxml import etree
# from odoo.osv.orm import setup_modifiers
from odoo.addons.base.models.ir_ui_view import transfer_node_to_modifiers, transfer_modifiers_to_node
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError, UserError

class product_template(models.Model):
    _inherit = 'product.template'

    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Sellable'), ('end', 'EOF'), ('refuse', 'Obselete')], string="Status", default='draft', track_visibility='always')
    approved_by = fields.Many2one('res.users', 'By', track_visibility='always', default=lambda self: self.env.user)

    #@api.model
    #def name_search(self, name='', args=None, operator='ilike', limit=100):
    #    if not args:
    #        args = []
     #   args += [['state', '=', 'confirmed']]
     #   res = super(product_template, self).name_search(name, args=args, operator=operator, limit=limit)
     #   return res

    @api.model
    def create(self, vals):
        res = super(product_template, self).create(vals)
        if not self.env.user.has_group('product_approval.group_product_manager'):
            ctx = {}
            domain = []
            if res.company_id:
                domain.append(('company_id', '=', res.company_id.id))
            email_list = [user.email for user in self.env['res.users'].sudo().search(domain) if user.has_group('product_approval.group_product_manager')]
            if email_list:
                ctx['product_manager_email'] = ','.join([email for email in email_list if email])
                ctx['email_from'] = self.env.user.email
                ctx['user_name'] = self.env.user.name
                ctx['product_name'] = res.name

                template = self.env.ref('product_approval.product_approve_mail_template')
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                db = self.env.cr.dbname
                ctx['action_url'] = "{}/web?db={}#id={}&view_type=form&model=product.template".format(base_url, db, res.id)
                template.with_context(ctx).sudo().send_mail(res.id, force_send=True, raise_exception=False)
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(product_template, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        if view_type == "form":
            doc = etree.XML(result['arch'])
            for node in doc.iter(tag="field"):
                if 'readonly' in node.attrib.get("modifiers", ''):
                    attrs = node.attrib.get("attrs", '')
                    if 'readonly' in attrs:
                        attrs_dict = safe_eval(node.get('attrs'))
                        readonly_list = attrs_dict.get('readonly',)
                        if type(readonly_list) == list:
                            readonly_list.insert(0, ('state', '!=', 'draft'))
                            if len(readonly_list) > 1:
                                readonly_list.insert(0, '|')
                        attrs_dict.update({'readonly': readonly_list})
                        node.set('attrs', str(attrs_dict))
                        transfer_node_to_modifiers(
                            node, result['fields'][node.get("name")])
                        transfer_modifiers_to_node(
                            result['fields'][node.get("name")], node)
                        continue
                    else:
                        continue                    
                # field readonly exception even the status is confirmed    
                if node.get("name")=="description_picking" or node.get("name")=="pos_categ_id" or node.get("name")=="list_price":
                    continue

                if node.get("name")=="dimensional_uom_id" or node.get("name")=="product_thick" or node.get("name")=="product_int_dia":
                    continue
                if node.get("name")=="product_ext_dia" or node.get("name")=="product_width" or node.get("name")=="product_height":
                    continue
                if node.get("name")=="product_length" or node.get("name")=="weight" or node.get("name")=="volume":
                    continue                
                if node.get("name")=="image_1920":
                    continue
                node.set('attrs', "{'readonly':[('state','!=','draft')]}")
                transfer_node_to_modifiers(
                    node, result['fields'][node.get("name")])
                transfer_modifiers_to_node(
                    result['fields'][node.get("name")], node)
            result['arch'] = etree.tostring(doc)
        return result

    def product_confirm(self):
        if self.barcode == False :
            raise UserError(_('No Barcode'))

        if self.lst_price < 500 :
            raise UserError(_('Price < 500'))

        if self.default_code == False :
            raise UserError(_('No Internal Reference'))


        self.state = 'confirmed'
        self.approved_by = self.env.user.id

    def product_refuse(self):
        self.state = 'refuse'
        self.approved_by = self.env.user.id

    def product_eof(self):
        self.state = 'end'
        self.approved_by = self.env.user.id

    def reset_to_draft_product(self):
        self.state = 'draft'
        self.approved_by = self.env.user.id


class product_product(models.Model):
    _inherit = 'product.product'

    #@api.model
    #def name_search(self, name='', args=None, operator='ilike', limit=100):
    #    if not args:
    #        args = []
    #        args += [['state', '=', 'confirmed']]
    #    args += [['list_price', '>', 1]]
    #        res = super(product_product, self).name_search(name, args, operator, limit)
    #    return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(product_product, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        if view_type == "form":
            doc = etree.XML(result['arch'])
            for node in doc.iter(tag="field"):
                if 'readonly' in node.attrib.get("modifiers", ''):
                    attrs = node.attrib.get("attrs", '')
                    if 'readonly' in attrs:
                        attrs_dict = safe_eval(node.get('attrs'))
                        readonly_list = attrs_dict.get('readonly',)
                        if type(readonly_list) == list:
                            readonly_list.insert(0, ('state', '!=', 'draft'))
                            if len(readonly_list) > 1:
                                readonly_list.insert(0, '|')
                        attrs_dict.update({'readonly': readonly_list})
                        node.set('attrs', str(attrs_dict))
                        transfer_node_to_modifiers(
                            node, result['fields'][node.get("name")])
                        transfer_modifiers_to_node(
                            result['fields'][node.get("name")], node)
                        continue
                    else:
                        continue

                if node.get("name")=="dimensional_uom_id" or node.get("name")=="product_thick" or node.get("name")=="product_int_dia":
                    continue

                node.set('attrs', "{'readonly':[('state','!=','draft')]}")
                if node.get("name") in result['fields']:
                    transfer_node_to_modifiers(
                        node, result['fields'][node.get("name")])
                    transfer_modifiers_to_node(
                        result['fields'][node.get("name")], node)
            result['arch'] = etree.tostring(doc)
        return result

    def product_confirm(self):

        if self.barcode == False :
            raise UserError(_('No Barcode'))

        #if self.lst_price < 500 :
        #    raise UserError(_('Price < 500'))
        
        
        if self.default_code == False :
            raise UserError(_('No Internal Reference'))

        self.state = 'confirmed'
        self.approved_by = self.env.user.id

    def product_refuse(self):
        self.state = 'refuse'
        self.approved_by = self.env.user.id

    def reset_to_draft_product(self):
        self.state = 'draft'
        self.approved_by = self.env.user.id

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_id = fields.Many2one(
        'product.product', string='Product',
        domain="[('state', 'in', ['confirmed','end']), ('sale_ok', '=', True), '|', ('company_id', '=', False),('company_id', '=', company_id)]", change_default=True, ondelete='restrict', check_company=True)

    @api.constrains('product_id')
    def _check_state_product_id(self):
        sellable_state = ['confirmed','end']
        for  line in self:            
            if  line.product_id and (line.product_id.state  not in sellable_state):
                #bad_products = order.order_line.product_id.filtered(lambda p: p.company_id and p.company_id != order.company_id)
                raise ValidationError((_("There is Product with Status Not Sellable")))

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'      


    @api.constrains('product_id')
    def _check_state_product_id(self):
        sellable_state = ['confirmed','end']
        for  line in self:            
            if  line.product_id and line.product_id.state  != 'confirmed':
                #bad_products = order.order_line.product_id.filtered(lambda p: p.company_id and p.company_id != order.company_id)
                raise ValidationError((_("There is Product with Status Not Sellable")))
            
class StockMove(models.Model):
    _inherit = "stock.move"

    @api.constrains('product_id')
    def _check_state_product_id(self):
        sellable_state = ['confirmed','end']
        for  line in self:            
            if  line.product_id and (line.product_id.state  not in sellable_state):
                #bad_products = order.order_line.product_id.filtered(lambda p: p.company_id and p.company_id != order.company_id)
                raise ValidationError((_("There is Product with Status Not Sellable")))