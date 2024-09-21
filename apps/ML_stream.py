import requests
from io import BytesIO

from PIL import Image  # Ensure Pillow is installed

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, udf
from pyspark.sql.types import StructType, StructField, StringType

from tensorflow import keras
from keras.preprocessing import image
from keras.applications.mobilenet_v2 import preprocess_input

import numpy as np


def predict_gender(image_url):
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))  # Use PIL to open the image
        img = img.resize((224, 224))  # Resize the image to the required size
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        prediction = model.predict(img_array)[0, 0]
        return "male" if prediction >= 0.5 else "female"
    except Exception as e:
        return str(e)
    
# Register UDF
predict_gender_udf = udf(predict_gender, StringType())

    
if __name__ == "__main__":

    # Load pre-trained model
    model = keras.models.load_model('Models/gender_classification_model.keras')

    # Define schema for the data
    schema = StructType([
        StructField("id", StringType(), False),
        StructField("firstname", StringType(), False),
        StructField("lastname", StringType(), False),
        StructField("gender", StringType(), False),
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
    df = (spark.readStream
                .format('kafka')
                .option('kafka.bootstrap.servers', 'kafka:9092')
                .option('subscribe', 'usercreated')
                .option('startingOffsets', 'earliest')
                .option('failOnDataLoss', 'false')
                .load())
    

    # Select and filter data
    df = (df.selectExpr("CAST(value AS STRING)")
                .select(from_json(col("value"), schema).alias("data"))
                .select("data.*"))

    
    
    # Apply UDF to the streaming DataFrame
    df = df.withColumn("predicted_gender", predict_gender_udf(df["picture"]))

    # Apply the model to predict missing values and update the model with new data
    query = df.writeStream \
        .outputMode("append") \
        .trigger(processingTime="5 seconds") \
        .option("checkpointLocation", "/tmp/checkpoints") \
        .format("console") \
        .start()

    query.awaitTermination()
    spark.stop()