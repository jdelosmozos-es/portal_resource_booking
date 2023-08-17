from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from odoo.tools import date_utils
from datetime import datetime

class BookingAdditionalInformation(models.Model):
    _name = 'booking.additional.information'
    _description = 'Additional informatin to show on bookings depending on agenda and time.'
        
    agenda = fields.Many2one(comodel_name='booking.resource.agenda')
    time_float = fields.Float()
    text = fields.Char(required=True)
    image = fields.Image()
        
    @api.constrains('time_float')
    def _check_hour(self):
        today = fields.Datetime.today()
        for record in self:
            if record.agenda.additional_info_is_for_all_times:
                if record.time_float != False:
                    raise ValidationError("You cannot define hour if instruction is for all times.")
                return
            start_time = datetime.combine(today,datetime.min.time()) + relativedelta(hours=record.agenda.start_time_float)
            if int(record.agenda.minutes_slot) == 0:
                valid_datetimes = [start_time]
            else:
                end_time = datetime.combine(today,datetime.min.time()) + relativedelta(hours=record.agenda.end_time_float)
                valid_datetimes = date_utils.date_range(start_time,end_time,
                                            step=relativedelta(minutes=int(record.agenda.minutes_slot))
                                    )
            my_time = datetime.combine(today,datetime.min.time()) + relativedelta(hours=record.time_float)
            if my_time not in valid_datetimes:
                raise ValidationError("The hour should be one of %s." % record.agenda.event_times)
    