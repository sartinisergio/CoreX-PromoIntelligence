"""
coverage_analyzer.py
Analisi copertura syllabus vs framework
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class SyllabusCoverage:
    syllabus_id: str
    university: str
    professor: str
    module_coverage: dict[str, float] = field(default_factory=dict)
    overall_coverage: float = 0.0
    concepts_found: list[str] = field(default_factory=list)
    core_concepts_found: list[str] = field(default_factory=list)
    core_concepts_missing: list[str] = field(default_factory=list)
    n_concepts_found: int = 0
    n_core_found: int = 0
    n_core_missing: int = 0


@dataclass
class CoverageMatrix:
    syllabus_ids: list[str]
    module_ids: list[str]
    module_names: list[str]
    matrix: np.ndarray = None
    module_avg_coverage: dict[str, float] = field(default_factory=dict)
    syllabus_avg_coverage: dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "syllabus_ids": self.syllabus_ids,
            "module_ids": self.module_ids,
            "module_names": self.module_names,
            "matrix": self.matrix.tolist() if self.matrix is not None else [],
            "module_avg_coverage": self.module_avg_coverage,
            "syllabus_avg_coverage": self.syllabus_avg_coverage
        }


class CoverageAnalyzer:
    def __init__(self, framework):
        self.framework = framework
        self._concept_to_module = {}
        self._core_concepts = set()
        
        for m in framework.modules:
            for c in m.concepts:
                self._concept_to_module[c.canonical_name.lower()] = m.id
                for v in c.variants:
                    self._concept_to_module[v.lower()] = m.id
                if hasattr(c.classification, 'value'):
                    if c.classification.value == "CORE":
                        self._core_concepts.add(c.canonical_name.lower())
    
    def analyze_syllabus(self, syllabus_id: str, concepts: list[str], 
                        university: str = "", professor: str = "") -> SyllabusCoverage:
        cov = SyllabusCoverage(syllabus_id=syllabus_id, university=university, professor=professor)
        concepts_lower = set(c.lower() for c in concepts)
        
        for m in self.framework.modules:
            m_concepts = set(c.canonical_name.lower() for c in m.concepts)
            for c in m.concepts:
                for v in c.variants:
                    m_concepts.add(v.lower())
            
            found = concepts_lower & m_concepts
            pct = (len(found) / len(m.concepts) * 100) if m.concepts else 0
            cov.module_coverage[m.id] = round(pct, 1)
        
        all_fw = set(self._concept_to_module.keys())
        cov.concepts_found = list(concepts_lower & all_fw)
        cov.n_concepts_found = len(cov.concepts_found)
        
        cov.core_concepts_found = list(concepts_lower & self._core_concepts)
        cov.core_concepts_missing = list(self._core_concepts - concepts_lower)
        cov.n_core_found = len(cov.core_concepts_found)
        cov.n_core_missing = len(cov.core_concepts_missing)
        
        total_weight = sum(m.suggested_weight for m in self.framework.modules)
        if total_weight > 0:
            weighted = sum(cov.module_coverage.get(m.id, 0) * m.suggested_weight for m in self.framework.modules)
            cov.overall_coverage = round(weighted / total_weight, 1)
        
        return cov
    
    def analyze_collection(self, collection, metadata: Optional[dict] = None):
        metadata = metadata or {}
        concepts_by_syl = {}
        
        for c in collection.concepts:
            for sid in c.source_syllabus_ids:
                if sid not in concepts_by_syl:
                    concepts_by_syl[sid] = []
                concepts_by_syl[sid].append(c.canonical_name)
        
        coverages = []
        for sid, concepts in concepts_by_syl.items():
            meta = metadata.get(sid, {})
            cov = self.analyze_syllabus(sid, concepts, 
                                       meta.get("university", ""), meta.get("professor", ""))
            coverages.append(cov)
        
        matrix = self._build_matrix(coverages)
        return coverages, matrix
    
    def _build_matrix(self, coverages: list[SyllabusCoverage]) -> CoverageMatrix:
        syl_ids = [c.syllabus_id for c in coverages]
        mod_ids = [m.id for m in self.framework.modules]
        mod_names = [m.name for m in self.framework.modules]
        
        mat = np.zeros((len(syl_ids), len(mod_ids)))
        for i, cov in enumerate(coverages):
            for j, mid in enumerate(mod_ids):
                mat[i, j] = cov.module_coverage.get(mid, 0)
        
        result = CoverageMatrix(syllabus_ids=syl_ids, module_ids=mod_ids, 
                               module_names=mod_names, matrix=mat)
        
        for j, mid in enumerate(mod_ids):
            result.module_avg_coverage[mid] = float(np.mean(mat[:, j]))
        for i, sid in enumerate(syl_ids):
            result.syllabus_avg_coverage[sid] = float(np.mean(mat[i, :]))
        
        return result