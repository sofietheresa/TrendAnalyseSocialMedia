import pandas as pd
from pipelines.steps.data_ingestion import ingest_data
from pipelines.steps.preprocessing import preprocess_data
from pipelines.steps.data_exploration import explore_data
from pipelines.steps.predictions import make_predictions

def test_ingest():
    df = ingest_data().run()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty, "Ingested DataFrame is empty."

def test_preprocessing():
    raw_df = ingest_data().run()
    processed_df = preprocess_data().run(raw_df)
    assert isinstance(processed_df, pd.DataFrame)
    assert 'lemmatized_text' in processed_df.columns

def test_exploration():
    df = preprocess_data().run(ingest_data().run())
    results = explore_data().run(df)
    assert isinstance(results, dict)

def test_prediction():
    df = preprocess_data().run(ingest_data().run())
    exploration = explore_data().run(df)
    predictions = make_predictions().run(df, exploration)
    assert predictions is not None
