"""
BIMRepair — Model Training Step
Trains a retrieval index (TF-IDF) and a surrogate classifier (RandomForest) 
on the synthetic dataset to predict repair confidence and auto-apply safety.
"""
import os
import sys
import json
import joblib
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import BASE_DIR, DATA_DIR

ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
MODEL_DIR = os.path.join(ARTIFACTS_DIR, "model")

def train_model():
    print("Starting Model Training...")
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    train_path = os.path.join(DATA_DIR, "synthetic_cases_train.jsonl")
    val_path = os.path.join(DATA_DIR, "synthetic_cases_val.jsonl")
    
    if not os.path.exists(train_path):
        print(f"Error: Training data not found at {train_path}")
        return
        
    def load_jsonl(path):
        data = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line))
        return data

    train_cases = load_jsonl(train_path)
    val_cases = load_jsonl(val_path)
    
    print(f"Loaded {len(train_cases)} train cases and {len(val_cases)} val cases.")

    # 1. Train TF-IDF Vectorizer
    print("Training TF-IDF Vectorizer...")
    train_texts = [c.get("search_text", c["defect_description"]) for c in train_cases]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(train_texts)
    
    # 2. Train Surrogate Classifier (Predicts safe_to_auto_apply)
    print("Training Surrogate Classifier (LogisticRegression)...")
    y_train = [1 if c["safe_to_auto_apply"] else 0 for c in train_cases]
    clf = LogisticRegression(random_state=42, max_iter=1000)
    clf.fit(tfidf_matrix, y_train)
    
    # Validate
    val_texts = [c.get("search_text", c["defect_description"]) for c in val_cases]
    y_val = [1 if c["safe_to_auto_apply"] else 0 for c in val_cases]
    X_val = vectorizer.transform(val_texts)
    y_pred = clf.predict(X_val)
    acc = accuracy_score(y_val, y_pred)
    print(f"Validation Accuracy on 'safe_to_auto_apply': {acc:.2%}")
    
    # 3. Save Artifacts
    print("Saving artifacts...")
    joblib.dump(vectorizer, os.path.join(MODEL_DIR, "vectorizer.joblib"))
    joblib.dump(tfidf_matrix, os.path.join(MODEL_DIR, "tfidf_index.joblib"))
    joblib.dump(clf, os.path.join(MODEL_DIR, "classifier.joblib"))
    
    # Save the training cases as the runtime library for retrieval
    with open(os.path.join(MODEL_DIR, "train_cases.json"), "w", encoding="utf-8") as f:
        json.dump(train_cases, f, ensure_ascii=False)
        
    # Create manifest
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "model_type": "TF-IDF + RandomForest Surrogate",
        "training_samples": len(train_cases),
        "validation_samples": len(val_cases),
        "metrics": {
            "val_accuracy": round(acc, 4)
        },
        "artifacts": [
            "model/vectorizer.joblib",
            "model/tfidf_index.joblib",
            "model/classifier.joblib",
            "model/train_cases.json"
        ],
        "features": len(vectorizer.vocabulary_)
    }
    
    with open(os.path.join(ARTIFACTS_DIR, "train_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Training complete. Artifacts saved to {ARTIFACTS_DIR}")

if __name__ == "__main__":
    train_model()
