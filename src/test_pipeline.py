import pandas as pd
from src.pipelines.steps.data_ingestion import ingest_data
from src.pipelines.steps.preprocessing import preprocess_data
from src.pipelines.steps.data_exploration import explore_data
from src.pipelines.steps.predictions import make_predictions

def test_ingest():
    df = ingest_data()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty, "Ingested DataFrame is empty."

def test_preprocessing():
    raw_df = ingest_data()
    processed_df = preprocess_data(raw_df)
    assert isinstance(processed_df, pd.DataFrame)
    assert 'lemmatized_text' in processed_df.columns

def test_exploration():
    df = preprocess_data(ingest_data())
    results = explore_data(df)
    assert isinstance(results, dict)

def test_prediction():
    df = preprocess_data(ingest_data())
    exploration = explore_data(df)
    predictions = make_predictions(df, exploration)
    assert predictions is not None
