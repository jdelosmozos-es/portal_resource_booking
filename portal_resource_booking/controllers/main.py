# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import fields, http
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, date_utils
from babel.dates import format_date

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
        import sys;sys.path.append(r'/home/javier/eclipse/jee-2021/eclipse/plugins/org.python.pydev.core_10.2.1.202307021217/pysrc')
        import pydevd;pydevd.settrace('127.0.0.1',port=9999)
        ctx = dict (request.context)
        ctx.update ({'tz': self._get_tz()})
        self._context = ctx
        for date in dates_list: #FIXME: a ver cómo lo espera el cliente
            date_datetime = datetime.combine(date, datetime.time())
            localized_date_string = format_date(
                            fields.Datetime.context_timestamp(self, date_datetime).date(),
                            format='short',
                            locale=request.context['lang'])
            available_dates.append(localized_date_string.replace('/','-'))
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
            

    @http.route('/appointment/book', auth="public", website=True)
    def book_time(self, selectedDate,selectedTime, space_id, num_persons):
        tz = self._get_tz()
        date_time = '%s %s' % (selectedDate,selectedTime)
        start_date = datetime.strptime(date_time, '%d-%m-%Y %H:%M')
#            minutes_slot = post.get('minutes_slot')
        utc_date = request.env['web.online.appointment'].get_utc_date(start_date, tz)
        space = request.env['calendar.event.location'].sudo().browse(space_id)
        line = request.env['web.online.appointment.line'].search([('start_datetime','=',utc_date),('space','=',space_id)])
        calendar_id = line.line_id
