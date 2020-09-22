import sys
import time
import datetime

import requests

import json


from .mqtt_iot import publish   
from background_task import background

from .models import CalendarGroups,Calendar

#funzione da attivare in background per inviare eventi in corso o prossimi a iot
@background(schedule=60)
def publishEvent():
   print("dentro publish event")
   groups= CalendarGroups.objects.all()
   calendars = Calendar.objects.all()
   for group in groups:
      for calendar in calendars.filter(group_id=group.id):
         publish(group.id,calendar.id)









