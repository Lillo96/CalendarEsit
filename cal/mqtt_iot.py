import base64
import datetime as datet
import functools
import hashlib
import hmac
import os
import uuid
import json

import time
import requests


from paho.mqtt.client import Client
MQTT_TOPIC = [("event/new",0),("event/update",0)]

def get_amazon_auth_headers(access_key, secret_key, region, host, port, headers=None):
    """ Get the amazon auth headers for working with the amazon websockets
    protocol

    Requires a lot of extra stuff:

    http://docs.aws.amazon.com/general/latest/gr//sigv4-create-canonical-request.html
    http://docs.aws.amazon.com/general/latest/gr//signature-v4-examples.html#signature-v4-examples-pythonw
    http://docs.aws.amazon.com/general/latest/gr//sigv4-signed-request-examples.html#sig-v4-examples-get-auth-header

    Args:
        access_key (str): Amazon access key (AWS_ACCESS_KEY_ID)
        secret_key (str): Amazon secret access key (AWS_SECRET_ACCESS_KEY)
        region (str): aws region
        host (str): iot endpoint (xxxxxxxxxxxxxx.iot.<region>.amazonaws.com)
        headers (dict): a dictionary of the original headers- normally websocket headers

    Returns:
        dict: A string containing the headers that amazon expects in the auth
            request for the iot websocket service
    """

    # pylint: disable=unused-variable,unused-argument

    def sign(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def getSignatureKey(key, dateStamp, regionName, serviceName):
        kDate = sign(("AWS4" + key).encode("utf-8"), dateStamp)
        kRegion = sign(kDate, regionName)
        kService = sign(kRegion, serviceName)
        kSigning = sign(kService, "aws4_request")
        return kSigning

    service = "iotdevicegateway"
    algorithm = "AWS4-HMAC-SHA256"

    t = datet.datetime.utcnow()
    amzdate = t.strftime('%Y%m%dT%H%M%SZ')
    datestamp = t.strftime("%Y%m%d") # Date w/o time, used in credential scope

    if headers is None:
        headers = {
            "Host": "{0:s}:443".format(host),
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Origin": "https://{0:s}:443".format(host),
            "Sec-WebSocket-Key": base64.b64encode(uuid.uuid4().bytes),
            "Sec-Websocket-Version": "13",
            "Sec-Websocket-Protocol": "mqtt",
        }

    headers.update({
        "X-Amz-Date": amzdate,
    })

    # get into 'canonical' form - lowercase, sorted alphabetically
    canonical_headers = "\n".join(sorted("{}:{}".format(i.lower(), j).strip() for i, j in headers.items()))
    # Headers to sign - alphabetical order
    signed_headers = ";".join(sorted(i.lower().strip() for i in headers.keys()))

    # No payload
    payload_hash = hashlib.sha256(str("").encode('utf-8')).hexdigest().lower()

    request_parts = [
        "GET",
        "/mqtt",
        # no query parameters
        "",
        canonical_headers + "\n",
        signed_headers,
        payload_hash,
    ]

    canonical_request = "\n".join(request_parts)

    # now actually hash request and sign
    hashed_request = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    credential_scope = "{datestamp:s}/{region:s}/{service:s}/aws4_request".format(**locals())
    string_to_sign = "{algorithm:s}\n{amzdate:s}\n{credential_scope:s}\n{hashed_request:s}".format(**locals())

    signing_key = getSignatureKey(secret_key, datestamp, region, service)
    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

    # create auth header
    authorization_header = "{algorithm:s} Credential={access_key:s}/{credential_scope:s}, SignedHeaders={signed_headers:s}, Signature={signature:s}".format(**locals())

    # get final header string
    headers["Authorization"] = authorization_header

    return headers

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_TOPIC)
    #client.subscribe("event/new")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("Messaggio ricevuto dal topic sottoscritto:")
    print(msg.topic)
    
    #convert byte json to json object and then to python dict to extract urls parameters
    print(type(msg.payload))
    byte_payload = msg.payload
    string_payload = byte_payload.decode('utf-8')
    data_dict = json.loads(string_payload)
    print("data type: ")
    print(type(data_dict))
    print("json estratto")
    group_id = data_dict['group_id']
    calendar_id = data_dict['calendar_id']
    print("calendar_id: ")
    print(calendar_id)
    #in base al topic su cui ho ricevuto il messaggio faccio un azione o l'altra
    if ( msg.topic == "event/update"):
       #invio l'evento più prossimo alla board 
       publish(group_id,calendar_id,client)
    elif ( msg.topic == "event/new"):
       #il messaggio attiverà l'aggiunta di un evento facendo una post sul link adatto
       url = 'http://127.0.0.1:8000/homeProva1/%d/calendars/%d/events/new/' % (group_id,calendar_id)
       print(url)
       now= datet.datetime.now().time()
       end_time = datet.datetime.now() + datet.timedelta(hours=1)
       end_time = end_time.strftime("%H:%M:%S")
       now = now.strftime("%H:%M:%S")
       dt = datet.datetime.today()
       dt = dt.strftime("%Y-%m-%d")
       print(now)
       print(end_time)
       print(dt)
       #di default la prenotazione viene effettuata per 1 ora
       print("dati form aggiunta evento")
       
       title = "Evento Node"
       description = "Evento prenotato in loco"
    
       payload = {"title": title, "day": dt, "start_time": now, "end_time": end_time, "notes":description}
       
       print("Payload")
       print(type(payload))
       print(payload)
       
       resp = requests.post(url,data=payload)
       content= response.content
       print (content)

def on_publish(client,userdata,result):            #create function for callback
   
    print(result)
    print("data published \n")
    pass

def init_client():
    #variabili di sistema settate 
    access_key = os.environ["AWS_ACCESS_KEY_ID"]
    secret_key = os.environ["AWS_SECRET_ACCESS_KEY"]
    port = 443

    region = "us-east-2"

    # This is specific to your AWS account
    host = "a3pwbt0axh6wnd-ats.iot.us-east-2.amazonaws.com".format(region)

    extra_headers = functools.partial(
        get_amazon_auth_headers,
        access_key,
        secret_key,
        region,
        host,
        port,
    )

    client = Client(transport="websockets")
  
    client.ws_set_options(headers=extra_headers)
    
    # Use client as normal from here
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish

    client.tls_set()
    client.connect(host, 443,60)
    
    return client
    #print("After the connection");
    #client.publish("ciao","stato:pubblico")
    #client.subscribe("group",0)
    #client.loop_start()

def publish(arg1,arg2,client):
    print(arg1)
    print(arg2)
    topic1 = "$aws/things/%d-%d/shadow/update" % (arg1,arg2)
    
    params= {'pk':arg1,'pk1':arg2}
    url = 'http:/127.0.0.1:8000/mqtt/%d/calendars/%d/events/' % (arg1,arg2)
    resp = requests.get(url=url)
    json1 = resp.json()
   
    j = json.dumps(json1)
    print("evento in json: " + j)
  
    print("try to publish")
    #client = init_client()
    #print("Post init_client()")
    client.publish(topic1, j)
    time.sleep(1)   

client = init_client()


