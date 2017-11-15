# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    stations = fields.Many2many(
        "vegavizyon.station", string="Gideceği İstasyonlar")


class Station(models.Model):
    _name = "vegavizyon.station"

    name = fields.Char(string="İstasyon Adı", require=True)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    stations = fields.Many2many("vegavizyon.station", string="Gideceği İstasyonlar",
                                compute="compute_stations", store=True)

    @api.one
    @api.depends('product_id')
    def compute_stations(self):
        self.stations = self.product_id.stations


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    total_weight = fields.Char(string="Toplam Ağırlık")

    @api.onchange('product_qty')
    def _onchange_product_qty_weight(self):
        productid = self.product_id
        totalweight = 0
        if productid.weight:
            totalweight = self.product_qty * productid.weight

        self.total_weight = totalweight


class PackOperation(models.Model):
    _inherit = "stock.pack.operation"

    total_weight = fields.Char(
        string="Toplam Ağırlık", compute="compute_weight")

    @api.one
    def compute_weight(self):
        productid = self.product_id
        totalweight = 0

        if productid.weight:
            totalweight = self.product_qty * productid.weight

        self.total_weight = totalweight


class ProductCreator(models.Model):
    _name = "vegavizyon.productcreator"
    _description = "Product Creator Object"

    name = fields.Char(string="Ana Ürün Kodu", required=True)
    main_code_station1 = fields.Integer(string="Ana Kod Al.Kesim", required=True)
    main_code_station2 = fields.Integer(string="Ana Kod CNC", required=True)
    main_code_station3 = fields.Integer(string="Ana Kod Çelik Kesim", required=True)
    main_code_station4 = fields.Integer(string="Ana Kod Kaynak", required=True)
    main_code_station5 = fields.Integer(string="Ana Kod Giyotin", required=True)
    main_code_station6 = fields.Integer(string="Ana Kod Akbant", required=True)
    main_code_station7 = fields.Integer(string="Ana Kod Router", required=True)
    main_code_station8 = fields.Integer(string="Ana Kod Fason", required=True)
    main_code_station9 = fields.Integer(string="Ana Kod Montaj", required=True)
    main_code_route1 = fields.Integer(string="Ana Kod Üretim", required=True)
    main_code_route2 = fields.Integer(string="Ana Kod Satın Al", required=True)
    main_code_route3 = fields.Integer(string="Ana Kod MTO", required=True)
    main_code_internal_referance = fields.Char(string="Ana Kod İç Referans")
    sub_code = fields.Char(string="Alt Ürün Kodu")
    sub_code_quantity = fields.Char("Adet")
    sub_code_station1 = fields.Integer(string="Alt Kod Al.Kesim")
    sub_code_station2 = fields.Integer(string="Alt Kod CNC")
    sub_code_station3 = fields.Integer(string="Alt Kod Çelik Kesim")
    sub_code_station4 = fields.Integer(string="Alt Kod Kaynak")
    sub_code_station5 = fields.Integer(string="Alt Kod Giyotin")
    sub_code_station6 = fields.Integer(string="Alt Kod Akbant")
    sub_code_station7 = fields.Integer(string="Alt Kod Router")
    sub_code_station8 = fields.Integer(string="Alt Kod Fason")
    sub_code_station9 = fields.Integer(string="Alt Kod Montaj")
    sub_code_route1 = fields.Integer(string="Alt Kod Üretim")
    sub_code_route2 = fields.Integer(string="Alt Kod Satın Al")
    sub_code_route3 = fields.Integer(string="Alt Kod MTO")
    sub_code_internal_referance = fields.Char(string="Alt Kod İç Referans")
    mainproduct_created = fields.Boolean("Ana Ürün Oluşturuldu")
    mainproduct_failreason = fields.Text(string="Ana Ürün Oluşturulmama Nedeni")
    subproduct_created = fields.Boolean(string="Alt Ürün Oluşturuldu")
    subproduct_failreason = fields.Boolean(string="Alt Ürün Oluşturulmama Nedeni")
    exception_thrown = fields.Boolean(string="Hata Alındı Mı?")
    exception_message = fields.Text(string="Alınan Hata")

    @api.model
    def create(self, vals):
        try:
            productenv = self.env["product.product"]
            bomenv = self.env["mrp.bom"]
            bomlineenv = self.env["mrp.bom.line"]

            mainproductname = vals["name"]

            # search for products with the same code first
            foundproducts = productenv.search([('name', '=ilike',
                                                mainproductname)])
            # main product is not available
            if len(foundproducts) == 0:

                stations = self.getmainstationslist(vals)
                routes = self.getmainroutelist(vals)
                productvalues = {}
                if len(stations) > 0:
                    productvalues["stations"] = [(6, 0, stations)]
                if len(routes) > 0:
                    productvalues["route_ids"] = [(6, 0, routes)]
                productvalues["name"] = mainproductname
                productvalues["type"] = "product"

                if "main_code_internal_referance" in vals:
                    if vals["main_code_internal_referance"]:
                        int_referance = vals["main_code_internal_referance"]
                        productvalues["default_code"] = int_referance
                # create main product
                createdmainproduct = productenv.create(productvalues)

                vals.update({"mainproduct_created": True})

                # create or find sub product
                if "sub_code" in vals and "sub_code_quantity" in vals:
                    subcode = vals["sub_code"]
                    subquantity = vals["sub_code_quantity"]
                    if subcode and subquantity:
                        if self.subproductavailable(subcode):
                            subproduct = self.getsubproduct(subcode)
                            # create main product BOM
                            mainproductbom = bomenv.create({
                                'product_tmpl_id':
                                createdmainproduct.product_tmpl_id.id,
                                "product_qty":
                                1
                            })

                            # add subcode to main products BOM
                            bomlineenv.create({
                                "product_id": subproduct.id,
                                "product_qty": subquantity,
                                "bom_id": mainproductbom.id
                            })
                        else:
                            subproductvalues = self.getsubproductvalues(vals)
                            if len(subproductvalues) > 0:
                                createdsubproduct = productenv.create(
                                    subproductvalues)
                                vals.update({'subproduct_created': True})

                                # create main product BOM
                                mainproductbom = bomenv.create({
                                    'product_tmpl_id':
                                    createdmainproduct.product_tmpl_id.id,
                                    "product_qty":
                                    1
                                })

                                # add subcode to main products BOM
                                bomlineenv.create({
                                    "product_id":
                                    createdsubproduct.id,
                                    "product_qty":
                                    subquantity,
                                    "bom_id":
                                    mainproductbom.id
                                })
                    else:
                        vals.update({'subproduct_created': False})
                        vals.update({
                            'subproduct_failreason':
                            "Alt ürün adet bilgisi içermiyor."
                        })
                else:
                    vals.update({'subproduct_created': False})
                    vals.update({
                        'subproduct_failreason':
                        "Alt ürün adet bilgisi içermiyor."
                    })

            # main product is available
            elif len(foundproducts) == 1:
                mainproduct = foundproducts[0]
                vals.update({'mainproduct_created': False})
                vals.update({'mainproduct_failreason': 'Ürün zaten mevcut.'})
                bom = None
                if self.mainproducthasbom(mainproduct):
                    bom = self.getmainproductbom(mainproduct)
                # create sub products and update boms
                if "sub_code" in vals and "sub_code_quantity" in vals:
                    subcode = vals["sub_code"]
                    subquantity = vals["sub_code_quantity"]
                    if subcode and subquantity:
                        if self.subproductavailable(subcode):
                            subproduct = self.getsubproduct(subcode)
                            if bom == None:
                                mainproductbom = bomenv.create({
                                    'product_tmpl_id':
                                    mainproduct.product_tmpl_id.id,
                                    "product_qty":
                                    1
                                })

                                # add subcode to main products BOM
                                bomlineenv.create({
                                    "product_id": subproduct.id,
                                    "product_qty": subquantity,
                                    "bom_id": mainproductbom.id
                                })
                            else:
                                lineenvs = bomlineenv.search([('bom_id', '=',
                                                               bom.id)])
                                product_available = False
                                for lineenv in lineenvs:
                                    if lineenv.product_id == subproduct.id:
                                        product_available = True
                                        break
                                if not product_available:
                                    # add subcode to main products BOM
                                    bomlineenv.create({
                                        "product_id":
                                        subproduct.id,
                                        "product_qty":
                                        subquantity,
                                        "bom_id":
                                        bom.id
                                    })
                        else:
                            subproductvalues = self.getsubproductvalues(vals)
                            if len(subproductvalues) > 0:
                                createdsubproduct = productenv.create(
                                    subproductvalues)
                                vals.update({'subproduct_created': True})
                                if bom == None:
                                    mainproductbom = bomenv.create({
                                        'product_tmpl_id':
                                        mainproduct.product_tmpl_id.id,
                                        "product_qty":
                                        1
                                    })

                                    # add subcode to main products BOM
                                    bomlineenv.create({
                                        "product_id":
                                        createdsubproduct.id,
                                        "product_qty":
                                        subquantity,
                                        "bom_id":
                                        mainproductbom.id
                                    })
                                else:
                                    # add subcode to main products BOM
                                    bomlineenv.create({
                                        "product_id":
                                        createdsubproduct.id,
                                        "product_qty":
                                        subquantity,
                                        "bom_id":
                                        bom.id
                                    })
        except Exception as e:
            vals.update({'exception_thrown': True})
            vals.update({'exception_message': str(e)})

        return super(ProductCreator, self).create(vals)

    def getsubproductvalues(self, vals):
        subproductvalues = {}

        name = vals["sub_code"]
        station_list = self.getsubstationlist(vals)
        route_list = self.getsubroutelist(vals)

        subproductvalues["name"] = name
        if len(station_list) > 0:
            subproductvalues["stations"] = [(6, 0, station_list)]
        if len(route_list) > 0:
            subproductvalues["route_ids"] = [(6, 0, route_list)]

        subproductvalues["type"] = "product"

        if "sub_code_internal_referance" in vals:
            if vals["sub_code_internal_referance"]:
                subproductvalues["default_code"] = vals["sub_code_internal_referance"]

        return subproductvalues

    def mainproducthasbom(self, product):
        bomenv = self.env["mrp.bom"]
        boms = bomenv.search([('product_tmpl_id', '=',
                               product.product_tmpl_id.id)])
        return len(boms) > 0

    def getmainproductbom(self, product):
        bomenv = self.env["mrp.bom"]
        boms = bomenv.search([('product_tmpl_id', '=',
                               product.product_tmpl_id.id)])
        return boms[0]

    def subproductavailable(self, productname):
        productenv = self.env["product.product"]
        foundproducts = productenv.search([('name', '=ilike', productname)])
        return len(foundproducts) > 0

    def getsubproduct(self, productname):
        productenv = self.env["product.product"]
        foundproducts = productenv.search([('name', '=ilike', productname)])
        return foundproducts[0]

    def getmainroutelist(self, vals):
        routelist = []
        route1 = vals["main_code_route1"]
        route2 = vals["main_code_route2"]
        route3 = vals["main_code_route3"]

        if route1 == 1:
            routeid = self.getrouteid("Üretim")
            if routeid != 0:
                routelist.append(routeid)
        if route2 == 1:
            routeid = self.getrouteid("Satın")
            if routeid != 0:
                routelist.append(routeid)
        if route3 == 1:
            routeid = self.getrouteid("MTO")
            if routeid != 0:
                routelist.append(routeid)

        return routelist

    def getsubroutelist(self, vals):
        routelist = []
        route1 = vals["sub_code_route1"]
        route2 = vals["sub_code_route2"]
        route3 = vals["sub_code_route3"]

        if route1 == 1:
            routeid = self.getrouteid("Üretim")
            if routeid != 0:
                routelist.append(routeid)
        if route2 == 1:
            routeid = self.getrouteid("Satın")
            if routeid != 0:
                routelist.append(routeid)
        if route3 == 1:
            routeid = self.getrouteid("MTO")
            if routeid != 0:
                routelist.append(routeid)

        return routelist

    def getrouteid(self, routename):
        routes = self.env["stock.location.route"].search([('name', 'ilike',
                                                           routename)])

        routeid = 0

        if len(routes) > 0:
            routeid = routes[0].id

        return routeid

    def getsubstationlist(self, vals):

        stationslist = []
        station1 = vals["sub_code_station1"]
        station2 = vals["sub_code_station2"]
        station3 = vals["sub_code_station3"]
        station4 = vals["sub_code_station4"]
        station5 = vals["sub_code_station5"]
        station6 = vals["sub_code_station6"]
        station7 = vals["sub_code_station7"]
        station8 = vals["sub_code_station8"]
        station9 = vals["sub_code_station9"]

        if station1 == 1:
            stationId = self.getstationId("Al. Kesim")
            if stationId != 0:
                stationslist.append(stationId)
        if station2 == 1:
            stationId = self.getstationId("CNC")
            if stationId != 0:
                stationslist.append(stationId)
        if station3 == 1:
            stationId = self.getstationId("Çelik Kesim")
            if stationId != 0:
                stationslist.append(stationId)
        if station4 == 1:
            stationId = self.getstationId("Kaynak")
            if stationId != 0:
                stationslist.append(stationId)
        if station5 == 1:
            stationId = self.getstationId("Giyotin")
            if stationId != 0:
                stationslist.append(stationId)
        if station6 == 1:
            stationId = self.getstationId("Abkant")
            if stationId != 0:
                stationslist.append(stationId)
        if station7 == 1:
            stationId = self.getstationId("Router")
            if stationId != 0:
                stationslist.append(stationId)
        if station8 == 1:
            stationId = self.getstationId("Fason")
            if stationId != 0:
                stationslist.append(stationId)
        if station9 == 1:
            stationId = self.getstationId("Montaj")
            if stationId != 0:
                stationslist.append(stationId)

        return stationslist

    def getmainstationslist(self, vals):

        stationslist = []
        station1 = vals["main_code_station1"]
        station2 = vals["main_code_station2"]
        station3 = vals["main_code_station3"]
        station4 = vals["main_code_station4"]
        station5 = vals["main_code_station5"]
        station6 = vals["main_code_station6"]
        station7 = vals["main_code_station7"]
        station8 = vals["main_code_station8"]
        station9 = vals["main_code_station9"]

        if station1 == 1:
            stationId = self.getstationId("Al. Kesim")
            if stationId != 0:
                stationslist.append(stationId)
        if station2 == 1:
            stationId = self.getstationId("CNC")
            if stationId != 0:
                stationslist.append(stationId)
        if station3 == 1:
            stationId = self.getstationId("Çelik Kesim")
            if stationId != 0:
                stationslist.append(stationId)
        if station4 == 1:
            stationId = self.getstationId("Kaynak")
            if stationId != 0:
                stationslist.append(stationId)
        if station5 == 1:
            stationId = self.getstationId("Giyotin")
            if stationId != 0:
                stationslist.append(stationId)
        if station6 == 1:
            stationId = self.getstationId("Abkant")
            if stationId != 0:
                stationslist.append(stationId)
        if station7 == 1:
            stationId = self.getstationId("Router")
            if stationId != 0:
                stationslist.append(stationId)
        if station8 == 1:
            stationId = self.getstationId("Fason")
            if stationId != 0:
                stationslist.append(stationId)
        if station9 == 1:
            stationId = self.getstationId("Montaj")
            if stationId != 0:
                stationslist.append(stationId)

        return stationslist

    def getstationId(self, stationname):

        stations = self.env["vegavizyon.station"].search([])

        stationid = 0

        for station in stations:
            if station.name == stationname:
                stationid = station.id
                break

        return stationid
