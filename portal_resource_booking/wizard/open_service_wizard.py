from odoo import models, fields, api
import json

class OpenServiceWizard(models.TransientModel):
    _name='booking.open.service.wizard'
    _description = 'Wizard to close services.'
    
    name = fields.Char()
    date = fields.Date()
    services = fields.Many2many('booking.resource.service')
    services_domain = fields.Char(compute='_compute_domain')
    
    @api.depends('date')
    def _compute_domain(self):
        for record in self:
            services = self.env['booking.resource.service'].search([('date','=',record.date),('is_open_online','=',False)])
#                ('start_date','<=',record.date),('end_date','>=',record.date),
#            ]).filtered(lambda x: record.date in {y.date() for y in x.booking_slots.mapped('start_datetime')})
            if services:
                record.services_domain = json.dumps([('id','in',services.ids)])
            else:
                record.services_domain = []

    def action_open_service(self):
        self.services.open_online()
        return {
#            'type': 'ir.actions.close_wizard_refresh_view'
            'type': 'ir.actions.client',
            'tag': 'reload',  
            }