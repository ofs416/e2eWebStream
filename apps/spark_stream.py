import logging

from cassandra.cluster import Cluster, DCAwareRoundRobinPolicy, ExecutionProfile, EXEC_PROFILE_DEFAULT
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType


def create_keyspace(session):
    """Like a schema for cassandra."""
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS sparkstreams
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'};
    """)
    print("Keyspace created successfully!")


def create_table(session):
    session.execute("""
        CREATE TABLE IF NOT EXISTS sparkstreams.createdusers (
        id UUID PRIMARY KEY,
        firstname TEXT,
        lastname TEXT,
        gender TEXT,
        address TEXT,
        postcode TEXT,
        email TEXT,
        username TEXT,
        registrationdate TEXT,
        phone TEXT,
        picture TEXT);
    """)
    print("Table created successfully.")


if __name__ == "__main__":

    # Set up logging
    logging.getLogger().setLevel(logging.WARNING)

    # create spark connection
    # noinspection PyInterpreter
    spark_conn = (SparkSession.builder
                    .master("spark://spark-master:7077")
                    .appName('SparkDataStreaming')
                    .config('spark.cassandra.connection.port', '9042')
                    .config('spark.cassandra.connection.host', 'cassandra')
                    .getOrCreate())
    
    logging.info("Spark connection created successfully!")

    # connect to kafka with spark connection
    spark_df = (spark_conn.readStream
                .format('kafka')
                .option('kafka.bootstrap.servers', 'kafka:9092')
                .option('subscribe', 'usercreated')
                .option('startingOffsets', 'earliest')
                .load())
    logging.info("kafka dataframe created successfully")

    # Define schema for the data
    schema = StructType([
        StructField("id", StringType(), False),
        StructField("firstname", StringType(), False),
        StructField("lastname", StringType(), False),
        StructField("gender", StringType(), False),
        StructField("address", StringType(), False),
        StructField("postcode", StringType(), False),
        StructField("email", StringType(), False),
        StructField("username", StringType(), False),
        StructField("registrationdate", StringType(), False),
        StructField("phone", StringType(), False),
        StructField("picture", StringType(), False)
    ])

    # Select the data from the kafka stream
    selection_d = (spark_df.selectExpr("CAST(value AS STRING)")
                    .select(from_json(col("value"), schema).alias("data"))
                .select("data.*"))
    selection_df = selection_d.filter(selection_d.id.isNotNull())
    selection_df.printSchema()


    # Define the execution profile
    execution_profile = ExecutionProfile(
        load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1')
    )

    # Create a cluster instance with the authentication provider and execution profile
    cas_cluster = Cluster(
        contact_points=['cassandra'],
        execution_profiles={EXEC_PROFILE_DEFAULT: execution_profile},
        protocol_version=5  # Set this to the version supported by your Cassandra cluster
    )
    cassandra_session = cas_cluster.connect()
    create_keyspace(cassandra_session)
    create_table(cassandra_session)

    # Start the stream
    logging.info("Starting stream...")

    # Write the data to the console
    # (selection_df.writeStream 
    # .trigger(processingTime="10 seconds")
    # .outputMode("append") 
    # .format("console") 
    # .start()    
    # .awaitTermination())

    # Write the data to the cassandra table
    streaming_query = (selection_df
                        .writeStream
                        .format("org.apache.spark.sql.cassandra")
                        .option('checkpointLocation', '/tmp/checkpoint')
                        .option('keyspace', 'sparkstreams')
                        .option('table', 'createdusers')
                        .start())
    streaming_query.awaitTermination()
