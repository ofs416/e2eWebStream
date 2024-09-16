# Step 1: Install gensim
# Run this command in your terminal
# pip install gensim

# Step 2: Download the pre-trained GloVe embeddings
# You can download the GloVe Twitter embeddings from:
# http://nlp.stanford.edu/data/glove.twitter.27B.zip

# Step 3: Load the GloVe model directly using gensim
from gensim.models import KeyedVectors

glove_input_file = '/opt/bitnami/spark/Models/GloVe/glove.twitter.27B.25d.txt'
word2vec_model = KeyedVectors.load_word2vec_format(glove_input_file, binary=False, no_header=True)

# Step 4: Use the model
# Example: Get the vector for a name
try:
    name_vector = word2vec_model['nurse']
    print(name_vector)
except KeyError:
    print("Key 'John' not present in the embeddings")

# Example: Find most similar names
try:
    similar_names = word2vec_model.most_similar('nurse')
    print(similar_names)
except KeyError:
    print("Key 'John' not present in the embeddings")