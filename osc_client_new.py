import subprocess
import sys
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
try:
    from pythonosc import udp_client
except ImportError as e:
    install('python-osc')
    from pythonosc import udp_client

import argparse
import random
import requests
import time
import concurrent
from concurrent.futures import ThreadPoolExecutor
import json
import pandas as pd
import numpy as np

def get_data(entityId):
    url2 = f"http://thingsboard.pidev.arup.com:80/api/plugins/telemetry/DEVICE/{entityId}/values/timeseries"
    response2 = requests.request("GET", url2, headers=headers)
    return response2.json()

def get_metric(list_ids):
    result = []
    threads = 20
    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_url = {executor.submit(get_data, char) 
                         for char in list_ids}
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                data = future.result()
                result.append(data)
            except Exception as e:
                print('Looks like something went wrong:', e)
    return result

def get_token():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = '{\n  "username": "Maxine.Setiawan@arup.com",\n  "password": "thingsboard-api-0921"\n}'
    response = requests.post('https://thingsboard.pidev.arup.com:443/api/auth/login', headers=headers, data=data)
    TOKEN = response.json()['token']
    headers['Authorization'] = f'Bearer  {TOKEN}'
    
    return TOKEN, headers

def get_device_ids():
    TOKEN, headers = get_token()
    #get device keys 
    url = "http://thingsboard.pidev.arup.com:80/api/tenant/devices?page=0&pageSize=10000"
    payload = ""
    response = requests.request("GET", url, headers=headers, data=payload)
    df_devices = pd.json_normalize(response.json()['data'])

    # get device ids
    iot_ids = df_devices[df_devices.name.str.contains('iotdesk-80.1')].loc[:,['name','id.id']].set_index('name').to_dict()['id.id']
    people_counter_ids = df_devices[df_devices.type == "CogniPoint People Counter"].loc[:,['name','id.id']].set_index('name').to_dict()['id.id']
    traffic_counter_ids = df_devices[df_devices.type == "CogniPoint People Traffic Counter"].loc[:,['name','id.id']].set_index('name').to_dict()['id.id']
    return iot_ids, people_counter_ids, traffic_counter_ids
    
def get_all_data():
    global iot_data
    traffic_data = get_metric(list(traffic_counter_ids.values()))
    ppl_data = get_metric(list(people_counter_ids.values()))
    iot_data = get_metric(list(iot_ids.values()))

    n_people = int(sum([float(x['count'][0]['value']) for x in ppl_data if 'count' in x]))
    n_traffic = int(sum([float(x['count'][0]['value']) for x in traffic_data if 'count' in x]))
    iot_dict = dict(zip(sensors, list(map(get_val, sensors))))
    return n_people, n_traffic, iot_dict
    
def get_val(sense):
    return round(np.mean([float(x[sense][0]['value']) for x in iot_data if sense in x]), 2)
    
sensors = ['Sound_Pressure_Sensor', 'Air_Quality_Sensor', 'Air_Quality_Sensor_Accuracy', 'Temperature_Sensor', 'Humidity_Sensor', 'Air_Pressure_Sensor']


if __name__ == "__main__":

    TOKEN, headers = get_token()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="172.30.16.1", help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=4560, help="The port the OSC server is listening on")
    args = parser.parse_args()
    
    client = udp_client.SimpleUDPClient(args.ip, args.port)
    iot_ids, people_counter_ids, traffic_counter_ids = get_device_ids()

    while True:
        try:
            n_people, n_traffic, iot_dict = get_all_data()
    
            client.send_message('/trigger/soundpressure', round(iot_dict[sensors[0]], 2))
            client.send_message('/trigger/airquality',  round(iot_dict[sensors[1]], 2))
            client.send_message('/trigger/temperature',  round(iot_dict[sensors[3]], 2))
            client.send_message('/trigger/humidity',  round(iot_dict[sensors[4]], 2))
            client.send_message('/trigger/airpressure',  round(iot_dict[sensors[5]], 2))
            client.send_message('/trigger/people', n_people)
            client.send_message('/trigger/traffic',  n_traffic)

        except Exception as e:
            print(e)
            continue
        time.sleep(20)
