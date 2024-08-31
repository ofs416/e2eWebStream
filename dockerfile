# Define the Bitnami Spark version as an argument
ARG BITNAMI_SPARK_VERSION=3.5.1
# Define the Apache Airflow version as an argument
ARG AIRFLOW_VERSION=2.10.0
# Define the Kafka version as an argument
ARG KAFKA_VERSION=3.5.1
# Define the PostgreSQL version as an argument
ARG POSTGRES_VERSION=14.0

# --------------------------------------------------------------------- #

# Use the Bitnami Kafka image with the specified version
FROM bitnami/kafka:${KAFKA_VERSION} AS kafka

# --------------------------------------------------------------------- #

# Use the Bitnami Spark image with the specified version
FROM bitnami/spark:${BITNAMI_SPARK_VERSION} AS spark
ARG BITNAMI_SPARK_VERSION

# Copy the requirements file
ADD requirements/spark.txt .

# Install the required Python packages
RUN pip install -r spark.txt pyspark==${BITNAMI_SPARK_VERSION}

# --------------------------------------------------------------------- #

# Use the Apache Airflow image with the specified version
FROM apache/airflow:${AIRFLOW_VERSION}-python3.11 AS airflow

# Copy the requirements file
ADD requirements/airflow.txt .

# Install the required Python packages
RUN pip install -r airflow.txt 

# Copy the entrypoint script
COPY --chmod=755 scripts/entrypoint.sh /entrypoint.sh

# Set the entrypoint to the script
ENTRYPOINT ["/entrypoint.sh"]

# --------------------------------------------------------------------- #

# Use the official PostgreSQL image with the specified version
FROM postgres:${POSTGRES_VERSION} AS postgres
