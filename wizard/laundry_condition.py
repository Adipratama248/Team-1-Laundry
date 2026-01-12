from odoo import models, fields, api

class LaundryCondition(models.TransientModel):
    _name = 'laundry.condition'
    _description = 'Wizard Kondisi Barang'

    line_id = fields.Many2one('laundry.order.line', string='Line Referensi')
    
    # Checklist
    is_torn = fields.Boolean(string='Sobek / Bolong')
    torn_note = fields.Char(string='Lokasi Sobek', help="Contoh: Lengan Kiri, Kerah")
    
    is_stain = fields.Boolean(string='Bernoda')
    stain_type = fields.Selection([
        ('tinta', 'Tinta'),
        ('minyak', 'Minyak/Oli'),
        ('darah', 'Darah'),
        ('karat', 'Karat'),
        ('lain', 'Lainnya'),
    ], string='Jenis Noda')
    
    is_faded = fields.Boolean(string='Luntur / Pudar')
    is_button_missing = fields.Boolean(string='Kancing Hilang')
    
    additional_note = fields.Text(string='Catatan Tambahan')

    def action_save_condition(self):
        self.ensure_one()
        notes = []
        
        # Logic penggabungan teks
        if self.is_torn:
            det = f" ({self.torn_note})" if self.torn_note else ""
            notes.append(f"[SOBEK{det}]")
            
        if self.is_stain:
            jenis = dict(self._fields['stain_type'].selection).get(self.stain_type, '')
            notes.append(f"[NODA: {jenis}]")
            
        if self.is_faded:
            notes.append("[LUNTUR]")
            
        if self.is_button_missing:
            notes.append("[KANCING HILANG]")
            
        if self.additional_note:
            notes.append(f"Note: {self.additional_note}")

        # Update ke Line yang memanggil wizard ini
        final_note = " ".join(notes)
        self.line_id.write({'note_in': final_note})
        
        return {'type': 'ir.actions.act_window_close'}