# Skill Name: my-calendar
# Author: Dan Arguello
# email: gDan@posteo.net
# Date created: 12/11/2021
# Date last modified: 12/16/2021
# Python Version: 3.8.10
# Github repository: https://github.com/dan8745/my-calendar
# License: GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007

from mycroft import MycroftSkill, intent_file_handler
from lingua_franca.parse import extract_datetime, normalize
from datetime import date, datetime, timedelta
import caldav
import pickle



class MyCalendar(MycroftSkill):


    def __init__(self):
        ''' Initialize variables with None value. '''
        
        MycroftSkill.__init__(self)


        self.user = None
        self.password = None
        self.url = None
        self.credentials_set = False

        self.calendars = list()

                
        self.day_num = {'monday': 0, 'tuesday': 1, 'wednesday': 2,
                        'thursday': 3, 'friday': 4, 'saturday': 5,
                        'sunday': 6}


    def reset_credentials(self):
        ''' Set CalDAV login credentials to None.

        Called to reset CalDAV user, password, and url to None. Ensures all
        credential data is reset to prevent further errors from incomplete
        login data.
        '''
        
        self.user = None
        self.password = None
        self.url = None
        self.credentials_set = False

        
    def initialize(self):
        ''' Perform final setup, including retrieve CalDAV login credentials,
        and retrieve calendar data from the CalDAV server.

        The initialize method is called after the Skill is fully
        constructed and registered with the system. It is used to perform
        any final setup for the Skill including accessing Skill settings.
        '''
        
        self.register_entity_file('when.entity')
                
        self.setting_change_callback = self.on_websettings_changed
        self.on_websettings_changed()

        
    def on_websettings_changed(self):
        ''' Check periodically for user settings and update data.

        Retrieve and update user credentials from account.mycroft.ai to the
        skill's settings.json file. Then retrieve associated calendar data
        from the CalDAV server.
        '''
        
        self.get_credentials()
        self.get_calendars()



    def get_credentials(self):
        ''' Collect CalDAV server login credientials from user settings.

        Retrieve username, password, and url from account.mycroft.ai
        and write to the skill's settings.json file. Log any errors to
        /var/log/mycroft/skills.log.
        '''
        
        self.log.info('Collecting CalDAV credentials')

        try:
            self.user = self.settings.get('user')
            self.password = self.settings.get('password')
            self.url = self.settings.get('url')
            if (self.user and self.password and self.url):
                self.credentials_set = True

        except:
            self.log.exception('Failed to properly retrieve CalDAV credentials')
            self.speak('i could not retrieve your calendar credentials')
            self.speak('i will not be able to update your calendar')
            self.speak('this could be a problem with your internet connection.')

            self.reset_credentials()

        if not self.credentials_set:
            self.log.info('CalDAV credentials seem to be missing')
            self.log.info('Check your settings at account.mycroft.ai')
            self.speak('some of your cal dav credentials are missing')
            self.speak('please check your settings at mycroft dot a i')
            
            self.reset_credentials()
        
        else:
            self.log.info('Collected CalDAV credentials')


            
    def get_calendars(self):
        ''' Retrieve calendar object data from CalDAV server and store
        in self.calendars '''
        
        if self.credentials_set:
            client = caldav.DAVClient(url=self.url, \
                                      username=self.user, \
                                      password=self.password)
            try:
                my_principal = client.principal() # Connect to CalDAV server
                self.calendars = my_principal.calendars()
            except:
                self.log.exception('Failed to retrieve data from CalDAV server')
                self.speak('i could not retrieve your calendar data')
                self.speak('this may be an issue with your log in credentials')
                self.speak('please check your settings at mycroft dot aee i')

                self.calendars = None



    def get_events(self, start_date, end_date):
        ''' Retrieve events from self.calendars between two dates.

        Parameters:

        Returns:
        list: Items are dictionaries, each describes a calendar event with keys
        'uid', 'summary', 'dtstart', 'dtend', 'dtstamp'
        '''
        
        events = list()
        if self.calendars is not None:
            for calendar in self.calendars:
                for event in calendar.date_search(start=start_date,
                                                  end=end_date):
                    
                    events.append(
                        {'uid': event.vobject_instance.vevent.uid,
                         'summary': event.vobject_instance.vevent.summary,
                         'dtstart': event.vobject_instance.vevent.dtstart,
                         'dtend': event.vobject_instance.vevent.dtend,
                         'dtstamp': event.vobject_instance.vevent.dtstamp}
                    )
                    
        return events
        
    @intent_file_handler('calendar.my.intent')
    def handle_calendar_my(self, message):
        ''' Retrieve and speak events for the requested day or date.

        Lists events from all calendars for the URL provided in the user's
        settings at account.mycroft.ai.

        '''


        start_date, rest = extract_datetime(message.data.get('utterance', ''),
                                    datetime.today())
        start_date = start_date.date() # Remove the time; keep the date
        end_date = start_date + timedelta(days=1)

        when = message.data.get('when') # I don't like this
        if when in self.day_num.keys(): # block of code
            when = 'on ' + when         # here.

        events = self.get_events(start_date, end_date)

        if len(events) > 0:
            self.speak_dialog('calendar.my')
            response = f'i see you have {len(events)} events {when}. '
            for event in self.events:
                if event['dtstart'] < start_date and event['dtend'] < end_date:
                    response += event['summary'].value.lower() + '. '
        else:
            response = f'there are no events on your calendar {when}. '
        

        self.speak(response)

        

def create_skill():
    ''' Register the skill. '''
    return MyCalendar()
