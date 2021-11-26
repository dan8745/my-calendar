from mycroft import MycroftSkill, intent_file_handler
from datetime import date, datetime, timedelta
import caldav

# To do: (In no particular order.)
#   1. Retrieve calendar free space for given interval.
#   2. Only retrieve events from a specific calendar.
#   3. Retrieve calendar names.
#   4. Add an event to a calendar.
#   5. Send an invitation to somebody for an event.
#   6. Retrieve calendar events between specific date range.
#   7. Add docstrings.

class MyCalendar(MycroftSkill):


    def __init__(self):
        MycroftSkill.__init__(self)

        # To Do: Register data from settingsmeta.json

        self.user = None
        self.password = None
        self.url = None
                
        self.day_num = {'monday': 0, 'tuesday': 1, 'wednesday': 2,
                        'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}


    def initialize(self):
        self.register_entity_file('when.entity')
                
        self.setting_change_callback = self.on_websettings_changed
        self.on_websettings_changed()

        
    def on_websettings_changed(self):

        self.log.info('Collecting login information')

        self.user = self.settings.get('user')
        if not self.user:
            self.log.info('Failed to retrieve username')

        self.password = self.settings.get('password')
        if not self.password:
            self.log.info('failed to retrieve password')

        self.url = self.settings.get('url')
        if not self.url:
            self.log.info('failed to retrieve url')

        self.log.info('Completed login information retrieval attempt')
        
    def get_calendars(self):
        client = caldav.DAVClient(url=self.url, \
                                  username=self.user, \
                                  password=self.password)
        my_principal = client.principal()
        calendars = my_principal.calendars()

        return calendars


    def get_events(self, calendars, start_date, end_date):
        # To do:
        #   1. Return events with time stamp. (They currently have only dates.)
        #   2. Return events in chronological order.
        #   3. Add datetime start/end filters. (Currently supports only dates.)

        # Note: calendar.date_search() only supports datetime.date
        #       Will need to add a manual filter to support datetime.datetime
        events = [{'uid': str(event.vobject_instance.vevent.uid.value),
                   'summary': str(event.vobject_instance.vevent.summary.value),
                   'dtstart': str(event.vobject_instance.vevent.dtstart.value),
                   'dtend': str(event.vobject_instance.vevent.dtend.value),
                   'dtstamp': str(event.vobject_instance.vevent.dtstamp.value)}
                  for calendar in calendars
                  for event in calendar.date_search(
                          start=start_date,
                          end=end_date)]

        return events
        
        
    @intent_file_handler('calendar.my.intent')
    def handle_calendar_my(self, message):
        # To do: Add entity to retrieve only specific calendars.
        #   i.e. 'hey mycroft. what do i have today on my {calendar} calendar.'
        #        Where {calendar} could be 'work', 'family', etc.
        self.speak_dialog('calendar.my')


 
        start_date = date.today()
        end_date = start_date + timedelta(days=1)



        # To do: Add functionality to retrieve a specific date/time interval
        when = message.data.get('when')
        if when == 'tomorrow':
            start_date = end_date
            end_date = start_date + timedelta(days=1)



        if when in self.day_num.keys():
            # To do: Add date to dialog when utterance specifies
            # a weekday that is the same as today().weekday()
            day_diff = self.day_num[when] - datetime.today().weekday()
            if day_diff != 0:
                if day_diff < 0:
                    day_diff += 7
                start_date = start_date + timedelta(days=day_diff)
                end_date = start_date + timedelta(days=1)
                when = 'on ' + when

        # To do: Move start_date & end_date to get_calendars()        
        calendars = self.get_calendars()
        events = self.get_events(calendars, start_date, end_date)


        response = 'i see you have {} events {}. '.format(len(events), when)
        for event in events:
            response = response + event['summary'].lower() + '. '


        self.speak(response)


def create_skill():
    return MyCalendar()
