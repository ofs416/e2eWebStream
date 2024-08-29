#!/bin/bash

# Initialize the Airflow database
airflow db migrate

# Create the Airflow user
airflow users create \
    --username "$AIRFLOW_USER" \
    --password "$AIRFLOW_PASSWORD" \
    --firstname "$AIRFLOW_FIRSTNAME" \
    --lastname "$AIRFLOW_LASTNAME" \
    --role "$AIRFLOW_ROLE" \
    --email "$AIRFLOW_EMAIL"

# Upgrade the Airflow database
airflow db upgrade

# Start the Airflow webserver
exec airflow webserver