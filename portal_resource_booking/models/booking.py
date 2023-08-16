from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools import date_utils
from dateutil.relativedelta import relativedelta 
from datetime import timedelta, datetime

class BookingResourceAgenda(models.Model):
    _name = 'booking.resource.agenda'
    _description = 'Agenda of resource bookings. Define possible time slots to book.'
    
    DEFAULT_AGENDA_DAY_TIME_LENGTH_HOURS = 3

    name = fields.Char(required=True)
    display_name = fields.Char(compute='_compute_display_name')
    space = fields.Many2one(comodel_name='calendar.event.location', required=True)
    capacity = fields.Integer(related='space.capacity')
    dayoff_start = fields.Float("Day-off start")
    dayoff_end = fields.Float("Day-off end")
    start_date = fields.Date(string='Start Date', required=True, default=fields.Datetime.now)
    end_date = fields.Date(string='End Date', compute='_compute_end_date')
    start_time_float = fields.Float("First bookable hour", required=True)
    minutes_slot = fields.Char("Slot in mins.", help='Period between bookable hours')
    end_time_float = fields.Float("Last bookable hour", required=True) #TODO: Poner por defecto tres horas después de la inicial
#    start_time = fields.Datetime(compute="_compute_start_end_time")
#    end_time = fields.Datetime(compute="_compute_start_end_time")
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

    @api.depends('type','space')
    def _compute_display_name(self):
        self.display_name = '%s%s%s' % (
                        '[%s] ' % self.space.name if self.space.name else '',
                        '[%s] ' % self.type.name if self.type.name else '',
                        self.name if self.name else ''
                    )
        
    @api.onchange('additional_info_is_for_all_times')
    def _onchange_additional_info_is_for_all_times(self):
        if self.additional_info_is_for_all_times:
            if len(self.additional_info) == 1:
                self.additional_info[0].time_float = False
        else:
            if self.start_time == self.end_time and len(self.additional_info)==1:
                self.additional_info[0].time_float = self.start_time_float
                
    @api.constrains('additional_info','additional_info_is_for_all_times')
    def _check_additinal_onfo(self):
        for record in self:
            if record.additional_info_is_for_all_times:
                if len(record.additional_info) > 1:
                    raise ValidationError("You cannot define more than one instruction for all times.")
                if record.additional_info[0].hour != False:
                    raise ValidationError("You cannot define hour if instruction is for all times.")
            else:
                times_float = []
                for additional_info in record.additional_info:
                    additional_info._check_hour()
                    if additional_info.time_float in times_float:
                        raise ValidationError(_('You cannot define two additional informations for the same time'))
                    times_float.append(additional_info.time_float)
                    
    @api.depends('start_time_float','end_time_float')
    def _compute_start_end_time(self):
        DateTimeHelper = self.env['booking.datetime.helper']
        for record in self:
            record.start_time = DateTimeHelper.get_server_time_from_float(record.start_time_float)
            record.end_time = DateTimeHelper.get_server_time_from_float(record.end_time_float)
        
    @api.depends('start_time','minutes_slot','end_time')
    def _compute_times(self):
        DateTimeHelper = self.env['booking.datetime.helper']
        for record in self:
            if record.start_time and record.end_time:
                if record.start_time == record.end_time:
                    record.event_times = DateTimeHelper.get_user_datetime(record.start_time).strftime('%H:%M')
                else:
                    if record.minutes_slot:
                        datetimes = date_utils.date_range(
                                            DateTimeHelper.get_user_datetime(record.start_time),
                                            DateTimeHelper.get_user_datetime(record.end_time),
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
        for record in self:
            if not record.minutes_slot or record.minutes_slot == '' or record.minutes_slot == '0':
                record.end_time_float = record.start_time_float
            else:
                record._onchange_endtime()
                
    @api.onchange('end_time')
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
        default.update({'calendar_line_ids': False, 'duration': 0})
        return super(BookingResourceAgenda, self).copy(default)
    
    @api.model
    def create(self, vals):
        agenda = super(BookingResourceAgenda, self).create(vals)
        agenda._generate_agenda()
        return agenda
    
    def write(self, values):
        res = super(BookingResourceAgenda, self).write(values)
        fields_list = ['minutes_slot', 'start_date', 'start_time_float', 'end_time_float', 'duration', 'holiday_ids', 'weekoff_ids']
        if any(key in values for key in fields_list):
            for record in self:
                record.booking_slots.unlink()
                record._generate_agenda()
        return res
    
    def _generate_agenda(self):
        import sys;sys.path.append(r'/home/javier/eclipse/jee-2021/eclipse/plugins/org.python.pydev.core_10.1.4.202304151203/pysrc')
        import pydevd;pydevd.settrace('127.0.0.1',port=9999)
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
                start_datetime = datetime.combine(day.date(), agenda.start_time.time())
                if agenda.minutes_slot:
                    end_datetime = datetime.combine(day.date(), agenda.end_time.time())
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
                        'start_datetime': slot_start,
                        'end_datetime': slot_end,
                    }
                    existing_slot = Slot.search([('start_datetime', '=', slot_start), ('end_datetime', '=', slot_end), ('agenda', '=', agenda.id)])
                    if not existing_slot:
                        Slot.create(slot)
        return True                     

class BookingResourceAgendaSlot(models.Model):
    _name = 'booking.resource.agenda.slot'
    _description = 'Every time slot from an agenda that is bookable.'

    agenda = fields.Many2one('booking.resource.agenda', string='Booking agenda', ondelete='cascade')
    space = fields.Many2one(related='agenda.space')
    type = fields.Many2one(related='agenda.type')
    start_datetime = fields.Datetime()
    end_datetime = fields.Datetime()
#    duration = fields.Float('Duration in mins') #TODO: ¿Ésto se utiliza para algo?
    capacity = fields.Integer(related='space.capacity')
    occupancy = fields.Integer(readonly=True)
    availability = fields.Integer(compute='_compute_availability', store=True)
    is_open = fields.Boolean('Open', default=True)
    is_past = fields.Boolean('Past', compute='_compute_is_past')
                            
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
            else:
                record.is_past = False
        
    def write(self, vals):
        if 'start_datetime' in vals or \
            'end_datetime' in vals:
            raise UserError(_('You cannot change these values manually.'))
        super(BookingResourceAgendaSlot, self).write(vals)
        
    def unlink(self):
        for record in self:
            if record.occupancy != 0:
                raise UserError(_('You cannot delete an already reserved slot.'))
        super(BookingResourceAgendaSlot, self).unlink()

    def name_get(self):
        result = []
        DateTimeHelper = self.env['booking.datetime.helper']
        for record in self:
            date = DateTimeHelper.get_user_datetime(record.start_datetime)
            result.append((record.id, '%s - %s [%d]' % (date.time(), date.date(), record.availability)))
        return result
    
    def get_additional_info(self):
        if self.agenda.additional_info_is_for_all_times:
            if self.agenda.additional_info:
                return self.agenda.additional_info[0].text
        time = self.start_datetime.time()
        lines = filter(lambda x: x.time.time() == time, self.agenda.additional_info)
        return list(lines)[0].text
    
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

    name = fields.Char(required=True)
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
        ], 'Day of Week', required=True, index=True, default='6')