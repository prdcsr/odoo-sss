# -*- coding: utf-8 -*-
# from odoo import http


# class HmsStockAutoValidate(http.Controller):
#     @http.route('/hms_stock_auto_validate/hms_stock_auto_validate/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hms_stock_auto_validate/hms_stock_auto_validate/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hms_stock_auto_validate.listing', {
#             'root': '/hms_stock_auto_validate/hms_stock_auto_validate',
#             'objects': http.request.env['hms_stock_auto_validate.hms_stock_auto_validate'].search([]),
#         })

#     @http.route('/hms_stock_auto_validate/hms_stock_auto_validate/objects/<model("hms_stock_auto_validate.hms_stock_auto_validate"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hms_stock_auto_validate.object', {
#             'object': obj
#         })
