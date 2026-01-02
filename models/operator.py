from odoo import models, fields, api

class Operator(models.Model):
    _name = 'cdn.operator'
    _description = 'Master Operator'
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    
    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.name = self.name.capitalize()