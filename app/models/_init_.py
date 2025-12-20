"""
Modelli dati per CoreX
"""

from .concept import Concept, ConceptCollection, RawConcept, ConceptClassification, EntityType
from .framework import Module, Framework, ModuleClassification

__all__ = [
    "Concept", "ConceptCollection", "RawConcept", 
    "ConceptClassification", "EntityType",
    "Module", "Framework", "ModuleClassification"
]