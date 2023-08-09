from odoo import models, fields

class BookingResourceAgenda(models.Model):
    _name = 'booking.resource.agenda'
    _description = 'Agenda of resource bookings. Define possible time slots to book'

    name = fields.Char(required=True)
    space = fields.Many2one(comodel_name='calendar.event.location', required=True)
    capacity = fields.Integer(related='space.capacity')
    minutes_slot = fields.Char("Slot in mins.", help='Period between bookable hours')
    dayoff_start = fields.Float("Day-off start")
    dayoff_end = fields.Float("Day-off end")
    start_date = fields.Date(string='Start Date', required=True, default=fields.Datetime.now)
    end_date = fields.Date(string='End Date', compute='_compute_end_date')
    start_time = fields.Float("Start Time", required=True)
    end_time = fields.Float("End TIme", required=True) #TODO: Poner por defecto tres horas después de la inicial
    duration = fields.Integer('Duration in days', required=True)
    booking_slots = fields.One2many(comodel_name='booking.resource.agenda.slot', inverse_name='agenda', string='Booking lines')
    holiday_lines = fields.One2many('booking.holiday', 'jt_calendar_id', 'Holidays')
    reminders = fields.Many2many(comodel_name='calendar.alarm',
                                relation='booking_reminder_calendar_event_rel',
                                string='Reminders', ondelete="restrict")
    weekoffs = fields.Many2many("booking.weekoff", string="Weekoff Days")
    event_duration_minutes = fields.Integer(compute='_compute_event_duration')
    event_duration = fields.Char('Event duration (minutes)', help='If not set the duration is all available')
    event_times = fields.Char(compute='_compute_times')
    additional_info = fields.One2many(comodel_name='booking.additional.information', inverse_name='agenda')
    additinal_info_is_for_all_times = fields.Boolean()


class BookingResourceAgendaSlot(models.Model):
    _name = 'booking.resource.agenda.slot'
    _description = 'Every time slot from an agenda that is bookable'

    agenda = fields.Many2one('booking.resource.agenda', string='Booking agenda', ondelete='cascade')
    space = fields.Many2one(comodel_name="calendar.event.location")
    start_datetime = fields.Datetime()
    end_datetime = fields.Datetime()
    duration = fields.Float('Duration in mins') #TODO: ¿Ésto se utiliza para algo?
    capacity = fields.Integer(related='space.capacity')
    occupancy = fields.Integer(readonly=True)
    availability = fields.Integer(compute='_compute_availability', store=True)
    is_open = fields.Boolean('Open', default=True)
    is_past = fields.Boolean('Past', compute='_compute_availability')
                            
    _sql_constraints = [
                            ('slot_uniq', 'unique (space,start_datetime)','There cannot be two slots at the same time for the same space.')
                        ]
    