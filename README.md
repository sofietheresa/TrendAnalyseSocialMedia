
# TrendSage – Social Media Trend Discovery for Publishing

**TrendSage** is an open-source machine learning project designed to automatically discover trending topics and sentiments from social media platforms such as Twitter and Reddit. This tool is intended for publishers, authors, content creators, and media professionals who want to identify emerging trends before they go mainstream.

The project focuses on unsupervised topic modeling, sentiment analysis, and intuitive data visualization – all using free, open-source Python tools.

---

## Project Goals

- Extract fresh social media data on a daily basis
- Identify and group emerging topics (topic modeling)
- Analyze the sentiment of users around each topic
- Visualize trends and sentiment evolution in a clean dashboard
- Stay lean and implementable by a single developer in 4–6 weeks

---

##  Project Structure

```text
trendsage/
│
├── data/                 # Raw and processed data (CSV, JSON, etc.)
│   ├── raw/
│   └── processed/
│
├── notebooks/            # Jupyter Notebooks for development & testing
│   ├── 01_data_collection.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_topic_modeling.ipynb
│   ├── 04_sentiment_analysis.ipynb
│   └── 05_visualization.ipynb
│
├── app/                  # Streamlit dashboard application
│   ├── dashboard.py
│   └── utils.py
│
├── models/               # Saved models (if any fine-tuning occurs)
│
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── config.yaml           # Configuration for API keys, settings etc.
```

---

##  Methodology

### 1. **Data Collection**
- Twitter data collected via `snscrape` or Twitter API
- Reddit posts extracted using the `PRAW` API
- Only textual content is extracted (tweets/posts), along with timestamps and metadata

### 2. **Text Preprocessing**
- Lowercasing, removing stopwords, emojis, links, and mentions
- Tokenization using `spaCy` or `NLTK`
- Prepared for embedding and modeling

### 3. **Topic Modeling**
- Sentence embeddings generated via `sentence-transformers` (`MiniLM` model)
- Dimensionality reduced using `UMAP`
- Clustering with `HDBSCAN`
- Topic generation with `BERTopic`

### 4. **Sentiment Analysis**
- Pre-trained transformer model from HuggingFace (`cardiffnlp/twitter-roberta-base-sentiment`)
- Each tweet/post classified as Positive / Neutral / Negative
- Sentiment trends tracked over time and per topic

### 5. **Visualization**
- Interactive dashboard built using `Streamlit`
- Key views:
  - Trending topics (word clouds, topic labels)
  - Sentiment timeline
  - Top keywords and posts per topic
  - Searchable trend explorer

---

##  Technologies Used

| Task | Tools |
|------|-------|
| Data Collection | `snscrape`, `PRAW`, `pandas` |
| NLP | `spaCy`, `re`, `NLTK`, `transformers` |
| Topic Modeling | `sentence-transformers`, `BERTopic`, `HDBSCAN`, `UMAP` |
| Sentiment | HuggingFace Transformers |
| Visualization | `Streamlit`, `Plotly`, `Altair` |
| Storage | CSV, JSON, SQLite (optional) |

---

##  Status

- [x] Project initialized
- [ ] Twitter/Reddit data collection implemented
- [ ] Topic modeling pipeline complete
- [ ] Sentiment analysis integrated
- [ ] Streamlit dashboard MVP live
