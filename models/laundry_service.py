# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LaundryService(models.Model):
    _name = 'cdn.laundry.service'
    _description = 'Laundry Service'

    name = fields.Char(string='Nama Layanan', required=True)
    category = fields.Char(string='Kategori Layanan')
    unit = fields.Selection([('kg', 'Kg'), ('pcs', 'Pcs'),], string='Satuan', required=True)
    price = fields.Float(string='Harga Jual', required=True)
    estimated_time = fields.Char(string='Estimasi Waktu')
    service_type = fields.Selection([('reguler', 'Reguler'),('express', 'Express'),], string='Tipe Layanan', required=True)
    tax_rate = fields.Float(string='Pajak (%)')
    active = fields.Boolean(string='Aktif', default=True)

