from odoo import models, fields, api

class Partner(models.Model):
    _inherit = 'res.partner'
    
    booking_as_customer_count = fields.Integer(compute='_compute_bookings')
    booking_shown_count = fields.Integer(compute='_compute_bookings')
    booking_not_shown_count = fields.Integer(compute='_compute_bookings')
    bookings = fields.Many2many(comodel_name='calendar.event', compute='_compute_bookings')
    bookings_shown = fields.Many2many(comodel_name='calendar.event', compute='_compute_bookings')
    bookings_not_shown = fields.Many2many(comodel_name='calendar.event', compute='_compute_bookings')
    
    @api.depends('name')
    def _compute_bookings(self):
        for record in self:
            attendees = record.env['calendar.attendee'].search([('partner_id','=',record.id)])
            if attendees:
                record.bookings = attendees.mapped('event_id').filtered(
                        lambda x: x.is_from_reservation_system)
                record.bookings_not_shown = record.bookings.filtered(
                        lambda x: x.state == '7customer_not_shown')
                record.bookings_shown = record.bookings.filtered(
                        lambda x: x.state in ['5customer_present_auto', '6customer_present_confirmed'])
                record.booking_as_customer_count = len(record.bookings)
                record.booking_shown_count = len(record.bookings_shown)
                record.booking_not_shown_count = len(record.bookings_not_shown)
            else:
                record.bookings = False
                record.booking_as_customer_count = 0
                record.bookings_not_shown = False
                record.booking_shown_count = 0
                record.bookings_shown = False
                record.booking_not_shown_count = 0
            
    def action_show_bookings(self):
        return self.bookings_action(self.bookings)
    
    def action_show_bookings_shown(self):
        return self.bookings_action(self.bookings_shown)
    
    def action_show_bookings_not_shown(self):
        return self.bookings_action(self.bookings_not_shown)
        
    def bookings_action(self,records):
        action = (
            self.env.ref("calendar.action_calendar_event")
            .with_context(active_id=self.id)
            .read()[0]
        )
        action["domain"] = [("id", "in", records.ids)]
        action.update(
            view_mode="tree,form", view_id=False, views=False,
        )
        return action
    