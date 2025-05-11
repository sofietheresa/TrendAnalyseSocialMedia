from setuptools import setup, find_packages
from pathlib import Path

# Lade requirements.txt
requirements_path = Path(__file__).parent / "requirements.txt"
with requirements_path.open(encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="trend_analyse_social_media",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
)
