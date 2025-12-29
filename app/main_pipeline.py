"""
CoreX - Main Pipeline
Orchestrazione completa dell'analisi programmi
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from app.pdf_extractor import PDFExtractor
from app.concept_extractor import ConceptExtractor
from app.clusterer import HierarchicalClusterer
from app.coverage_analyzer import CoverageAnalyzer
from app.framework_adapter import FrameworkAdapter


class FrameworkGenerationPipeline:
    """Pipeline completa per generazione framework da programmi"""
    
    def __init__(self, materia: str = "", use_llm: bool = True):
        self.materia = materia
        self.use_llm = use_llm
        self.pdf_extractor = PDFExtractor()
        self.concept_extractor = ConceptExtractor(use_llm=use_llm, materia=materia)
        self.clusterer = HierarchicalClusterer()
        self.framework_adapter = FrameworkAdapter()
    
    def extract_from_folder(self, folder_path: Path) -> Tuple[Dict[str, str], Dict[str, Dict]]:
        """Estrae testo da tutti i PDF in una cartella"""
        syllabus_texts = {}
        syllabus_metadata = {}
        
        pdf_files = list(folder_path.glob("*.pdf"))
        
        for pdf_path in pdf_files:
            result = self.pdf_extractor.extract(pdf_path)
            if result.success:
                syllabus_texts[result.id] = result.text
                syllabus_metadata[result.id] = {
                    "university": result.university,
                    "professor": result.professor,
                    "source_path": str(pdf_path)
                }
        
        return syllabus_texts, syllabus_metadata
    
    def extract_from_files(self, pdf_paths: List[Path]) -> Tuple[Dict[str, str], Dict[str, Dict]]:
        """Estrae testo da una lista di PDF"""
        syllabus_texts = {}
        syllabus_metadata = {}
        
        for pdf_path in pdf_paths:
            result = self.pdf_extractor.extract(pdf_path)
            if result.success:
                syllabus_texts[result.id] = result.text
                syllabus_metadata[result.id] = {
                    "university": result.university,
                    "professor": result.professor,
                    "classe": pdf_path.parent.name,
                    "source_path": str(pdf_path)
                }
        
        return syllabus_texts, syllabus_metadata
    
    def run_analysis(
        self,
        syllabus_texts: Dict[str, str],
        syllabus_metadata: Dict[str, Dict],
        project_name: str,
        n_clusters: Optional[int] = None,
        use_llm: bool = True
    ) -> Tuple:
        """Esegue l'analisi completa"""
        
        # Aggiorna l'estrattore se use_llm è cambiato
        if use_llm != self.use_llm:
            self.use_llm = use_llm
            self.concept_extractor = ConceptExtractor(use_llm=use_llm, materia=self.materia)
        
        # Step 1: Estrazione concetti
        concept_collection = self.concept_extractor.process_multiple_syllabus(
            syllabus_texts, 
            project_name
        )
        
        # Step 2: Clustering e generazione framework
        framework = self.clusterer.generate_framework(
            concept_collection,
            project_name,
            n_clusters,
            use_llm
        )
        
        # Step 3: Analisi copertura
        analyzer = CoverageAnalyzer(framework)
        coverages, coverage_matrix = analyzer.analyze_collection(
            concept_collection,
            syllabus_metadata
        )
        
        return concept_collection, framework, coverages, coverage_matrix
    
    def generate_zanichelli_output(
        self,
        materia: str,
        concept_collection,
        coverages: List,
        syllabus_metadata: Dict[str, Dict],
        classi_analizzate: List[str]
    ) -> Dict:
        """Genera output nel formato Zanichelli"""
        
        # Prepara lista concetti aggregati
        concepts = [
            {
                "name": c.canonical_name,
                "frequency": c.frequency_percentage,
                "n_syllabus": c.frequency_absolute
            }
            for c in concept_collection.concepts
        ]
        
        # Prepara dati syllabus CON i concetti specifici di ciascuno
        syllabus_data = []
        for cov in coverages:
            meta = syllabus_metadata.get(cov.syllabus_id, {})
            
            # Recupera i concetti specifici di questo syllabus
            syllabus_concepts = []
            for concept in concept_collection.concepts:
                if cov.syllabus_id in concept.source_syllabus_ids:
                    syllabus_concepts.append(concept.canonical_name.lower())
            
            syllabus_data.append({
                "id": cov.syllabus_id,
                "university": cov.university,
                "professor": cov.professor,
                "classe": meta.get("classe", "N/D"),
                "coverage": cov.overall_coverage,
                "concepts": syllabus_concepts,
                "n_concepts": len(syllabus_concepts)
            })
        
        return self.framework_adapter.generate_zanichelli_output(
            materia=materia,
            concepts=concepts,
            syllabus_data=syllabus_data,
            classi_analizzate=classi_analizzate
        )
    
    def run_full_pipeline(
        self,
        pdf_paths: List[Path],
        materia: str,
        project_name: str,
        classi_analizzate: List[str],
        n_clusters: Optional[int] = None,
        use_llm: bool = True,
        existing_framework_path: Optional[Path] = None
    ) -> Dict:
        """
        Pipeline completa: da PDF a output Zanichelli
        """
        
        # Aggiorna materia nell'estrattore
        if materia != self.materia:
            self.materia = materia
            self.concept_extractor = ConceptExtractor(use_llm=use_llm, materia=materia)
        
        # Estrazione testi
        syllabus_texts, syllabus_metadata = self.extract_from_files(pdf_paths)
        
        if not syllabus_texts:
            raise ValueError("Nessun testo estratto dai PDF")
        
        # Analisi
        concept_collection, framework, coverages, coverage_matrix = self.run_analysis(
            syllabus_texts,
            syllabus_metadata,
            project_name,
            n_clusters,
            use_llm
        )
        
        # Output Zanichelli
        zanichelli_output = self.generate_zanichelli_output(
            materia=materia,
            concept_collection=concept_collection,
            coverages=coverages,
            syllabus_metadata=syllabus_metadata,
            classi_analizzate=classi_analizzate
        )
        
        # Confronto con framework esistente (se fornito)
        comparison = None
        if existing_framework_path and existing_framework_path.exists():
            from app.framework_comparator import FrameworkComparator
            comparator = FrameworkComparator(existing_framework_path)
            comparison = comparator.compare(framework)
        
        return {
            "concept_collection": concept_collection,
            "framework": framework,
            "coverages": coverages,
            "coverage_matrix": coverage_matrix,
            "zanichelli_output": zanichelli_output,
            "comparison": comparison,
            "metadata": {
                "materia": materia,
                "project_name": project_name,
                "classi_analizzate": classi_analizzate,
                "n_syllabus": len(syllabus_texts),
                "n_concepts": concept_collection.total_unique_concepts,
                "n_modules": framework.n_modules,
                "generation_date": datetime.now().isoformat()
            }
        }
