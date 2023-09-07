from odoo import models, fields, api
import json

class CloseServiceWizard(models.TransientModel):
    _name='booking.close.service.wizard'
    _description = 'Wizard to close services.'
    
    name = fields.Char()
    date = fields.Date()
    services = fields.Many2many('booking.resource.service')
    services_domain = fields.Char(compute='_compute_domain')
    
    @api.depends('date')
    def _compute_domain(self):
        for record in self:
            services = self.env['booking.resource.service'].search([('date','=',record.date),('is_open_online','=',True)])
#                ('start_date','<=',record.date),('end_date','>=',record.date),
#            ]).filtered(lambda x: record.date in {y.date() for y in x.booking_slots.mapped('start_datetime')})
            if services:
                record.services_domain = json.dumps([('id','in',services.ids)])
            else:
                record.services_domain = []

    def action_close_service(self):
        self.services.close_online()
        return {
#            'type': 'ir.actions.close_wizard_refresh_view'
            'type': 'ir.actions.client',
            'tag': 'reload',  
            }