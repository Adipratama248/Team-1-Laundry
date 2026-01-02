from odoo import models, fields, api

class Pelanggan(models.Model):
    _name = 'cdn.pelanggan'
    _description = 'Master Customer'
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    no_pelanggan = fields.Char(string='No. Pelanggan', readonly=True)
    
    @api.model
    def create(self, vals):
        vals['no_pelanggan'] = self.env['ir.sequence'].next_by_code('pelanggan')
        return super().create(vals)

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.name = self.name.capitalize()