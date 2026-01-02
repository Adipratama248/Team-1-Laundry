# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Layanan(models.Model):
    _name = 'cdn.layanan'
    _description = 'Master Layanan Laundry'

    nama_layanan = fields.Char(string='Nama Layanan', required=True)
    kategori_layanan = fields.Many2one('product.category', string='Kategori Layanan', required=True)
    satuan = fields.Selection([
        ('kg', 'Kg'),
        ('pcs', 'Pcs'),
    ], string='Satuan', required=True)
    harga_jual = fields.Monetary(string='Harga Jual', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    estimasi_hari = fields.Integer(string='Estimasi Waktu (Hari)')
    estimasi_jam = fields.Integer(string='Estimasi Waktu (Jam)')
    tipe_layanan = fields.Selection([
        ('reguler', 'Reguler'),
        ('express', 'Express'),
    ], string='Tipe Layanan', required=True)
    pajak = fields.Float(string='Pajak (%)', help='Persentase pajak')
    active = fields.Boolean(string='Aktif', default=True)