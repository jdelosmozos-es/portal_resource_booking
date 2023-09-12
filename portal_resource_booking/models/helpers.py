from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime
import pytz

class DateTimeHelper(models.AbstractModel):
    _name = 'booking.datetime.helper'
    _description = 'Helper for operations on time and date fields.'
    
    @api.model
    def get_server_datetime_controller(self, date, time_string, tz):
        minutes = int(time_string.split(':')[0])*60 + int(time_string.split(':')[1])
        local_time = datetime.datetime.combine(date,datetime.time()) + datetime.timedelta(minutes=minutes)
        localized_local_time = pytz.timezone(tz).localize(local_time)
        server_time = localized_local_time.astimezone(pytz.utc)
        return server_time.replace(tzinfo=None)
        
    @api.model
    def get_server_time_from_float(self, float_time):
        minutes = float_time*60
        local_time = datetime.datetime.combine(fields.Datetime.today(),datetime.time()) + datetime.timedelta(minutes=minutes)
        localized_local_time = pytz.timezone(self.env.user.tz).localize(local_time)
        server_time = localized_local_time.astimezone(pytz.utc)
        return server_time.replace(tzinfo=None)
    
    @api.model
    def get_server_time(self, local_time):
        localized_local_time = pytz.timezone(self.env.user.tz).localize(local_time)
        server_time = localized_local_time.astimezone(pytz.utc)
        return server_time.replace(tzinfo=None)
    
    @api.model
    def get_user_datetime(self, datetime):
        return datetime.astimezone(pytz.timezone(self.env.user.tz))
        
    @api.model
    def slot_intersection(self, i1_start, i1_end, i2_start, i2_end):
        if i1_end < i1_start or i2_end < i2_start:
            raise UserError(_('Bad interval definition.'))
        if self._is_in(i1_start, i2_start, i2_end):
            return True
        if self._is_in(i1_end, i2_start, i2_end):
            return True
        return False
        
    @api.model
    def _is_in(self, moment, start, end):
        if moment >= start and moment <= end:
            return True
        else:
            return False
        
    @api.model
    def get_time_string_from_float(self, float_time):
        hours, minutes = divmod(float_time*60, 60)
        return '%i:%i' % (hours,minutes)
    