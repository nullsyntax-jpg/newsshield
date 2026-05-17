# NewsShield 🛡️

Brief description of what your project does. (e.g., An AI-driven pipeline for extracting features from GDELT news data and running Retrieval-Augmented Generation (RAG) models.)

## 📁 Project Structure

Notice: The `data/` and `paper/` directories are intentionally ignored by Git to keep the repository lightweight. 

* **`data/`**: (Hosted on Google Drive) Contains raw GDELT/GSCPI files and extracted parquet features.
* **`src/`**: Core Python scripts for data pulling, LLM extraction, feature engineering, and RAG modeling.
* **`notebooks/`**: Jupyter notebooks for Exploratory Data Analysis (EDA) and correlation testing. *(Note: Outputs are stripped before committing).*
* **`dashboard/`**: Streamlit/Flask app files for the frontend.
* **`paper/`**: (Hosted on Overleaf) LaTeX files for the academic write-up.

## 🚀 Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/nullsyntax-jpg/newsshield.git](https://github.com/nullsyntax-jpg/newsshield.git)
   cd newsshield
