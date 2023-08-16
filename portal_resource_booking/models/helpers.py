from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime
import pytz

class DateTimeHelper(models.AbstractModel):
    _name = 'booking.datetime.helper'
    _description = 'Helper for operations on time and date fields.'
    
    @api.model
    def get_server_time_from_float(self, float_time):
        #debe coger float_time y devolver un Datetime de hoy con la hora convertida a UTC desde tz del user
        minutes = float_time*60
        local_time = datetime.datetime.combine(fields.Datetime.today(),datetime.time()) + datetime.timedelta(minutes=minutes)
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
        
#    @api.model
#    def _get_hour(self, time):
#        vals = time.split(':')
#        return int(vals[0])+int(vals[1])/60