from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    provinsi_id = fields.Many2one(comodel_name='cdn.provinsi', string='Provinsi')
    kota_id = fields.Many2one(comodel_name='cdn.kota', string='Kota')
    kecamatan_id = fields.Many2one(comodel_name='cdn.kecamatan', string='Kecamatan')
    desa_id = fields.Many2one(comodel_name='cdn.desa', string='Desa/Kelurahan')
    jenis_kelamin = fields.Selection(string='Jenis Kelamin', selection=[('l', 'Laki-laki'), ('p', 'Perempuan'),])
    