from pyspark.sql import SparkSession

import tensorflow as tf
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras import layers

import tf2onnx
import onnx

from cassandra.cluster import Cluster
import numpy as np
import requests
from io import BytesIO

from PIL import Image  # Ensure Pillow is installed


# Initialize Spark session
spark = SparkSession.builder.appName("GenderClassifier").getOrCreate()

# Connect to Cassandra
cluster = Cluster(['cassandra'])
session = cluster.connect('sparkstreams')

# Query to fetch data
query = "SELECT picture, gender FROM createdusers LIMIT 150"
rows = session.execute(query)

# Preprocess the data

def fetch_image(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))  # Use PIL to open the image
    # Convert grayscale to RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img = img.resize((224, 224))  # Resize the image to the required size
    img_array = image.img_to_array(img)
    return img_array


data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal_and_vertical"),
    layers.RandomRotation(0.2),
    layers.RandomZoom(0.1),
])

def preprocess_label(label):
    return 1 if label.lower() == 'male' else 0


images = []
labels = []

for row in rows:
    images.append(fetch_image(row.picture))
    labels.append(preprocess_label(row.gender))

# Convert lists to TensorFlow datasets
image_dataset = tf.data.Dataset.from_tensor_slices(images)
label_dataset = tf.data.Dataset.from_tensor_slices(labels)
# Combine image and label datasets
dataset = tf.data.Dataset.zip((image_dataset, label_dataset))

batch_size = 32
AUTOTUNE = tf.data.AUTOTUNE

def prepare(ds, shuffle=False, augment=False):
    # Resize and rescale all datasets.
    ds = ds.map(lambda x, y: (preprocess_input(x), y), num_parallel_calls=AUTOTUNE)

    if shuffle:
        ds = ds.shuffle(1000)  

    # Batch all datasets.
    ds = ds.batch(batch_size)

    # Use data augmentation only on the training set.
    if augment:
        ds = ds.map(lambda x, y: (data_augmentation(x, training=True), y), 
                    num_parallel_calls=AUTOTUNE)

    # Use buffered prefetching on all datasets.
    return ds.prefetch(buffer_size=AUTOTUNE)

# Split the dataset into train and validation sets
train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size

train_dataset = dataset.take(train_size)
val_dataset = dataset.skip(train_size)

# Prepare the train and validation datasets
train_dataset = prepare(train_dataset, shuffle=True, augment=True)
val_dataset = prepare(val_dataset)

# Load the MobileNetV2 model without the top layer
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

# Add custom layers on top of MobileNetV2
x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(1024, activation='relu')(x)
predictions = Dense(1, activation='sigmoid')(x)

# Create the final model
model = Model(inputs=base_model.input, outputs=predictions)

# Freeze the layers of MobileNetV2
for layer in base_model.layers:
    layer.trainable = False

# Compile the model
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Train the model
model.fit(
    train_dataset,
    validation_data=val_dataset,
    epochs=40
)

model.summary()

# Convert the model to ONNX format
onnx_model, _ = tf2onnx.convert.from_keras(model)

# Save the ONNX model
onnx.save(onnx_model, '/opt/bitnami/spark/Models/gender_classification_model.onnx')

# Stop Spark session
spark.stop()
