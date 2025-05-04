import nltk

# Download required NLTK resources
resources = [
    'punkt',
    'stopwords',
    'wordnet',
    'averaged_perceptron_tagger',
    'punkt_tab'
]

for resource in resources:
    print(f"Downloading {resource}...")
    nltk.download(resource)

print("All NLTK resources downloaded successfully!") 