from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import date_utils
from dateutil.relativedelta import relativedelta 
from datetime import timedelta, datetime
from babel.dates import format_date
import logging

_logger = logging.getLogger(__name__)

class BookingResourceAgenda(models.Model):
    _name = 'booking.resource.agenda'
    _description = 'Agenda of resource bookings. Define possible time slots to book.'
    
    DEFAULT_AGENDA_DAY_TIME_LENGTH_HOURS = 3

    name = fields.Char(required=True)
    display_name = fields.Char(compute='_compute_display_name')
    space = fields.Many2one(comodel_name='calendar.event.location', required=True, ondelete='restrict')
    capacity = fields.Integer(related='space.capacity')
    dayoff_start = fields.Float("Day-off start")
    dayoff_end = fields.Float("Day-off end")
    start_date = fields.Date(string='Start Date', required=True, default=fields.Datetime.now)
    end_date = fields.Date(string='End Date', compute='_compute_end_date')
    start_time_float = fields.Float("First bookable hour", required=True)
    minutes_slot = fields.Char("Slot in mins.", help='Period between bookable hours')
    end_time_float = fields.Float("Last bookable hour", required=True) #TODO: Poner por defecto tres horas después de la inicial
    duration = fields.Integer('Duration in days', required=True, default=1)
    booking_slots = fields.One2many(comodel_name='booking.resource.agenda.slot', inverse_name='agenda', string='Booking lines')
    holiday_lines = fields.One2many('booking.holiday', 'agenda', 'Holidays')
    reminders = fields.Many2many(comodel_name='calendar.alarm',
                                relation='booking_reminder_calendar_event_rel',
                                string='Reminders', ondelete="restrict")
    weekoffs = fields.Many2many("booking.weekoff", string="Weekoff Days")
    event_duration_minutes = fields.Integer(compute='_compute_event_duration')
    event_duration = fields.Char('Event duration (minutes)', help='If not set the duration is all available')
    event_times = fields.Char(compute='_compute_times')
    additional_info = fields.One2many(comodel_name='booking.additional.information', inverse_name='agenda')
    additional_info_is_for_all_times = fields.Boolean()
    type = fields.Many2one(comodel_name='booking.resource.agenda.type', required=True)
    hide_slots = fields.Boolean(compute='_compute_hide_slots')

    @api.depends('booking_slots')
    def _compute_hide_slots(self):
        for record in self:
            if record.booking_slots:
                record.hide_slots = False
            else:
                record.hide_slots = True
            
    @api.depends('type','space')
    def _compute_display_name(self):
        for record in self:
            record.display_name = '%s%s%s' % (
                            '[%s] ' % record.space.name if record.space.name else '',
                            '[%s] ' % record.type.name if record.type.name else '',
                            record.name if record.name else ''
                        )
        
    @api.onchange('additional_info_is_for_all_times')
    def _onchange_additional_info_is_for_all_times(self):
        if self.additional_info_is_for_all_times:
            if len(self.additional_info) == 1:
                self.additional_info[0].time_float = False
        else:
            if self.start_time_float == self.end_time_float and len(self.additional_info)==1:
                self.additional_info[0].time_float = self.start_time_float
                
    @api.constrains('additional_info','additional_info_is_for_all_times')
    def _check_additional_info(self):
        for record in self:
            if record.additional_info_is_for_all_times:
                if len(record.additional_info) > 1:
                    raise ValidationError("You cannot define more than one instruction for all times.")
                if record.additional_info[0].time_float != False:
                    raise ValidationError("You cannot define hour if instruction is for all times.")
            else:
                times_float = []
                for additional_info in record.additional_info:
                    additional_info._check_hour()
                    if additional_info.time_float in times_float:
                        raise ValidationError(_('You cannot define two additional informations for the same time'))
                    times_float.append(additional_info.time_float)
                          
    @api.depends('start_time_float','minutes_slot','end_time_float')
    def _compute_times(self):
        for record in self:
            if record.start_time_float and record.end_time_float:
                start_time = datetime.combine(record.start_date,datetime.min.time()) + relativedelta(hours=record.start_time_float)
                if record.start_time_float == record.end_time_float:
                    record.event_times = start_time.strftime('%H:%M')
                else:
                    if record.minutes_slot:
                        end_time = datetime.combine(record.start_date,datetime.min.time()) + relativedelta(hours=record.end_time_float)
                        datetimes = date_utils.date_range(
                                            start_time,
                                            end_time,
                                            step=relativedelta(minutes=int(record.minutes_slot))
                                    )
                        record.event_times = ' - '.join([x.strftime('%H:%M') for x in datetimes])
                    else:
                        record.event_times = ''
            else:
                record.event_times = ''
                
    @api.depends('event_duration')
    def _compute_event_duration(self):
        for record in self:
            record.event_duration_minutes = int(record.event_duration)
            
    @api.depends('start_date','duration')
    def _compute_end_date(self):
        for record in self:
            record.end_date = record.start_date + timedelta(days=(record.duration-1))
            
    @api.onchange('start_time_float')
    def _onchange_starttime(self):
        if not self._origin.end_time_float and not self.end_time_float and self.start_time_float:
            if self.minutes_slot:
                self.end_time_float = self.start_time_float + self.DEFAULT_AGENDA_DAY_TIME_LENGTH_HOURS
            else:
                self.end_time_float = self.start_time_float
        else:
            self._check_times()
            
    @api.onchange('minutes_slot')
    def _onchange_minutes_slot(self):
        if not self.minutes_slot or self.minutes_slot == '' or self.minutes_slot == '0':
            self.end_time_float = self.start_time_float
        else:
            self._onchange_endtime()
                
    @api.onchange('end_time_float')
    def _onchange_endtime(self):
        for record in self:
            self._check_times()
            if record.minutes_slot and record.minutes_slot != '' and record.minutes_slot != '0':
                diff = record.end_time_float*60 - record.start_time_float*60
                if int(record.minutes_slot) != 0 and diff % int(record.minutes_slot) != 0:
                    occurrences = divmod(diff, int(record.minutes_slot))
                    record.end_time_float = (record.start_time_float*60 + (occurrences[0]+1)*int(record.minutes_slot)) /60
                    
    def _check_times(self):
        if self.start_time_float > self.end_time_float:
                raise UserError(_('End time should not be before start time.'))
            
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.update({'booking_slots': False, 'duration': 1})
        self = self.with_context( { 'agenda_copy': True } )
        return super(BookingResourceAgenda, self).copy(default)
    
    @api.model
    def create(self, vals):
        agenda = super(BookingResourceAgenda, self).create(vals)
        if not 'agenda_copy' in self.env.context or not self.env.context.get('agenda_copy'):
            agenda._generate_agenda()
        return agenda
    
    def write(self, values):
        res = super(BookingResourceAgenda, self).write(values)
        fields_list = ['minutes_slot', 'start_date', 'start_time_float', 'end_time_float', 'duration', 'holiday_ids', 'weekoffs']
        if any(key in values for key in fields_list):
            for record in self:
                record.booking_slots.unlink()
                record._generate_agenda()
                for service in record.env['booking.resource.service'].search([('agenda','=',record.id)]):
                    if not service.slots:
                        service.unlink()
        return res
    
    def _generate_agenda(self):
        DateTimeHelper = self.env['booking.datetime.helper']
        Slot = self.env['booking.resource.agenda.slot']
        for agenda in self:
            if agenda.start_date == agenda.end_date:
                days = [datetime.combine(agenda.start_date,datetime.min.time())]
            else:
                days = date_utils.date_range(
                                                datetime.combine(agenda.start_date,datetime.min.time()), 
                                                datetime.combine(agenda.end_date,datetime.min.time()),
                                                step=relativedelta(days=1)
                                            )
            for day in days:
                off_day = False
                for holiday_line in agenda.holiday_lines:
                    if day >= holiday_line.start_date and day <= holiday_line.end_date:
                        off_day = True
                if off_day:
                    continue
                weekoffdays = agenda.weekoffs.mapped('dayofweek')
                if str(day.weekday()) in weekoffdays:
                    continue
                start_datetime = datetime.combine(day.date(),datetime.min.time()) + relativedelta(hours=agenda.start_time_float)
                if agenda.minutes_slot:
                    end_datetime = datetime.combine(day.date(),datetime.min.time()) + relativedelta(hours=agenda.end_time_float)
                    datetimes = date_utils.date_range(start_datetime,end_datetime,step=relativedelta(minutes=int(agenda.minutes_slot)))
                else:
                    datetimes = [start_datetime]
                for slot_start in datetimes:
                    slot_end = slot_start + timedelta(minutes=int(agenda.minutes_slot))
                    dayoff_start = datetime.combine(
                                                    day.date(),
                                                    DateTimeHelper.get_server_time_from_float(agenda.dayoff_start).time()
                                                )
                    dayoff_end = datetime.combine(
                                                    day.date(),
                                                    DateTimeHelper.get_server_time_from_float(agenda.dayoff_end).time()
                                                )                               
                    if DateTimeHelper.slot_intersection(slot_start, slot_end, dayoff_start, dayoff_end):
                        continue
                    slot = {
                        'agenda': agenda.id,
#                        'duration': duration,
                        'start_datetime': DateTimeHelper.get_server_time(slot_start),
                        'end_datetime': DateTimeHelper.get_server_time(slot_end),
                    }
                    existing_slot = Slot.search([
                            ('start_datetime', '=', DateTimeHelper.get_server_time(slot_start)), 
                            ('end_datetime', '=', DateTimeHelper.get_server_time(slot_end)), 
                            ('agenda', '=', agenda.id)])
                    if not existing_slot:
                        Slot.create(slot)
                service = self.env['booking.resource.service'].search([('agenda','=', agenda.id),('date','=',day.date())])
                if not service:
                    self.env['booking.resource.service'].create({'agenda': agenda.id, 'date': day.date()})
        return True                     

    @api.model
    def get_time_slots(self, date, num_persons, space_id, online=False):
        start = datetime.combine(date,datetime.min.time())
        end = start + timedelta(hours=24)
        Slot = self.env['booking.resource.agenda.slot']
        domain = [
                    ('start_datetime', '>=', start),
                    ('end_datetime','<',end),
                    ('space','=',space_id),
                    ('start_datetime', '>=', fields.Datetime.now())
                ]
        if online:
            domain.append(('is_open_online','=',True))
        open_slots = Slot.sudo().search(domain).sorted(lambda x:x.start_datetime)
        available_slots = Slot
        for slot in open_slots:
            event_duration_minutes = slot.agenda.event_duration_minutes
            if event_duration_minutes:
                event_end_time = slot.start_datetime + timedelta(minutes=event_duration_minutes)
            else:
                event_end_time = slot.agenda.get_last_time_in_date(date)
            event_slots = Slot.sudo().search([
                                        ('start_datetime','>=', slot.start_datetime),
                                        ('start_datetime','<=',event_end_time),
                                        ('space','=',space_id)
                                    ])
            if event_slots and min(event_slots.mapped('availability')) >= int(num_persons):
                available_slots |= slot
