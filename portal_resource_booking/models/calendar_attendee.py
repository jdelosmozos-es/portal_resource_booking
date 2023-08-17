import logging

from odoo import models, _

_logger = logging.getLogger(__name__)

class Attendee(models.Model):
    _inherit = 'calendar.attendee'
    
    def do_accept(self):
        super(Attendee, self).do_accept()
        for attendee in self:
            event = attendee.event_id
            if event.is_from_reservation_system:
                event._update_state(attendee,'accepted')
                if event._is_management(attendee):
                    mail_template = self.env.ref('web_online_appointment_resource.calendar_template_change_attendee_status', raise_if_not_found=False)
                    (event.attendee_ids - attendee)._send_mail_to_attendees(mail_template, force_send=True)
                else:
                    message = _('Customer has confirmed the booking.')
                    event.create_activity(self.env.ref('web_online_appointment_resource.appointment_manager_user'), message)
                    
    def do_tentative(self):
        for attendee in self:
            event = attendee.event_id
            if event.is_from_reservation_system:
                event._update_state(attendee,'tentative')
                if not event._is_management(attendee):
                    message = _('Customer has cancelled the booking.')
                    event.create_activity(self.env.ref('web_online_appointment_resource.appointment_manager_user'), message)
            super(Attendee, attendee).do_tentative()
    
    def do_decline(self):
        super(Attendee, self).do_decline()
        for attendee in self:
            event = attendee.event_id
            if event.is_from_reservation_system:
                event._update_state(attendee,'declined')
                if event._is_management(attendee):
                    event.liberate_slots()
                    event.write({'active': False})
                    mail_template = self.env.ref('web_online_appointment_resource.calendar_template_change_attendee_status', raise_if_not_found=False)
                    (event.attendee_ids - attendee)._send_mail_to_attendees(mail_template, force_send=True)
                else:
                    message = _('Customer has cancelled the booking.')
                    event.create_activity(self.env.ref('web_online_appointment_resource.appointment_manager_user'), message)
