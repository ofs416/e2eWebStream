from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, rand, split
from pyspark.sql.types import StructType, StructField, StringType
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.feature import Word2Vec


# Function to process each batch
def process_batch(batch_df, batch_id):
    print(f"Processing batch {batch_id}")

    # Partition 1: Unlabeled data missing the gender
    unlabeled_data = batch_df.filter(col("gender").isNull())

    # Partition 2 and 3: Split remaining data
    remaining_data = batch_df.filter(col("gender").isNotNull())
    split_data = remaining_data.randomSplit([0.15, 0.85], seed=42)
    validation_data = split_data[0]
    training_data = split_data[1]

    # Update the model with training data
    global_model = pipeline.fit(training_data)

    # Make predictions on unlabeled data
    predictions = global_model.transform(unlabeled_data)
    updated_unlabeled_data = predictions.withColumn("gender", when(col("gender").isNull(), col("prediction")))

    # Combine the updated unlabeled data with the remaining data
    result_df = remaining_data.unionByName(updated_unlabeled_data.select(remaining_data.columns))

    # Optionally, you can assign the result_df back to batch_df if needed
    batch_df = result_df

    # Check current error on validation data
    validation_predictions = global_model.transform(validation_data)


    validation_data.show()
    # Display the selected columns
    validation_predictions.show()

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

    # Tokenize the text data
    selection_df = selection_df.withColumn("firstname_tokens", split(col("firstname"), ""))

    # Apply Word2Vec to convert tokens into vectors
    word2vec_firstname = Word2Vec(inputCol="firstname_tokens", outputCol="firstnameVec", vectorSize=100, minCount=0)

    # Index the gender column
    gender_indexer = StringIndexer(inputCol="gender", outputCol="genderIndex")

    # Combine the vectors into a single feature vector
    # assembler = VectorAssembler(inputCols=["firstnameVec"], outputCol="features")

    # Define the logistic regression model
    lr = LogisticRegression(featuresCol="firstnameVec", labelCol="genderIndex")

    # Create a pipeline with the stages
    pipeline = Pipeline(stages=[word2vec_firstname, gender_indexer, lr])

    # Initialize a global variable for the model
    global_model = None

    # Apply the model to predict missing values and update the model with new data
    query = selection_df.writeStream \
        .outputMode("append") \
        .trigger(processingTime='20 seconds') \
        .foreachBatch(process_batch) \
        .start()

    query.awaitTermination()
