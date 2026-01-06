from odoo import models, fields, api

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    is_laundry_service = fields.Boolean(
        string="Layanan Laundry",
        default=False,
        help="Tandai jika produk ini adalah layanan laundry")

    estimated_hours = fields.Float(
        string="Estimasi Waktu (Jam)",
        help="Estimasi waktu pengerjaan layanan dalam jam")

    service_type = fields.Selection(
        [
            ('cks', 'Cuci Kering Setrika'),
            ('ck', 'Cuci Kering'),
            ('ironing', 'Setrika'),
            ('carpet', 'Cuci Karpet'),
            ('manual', 'Manual')
        ],
        string="Jenis Layanan", help="Kategori layanan laundry")

    category_service = fields.Selection([
        ('reguler', 'Reguler'),
        ('express', 'Express')
    ], string="Kategori Layanan", default='reguler')


    @api.model
    def create(self, vals):
        if vals.get('is_laundry_service'):
            vals['type'] = 'service'
        return super(ProductTemplateInherit, self).create(vals)
