from odoo import models, fields, api

class Pelanggan(models.Model):
    _name = 'cdn.pelanggan'
    _description = 'Master Customer'

    nama_pelanggan = fields.Char(string='Nama Pelanggan', required=True)
    no_hp = fields.Char(string='No HP / WhatsApp')
    alamat = fields.Text(string='Alamat')
    no_pelanggan = fields.Char(string='No. Pelanggan', readonly=True)
    
    @api.model
    def create(self, vals):
        vals['no_pelanggan'] = self.env['ir.sequence'].next_by_code('pelanggan')
        return super().create(vals)