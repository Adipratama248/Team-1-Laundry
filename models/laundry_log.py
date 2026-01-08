# -*- coding: utf-8 -*-

from odoo import models, fields, api

class LaundryOrder(models.Model):
    _inherit = 'laundry.order' 

    service_summary = fields.Char(string='Ringkasan Layanan', compute='_compute_service_summary', store=True)
    date_start_washing = fields.Datetime(string='Mulai Washing', readonly=True)
    duration_washing = fields.Float(compute='_compute_durations', string='Durasi Washing', store=True)
    date_start_drying = fields.Datetime(string='Mulai Drying', readonly=True)
    duration_drying = fields.Float(compute='_compute_durations', string='Durasi Drying', store=True)
    date_start_ironing = fields.Datetime(string='Mulai Ironing', readonly=True)
    duration_ironing = fields.Float(compute='_compute_durations', string='Durasi Ironing', store=True)
    date_start_qc = fields.Datetime(string='Mulai QC', readonly=True)
    duration_qc = fields.Float(compute='_compute_durations', string='Durasi QC', store=True)
    total_process_duration = fields.Float(compute='_compute_durations', string='Total Durasi', store=True)

    @api.depends('line_laundry_ids', 'category_service')
    def _compute_service_summary(self):
        for rec in self:
            line = rec.line_laundry_ids[:1]
            if line and line.product_id:
                st_label = dict(self.env['product.template'].fields_get(['laundry_service_type'])['laundry_service_type']['selection']).get(line.product_id.laundry_service_type, '')
                cat_label = dict(self._fields['category_service'].selection).get(rec.category_service, rec.category_service)
                rec.service_summary = f"{st_label} ({cat_label})" if st_label else "-"
            else:
                rec.service_summary = "-"

    @api.depends(
        'date_start_washing', 'date_start_drying', 
        'date_start_ironing', 'date_start_qc', 
        'date_finished'
    )
    def _compute_durations(self):
        for rec in self:
            def diff(start, end):
                # Hitung selisih dalam Jam (Float)
                return (end - start).total_seconds() / 3600.0 if start and end else 0.0

            # Logic: Akhir tahap A adalah Awal tahap B (atau C/D jika B dskip)
            
            # 1. Washing
            end_wash = rec.date_start_drying or rec.date_start_ironing or rec.date_start_qc or rec.date_finished
            rec.duration_washing = diff(rec.date_start_washing, end_wash)

            # 2. Drying
            end_dry = rec.date_start_ironing or rec.date_start_qc or rec.date_finished
            rec.duration_drying = diff(rec.date_start_drying, end_dry)

            # 3. Ironing
            end_iron = rec.date_start_qc or rec.date_finished
            rec.duration_ironing = diff(rec.date_start_ironing, end_iron)

            # 4. QC
            rec.duration_qc = diff(rec.date_start_qc, rec.date_finished)
            
            rec.total_process_duration = rec.duration_washing + rec.duration_drying + rec.duration_ironing + rec.duration_qc

    # =================================================================================
    # ACTION INTERCEPT
    # =================================================================================
    def _on_state_change(self, next_state):
        super(LaundryOrder, self)._on_state_change(next_state)
       
        now = fields.Datetime.now()
        vals = {}

        if next_state == 'washing':
            vals = {'date_start_washing': now}
        elif next_state == 'drying':
            vals = {'date_start_drying': now}
        elif next_state == 'ironing':
            vals = {'date_start_ironing': now}
        elif next_state == 'qc':
            vals = {'date_start_qc': now}

        if vals:
            self.write(vals)