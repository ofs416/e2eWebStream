# Define the Bitnami Spark version as an argument
ARG BITNAMI_SPARK_VERSION=3.5.1
# Define the Apache Airflow version as an argument
ARG AIRFLOW_VERSION=2.10.0

# --------------------------------------------------------------------- #

# Use the Bitnami Spark image with the specified version
FROM bitnami/spark:${BITNAMI_SPARK_VERSION}

# Install the corresponding PySpark version and other Python requirements
RUN pip install pyspark==${BITNAMI_SPARK_VERSION}

# --------------------------------------------------------------------- #

# Use the Apache Airflow image with the specified version
FROM apache/airflow:${AIRFLOW_VERSION}-python3.11

# Copy the requirements file
ADD requirements.txt .

# Install the required Python packages
RUN pip install -r requirements.txt 

# Copy the entrypoint script
COPY --chmod=755 scripts/entrypoint.sh /entrypoint.sh

# Set the entrypoint to the script
ENTRYPOINT ["/entrypoint.sh"]
