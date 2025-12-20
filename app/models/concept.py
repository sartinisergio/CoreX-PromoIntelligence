"""
models/concept.py
Modelli dati per concetti estratti
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class ConceptClassification(str, Enum):
    CORE = "CORE"
    COMUNE = "COMUNE"
    SPECIFICO = "SPECIFICO"
    UNCLASSIFIED = "UNCLASSIFIED"


class EntityType(str, Enum):
    REACTION = "REACTION"
    MECHANISM = "MECHANISM"
    FUNCTIONAL_GROUP = "FUNCTIONAL_GROUP"
    COMPOUND_CLASS = "COMPOUND_CLASS"
    BIOMOLECULE = "BIOMOLECULE"
    STEREOCHEMISTRY = "STEREOCHEMISTRY"
    TECHNIQUE = "TECHNIQUE"
    RULE = "RULE"
    GENERIC = "GENERIC"


class RawConcept(BaseModel):
    text: str
    source_syllabus_id: str
    position_in_text: int
    context: str
    entity_type: EntityType = EntityType.GENERIC
    confidence: float = 1.0


class Concept(BaseModel):
    id: str
    canonical_name: str
    variants: list[str] = Field(default_factory=list)
    source_syllabus_ids: list[str] = Field(default_factory=list)
    frequency_absolute: int = 0
    frequency_percentage: float = 0.0
    classification: ConceptClassification = ConceptClassification.UNCLASSIFIED
    entity_type: EntityType = EntityType.GENERIC
    parent_module_id: Optional[str] = None
    embedding: Optional[list[float]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    manually_validated: bool = False
    
    def add_variant(self, variant: str):
        if variant.lower() != self.canonical_name.lower():
            if variant not in self.variants:
                self.variants.append(variant)
    
    def add_source(self, syllabus_id: str):
        if syllabus_id not in self.source_syllabus_ids:
            self.source_syllabus_ids.append(syllabus_id)
            self.frequency_absolute = len(self.source_syllabus_ids)
    
    def compute_classification(self, total_syllabus: int, 
                                threshold_core: float = 0.85,
                                threshold_comune: float = 0.40):
        if total_syllabus == 0:
            return
        
        self.frequency_percentage = (self.frequency_absolute / total_syllabus) * 100
        
        if self.frequency_absolute / total_syllabus >= threshold_core:
            self.classification = ConceptClassification.CORE
        elif self.frequency_absolute / total_syllabus >= threshold_comune:
            self.classification = ConceptClassification.COMUNE
        else:
            self.classification = ConceptClassification.SPECIFICO


class ConceptCollection(BaseModel):
    id: str
    name: str
    discipline: str = "Chimica Organica"
    degree_class: str = "L-13"
    concepts: list[Concept] = Field(default_factory=list)
    total_syllabus_analyzed: int = 0
    total_raw_concepts_extracted: int = 0
    total_unique_concepts: int = 0
    n_core: int = 0
    n_comune: int = 0
    n_specifico: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    
    def add_concept(self, concept: Concept):
        self.concepts.append(concept)
        self.total_unique_concepts = len(self.concepts)
    
    def compute_statistics(self):
        self.n_core = sum(1 for c in self.concepts if c.classification == ConceptClassification.CORE)
        self.n_comune = sum(1 for c in self.concepts if c.classification == ConceptClassification.COMUNE)
        self.n_specifico = sum(1 for c in self.concepts if c.classification == ConceptClassification.SPECIFICO)
    
    def get_by_classification(self, classification: ConceptClassification) -> list[Concept]:
        return [c for c in self.concepts if c.classification == classification]