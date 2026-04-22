"""
BIMRepair — Case Library & TF-IDF Retrieval
Loads the synthetic case library and retrieves similar past repairs.
"""
import os
import json
import joblib
import logging
from sklearn.metrics.pairwise import cosine_similarity

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import BASE_DIR

logger = logging.getLogger(__name__)


class CaseLibrary:
    """Case-based retrieval engine using pre-trained TF-IDF model artifacts."""
    
    def __init__(self, case_library_path=None):
        # We ignore case_library_path and strictly load from artifacts/model
        model_dir = os.path.join(BASE_DIR, "artifacts", "model")
        logger.info(f"Loading pre-trained model artifacts from {model_dir}")
        
        vectorizer_path = os.path.join(model_dir, "vectorizer.joblib")
        index_path = os.path.join(model_dir, "tfidf_index.joblib")
        cases_path = os.path.join(model_dir, "train_cases.json")
        clf_path = os.path.join(model_dir, "classifier.joblib")
        
        if not os.path.exists(vectorizer_path):
            raise FileNotFoundError(f"Model artifacts not found. Please run 'python src/train_model.py' first.")
            
        self.vectorizer = joblib.load(vectorizer_path)
        self.tfidf_matrix = joblib.load(index_path)
        self.classifier = joblib.load(clf_path)
        
        with open(cases_path, "r", encoding="utf-8") as f:
            self.cases = json.load(f)
            
        logger.info(f"Loaded {len(self.cases)} training cases and model artifacts.")
    
    def retrieve(self, defect, top_k=3, min_similarity=0.1):
        """
        Retrieve top-K similar cases for a given defect.
        
        Args:
            defect: Defect object with defect_type, entity_type, description
            top_k: Number of cases to retrieve
            min_similarity: Minimum cosine similarity threshold
        
        Returns:
            List of (case_dict, similarity_score) tuples
        """
        # Build query from defect attributes
        query_parts = [
            defect.defect_type,
            defect.entity_type,
            defect.description,
        ]
        # Add context info if available
        ctx = defect.context
        if "property_set" in ctx:
            query_parts.append(ctx["property_set"])
        if "property_name" in ctx:
            query_parts.append(ctx["property_name"])
        
        query_text = " ".join(query_parts)
        query_vec = self.vectorizer.transform([query_text])
        
        # Compute similarities
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Get top-K indices sorted by similarity
        top_indices = similarities.argsort()[::-1][:top_k * 2]  # Get extra for filtering
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= min_similarity and len(results) < top_k:
                results.append((self.cases[idx], score))
        
        # Boost exact defect_type matches
        boosted = []
        for case, score in results:
            if case["defect_type"] == defect.defect_type:
                boosted.append((case, min(score * 1.2, 1.0)))  # 20% boost
            else:
                boosted.append((case, score))
        
        boosted.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Retrieved {len(boosted)} cases for defect {defect.defect_id} "
                     f"(best sim: {boosted[0][1]:.3f})" if boosted else "No matches")
        
        return boosted[:top_k]
    
    def get_case_by_id(self, case_id):
        """Get a specific case by ID."""
        for case in self.cases:
            if case["case_id"] == case_id:
                return case
        return None
