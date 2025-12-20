"""
embeddings.py
Gestione embeddings semantici - Versione TF-IDF (senza PyTorch)
"""

import numpy as np
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer


class EmbeddingModel:
    """Modello di embedding basato su TF-IDF (leggero, senza PyTorch)."""
    
    def __init__(self, model_name: str = None):
        self.dimension = 300
        self.vectorizer = TfidfVectorizer(
            max_features=self.dimension,
            ngram_range=(1, 2),
            lowercase=True,
            sublinear_tf=True
        )
        self._fitted = False
        print("Usando TF-IDF per gli embeddings (modalità leggera)")
    
    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.array([])
        
        if not self._fitted:
            embeddings = self.vectorizer.fit_transform(texts).toarray()
            self._fitted = True
        else:
            embeddings = self.vectorizer.transform(texts).toarray()
        
        return embeddings.astype(np.float32)
    
    def pairwise_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        normalized = embeddings / norms
        return np.dot(normalized, normalized.T)


class ConceptEmbedder:
    """Embedder specializzato per concetti chimici."""
    
    def __init__(self, model: Optional[EmbeddingModel] = None):
        self.model = model or EmbeddingModel()
        self._cache = {}
        self._all_texts = []
        self._all_ids = []
    
    def embed_concepts(self, concepts: list, use_variants: bool = True) -> dict[str, np.ndarray]:
        texts = []
        ids = []
        
        for c in concepts:
            text = c.canonical_name
            if use_variants and c.variants:
                text += " " + " ".join(c.variants[:3])
            texts.append(text)
            ids.append(c.id)
        
        if texts:
            embeddings = self.model.encode(texts)
            for i, cid in enumerate(ids):
                self._cache[cid] = embeddings[i]
        
        return {c.id: self._cache.get(c.id) for c in concepts if c.id in self._cache}
    
    def get_similarity_matrix(self, concepts: list) -> tuple[np.ndarray, list[str]]:
        # Genera tutti gli embeddings insieme per TF-IDF
        texts = []
        ids = []
        
        for c in sorted(concepts, key=lambda x: x.id):
            text = c.canonical_name
            if c.variants:
                text += " " + " ".join(c.variants[:3])
            texts.append(text)
            ids.append(c.id)
        
        # Encode tutti insieme (importante per TF-IDF)
        embeddings = self.model.encode(texts)
        
        # Aggiorna cache
        for i, cid in enumerate(ids):
            self._cache[cid] = embeddings[i]
        
        # Calcola matrice similarità
        sim_matrix = self.model.pairwise_similarity_matrix(embeddings)
        
        return sim_matrix, ids
