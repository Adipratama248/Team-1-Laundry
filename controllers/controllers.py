# -*- coding: utf-8 -*-
# from odoo import http


# class Laundry(http.Controller):
#     @http.route('/laundry/laundry', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/laundry/laundry/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('laundry.listing', {
#             'root': '/laundry/laundry',
#             'objects': http.request.env['laundry.laundry'].search([]),
#         })

#     @http.route('/laundry/laundry/objects/<model("laundry.laundry"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('laundry.object', {
#             'object': obj
#         })

