import mlflow

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.register_model("runs:/<run_id>/model", "tiktok-classifier")
