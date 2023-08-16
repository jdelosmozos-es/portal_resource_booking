from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from odoo.tools import date_utils

class BookingAdditionalInformation(models.Model):
    _name = 'booking.additional.information'
    _description = 'Additional informatin to show on bookings depending on agenda and time.'
        
    agenda = fields.Many2one(comodel_name='booking.resource.agenda')
    time_float = fields.Float()
    text = fields.Char(required=True)
    image = fields.Image()
    time = fields.Datetime(compute="_compute_time")
    
    @api.depends('time_float')
    def _compute_time(self):
        DateTimeHelper = self.env['booking.datetime.helper']
        for record in self:
            record.time = DateTimeHelper.get_server_time_from_float(record.time_float)
        
    @api.constrains('hour')
    def _check_hour(self):
        for record in self:
            if record.agenda.additinal_info_is_for_all_times:
                if record.hour != False:
                    raise ValidationError("You cannot define hour if instruction is for all times.")
                return
            if int(record.agenda.minutes_slot) == 0:
                valid_datetimes = [record.agenda.start_time]
            else:
                valid_datetimes = date_utils.date_range(record.agendastart_time,record.agenda.end_time,
                                            step=relativedelta(minutes=int(record.agenda.minutes_slot))
                                    )
            if record.time.time() not in [x.time() for x in valid_datetimes]:
                raise ValidationError("The hour should be one of %s." % record.agenda.event_times)
    