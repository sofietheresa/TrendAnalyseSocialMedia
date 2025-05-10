from setuptools import setup, find_packages

setup(
    name="trend_analyse_social_media",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "zenml",
        "pandas",
        "numpy",
        "scikit-learn",
        "nltk",
        "textblob",
        "tensorflow",
        "python-dotenv",
        "requests",
        "beautifulsoup4",
        "selenium",
        "webdriver-manager",
        "matplotlib",
        "seaborn",
        "joblib",
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0"
    ],
    python_requires=">=3.8",
) 