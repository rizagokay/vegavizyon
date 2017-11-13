# -*- coding: utf-8 -*-
from odoo import http

# class Vegavizyon(http.Controller):
#     @http.route('/vegavizyon/vegavizyon/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vegavizyon/vegavizyon/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('vegavizyon.listing', {
#             'root': '/vegavizyon/vegavizyon',
#             'objects': http.request.env['vegavizyon.vegavizyon'].search([]),
#         })

#     @http.route('/vegavizyon/vegavizyon/objects/<model("vegavizyon.vegavizyon"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vegavizyon.object', {
#             'object': obj
#         })