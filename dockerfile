# Define the Bitnami Spark version as an argument
ARG BITNAMI_SPARK_VERSION=3.5.1
# Define the Apache Airflow version as an argument
ARG AIRFLOW_VERSION=2.10.0
# Define the Kafka version as an argument
ARG KAFKA_VERSION=3.7.0
# Define the PostgreSQL version as an argument
ARG POSTGRES_VERSION=14.0

# --------------------------------------------------------------------- #

# Use the Bitnami Kafka image with the specified version
FROM bitnami/kafka:${KAFKA_VERSION} AS kafka

# --------------------------------------------------------------------- #

# Use the Bitnami Spark image with the specified version
FROM bitnami/spark:${BITNAMI_SPARK_VERSION} AS spark
ARG BITNAMI_SPARK_VERSION
ARG KAFKA_VERSION

# Copy the requirements file
ADD requirements/spark.txt .

# Install the required Python packages
RUN pip install -r spark.txt pyspark==${BITNAMI_SPARK_VERSION}

# Install wget and create a directory for storing the Scala version file
USER root
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/* && \
    mkdir -p /opt/bitnami/spark/scala_version

# Extract Scala version from Spark and download the required JAR files
RUN SCALA_VERSION=$(/opt/bitnami/spark/bin/spark-submit --version 2>&1 | grep -oP 'Scala version \K[0-9]+\.[0-9]+') && \
    echo "Using Scala version: $SCALA_VERSION" && \
    wget -q -O /opt/bitnami/spark/jars/kafka-clients-${KAFKA_VERSION}.jar https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/${KAFKA_VERSION}/kafka-clients-${KAFKA_VERSION}.jar && \
    wget -q -O /opt/bitnami/spark/jars/spark-sql-kafka-0-10_${SCALA_VERSION}-${BITNAMI_SPARK_VERSION}.jar https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_${SCALA_VERSION}/${BITNAMI_SPARK_VERSION}/spark-sql-kafka-0-10_${SCALA_VERSION}-${BITNAMI_SPARK_VERSION}.jar && \
    wget -q -O /opt/bitnami/spark/jars/spark-streaming-kafka-0-10_${SCALA_VERSION}-${BITNAMI_SPARK_VERSION}.jar https://repo1.maven.org/maven2/org/apache/spark/spark-streaming-kafka-0-10_${SCALA_VERSION}/${BITNAMI_SPARK_VERSION}/spark-streaming-kafka-0-10_${SCALA_VERSION}-${BITNAMI_SPARK_VERSION}.jar && \
    wget -q -O /opt/bitnami/spark/jars/spark-token-provider-kafka-0-10_${SCALA_VERSION}-${BITNAMI_SPARK_VERSION}.jar https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_${SCALA_VERSION}/${BITNAMI_SPARK_VERSION}/spark-token-provider-kafka-0-10_${SCALA_VERSION}-${BITNAMI_SPARK_VERSION}.jar && \
    wget -q -O /opt/bitnami/spark/jars/commons-pool2-2.11.1.jar https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar

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
