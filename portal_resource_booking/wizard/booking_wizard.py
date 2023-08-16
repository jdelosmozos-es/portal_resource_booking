from odoo import models, fields, api
from datetime import datetime, timedelta
import json

class BookingWizard(models.TransientModel):
    _name = 'booking.wizard'
    _description = 'Wizard to create bookings in the backend.'
        
    date = fields.Date(required=True)
    space = fields.Many2one(comodel_name='calendar.event.location',required=True)
    space_domain = fields.Char(compute='_compute_space_domain')
    num_persons = fields.Integer(required=True)
    slot = fields.Many2one(comodel_name='booking.resource.agenda.slot',required=True)
    slot_domain = fields.Char(compute='_compute_slot_domain')
    partner = fields.Many2one(comodel_name='res.partner',required=True)
#    comments = fields.Char()
    instructions = fields.Text(compute='_compute_instructions')
    requests = fields.Many2many(comodel_name='booking.request')
    special_request = fields.Char()
    
    @api.depends('slot')
    def _compute_instructions(self):
        for record in self:
            if not record.slot:
                record.instructions = False
            else:
                time = self.env['booking.resource.agenda'].get_tz_date(record.slot.start_datetime,self.env.user.tz).strftime('%H:%M')
                hour = self.env['booking.additional.information']._get_hour(time)
                instruction = record.slot.line_id.instructions.filtered(lambda x:x.hour == hour)
                record.instructions = instruction.text
                
    @api.depends('date')
    def _compute_space_domain(self):
        self.ensure_one()
        if self.date:
            start_date = self.date
            end_date = start_date + timedelta(days=1)
            Line = self.env['booking.resource.agenda.slot']
            calendar_lines = Line.search([('start_datetime', '>=', start_date),
                                           ('end_datetime','<',end_date),
                                                 ('is_open','=',True)])
            self.space_domain = json.dumps([('id','in',calendar_lines.mapped('space').ids)])
        else:
            self.space_domain = json.dumps([])
    
    @api.depends('date','space','num_persons')   
    def _compute_slot_domain(self):
        self.ensure_one()
        if self.date and self.space and self.num_persons != 0:
            Appointment = self.env['booking.resource.agenda']
            date = Appointment.get_tz_date(datetime(self.date.year, self.date.month, self.date.day), self.env.context['tz'])
            slots = Appointment.get_time_slots(date.strftime("%d-%m-%Y"), self.num_persons, self.space.id)
            self.slot_domain = json.dumps([('id','in',slots.ids)])
        else:
            self.slot_domain = json.dumps([])
    
    def action_book(self):
        line = self.slot
        start_date = line.start_datetime
        calendar_id = line.line_id
        if calendar_id.event_duration_minutes:
            stop_date = start_date + timedelta(minutes=int(calendar_id.event_duration_minutes))
        else:
            stop_date = calendar_id.get_last_time_in_date(start_date.date())
        management_user = self.env.ref('portal_resource_booking.appointment_manager_user').sudo()
        domain = [('line_id', '=', calendar_id.id), ('start_datetime', '>=', fields.Datetime.to_string(start_date)), ('start_datetime', '<', fields.Datetime.to_string(stop_date))]
        lines = self.env['booking.resource.agenda.slot'].sudo().search(domain)
        event = {
            'name': '%s %spax %s %s' % (self.partner.name.split(" ")[0],self.num_persons,self.space.name,'**' if (self.requests or self.special_request) else ''),
            'partner_ids': [(6, 0, [self.partner.id,management_user.partner_id.id])],
#            'duration': duration,
            'start': fields.Datetime.to_string(start_date),
            'stop': fields.Datetime.to_string(stop_date),
            'alarm_ids': [(6, 0, calendar_id.alarm_ids.ids)],
            'resource': self.space.id,
#            'description': self.comments,
            'num_persons': self.num_persons,
            'location': self.space.name,
            'event_location_id': self.space.id,
            'instructions': self.instructions,
            'is_from_reservation_system': True,
            'slots': lines.ids,
            'requests': self.requests,
            'special_request': self.special_request,
        }
        user = self.env.ref('portal_resource_booking.appointment_system_user').sudo()
        self.env['calendar.event'].sudo().with_user(user).create(event)
        for line in lines:
            new_occupancy = line.occupancy + self.num_persons
            line.occupancy = new_occupancy
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',  }