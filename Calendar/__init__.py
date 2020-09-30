import sys
#sys.path.insert(0, '/home/ubuntu/CalendarEsit/cal/')
sys.path.insert(0, '/home/lillo/CalendarEsit/cal/')
import mqtt_iot
mqtt_iot.client.loop_start()
mqtt_iot.client1.loop_start()
