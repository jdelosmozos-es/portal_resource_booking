from odoo import models, fields, api, _
from datetime import timedelta
import json

class BookingWizard(models.TransientModel):
    _name = 'booking.wizard'
    _description = 'Wizard to create bookings in the backend.'
    
    def _partner_domain(self):
        management_user = self.env.ref('portal_resource_booking.appointment_manager_user', raise_if_not_found=False)
        system_user = self.env.ref('portal_resource_booking.appointment_system_user', raise_if_not_found=False).sudo()
        if management_user and not system_user:
            return [management_user.partner_id.id]
        elif not management_user and system_user:
            return [system_user.partner_id.id]
        elif not management_user and not system_user:
            return []
        else:
            non_valid_partner_ids = [management_user.partner_id.id, system_user.partner_id.id]
            return [('id', 'not in', non_valid_partner_ids)]
        
    date = fields.Date(required=True)
    space = fields.Many2one(comodel_name='calendar.event.location',required=True)
    space_domain = fields.Char(compute='_compute_space_domain')
    num_persons = fields.Integer(required=True)
    slot = fields.Many2one(comodel_name='booking.resource.agenda.slot',required=True)
    slot_domain = fields.Char(compute='_compute_slot_domain')
    partner = fields.Many2one(comodel_name='res.partner',required=True, domain=_partner_domain)
    additional_info = fields.Text(compute='_compute_additional_info')
    requests = fields.Many2many(comodel_name='booking.request')
    special_request = fields.Char()
    email = fields.Char()
    today = fields.Date(compute='_compute_today')
    
    @api.depends('slot')
    def _compute_today(self):
        for record in self:
            record.today = fields.Date.today()
    
    @api.onchange('partner')
    def _onchange_partner(self):
        if self.partner and self.partner.email:
            self.email = self.partner.email
    
    @api.depends('slot')
    def _compute_additional_info(self):
        for record in self:
            if record.slot:
                record.additional_info = record.slot.get_additional_info()
            else:
                record.additional_info = False
                
    @api.depends('date')
    def _compute_space_domain(self):
        self.ensure_one()
        if self.date:
            start_date = self.date
            end_date = start_date + timedelta(days=1)
            Slot = self.env['booking.resource.agenda.slot']
            slots = Slot.search([('start_datetime', '>=', start_date),
                                           ('end_datetime','<',end_date)
                                ])
            self.space_domain = json.dumps([('id','in',slots.mapped('space').ids)])
        else:
            self.space_domain = json.dumps([])
    
    @api.depends('date','space','num_persons')   
    def _compute_slot_domain(self):
        for record in self:
            if record.date and record.space and record.num_persons != 0:
                Agenda = self.env['booking.resource.agenda']
                slots = Agenda.get_time_slots(record.date, record.num_persons, record.space.id)
                record.slot_domain = json.dumps([('id','in',slots.ids)])
            else:
                record.slot_domain = json.dumps([])
    
    def action_book(self):
        slot = self.slot
        start_datetime = slot.start_datetime
        agenda = slot.agenda
        if agenda.event_duration_minutes:
            stop_datetime = start_datetime + timedelta(minutes=int(agenda.event_duration_minutes))
        else:
            stop_datetime = agenda.get_last_time_in_date(start_datetime.date())
        management_user = self.env.ref('portal_resource_booking.appointment_manager_user').sudo()
        domain = [('agenda', '=', agenda.id), ('start_datetime', '>=', start_datetime), ('start_datetime', '<=', stop_datetime)]
        slots = self.env['booking.resource.agenda.slot'].sudo().search(domain)
        event_vals = {
            'name': '%s %spax %s %s' % (self.partner.name.split(" ")[0],self.num_persons,self.space.name,'**' if (self.requests or self.special_request) else ''),
            'partner_ids': [(6, 0, [self.partner.id,management_user.partner_id.id])],
            'start': fields.Datetime.to_string(start_datetime),
            'stop': fields.Datetime.to_string(stop_datetime),
            'alarm_ids': [(6, 0, agenda.reminders.ids)],
            'resource': self.space.id,
            'description': _('Manual booking by user internal'),
            'resource_occupancy': self.num_persons,
            'location': self.space.name,
            'event_location_id': self.space.id,
            'additional_information': self.additional_info,
            'is_from_reservation_system': True,
            'slots': slots.ids,
            'requests': self.requests,
            'special_request': self.special_request,
        }
        user = self.env.ref('portal_resource_booking.appointment_system_user').sudo()
        event = self.env['calendar.event'].sudo().with_user(user).create(event_vals)
        for slot in slots:
            new_occupancy = slot.occupancy + self.num_persons
            slot.write({
                            'occupancy': new_occupancy,
                            'calendar_events': [(4,event.id,0)]
                        })
        
        if self.partner and not self.partner.email:
            self.partner.write({'email': self.email})
        
        return {
#            'type': 'ir.actions.close_wizard_refresh_view'
            'type': 'ir.actions.client',
            'tag': 'reload',  
            }
        