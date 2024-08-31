#!/bin/bash

# Initialize the Airflow database
airflow db migrate

# Create the Airflow user
airflow users create \
    --username "admin" \
    --password "admin" \
    --firstname "Admin" \
    --lastname "User" \
    --role "Admin" \
    --email "admin@example.com"

# Upgrade the Airflow database
airflow db upgrade

# Start the Airflow webserver
airflow scheduler & exec airflow webserver