#        slots = Slot
#        for line in available_lines:
#            start_datetime = fields.Datetime.to_string(line.start_datetime)
#            date = line.line_id.get_tz_date(datetime.strptime(start_datetime, DEFAULT_SERVER_DATETIME_FORMAT), self.env.context['tz'])
#            if int(date.day) == int(day) and int(date.month) == int(month) and int(date.year) == int(year):
#                slots += line
        return available_slots

    def get_last_time_in_date(self, date):
        dates_lines = self.booking_slots.filtered(lambda x: x.start_datetime.date() == date)
        last_date_line = dates_lines.sorted(key=lambda x: x.end_datetime.time(),reverse=True)[0]
        return last_date_line.end_datetime + timedelta(minutes=int(self.minutes_slot))
    
class BookingResourceAgendaSlot(models.Model):
    _name = 'booking.resource.agenda.slot'
    _description = 'Every time slot from an agenda that is bookable.'
    _order = 'start_datetime'

    agenda = fields.Many2one('booking.resource.agenda', string='Booking agenda', ondelete='cascade',required=True)
    space = fields.Many2one(related='agenda.space',store=True)
    type = fields.Many2one(related='agenda.type')
    start_datetime = fields.Datetime(required=True)
    end_datetime = fields.Datetime(required=True)
    capacity = fields.Integer(related='space.capacity')
    occupancy = fields.Integer(readonly=True)
    availability = fields.Integer(compute='_compute_availability', store=True)
    is_open_online = fields.Boolean('Open', default=True)
    is_past = fields.Boolean('Past', compute='_compute_is_past')
    calendar_events = fields.Many2many(comodel_name='calendar.event')
                            
    _sql_constraints = [
                            ('slot_uniq', 'unique (space,start_datetime)','There cannot be two slots at the same time for the same space.')
                        ]
    
    @api.constrains('start_datetime', 'end_datetime')
    def _check_closing_date(self):
        for line in self:
            if line.start_datetime and line.end_datetime and line.end_datetime < line.start_datetime:
                raise ValidationError(_('Ending datetime cannot be set before starting datetime.'))

    @api.depends('occupancy')
    def _compute_availability(self):
        for record in self:
            record.availability = record.capacity - record.occupancy

    @api.depends('start_datetime')
    def _compute_is_past(self):
        for record in self:
            if record.start_datetime < fields.Datetime.now():
                record.is_past = True
                record.is_open_online = False
            else:
                record.is_past = False
        
    def write(self, vals):
        if 'start_datetime' in vals or \
            'end_datetime' in vals:
            raise UserError(_('You cannot change these values manually.'))
        super(BookingResourceAgendaSlot, self).write(vals)
        
    def unlink(self):
        for record in self:
            DateTimeHelper = self.env['booking.datetime.helper']
            if record.occupancy > 0:
                date = DateTimeHelper.get_user_datetime(record.start_datetime)
                _logger.warning(_('You cannot delete an already booked slot: %s - %s') % (date.time(), 
                                                        format_date(date.date(),locale=self.env.user.lang,format='short')))
            else:
                super(BookingResourceAgendaSlot, record).unlink()

    def name_get(self):
        result = []
        DateTimeHelper = self.env['booking.datetime.helper']
        for record in self:
            date = DateTimeHelper.get_user_datetime(record.start_datetime)
            result.append((record.id, '%s - %s [%d]' % (date.time(), 
                                                        format_date(date.date(),locale=self.env.user.lang,format='short'),
                                                        record.availability)))
        return result
    
    def get_additional_info(self):
        DateTimeHelper = self.env['booking.datetime.helper']
        if self.agenda.additional_info_is_for_all_times:
            if self.agenda.additional_info:
                return self.agenda.additional_info[0].text
        time = self.start_datetime.time()
        lines = list(filter(lambda x: DateTimeHelper.get_server_time_from_float(x.time_float).time() == time, self.agenda.additional_info))
        if lines:
            return lines[0].text
        else:
            return False

        
    
class BookingHoliday(models.Model):
    _name = 'booking.holiday'
    _description = 'Periods when it is not possible to make bookings.'

    name = fields.Char("Reason", required=True)
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    agenda = fields.Many2one(comodel_name='booking.resource.agenda', string='Booking agenda', ondelete='cascade')

class BookingWeekoff(models.Model):
    _name = 'booking.weekoff'
    _description = 'Week day when it is not possible to make bookings.'

    name = fields.Char(required=True, translate=True)
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
        ], 'Day of Week', required=True, index=True, default='6')