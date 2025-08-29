# -*- coding: utf-8 -*-
# from odoo import http


# class HmsRestrictUser(http.Controller):
#     @http.route('/hms_restrict_user/hms_restrict_user/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hms_restrict_user/hms_restrict_user/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hms_restrict_user.listing', {
#             'root': '/hms_restrict_user/hms_restrict_user',
#             'objects': http.request.env['hms_restrict_user.hms_restrict_user'].search([]),
#         })

#     @http.route('/hms_restrict_user/hms_restrict_user/objects/<model("hms_restrict_user.hms_restrict_user"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hms_restrict_user.object', {
#             'object': obj
#         })
