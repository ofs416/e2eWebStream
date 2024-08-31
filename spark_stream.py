import logging

from cassandra.cluster import Cluster, ExecutionProfile
from cassandra.policies import DCAwareRoundRobinPolicy
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
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
        registereddate TEXT,
        phone TEXT,
        picture TEXT);
    """)
    print("Table created successfully.")


def insert_data(session, **kwargs):
    print("inserting data...")

    userid = kwargs.get('id')
    firstname = kwargs.get('firstname')
    lastname = kwargs.get('lastname')
    gender = kwargs.get('gender')
    address = kwargs.get('address')
    postcode = kwargs.get('postcode')
    email = kwargs.get('email')
    username = kwargs.get('username')
    dob = kwargs.get('dob')
    registereddate = kwargs.get('registereddate')
    phone = kwargs.get('phone')
    picture = kwargs.get('picture')

    session.execute("""
            INSERT INTO sparkstreams.createdusers(id, firstname, lastname, gender, address, 
            postcode, email, username, dob, registereddate, phone, picture)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (userid, firstname, lastname, gender, address,
          postcode, email, username, dob, registereddate, phone, picture))
    logging.info(f"Data inserted for {firstname} {lastname}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # create spark connection
    # noinspection PyInterpreter
    spark_conn = (SparkSession.builder
                    .master("spark://localhost:7077")
                    .appName('SparkDataStreaming')
                    .config('spark.jars.packages',
                            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1")
                    .getOrCreate())
    
    # .config('spark.cassandra.connection.host', 'localhost')

    #spark_conn.sparkContext.setLogLevel("ERROR")
    logging.info("Spark connection created successfully!")

    # connect to kafka with spark connection
    spark_df = (spark_conn.readStream
                .format('kafka')
                .option('kafka.bootstrap.servers', 'localhost:9092')
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
        StructField("registereddate", StringType(), False),
        StructField("phone", StringType(), False),
        StructField("picture", StringType(), False)
    ])

    # Select the data from the kafka stream
    selection_df = (spark_df.selectExpr("CAST(value AS STRING)")
                    .select(from_json(col("value"), schema).alias("data"))
                .select("data.*"))
    selection_df.printSchema()

    # Create a cassandra cluster and connect to start the session.
    #profile = ExecutionProfile(load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1'))
    #cas_cluster = Cluster(execution_profiles={'EXEC_PROFILE_DEFAULT': profile}, protocol_version=5)
    cas_cluster = Cluster(['localhost'])
    cassandra_session = cas_cluster.connect()
    create_keyspace(cassandra_session)
    create_table(cassandra_session)

    # Start the stream

    logging.info("Starting stream...")

    (selection_df.writeStream 
    .outputMode("append") 
    .format("console") 
    .start() 
    .awaitTermination())

    """
    streaming_query = (selection_df
                       .writeStream
                       .trigger(processingTime="5 seconds")
                       .format("org.apache.spark.sql.cassandra")
                       .option('checkpointLocation', '/tmp/checkpoint')
                       .option('keyspace', 'sparkstreams')
                       .option('table', 'createdusers')
                       .start())
    streaming_query.awaitTermination()
    """