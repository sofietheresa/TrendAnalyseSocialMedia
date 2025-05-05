import pandas as pd
import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer

# NLTK Ressourcen laden
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Pfad zur Datei (kann für Container oder lokal angepasst werden)
data_path = os.getenv("DATA_PATH", "/mnt/data/cleaned_social_media_data.csv")

# Daten einlesen
df = pd.read_csv(data_path)

# Textquellen kombinieren: Titel + Beschreibung
df["full_text"] = df["title"].fillna('') + " " + df["description/text"].fillna('')

# Initialisiere NLP-Tools
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

# Vorverarbeitungsfunktion
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", '', text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = nltk.word_tokenize(text)
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words and word.isalpha()]
    return tokens

# Tokenisierung
df["tokens"] = df["full_text"].apply(preprocess_text)

# Für TF-IDF müssen Tokens als String vorliegen
df["preprocessed_text"] = df["tokens"].apply(lambda x: ' '.join(x))

# TF-IDF Vektorisierung
tfidf_vectorizer = TfidfVectorizer(max_features=1000)
tfidf_matrix = tfidf_vectorizer.fit_transform(df["preprocessed_text"])

# Ausgabe als DataFrame (für Topic Modeling oder Klassifikation)
tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=tfidf_vectorizer.get_feature_names_out())

# Optional: Speichern für spätere Verarbeitung in Vektor-DB
tfidf_df.to_csv("/mnt/data/tfidf_features.csv", index=False)
