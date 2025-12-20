"""
clusterer.py
Clustering gerarchico dei concetti
"""

import numpy as np
import hashlib
from typing import Optional
from collections import defaultdict

from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform

try:
    from sklearn.metrics import silhouette_score, silhouette_samples
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from .config import MIN_CLUSTER_SIZE, TARGET_N_MODULES
from .models.concept import ConceptCollection
from .models.framework import Module, Framework, ModuleClassification
from .embeddings import ConceptEmbedder
from .cooccurrence import CooccurrenceAnalyzer, build_combined_similarity
from .llm_client import get_llm_client


class HierarchicalClusterer:
    def __init__(self, semantic_weight: float = 0.6, cooccurrence_weight: float = 0.4):
        self.embedder = ConceptEmbedder()
        self.cooccurrence = CooccurrenceAnalyzer()
        self.llm = get_llm_client()
        self.semantic_weight = semantic_weight
        self.cooccurrence_weight = cooccurrence_weight
        
        self._similarity_matrix = None
        self._concept_ids = []
        self._id_counter = 0
    
    def _generate_id(self, prefix: str, text: str) -> str:
        self._id_counter += 1
        return f"{prefix}_{hashlib.md5(text.encode()).hexdigest()[:8]}"
    
    def build_similarity_matrix(self, collection: ConceptCollection) -> np.ndarray:
        concepts = collection.concepts
        print(f"Costruzione matrice similarità per {len(concepts)} concetti...")
        
        semantic_matrix, concept_ids = self.embedder.get_similarity_matrix(concepts)
        self._concept_ids = concept_ids
        
        self.cooccurrence.build_cooccurrence_matrix(collection)
        cooccurrence_matrix = self.cooccurrence.get_normalized_matrix()
        
        coocc_ids = self.cooccurrence.get_concept_ids()
        if coocc_ids != concept_ids:
            id_to_idx = {cid: i for i, cid in enumerate(coocc_ids)}
            reorder = [id_to_idx[cid] for cid in concept_ids]
            cooccurrence_matrix = cooccurrence_matrix[np.ix_(reorder, reorder)]
        
        self._similarity_matrix = build_combined_similarity(
            semantic_matrix, cooccurrence_matrix,
            self.semantic_weight, self.cooccurrence_weight
        )
        
        return self._similarity_matrix
    
    def perform_clustering(self, n_clusters: Optional[int] = None, method: str = "ward") -> np.ndarray:
        if self._similarity_matrix is None:
            raise ValueError("Costruisci prima la matrice")
        
        n_clusters = n_clusters or TARGET_N_MODULES
        print(f"Clustering (target: {n_clusters})...")
        
        distance = 1 - self._similarity_matrix
        np.fill_diagonal(distance, 0)
        distance = np.maximum((distance + distance.T) / 2, 0)
        
        condensed = squareform(distance, checks=False)
        linkage_matrix = linkage(condensed, method=method)
        labels = fcluster(linkage_matrix, n_clusters, criterion="maxclust")
        
        print(f"  Cluster generati: {len(set(labels))}")
        return labels
    
    def evaluate_clustering(self, labels: np.ndarray) -> dict:
        metrics = {"n_clusters": len(set(labels)), "cluster_sizes": {}}
        
        for label in set(labels):
            metrics["cluster_sizes"][int(label)] = int(np.sum(labels == label))
        
        if HAS_SKLEARN and len(set(labels)) > 1:
            try:
                distance = 1 - self._similarity_matrix
                avg_sil = silhouette_score(distance, labels, metric="precomputed")
                metrics["avg_silhouette"] = float(avg_sil)
            except:
                metrics["avg_silhouette"] = 0.0
        
        return metrics
    
    def build_modules(self, collection: ConceptCollection, labels: np.ndarray, use_llm: bool = True) -> list[Module]:
        concepts_by_id = {c.id: c for c in collection.concepts}
        clusters = defaultdict(list)
        
        for i, cid in enumerate(self._concept_ids):
            label = int(labels[i])
            concept = concepts_by_id.get(cid)
            if concept:
                clusters[label].append(concept)
        
        modules = []
        
        for cluster_id, concepts in sorted(clusters.items()):
            sorted_concepts = sorted(concepts, key=lambda c: c.frequency_percentage, reverse=True)
            concept_names = [c.canonical_name for c in sorted_concepts[:10]]
            
            if use_llm and self.llm.is_available():
                name, desc = self.llm.label_cluster(concept_names)
            else:
                name = self._fallback_name(concept_names)
                desc = ""
            
            module = Module(
                id=self._generate_id("mod", name),
                name=name,
                description=desc,
                cluster_id=cluster_id
            )
            
            for c in sorted_concepts:
                module.add_concept(c)
            
            module.compute_suggested_weight(collection.total_unique_concepts)
            modules.append(module)
        
        return modules
    
    def _fallback_name(self, names: list[str]) -> str:
        if not names:
            return "Modulo"
        
        keywords = {
            "stereo": "Stereochimica", "chiral": "Stereochimica",
            "alcan": "Idrocarburi", "alchen": "Idrocarburi",
            "aromat": "Aromatici", "carbonil": "Carbonilici",
            "carboidrat": "Carboidrati", "ammin": "Composti Azotati",
            "lipid": "Lipidi", "protein": "Proteine",
        }
        
        for name in names:
            for k, v in keywords.items():
                if k in name.lower():
                    return v
        
        return names[0].title()
    
    def order_modules(self, modules: list[Module], use_llm: bool = True) -> list[Module]:
        if use_llm and self.llm.is_available():
            names = [m.name for m in modules]
            ordered = self.llm.suggest_module_hierarchy(names)
            order_map = {info["name"]: info for info in ordered}
            
            for m in modules:
                if m.name in order_map:
                    m.order = order_map[m.name].get("order", 0)
                    m.group = order_map[m.name].get("group", "")
        else:
            for i, m in enumerate(sorted(modules, key=lambda x: -x.avg_frequency)):
                m.order = i + 1
        
        return sorted(modules, key=lambda m: m.order)
    
    def generate_framework(
        self, collection: ConceptCollection,
        name: str = "Framework Chimica Organica L-13",
        n_clusters: Optional[int] = None,
        use_llm: bool = True
    ) -> Framework:
        print(f"\n{'='*60}")
        print(f"GENERAZIONE FRAMEWORK: {name}")
        print(f"{'='*60}\n")
        
        self.build_similarity_matrix(collection)
        
        if n_clusters is None:
            n_clusters = TARGET_N_MODULES
        
        labels = self.perform_clustering(n_clusters)
        metrics = self.evaluate_clustering(labels)
        
        print(f"Silhouette: {metrics.get('avg_silhouette', 0):.3f}")
        
        modules = self.build_modules(collection, labels, use_llm)
        modules = self.order_modules(modules, use_llm)
        
        framework = Framework(
            id=self._generate_id("fw", name),
            name=name,
            n_syllabus_analyzed=collection.total_syllabus_analyzed
        )
        
        for m in modules:
            m.silhouette_score = metrics.get("silhouette_per_cluster", {}).get(m.cluster_id, 0)
            framework.add_module(m)
        
        framework.normalize_weights()
        
        print(f"\nFramework generato: {framework.n_modules} moduli, {framework.total_concepts} concetti")
        
        return framework


def cluster_concepts_to_framework(collection: ConceptCollection, name: str = "Framework", use_llm: bool = True) -> Framework:
    clusterer = HierarchicalClusterer()
    return clusterer.generate_framework(collection, name, use_llm=use_llm)