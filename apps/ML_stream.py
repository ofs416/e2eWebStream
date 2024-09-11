from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, rand
from pyspark.sql.types import StructType, StructField, StringType
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.evaluation import MulticlassClassificationEvaluator


# Function to update the model with new data
def update_model(batch_df, batch_id):
    global global_model
    global_model = pipeline.fit(batch_df)

# Function to make predictions using the current model
def make_predictions(batch_df, batch_id):
    global global_model
    predictions = global_model.transform(batch_df)
    filled_df = predictions.withColumn("prediction", when(col("gender").isNull(), col("prediction")).otherwise(col("gender")))
    return filled_df

# Function to process each batch
def process_batch(batch_df, batch_id):
    global selection_df
    # Partition 1: Unlabeled data missing the gender
    unlabeled_data = batch_df.filter(col("gender").isNull())
    
    # Partition 2 and 3: Split remaining data
    remaining_data = batch_df.filter(col("gender").isNotNull())
    split_data = remaining_data.randomSplit([0.1, 0.9], seed=42)
    validation_data = split_data[0]
    training_data = split_data[1]

    # Update the model with training data
    update_model(training_data, batch_id)
    
    # Make predictions on unlabeled data
    updated_unlabeled_data = make_predictions(unlabeled_data, batch_id)
    
    # Update selection_df with predictions
    selection_df = selection_df.union(updated_unlabeled_data)
    
    # Check current error on validation data
    validation_predictions = global_model.transform(validation_data)
    evaluator = MulticlassClassificationEvaluator(labelCol="genderIndex", predictionCol="prediction", metricName="accuracy")
    accuracy = evaluator.evaluate(validation_predictions)
    print(f"Batch {batch_id}: Validation Accuracy = {accuracy}")

    
if __name__ == "__main__":
    # Define schema for the data
    schema = StructType([
        StructField("id", StringType(), False),
        StructField("firstname", StringType(), False),
        StructField("lastname", StringType(), False),
        StructField("gender", StringType(), False),
        StructField("prediction", StringType(), False),
        StructField("address", StringType(), False),
        StructField("postcode", StringType(), False),
        StructField("email", StringType(), False),
        StructField("username", StringType(), False),
        StructField("registrationdate", StringType(), False),
        StructField("phone", StringType(), False),
        StructField("picture", StringType(), False)
    ])

    # Initialize Spark session
    spark = SparkSession.builder \
        .master("spark://spark-master:7077") \
        .appName('MLStreaming') \
        .config("spark.sql.adaptive.enabled", "false") \
        .getOrCreate()

    # Set up logging
    spark.sparkContext.setLogLevel("WARN")

    # Connect to Kafka with Spark connection
    spark_df = (spark.readStream
                .format('kafka')
                .option('kafka.bootstrap.servers', 'kafka:9092')
                .option('subscribe', 'usercreated')
                .option('startingOffsets', 'earliest')
                .load())

    # Select and filter data
    selection_d = (spark_df.selectExpr("CAST(value AS STRING)")
                .select(from_json(col("value"), schema).alias("data"))
                .select("data.*"))

    # Artificially make 1 in 10 rows have a null value in the gender column
    selection_df = selection_d.withColumn("gender", when(rand() < 0.1, None).otherwise(col("gender")))

    selection_df.printSchema()

    # Preprocess data
    gender_indexer = StringIndexer(inputCol="gender", outputCol="genderIndex")
    firstname_indexer = StringIndexer(inputCol="firstname", outputCol="firstnameIndex")
    username_indexer = StringIndexer(inputCol="username", outputCol="usernameIndex")
    assembler = VectorAssembler(inputCols=["firstnameIndex", "usernameIndex"], outputCol="features")

    # Define the model
    lr = LogisticRegression(featuresCol="features", labelCol="genderIndex")

    # Create a pipeline
    pipeline = Pipeline(stages=[gender_indexer, firstname_indexer, username_indexer, assembler, lr])

    # Initialize a global variable for the model
    global_model = None

    # Apply the model to predict missing values and update the model with new data
    query = selection_df.writeStream \
        .outputMode("append") \
        .trigger(processingTime='10 seconds') \
        .foreachBatch(process_batch) \
        .format("console") \
        .start()

    query.awaitTermination()
