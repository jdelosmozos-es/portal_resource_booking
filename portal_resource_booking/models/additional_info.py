from odoo import models, fields, api
from odoo.exceptions import ValidationError

class BookingAdditionalInformation(models.Model):
    _name = 'booking.additional.information'
        
    agenda = fields.Many2one(comodel_name='booking.resource.agenda')
    hour = fields.Float()
    text = fields.Char(required=True)
    image = fields.Image()
    
    @api.constrains('hour')
    def _check_hour(self):
        for record in self:
            if record.agenda.instruction_is_for_all_times:
                if record.hour != False:
                    raise ValidationError("You cannot define hour if instruction is for all times.")
                return
            valid_hours = []
            if int(record.agenda.minutes_slot) == 0:
                valid_hours.append(record.agenda.start_time)
            else:
                valid_times = record.agenda.event_times.split(' - ')
                for time in valid_times:
                    valid_hours.append(self._get_hour(time))
            if record.hour not in valid_hours:
                raise ValidationError("The hour should be one of %s." % record.agenda.event_times)
    
    #FIXME: Pasar ésto a un AbstractModel BookingDateTimeHelper
    @api.model
    def _get_hour(self, time):
        vals = time.split(':')
        return int(vals[0])+int(vals[1])/60
    