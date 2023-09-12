import logging

from odoo import models, _

_logger = logging.getLogger(__name__)

class Attendee(models.Model):
    _inherit = 'calendar.attendee'
    
    def do_accept(self):
        res = self.write({'state': 'accepted'})
#        res = super(Attendee, self).do_accept()
        if res:
            for attendee in self:
                event = attendee.event_id
                if event.is_from_reservation_system:
                    event._update_state(attendee,'accepted')
                    if event._is_management(attendee):
                        mail_template = self.env.ref('portal_resource_booking.calendar_template_change_attendee_status', raise_if_not_found=False)
                        (event.attendee_ids - attendee)._send_mail_to_attendees(mail_template, force_send=True)
                    else:
                        message = _('Customer has confirmed the booking.')
                        event.create_activity(self.env.ref('portal_resource_booking.appointment_manager_user'), message)
        return res
                
    def do_tentative(self):
#        res = super(Attendee, self).do_tentative()
        res = self.write({'state': 'tentative'})
        if res:
            for attendee in self:
                event = attendee.event_id
                if event.is_from_reservation_system:
                    event._update_state(attendee,'tentative')
                    if not event._is_management(attendee):
                        message = _('Customer has cancelled the booking.')
                        event.create_activity(self.env.ref('portal_resource_booking.appointment_manager_user'), message)
        return res
    
    def do_decline(self):
#        res = super(Attendee, self).do_decline()
        res = self.write({'state': '1declined'})
        if res:
            for attendee in self:
                event = attendee.event_id
                if event.is_from_reservation_system:
                    event._update_state(attendee,'1declined')
                    if event._is_management(attendee):
                        event.liberate_slots()
                        event.write({'active': False})
                        mail_template = self.env.ref('portal_resource_booking.calendar_template_change_attendee_status', raise_if_not_found=False)
                        (event.attendee_ids - attendee)._send_mail_to_attendees(mail_template, force_send=True)
                    else:
                        message = _('Customer has cancelled the booking.')
                        event.create_activity(self.env.ref('portal_resource_booking.appointment_manager_user'), message)
        return res
    