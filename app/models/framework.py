"""
models/framework.py
Modelli dati per framework e moduli
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

from .concept import Concept, ConceptClassification


class ModuleClassification(str, Enum):
    CORE = "CORE"
    COMUNE = "COMUNE"
    SPECIFICO = "SPECIFICO"


class Module(BaseModel):
    id: str
    name: str
    description: str = ""
    concept_ids: list[str] = Field(default_factory=list)
    concepts: list[Concept] = Field(default_factory=list)
    n_concepts: int = 0
    avg_frequency: float = 0.0
    classification: ModuleClassification = ModuleClassification.COMUNE
    suggested_weight: float = 0.0
    order: int = 0
    group: str = ""
    cluster_id: int = -1
    silhouette_score: float = 0.0
    
    def add_concept(self, concept: Concept):
        if concept.id not in self.concept_ids:
            self.concept_ids.append(concept.id)
            self.concepts.append(concept)
            self.n_concepts = len(self.concepts)
            self._update_statistics()
    
    def _update_statistics(self):
        if not self.concepts:
            return
        
        self.avg_frequency = sum(c.frequency_percentage for c in self.concepts) / len(self.concepts)
        
        n_core = sum(1 for c in self.concepts if c.classification == ConceptClassification.CORE)
        n_specifico = sum(1 for c in self.concepts if c.classification == ConceptClassification.SPECIFICO)
        
        if n_core / len(self.concepts) > 0.5:
            self.classification = ModuleClassification.CORE
        elif n_specifico / len(self.concepts) > 0.5:
            self.classification = ModuleClassification.SPECIFICO
        else:
            self.classification = ModuleClassification.COMUNE
    
    def compute_suggested_weight(self, total_concepts: int):
        if total_concepts == 0:
            return
        base_weight = self.n_concepts / total_concepts
        if self.classification == ModuleClassification.CORE:
            base_weight *= 1.2
        elif self.classification == ModuleClassification.SPECIFICO:
            base_weight *= 0.8
        self.suggested_weight = max(0.02, min(0.15, base_weight))


class Framework(BaseModel):
    id: str
    name: str
    version: str = "1.0"
    description: str = ""
    discipline: str = "Chimica Organica"
    degree_class: str = "L-13"
    n_syllabus_analyzed: int = 0
    generation_date: datetime = Field(default_factory=datetime.now)
    modules: list[Module] = Field(default_factory=list)
    total_concepts: int = 0
    n_modules: int = 0
    n_core_modules: int = 0
    n_comune_modules: int = 0
    n_specifico_modules: int = 0
    avg_silhouette_score: float = 0.0
    comparison_results: Optional[dict] = None
    
    def add_module(self, module: Module):
        self.modules.append(module)
        self._update_statistics()
    
    def _update_statistics(self):
        self.n_modules = len(self.modules)
        self.total_concepts = sum(m.n_concepts for m in self.modules)
        self.n_core_modules = sum(1 for m in self.modules if m.classification == ModuleClassification.CORE)
        self.n_comune_modules = sum(1 for m in self.modules if m.classification == ModuleClassification.COMUNE)
        self.n_specifico_modules = sum(1 for m in self.modules if m.classification == ModuleClassification.SPECIFICO)
        if self.modules:
            self.avg_silhouette_score = sum(m.silhouette_score for m in self.modules) / len(self.modules)
    
    def normalize_weights(self):
        total_weight = sum(m.suggested_weight for m in self.modules)
        if total_weight > 0:
            for module in self.modules:
                module.suggested_weight /= total_weight
    
    def to_summary_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "discipline": self.discipline,
            "degree_class": self.degree_class,
            "n_syllabus_analyzed": self.n_syllabus_analyzed,
            "generation_date": self.generation_date.isoformat(),
            "statistics": {
                "total_concepts": self.total_concepts,
                "n_modules": self.n_modules,
                "n_core_modules": self.n_core_modules,
                "n_comune_modules": self.n_comune_modules,
                "n_specifico_modules": self.n_specifico_modules,
            },
            "modules": [
                {
                    "id": m.id,
                    "name": m.name,
                    "order": m.order,
                    "n_concepts": m.n_concepts,
                    "classification": m.classification.value,
                    "suggested_weight": round(m.suggested_weight, 4)
                }
                for m in sorted(self.modules, key=lambda x: x.order)
            ]
        }