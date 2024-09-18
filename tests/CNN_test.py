import requests
from io import BytesIO

from PIL import Image  # Ensure Pillow is installed

from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input, decode_predictions

import numpy as np


def preprocess_image(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))  # Use PIL to open the image
    img = img.resize((224, 224))  # Resize the image to the required size
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    return img_array

def predict_gender(image_url):
    img_array = preprocess_image(image_url)
    predictions = model.predict(img_array)
    decoded_predictions = decode_predictions(predictions, top=1)[0]
    return decoded_predictions
    

test_url = "https://randomuser.me/api/portraits/med/men/52.jpg"

# Load pre-trained model
model = ResNet50(weights='imagenet')


print(predict_gender(test_url))