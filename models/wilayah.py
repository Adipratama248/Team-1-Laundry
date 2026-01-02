from odoo import models, fields, api


class Provinsi(models.Model):
    _name = 'cdn.provinsi'
    _description = 'Referensi Provinsi'
    
    name = fields.Char(string="Nama Provinsi", required=True, help="")
    kode = fields.Char(string="Kode", required=True)
    singkatan = fields.Char( string="Singkatan",  help="")
    description = fields.Text( string="Deskripsi",  help="")
    kota_ids = fields.One2many(comodel_name='cdn.kota',  inverse_name='provinsi_id',  string="Kota",  help="")


class Kota(models.Model):
    _name = 'cdn.kota'
    _description = 'Referensi Kota'

    name = fields.Char(required=True, string="Nama Kota",  help="")
    kode = fields.Char(string="Kode", required=True)
    singkatan = fields.Char( string="Singkatan",  help="")
    description = fields.Text( string="Deskripsi",  help="")
    provinsi_id = fields.Many2one(comodel_name='cdn.provinsi',  string="Provinsi",  help="")
    kecamatan_ids = fields.One2many(comodel_name='cdn.kecamatan',  inverse_name='kota_id',  string="Kecamatan",  help="")



class Kecamatan(models.Model):
    _name = 'cdn.kecamatan'
    _description = 'Referensi Data Kecamatan'

    name = fields.Char( required=True, string="Nama Kecamatan",  help="")
    kode = fields.Char(string="Kode")
    description = fields.Text( string="Deskripsi",  help="")
    kota_id = fields.Many2one(comodel_name='cdn.kota',  string="Kota",  help="")
    desa_ids = fields.One2many(comodel_name='cdn.desa',  inverse_name='kecamatan_id',  string="Desa/Kelurahan",  help="")


class Desa(models.Model):
    _name = 'cdn.desa'
    _description = 'Referensi Data Desa/Kelurahan'

    name = fields.Char( required=True, string="Nama Desa/Kelurahan",  help="")
    kode = fields.Char(string="Kode", required=True)
    description = fields.Text( string="Description",  help="")
    kecamatan_id = fields.Many2one(comodel_name='cdn.kecamatan',  string="Kecamatan",  help="")

    
