from pipelines.zenml_pipeline import trend_analysis_pipeline

if __name__ == "__main__":
    pipeline = trend_analysis_pipeline()
    pipeline.run()
