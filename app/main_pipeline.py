"""
main_pipeline.py
Pipeline completa end-to-end
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from .config import OUTPUT_DIR
from .pdf_extractor import PDFExtractor
from .concept_extractor import ConceptExtractor
from .clusterer import HierarchicalClusterer
from .coverage_analyzer import CoverageAnalyzer
from .framework_comparator import FrameworkComparator


class FrameworkGenerationPipeline:
    def __init__(self, pdf_dir, existing_framework_path=None, output_dir=None, use_llm=True):
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        self.use_llm = use_llm
        
        self.pdf_extractor = PDFExtractor()
        self.concept_extractor = ConceptExtractor()
        self.clusterer = HierarchicalClusterer()
        
        self.comparator = None
        if existing_framework_path and Path(existing_framework_path).exists():
            self.comparator = FrameworkComparator(Path(existing_framework_path))
        
        self.syllabus_texts = {}
        self.syllabus_metadata = {}
        self.concept_collection = None
        self.framework = None
        self.coverages = None
        self.coverage_matrix = None
        self.comparison = None
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self, framework_name="Framework Empirico L-13", n_clusters=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print("\n" + "="*60)
        print("COREX - PIPELINE GENERAZIONE FRAMEWORK")
        print("="*60 + "\n")
        
        # FASE 1: Estrazione PDF
        print("[1/5] Estrazione testo da PDF...")
        extracted = self.pdf_extractor.extract_batch(self.pdf_dir)
        
        for es in extracted:
            if es.success:
                self.syllabus_texts[es.id] = es.text
                self.syllabus_metadata[es.id] = {
                    "university": es.university,
                    "professor": es.professor
                }
        
        print(f"      Estratti: {len(self.syllabus_texts)} syllabus\n")
        
        # FASE 2: Estrazione concetti
        print("[2/5] Estrazione concetti...")
        self.concept_collection = self.concept_extractor.process_multiple_syllabus(
            self.syllabus_texts, framework_name
        )
        print(f"      Concetti: {self.concept_collection.total_unique_concepts}")
        print(f"      CORE: {self.concept_collection.n_core}, COMUNE: {self.concept_collection.n_comune}\n")
        
        # FASE 3: Clustering
        print("[3/5] Clustering e generazione framework...")
        self.framework = self.clusterer.generate_framework(
            self.concept_collection, framework_name, n_clusters, self.use_llm
        )
        
        # FASE 4: Copertura
        print("\n[4/5] Analisi copertura...")
        analyzer = CoverageAnalyzer(self.framework)
        self.coverages, self.coverage_matrix = analyzer.analyze_collection(
            self.concept_collection, self.syllabus_metadata
        )
        print(f"      Analizzati {len(self.coverages)} syllabus\n")
        
        # FASE 5: Confronto
        if self.comparator:
            print("[5/5] Confronto con framework esistente...")
            self.comparison = self.comparator.compare(self.framework)
            print(f"      Similarità: {self.comparison.overall_similarity:.1%}\n")
        else:
            print("[5/5] Confronto: skipped (nessun framework esistente)\n")
        
        # Export
        results = self._export(timestamp)
        
        print("="*60)
        print("COMPLETATO")
        print("="*60)
        
        return results
    
    def _export(self, timestamp: str) -> dict:
        files = []
        
        # Framework
        fw_file = self.output_dir / f"framework_{timestamp}.json"
        fw_data = {
            "metadata": {
                "name": self.framework.name,
                "n_syllabus": self.framework.n_syllabus_analyzed,
                "generation_date": self.framework.generation_date.isoformat()
            },
            "statistics": {
                "total_concepts": self.framework.total_concepts,
                "n_modules": self.framework.n_modules
            },
            "modules": [
                {
                    "order": m.order,
                    "name": m.name,
                    "n_concepts": m.n_concepts,
                    "weight": round(m.suggested_weight, 4),
                    "concepts": [
                        {"name": c.canonical_name, "frequency": c.frequency_percentage}
                        for c in sorted(m.concepts, key=lambda x: -x.frequency_percentage)[:20]
                    ]
                }
                for m in sorted(self.framework.modules, key=lambda x: x.order)
            ]
        }
        with open(fw_file, "w", encoding="utf-8") as f:
            json.dump(fw_data, f, ensure_ascii=False, indent=2)
        files.append(fw_file.name)
        
        # Coverage
        cov_file = self.output_dir / f"coverage_{timestamp}.json"
        cov_data = {
            "matrix": self.coverage_matrix.to_dict(),
            "syllabus": [
                {"id": c.syllabus_id, "university": c.university, 
                 "coverage": c.overall_coverage}
                for c in sorted(self.coverages, key=lambda x: -x.overall_coverage)
            ]
        }
        with open(cov_file, "w", encoding="utf-8") as f:
            json.dump(cov_data, f, ensure_ascii=False, indent=2)
        files.append(cov_file.name)
        
        # Comparison
        if self.comparison:
            comp_file = self.output_dir / f"comparison_{timestamp}.json"
            with open(comp_file, "w", encoding="utf-8") as f:
                json.dump(self.comparison.to_dict(), f, ensure_ascii=False, indent=2)
            files.append(comp_file.name)
        
        return {"timestamp": timestamp, "output_dir": str(self.output_dir), "files": files}


def run_pipeline(pdf_dir, existing_framework=None, output_dir=None, 
                framework_name="Framework Empirico L-13", use_llm=True, n_clusters=None):
    pipeline = FrameworkGenerationPipeline(pdf_dir, existing_framework, output_dir, use_llm)
    return pipeline.run(framework_name, n_clusters)