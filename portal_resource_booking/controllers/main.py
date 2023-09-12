# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta

from odoo import fields, http
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, date_utils
from babel.dates import format_date
import json

#import json


FILETYPE_BASE64_MAGICWORD = {
    b'/': 'jpg',
    b'R': 'gif',
    b'i': 'png',
    b'P': 'svg+xml',
}

class MemberAppointment(http.Controller):

    def _get_available_dates(self):
        now = fields.Datetime.now()
        lines = request.env['booking.resource.agenda.slot'].search([
                ('availability','>',0),('is_open_online','=',True)
            ]).filtered(lambda x: x.start_datetime >= now)
        datetimes = lines.mapped('start_datetime')
        dates = set()
        for datetime in datetimes:
            date = datetime.date()
            if date not in dates:
                dates.add(date)
        available_dates = []
        dates_list = list(dates)
        dates_list.sort()
        for date in dates_list:
            available_dates.append(json.dumps({"day": date.day,'month': date.month, 'year': date.year}))
        return available_dates

    def _get_tz(self):
        #TODO: revisar tz
        if 'tz' in request.context:
            tz = request.context['tz']
        else:
            user = request.env.ref('portal_resource_booking.appointment_system_user').sudo()
            tz = user.tz
        return tz
    
    def image_data_uri(self,base64_source):
        """This returns data URL scheme according RFC 2397
        (https://tools.ietf.org/html/rfc2397) for all kind of supported images
        (PNG, GIF, JPG and SVG), defaulting on PNG type if not mimetype detected.
        """
        return 'data:image/%s;base64,%s' % (
            FILETYPE_BASE64_MAGICWORD.get(base64_source[:1], 'png'),
            base64_source.decode(),
        )
    
    @http.route('/appointment', auth="public", website=True)
    def appointment_start(self, **post):
        lines = request.env['booking.resource.agenda.slot'].sudo().search([])
        availabilities = lines.sorted(lambda x:x.availability,reverse=True)
        if availabilities:
            max_capacity = availabilities[0].availability
        else:
            max_capacity = 0
            #TODO: decir que no hay fechas disponibles
        spaces = lines.mapped('space')
        available_dates = self._get_available_dates()
        values = {
            'name': False,
            'email': False,
            'phone': False
        }
        if request.uid != 4: #TODO: Comprobar bien que es el Public User
            partner = request.env['res.users'].browse(request.uid).partner_id
            values['name'] = partner.name
            if partner.email:
                values['email'] = partner.email
            if partner.phone:
                values['phone'] = partner.phone
            elif partner.mobile:
                values['phone'] = partner.mobile

        return request.render('portal_resource_booking.appointment_calendar', 
                              {'max_capacity': max_capacity,
                               'spaces': spaces, 
                               'available_dates': available_dates, 
                               'user_name': values['name'], 
                               'user_email': values['email'], 
                               'user_phone': values['phone'], 
                               'requests': request.env['booking.request'].search([])
                               })
            

    @http.route('/appointment/book/confirm', auth="public", type='json')
    def confirm_booking(self, values):
        DatetimeHelper = request.env['booking.datetime.helper']
#        requests = request.httprequest.form.to_dict(flat=False).get('requests') Esto es necesario si se envía por form
        tz = self._get_tz()
        Partner = request.env['res.partner'].sudo()
        date_value = date(int(values['date']['year']),int(values['date']['month']),int(values['date']['day']))
        space_id = int(values['space_id']) # = request.env['calendar.event.location'].sudo().browse(int(values['space_id']))
        requests = [int(x) for x in values['request']]
        partner = Partner.search([('email', '=', values['email'])], limit=1)
        if not partner:
            partner = Partner.create({
                'name': values['name'],
                'email': values['email'],
                'phone': values['phone'],
                'tz': tz,
            })
        num_persons = int(values['num_persons'])
        start_datetime = DatetimeHelper.get_server_datetime_controller(date_value,values['time_string'],tz)
        Agenda = request.env['booking.resource.agenda']
        slot = Agenda.get_time_slots(date_value, num_persons, space_id).filtered(
                lambda x : x.start_datetime == start_datetime
            )
        Wizard = request.env['booking.wizard']
        wizard = Wizard.sudo().create({
                'date': date_value,
                'space': space_id,
                'num_persons': num_persons,
                'slot': slot[0].id,
                'partner': partner.id,
                'requests': [(6,0,requests)] if requests else False,
                'special_request': values['special_request']
            })
        wizard.action_book()
        return values

    @http.route('/calendar/timeslots', type='json', auth='public')
    def get_time_slots(self, selectedDate, num_persons, space_id):
        DatetimeHelper = request.env['booking.datetime.helper']
        ctx = dict (request.context)
        ctx.update ({'tz': self._get_tz()})
        self._context = ctx
        str_date = str(selectedDate)
        sel_date = str_date.split("-")
        date_date = date(int(sel_date[2]), int(sel_date[1]), int(sel_date[0]))
        slots = request.env['booking.resource.agenda'].get_time_slots(date_date, int(num_persons), int(space_id), online=True)
        mylst = [fields.Datetime.context_timestamp(self, s.start_datetime).strftime('%H:%M').replace(':', '') for s in slots]
        sorted_slots = [my_hash[:2] + ':' + my_hash[2:] for my_hash in sorted(mylst, key=int)]
        info_list = []
        agendas = slots.mapped('agenda')
        for agenda in agendas:
            if agenda.additional_info_is_for_all_times:
                add_info = agenda.additional_info[0]
                for slot in sorted_slots:
                    info_list.append({'hour': slot, 
                                      'text': add_info.text, 
                                      'img': self.image_data_uri(add_info.image) if add_info.image else False})
            else:
                for add_info in agenda.additional_info:
                    if add_info not in info_list:
                        info_list.append({'hour': DatetimeHelper.get_time_string_from_float(add_info.time_float), 
                                      'text': add_info.text, 
                                      'img': self.image_data_uri(add_info.image) if add_info.image else False})
       
        return {'slots': sorted_slots,'instructions': info_list}