#            calendar_id = post.get('calendar_id')
#            stop_date = start_date + timedelta(minutes=int(minutes_slot))
        values = ({
            'booking_time': '%s | %s %s , %s' % (selectedTime, start_date.strftime('%B'), start_date.day, start_date.year),
            'start_datetime': fields.Datetime.to_string(start_date),
            'start': fields.Datetime.to_string(start_date),
#                'stop': fields.Datetime.to_string(stop_date),
#                'duration': round((float(minutes_slot) / 60.0), 2),
#                'calendar_id': int(calendar_id),
#                'minutes_slot': int(post.get('minutes_slot')),
            'space': space,
            'num_persons': num_persons,
            'phone': False,
            'name': False,
            'email': False,
            'instructions': line.get_instruction(),
            'requests': request.env['booking.request'].search([]),
            'terms_conditions': False
        })
        if request.uid != 4: #TODO: Comprobar bien que es el Public User
            partner = request.env['res.users'].browse(request.uid).partner_id
            values['name'] = partner.name
            if partner.email:
                values['email'] = partner.email
            if partner.phone:
                values['phone'] = partner.phone
            elif partner.mobile:
                values['phone'] = partner.mobile
        return values
    
    @http.route('/appointment/book/confirm', auth="public", type='json')
    def confirm_booking(self, values):
        tz = self._get_tz()
        requests = request.httprequest.form.to_dict(flat=False).get('requests')
        Partner = request.env['res.partner'].sudo()
        Space = request.env['calendar.event.location'].sudo()
        partner = Partner.search([('email', '=', values['email'])], limit=1)
        start_date = datetime.strptime(values['start_datetime'], '%Y-%m-%d %H:%M:%S')
        utc_date = request.env['web.online.appointment'].get_utc_date(start_date, tz)
        line = request.env['web.online.appointment.line'].search([('start_datetime','=',utc_date),('space','=',int(values['space_id']))])
        space = Space.browse(int(values['space_id']))
        calendar_id = line.line_id
        if calendar_id.event_duration_minutes:
            stop_date = utc_date + timedelta(minutes=int(calendar_id.event_duration_minutes))
        else:
            stop_date = line.end_datetime
        values['space'] = space
        if not partner:
            partner = Partner.create({
#                    'name': "%s %s" % (post.get('first_name'), post.get('last_name') and post.get('last_name') or ''),
                'name': values['name'],
                'email': values['email'],
                'phone': values['phone'],
                'tz': tz,
            })
        management_user = request.env.ref('web_online_appointment_resource.appointment_manager_user').sudo()
        domain = [('line_id', '=', calendar_id.id), ('start_datetime', '>=', fields.Datetime.to_string(utc_date)), ('start_datetime', '<', fields.Datetime.to_string(stop_date))]
        lines = request.env['web.online.appointment.line'].sudo().search(domain)
        event = {
#           'name': '%s %s %spax %s' % (post.get('name').split(" ")[0], post.get('start_datetime'),post.get('num_persons'),space.name),
            'name': '%s %spax %s %s' % (values['name'].split(" ")[0],values['num_persons'],space.name,'**' if (values['request'] or values['special_request']) else ''),
            'partner_ids': [(6, 0, [partner.id,management_user.partner_id.id])],
#            'duration': duration,
            'start': fields.Datetime.to_string(utc_date),
            'stop': fields.Datetime.to_string(stop_date),
            'alarm_ids': [(6, 0, calendar_id.alarm_ids.ids)],
            'resource': space.id,
#            'description': post.get('comments'),
            'num_persons': values['num_persons'],
            'location': space.name,
            'event_location_id': space.id,
            'instructions': line.get_instruction(),
            'is_from_reservation_system': True,
            'slots': lines.ids,
            'requests': [(6,0,requests)] if requests else False,
            'special_request': values['special_request'],
        }
        #TODO: ¿no_mail? si es false envía email de confirmación
        user = request.env.ref('web_online_appointment_resource.appointment_system_user').sudo()
        #app = request.env['calendar.event'].sudo().with_context({'no_mail': True}).with_user(user).create(event)
        app = request.env['calendar.event'].sudo().with_user(user).create(event)
        # domain = [('line_id', '=', int(post.get('calendar_id'))), ('start_datetime', '=', fields.Datetime.to_string(utc_date)), ('end_datetime', '=', fields.Datetime.to_string(stop_date))]
        for line in lines:
            new_occupancy = line.occupancy + int(values['num_persons'])
            line.occupancy = new_occupancy
        values['event_id'] = app
        # mail_ids = []
        # Mail = request.env['mail.mail'].sudo()
        # template = request.env.ref('jupical_appointment_advanced.jupical_calendar_booking')
        # for attendee in app.attendee_ids:
        #     Mail.browse(template.sudo().send_mail(attendee.id)).send()
        # post['date'] = date_appointment
        return values



    @http.route('/calendar/timeslots', type='json', auth='public')
    def get_time_slots(self, selectedDate, num_persons, space_id):
        tz = self._get_tz()
        str_date = str(selectedDate)
        sel_date = str_date.split("-")
        day = sel_date[0]
        month = sel_date[1]
        year = sel_date[2]
        end_date = datetime(int(year), int(month), int(day), 0,0,0)
        end_date = end_date + timedelta(days=1)

        Line = request.env['web.online.appointment.line']
        calendar_lines = Line.sudo().search([('start_datetime', '>=', datetime.now()),
                                             ('end_datetime','<',end_date),
                                             ('space','=',int(space_id)),
                                             ('is_open','=',True)])
        
        available_lines = Line
        for line in calendar_lines:
            event_duration_minutes = line.line_id.event_duration_minutes
            if event_duration_minutes:
                event_end_time = line.start_datetime + timedelta(minutes=event_duration_minutes)
            else:
                event_end_time = line.line_id.get_last_time_in_date(line.start_datetime.date())
            event_lines = Line.sudo().search([
                                        ('start_datetime','>=', line.start_datetime),
                                        ('space','=',int(space_id)),
                                        ('start_datetime','<=',event_end_time)
                                    ])
            
            if event_lines and min(event_lines.mapped('availability')) >= int(num_persons):
                available_lines |= line
        slots = []
        for line in available_lines:
            start_datetime = fields.Datetime.to_string(line.start_datetime)
            date = line.line_id.get_tz_date(datetime.strptime(start_datetime, DEFAULT_SERVER_DATETIME_FORMAT), tz)
            if int(date.day) == int(day) and int(date.month) == int(month) and int(date.year) == int(year):
                slots.append(str(date.time())[0:5])
        mylst = [s.replace(':', '') for s in slots]
        sorted_slots = [my_hash[:2] + ':' + my_hash[2:] for my_hash in sorted(mylst, key=int)]
        instructions = []
        calendars = calendar_lines.mapped('line_id')
        for calendar in calendars:
            for instruction in calendar.instructions:
                if instruction not in instructions and instruction.image != False:
                    instructions.append({'img': self.image_data_uri(instruction.image), 'hour':instruction.hour, 'text': instruction.text})
        
        return {'slots': sorted_slots,'instructions': instructions}
