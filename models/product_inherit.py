from odoo import models, fields, api

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    is_laundry_service = fields.Boolean(string="Layanan Laundry", default=False, help="Tandai jika produk ini adalah layanan laundry")
    estimated_hours = fields.Float(string="Estimasi Waktu (Jam)", help="Estimasi waktu pengerjaan layanan dalam jam")
    laundry_service_type = fields.Selection([
        ('cks', 'Cuci Kering Setrika'),
        ('ck', 'Cuci Kering'),
        ('ironing', 'Setrika'),
        ('carpet', 'Cuci Karpet'),
    ], string="Jenis Layanan", help="Kategori layanan laundry")
    category_service = fields.Selection([('reguler', 'Reguler'), ('express', 'Express')], string="Kategori Layanan", default='reguler')

    @api.onchange('is_laundry_service')
    def _onchange_is_laundry_service(self):
        if not self.is_laundry_service:
            self.laundry_service_type = False
            self.category_service = 'reguler'

    @api.model
    def create(self, vals):
        if vals.get('is_laundry_service'):
            vals['type'] = 'service'
        return super(ProductTemplateInherit, self).create(vals)
