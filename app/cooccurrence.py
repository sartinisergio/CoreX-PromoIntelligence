"""
cooccurrence.py
Analisi co-occorrenza concetti
"""

import numpy as np
from collections import defaultdict
from typing import Optional


class CooccurrenceAnalyzer:
    def __init__(self):
        self._matrix: Optional[np.ndarray] = None
        self._concept_ids: list[str] = []
        self._id_to_index: dict[str, int] = {}
    
    def build_cooccurrence_matrix(self, collection) -> np.ndarray:
        concepts = collection.concepts
        n = len(concepts)
        
        self._concept_ids = [c.id for c in concepts]
        self._id_to_index = {cid: i for i, cid in enumerate(self._concept_ids)}
        self._matrix = np.zeros((n, n), dtype=np.float32)
        
        syllabus_to_concepts = defaultdict(set)
        for concept in concepts:
            for sid in concept.source_syllabus_ids:
                syllabus_to_concepts[sid].add(concept.id)
        
        for sid, cids in syllabus_to_concepts.items():
            cids_list = list(cids)
            for i, cid1 in enumerate(cids_list):
                idx1 = self._id_to_index[cid1]
                for cid2 in cids_list[i:]:
                    idx2 = self._id_to_index[cid2]
                    self._matrix[idx1, idx2] += 1
                    if idx1 != idx2:
                        self._matrix[idx2, idx1] += 1
        
        return self._matrix
    
    def get_normalized_matrix(self) -> np.ndarray:
        if self._matrix is None:
            raise ValueError("Costruisci prima la matrice")
        
        n = self._matrix.shape[0]
        normalized = np.zeros_like(self._matrix)
        diag = np.diag(self._matrix)
        
        for i in range(n):
            for j in range(i, n):
                co_occ = self._matrix[i, j]
                union = diag[i] + diag[j] - co_occ
                if union > 0:
                    normalized[i, j] = co_occ / union
                    normalized[j, i] = normalized[i, j]
        
        return normalized
    
    def get_concept_ids(self) -> list[str]:
        return self._concept_ids.copy()


def build_combined_similarity(
    semantic: np.ndarray, cooccurrence: np.ndarray,
    sem_weight: float = 0.6, coocc_weight: float = 0.4
) -> np.ndarray:
    return sem_weight * semantic + coocc_weight * cooccurrence