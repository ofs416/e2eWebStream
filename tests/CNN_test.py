import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.imagenet_utils import preprocess_input
import tensorflow as tf
from PIL import Image
import requests
from io import BytesIO
import time

def preprocess_image(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))  # Use PIL to open the image
    img = img.resize((224, 224))  # Resize the image to the required size
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    return img_array

def predict_gender_batch(image_urls):
    img_arrays = []
    for image_url in image_urls:
        img_array = preprocess_image(image_url)
        img_arrays.append(img_array)
    
    batch_array = np.vstack(img_arrays)
    predictions = model.predict(batch_array)
    
    results = ["male" if pred >= 0.5 else "female" for pred in predictions[:, 0]]
    return results

# Load pre-trained model
model = tf.keras.models.load_model('Models/gender_classification_model.keras')

test_urls = [
    "https://randomuser.me/api/portraits/med/men/52.jpg",
    "https://randomuser.me/api/portraits/med/women/52.jpg",
    "https://randomuser.me/api/portraits/med/men/52.jpg",
    "https://randomuser.me/api/portraits/med/women/52.jpg",
    "https://randomuser.me/api/portraits/med/men/52.jpg",
    "https://randomuser.me/api/portraits/med/women/52.jpg"
]

start_time = time.time()
print(predict_gender_batch(test_urls))
end_time = time.time()

print(f"Time taken: {end_time - start_time} seconds")