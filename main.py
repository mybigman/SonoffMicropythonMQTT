from network import WLAN, STA_IF
from mqtt import MQTTClient 
import machine 
import time 
 
 
WIFI_SSID_PASSWORD = 'WIFI_SSID','WIFI_PASSWORD'


PING_INTERVAL = 60



client = None #mqtt client
mqtt_con_flag = False #mqtt connection flag
pingresp_rcv_flag = True #indicator that we received PINGRESP
lock = True #to lock callback function from recursion when many commands are received look mqqt.py line 138


next_ping_time = 0 

def ping_reset():
 global next_ping_time
 next_ping_time = time.time() + PING_INTERVAL #we use time.time() for interval measuring interval
 print("Next MQTT ping at", next_ping_time)

def ping():
 client.ping()
 ping_reset()


def check():
 global next_ping_time
 global mqtt_con_flag
 global pingresp_rcv_flag
 if (time.time() >= next_ping_time): #we use time.time() for interval measuring interval
   if not pingresp_rcv_flag :
    mqtt_con_flag = False #we have not received an PINGRESP so we are disconnected
    print("We have not received PINGRESP so broker disconnected")
   else :
    print("MQTT ping at", time.time())
    ping()
    pingresp_rcv_flag = False
 res = client.check_msg()
 if(res == b"PINGRESP") :
  pingresp_rcv_flag = True
  print("PINGRESP")

led = machine.Pin(13, machine.Pin.OUT,value=1)
relay = machine.Pin(12, machine.Pin.OUT,value=0)
state = 0

def sub_cb(topic, msg): 
   global lock
   global state
   global client
   if not lock :
    lock = True
    if msg == b"ON":
        client.publish(topic="topic for reporting state of device", msg="ON",retain=True,qos=1) 
        relay.value(1)
        led.value(0)
        state = 1
        print("sent on")     
    elif msg == b"OFF":
        client.publish(topic="topic for reporting state of device", msg="OFF",retain=True,qos=1) 
        relay.value(0)
        led.value(1)
        state = 0
        print("sent off")
    lock = False 
   print(msg) 
 
client = MQTTClient(machine.unique_id(), "broker adress",user="username", password="password", port=port_number)
client.set_callback(sub_cb) 

def wifi_connect():
 while True:
  try:
   sta_if = WLAN(STA_IF)
   sta_if.active(True)
   sta_if.disconnect()
   sta_if.connect(*WIFI_SSID_PASSWORD)
   break
   time.sleep(0.5)
  except Exception as e:
   print("Error in Wlan connect: [Exception] %s: %s" % (type(e).__name__, e))
 

def mqtt_connect():
 global next_ping_time 
 global pingresp_rcv_flag
 global mqtt_con_flag
 global lock
 while not mqtt_con_flag:
  
  try:
   client.connect()
   client.subscribe(topic="topic for receiving commands",qos=0) #we subscribe with QoS 0 to avoid any retransmission of the command from the broker in case of network failure
   if state == 1 : 
    client.publish(topic="topic for reporting state of device", msg="ON",retain=True,qos=1)
   else :
    client.publish(topic="topic for reporting state of device", msg="OFF",retain=True,qos=1)
   mqtt_con_flag=True
   pingresp_rcv_flag = True
   next_ping_time = time.time() + PING_INTERVAL
   lock = False # we allow callbacks only after everything is set
  except Exception as e:
   print("Error in mqtt connect: [Exception] %s: %s" % (type(e).__name__, e))
  time.sleep(0.5) # to brake the loop
 print("Mqtt Broker connected")


wifi_connect()

while True: 
    mqtt_connect()#ensure connection to broker
    try:
     check()
    except Exception as e:
     print("Error in Mqtt check message: [Exception] %s: %s" % (type(e).__name__, e))
     print("MQTT disconnected due to network problem")
     lock = True # reset the flags for restart of connection
     mqtt_con_flag = False 
    time.sleep(0.5)






