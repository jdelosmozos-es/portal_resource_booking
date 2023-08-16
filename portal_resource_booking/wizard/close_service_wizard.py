from odoo import models, fields, api
import json

class CloseServiceWizard(models.TransientModel):
    _name='booking.close.service.wizard'
    _description = 'Wizard to close services.'
    
    name = fields.Char()
    date = fields.Date()
    agendas = fields.Many2many('booking.resource.agenda')
    agendas_domain = fields.Char(compute='_compute_domain')
    
    @api.depends('date')
    def _compute_domain(self):
        for record in self:
            agendas = self.env['booking.resource.agenda'].search([
                ('start_date','<=',record.date),('end_date','>=',record.date),
            ]).filtered(lambda x: record.date in {y.date() for y in x.calendar_line_ids.mapped('start_datetime')})
            if agendas:
                record.agendas_domain = json.dumps([('id','in',agendas.ids)])
            else:
                record.agendas_domain = []

    def action_close_service(self):
        lines = self.env['booking.resource.agenda.slot'].search([
                    ('line_id','in',self.calendars.ids),
            ]).filtered(lambda x:  x.start_datetime.date() == self.date)
        lines.is_open = False
        return