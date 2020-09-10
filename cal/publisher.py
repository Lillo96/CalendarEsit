import sys
import time
import datetime

import requests


from .mqtt_iot import init_client   
from background_task import background


from paho.mqtt.client import *

from .models import CalendarGroups,Calendar

def main(arg1,arg2):
   ##mqttc = mqtt.Client()	
   mqttc = init_client()
   print("client initialized")
   print(arg1)
   print(arg2)
   topic = "$aws/things/%s-%s/shadow/update" % (arg1,arg2)

   #accesscode = requests.GET.get('code')
   params= {'pk':arg1,'pk1':arg2}
   url = 'http://127.0.0.1:8000/mqtt/%d/calendars/%d/events/' % (arg1,arg2)
   resp = requests.get(url=url)
   json = resp.json()
   
   print(json)
  
   print("try to publish")
   mqttc.publish(topic, str(json))
   print("Time publish")
   time.sleep(1)

if __name__ == '__main__':
   
   import sys
   main(sys.argv[1:])


#funzione da attivare in background per inviare eventi in corso o prossimi a iot
@background(schedule=10)
def publishEvent():
   print("dentro publish event")
   groups= CalendarGroups.objects.all()
   calendars = Calendar.objects.all()
   for group in groups:
      for calendar in calendars.filter(group_id=group.id):
         main(group.id,calendar.id)









