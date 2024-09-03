import json
import requests
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from kafka import KafkaProducer
import time
import logging

default_args = {
    'owner': 'Oskar',
    'start_date': datetime(2024, 8, 9, 10, 00)
}

def get_data():
    """Fetches data from the api (random user generator)."""
    return requests.get('https://randomuser.me/api/').json()['results'][0]

def format_data(response):
    """Formats the data."""
    data = {}
    location = response["location"]
    data["id"] = response["login"]["uuid"]
    data["firstname"] = response["name"]["first"]
    data["lastname"] = response["name"]["last"]
    data["gender"] = response["gender"]
    data["address"] = f'{location["street"]["number"]} {location["street"]["name"]}' \
                      f'{location["city"]}, {location["state"]}, {location["country"]}'
    data["postcode"] = location["postcode"]
    data["email"] = response["email"]
    data["username"] = response["login"]["username"]
    data["dob"] = response["dob"]["date"]
    data["registrationdate"] = response["registered"]["date"]
    data["phone"] = response["phone"]
    data["picture"] = response["picture"]["medium"]

    return data

def stream_data():
    """Streams data from the free open-source random user generator."""

    producer = KafkaProducer(bootstrap_servers=['kafka:9092'], max_block_ms=5000)
    curr_time = time.time()

    while True:
        if time.time() > curr_time + 60: # 1 minute
            break

        try:
            response = format_data(get_data())
            producer.send('usercreated', json.dumps(response).encode("utf-8"))
        except Exception as e:
            logging.error(f"Error: {e}")
            continue


with DAG('user_automation',
         default_args=default_args,
            catchup=False) as dag:

    streaming_task = PythonOperator(
        task_id='stream_data_from_api',
        python_callable=stream_data,
    )