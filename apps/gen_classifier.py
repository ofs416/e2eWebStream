from pyspark.sql import SparkSession

import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions

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
query = "SELECT picture, gender FROM createdusers"
rows = session.execute(query)

# Preprocess the data
def preprocess_image(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))  # Use PIL to open the image
    # Convert grayscale to RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
    print(f"raw size: {img.size}")
    img = img.resize((224, 224))  # Resize the image to the required size
    print(f"Image resize: {img.size}")
    img_array = image.img_to_array(img)
    print(f"Image array: {img_array.shape}")
    img_array = np.expand_dims(img_array, axis=0)
    print(f"Image expand: {img_array.shape}")
    img_array = preprocess_input(img_array)
    print(f"Image preprocess: {img_array.shape}")
    print("-----------------")
    return img_array

def preprocess_label(label):
    return 1 if label.lower() == 'male' else 0

images = []
labels = []

for row in rows:
    print(row.picture)
    images.append(preprocess_image(row.picture))
    labels.append(preprocess_label(row.gender))

images = np.array(images)
labels = np.array(labels)

# Split the data into training and validation sets
split_index = int(0.8 * len(images))
train_images, val_images = images[:split_index], images[split_index:]
train_labels, val_labels = labels[:split_index], labels[split_index:]

# Create TensorFlow datasets
train_dataset = tf.data.Dataset.from_tensor_slices((train_images, train_labels)).batch(32)
val_dataset = tf.data.Dataset.from_tensor_slices((val_images, val_labels)).batch(32)

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
    epochs=10
)

# Save the model
model.save('gender_classification_model.h5')

# Stop Spark session
spark.stop()