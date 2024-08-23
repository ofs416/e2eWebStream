# Define the Bitnami Spark version as an argument
ARG BITNAMI_SPARK_VERSION=3.5.1

# Use the Bitnami Spark image with the specified version
FROM bitnami/spark:${BITNAMI_SPARK_VERSION}
ARG BITNAMI_SPARK_VERSION

# Install the corresponding PySpark version and other Python requirements
RUN pip install pyspark==${BITNAMI_SPARK_VERSION}

# Default command to run Spark master
CMD ["spark-class", "org.apache.spark.deploy.master.Master"]