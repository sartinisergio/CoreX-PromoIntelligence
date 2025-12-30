"""
CoreX - Multiclass Pipeline v2.0
Analisi multiclasse CON MAPPING SU FRAMEWORK IDEALE
Confronta i programmi di più classi rispetto ai moduli del framework ideale
"""

from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from app.pdf_extractor import PDFExtractor
from app.concept_extractor import ConceptExtractor
from app.clusterer import HierarchicalClusterer
from app.coverage_analyzer import CoverageAnalyzer
from app.framework_adapter import FrameworkAdapter


@dataclass
class ModuleCoverage:
    """Copertura di un modulo del framework ideale per una classe"""
    module_id: int
    module_name: str
    coverage_percentage: float
    matched_concepts: List[Dict]  # Concetti trovati che matchano questo modulo
    missing_contents: List[str]   # Contenuti del modulo non coperti
    n_contents_covered: int
    n_contents_total: int


@dataclass
class ClassAnalysisResult:
    """Risultato analisi per singola classe rispetto al framework ideale"""
    classe: str
    n_syllabus: int
    total_concepts_extracted: int
    overall_coverage: float  # Copertura media sul framework ideale
    module_coverages: Dict[int, ModuleCoverage]  # Copertura per ogni modulo
    syllabus_metadata: List[Dict]


@dataclass
class ModuleMulticlassAnalysis:
    """Analisi di un modulo del framework attraverso tutte le classi"""
    module_id: int
    module_name: str
    core_contents: List[str]
    
    # Copertura per classe
    coverage_by_class: Dict[str, float]
    
    # Concetti matchati per classe
    concepts_by_class: Dict[str, List[Dict]]
    
    # Classificazione
    is_core: bool = False          # Coperto bene in TUTTE le classi
    is_distinctive: bool = False   # Coperto molto meglio in alcune classi
    distinctive_for: List[str] = field(default_factory=list)  # Classi dove è distintivo
    gap_for: List[str] = field(default_factory=list)          # Classi dove è un gap
    
    # Statistiche
    avg_coverage: float = 0.0
    min_coverage: float = 0.0
    max_coverage: float = 0.0
    coverage_variance: float = 0.0


@dataclass
class MulticlassResult:
    """Risultato completo dell'analisi multiclasse su framework ideale"""
    materia: str
    classes: List[str]
    framework_name: str
    
    # Analisi per classe
    class_results: Dict[str, ClassAnalysisResult]
    
    # Analisi per modulo (attraverso le classi)
    module_analyses: Dict[int, ModuleMulticlassAnalysis]
    
    # Classificazione moduli
    core_modules: List[ModuleMulticlassAnalysis]        # Coperti bene ovunque
    distinctive_modules: List[ModuleMulticlassAnalysis] # Distintivi per alcune classi
    gap_modules: Dict[str, List[ModuleMulticlassAnalysis]]  # Gap per classe
    
    # Statistiche generali
    n_modules_total: int = 0
    n_modules_core: int = 0
    n_modules_distinctive: int = 0
    overall_coverage_by_class: Dict[str, float] = field(default_factory=dict)
    
    # Soglie usate
    core_threshold: float = 60.0
    gap_threshold: float = 40.0


class MulticlassFrameworkPipeline:
    """Pipeline per analisi multiclasse con mapping su framework ideale"""
    
    def __init__(
        self, 
        materia: str,
        use_llm: bool = True,
        core_threshold: float = 60.0,      # Soglia per considerare un modulo "core"
        gap_threshold: float = 40.0,        # Soglia sotto cui è un "gap"
        distinctive_delta: float = 25.0     # Differenza minima per essere "distintivo"
    ):
        self.materia = materia
        self.use_llm = use_llm
        self.core_threshold = core_threshold
        self.gap_threshold = gap_threshold
        self.distinctive_delta = distinctive_delta
        
        self.pdf_extractor = PDFExtractor()
        self.concept_extractor = ConceptExtractor(use_llm=use_llm, materia=materia)
        self.clusterer = HierarchicalClusterer()
        self.framework_adapter = FrameworkAdapter()
        
        # Carica framework ideale
        self.ideal_framework = self.framework_adapter.load_framework(materia)
        if not self.ideal_framework:
            raise ValueError(f"Framework ideale non trovato per materia: {materia}")
        
        self.modules = self.ideal_framework.get("syllabus_modules", [])
        print(f"[INFO] Caricato framework ideale con {len(self.modules)} moduli")
    
    def extract_by_class(
        self, 
        pdf_by_class: Dict[str, List[Path]]
    ) -> Dict[str, Tuple[Dict, Dict]]:
        """
        Estrae testi da PDF organizzati per classe
        Returns: {classe: (syllabus_texts, syllabus_metadata)}
        """
        class_data = {}
        
        for classe, pdf_list in pdf_by_class.items():
            syllabus_texts = {}
            syllabus_metadata = {}
            
            print(f"[INFO] Estrazione classe {classe}: {len(pdf_list)} PDF")
            
            for pdf_path in pdf_list:
                result = self.pdf_extractor.extract(pdf_path)
                if result.success:
                    syllabus_texts[result.id] = result.text
                    syllabus_metadata[result.id] = {
                        "university": result.university,
                        "professor": result.professor,
                        "classe": classe,
                        "source_path": str(pdf_path)
                    }
            
            class_data[classe] = (syllabus_texts, syllabus_metadata)
            print(f"[INFO] Classe {classe}: estratti {len(syllabus_texts)} syllabus")
        
        return class_data
    
    def analyze_class_vs_framework(
        self,
        classe: str,
        syllabus_texts: Dict[str, str],
        syllabus_metadata: Dict[str, Dict],
        project_name: str,
        n_clusters: Optional[int] = None
    ) -> ClassAnalysisResult:
        """
        Analizza una singola classe rispetto al framework ideale
        Questo è il cuore: mappa i concetti estratti sui moduli del framework
        """
        if not syllabus_texts:
            return ClassAnalysisResult(
                classe=classe,
                n_syllabus=0,
                total_concepts_extracted=0,
                overall_coverage=0,
                module_coverages={},
                syllabus_metadata=[]
            )
        
        print(f"[INFO] Analisi classe {classe} vs framework ideale...")
        
        # Step 1: Estrazione concetti
        concept_collection = self.concept_extractor.process_multiple_syllabus(
            syllabus_texts,
            f"{project_name}_{classe}"
        )
        
        # Step 2: Clustering
        framework = self.clusterer.generate_framework(
            concept_collection,
            f"{project_name}_{classe}",
            n_clusters,
            self.use_llm
        )
        
        # Step 3: Analisi copertura rispetto al framework ideale
        analyzer = CoverageAnalyzer(framework)
        coverages, coverage_matrix = analyzer.analyze_collection(
            concept_collection, 
            syllabus_metadata
        )
        
        # Step 4: Genera output Zanichelli (che include mapping su framework ideale)
        zanichelli_output = self.framework_adapter.generate_zanichelli_output(
            materia=self.materia,
            concepts=[
                {
                    "name": c.canonical_name,
                    "frequency": c.frequency_percentage,
                    "n_syllabus": c.frequency_absolute
                }
                for c in concept_collection.concepts
            ],
            syllabus_data=[
                {
                    "id": cov.syllabus_id,
                    "university": cov.university,
                    "professor": cov.professor,
                    "classe": syllabus_metadata.get(cov.syllabus_id, {}).get("classe", "N/D"),
                    "coverage": cov.overall_coverage,
                    "concepts": [
                        c.canonical_name.lower()
                        for c in concept_collection.concepts
                        if cov.syllabus_id in c.source_syllabus_ids
                    ]
                }
                for cov in coverages
            ],
            classi_analizzate=[classe]
        )
        
        # Step 5: Estrai copertura per modulo dal risultato
        modules_analysis = zanichelli_output.get("modules_analysis", {})
        overall_assessment = zanichelli_output.get("overall_assessment", {})
        
        module_coverages = {}
        for mod_id, mod_data in modules_analysis.items():
            try:
                mid = int(mod_id) if isinstance(mod_id, str) else mod_id
            except:
                mid = mod_data.get("module_id", 0)
            
            module_coverages[mid] = ModuleCoverage(
                module_id=mid,
                module_name=mod_data.get("module_name", ""),
                coverage_percentage=mod_data.get("coverage_percentage", 0),
                matched_concepts=mod_data.get("matched_concepts", []),
                missing_contents=mod_data.get("missing_contents", []),
                n_contents_covered=mod_data.get("n_contents_covered", 0),
                n_contents_total=mod_data.get("n_contents_total", 0)
            )
        
        overall_coverage = overall_assessment.get("coverage_percentage", 0)
        
        print(f"[INFO] Classe {classe}: copertura framework {overall_coverage:.1f}%, {len(module_coverages)} moduli analizzati")
        
        return ClassAnalysisResult(
            classe=classe,
            n_syllabus=len(syllabus_texts),
            total_concepts_extracted=concept_collection.total_unique_concepts,
            overall_coverage=overall_coverage,
            module_coverages=module_coverages,
            syllabus_metadata=list(syllabus_metadata.values())
        )
    
    def analyze_by_class(
        self,
        class_data: Dict[str, Tuple[Dict, Dict]],
        project_name: str,
        n_clusters: Optional[int] = None
    ) -> Dict[str, ClassAnalysisResult]:
        """
        Esegue analisi per ogni classe rispetto al framework ideale
        """
        class_results = {}
        
        for classe, (texts, metadata) in class_data.items():
            result = self.analyze_class_vs_framework(
                classe=classe,
                syllabus_texts=texts,
                syllabus_metadata=metadata,
                project_name=project_name,
                n_clusters=n_clusters
            )
            class_results[classe] = result
        
        return class_results
    
    def generate_multiclass_framework(
        self,
        class_results: Dict[str, ClassAnalysisResult],
        classes: List[str]
    ) -> MulticlassResult:
        """
        Genera il framework multiclasse analizzando la copertura dei moduli
        attraverso tutte le classi
        """
        print(f"[INFO] Generazione framework multiclasse per {len(classes)} classi...")
        
        # Analizza ogni modulo attraverso le classi
        module_analyses: Dict[int, ModuleMulticlassAnalysis] = {}
        
        for module in self.modules:
            mod_id = module.get("id", 0)
            mod_name = module.get("name", "")
            core_contents = module.get("core_contents", [])
            
            # Raccogli copertura per classe
            coverage_by_class = {}
            concepts_by_class = {}
            
            for classe in classes:
                class_result = class_results.get(classe)
                if class_result and mod_id in class_result.module_coverages:
                    mod_cov = class_result.module_coverages[mod_id]
                    coverage_by_class[classe] = mod_cov.coverage_percentage
                    concepts_by_class[classe] = mod_cov.matched_concepts
                else:
                    coverage_by_class[classe] = 0.0
                    concepts_by_class[classe] = []
            
            # Calcola statistiche
            coverages = list(coverage_by_class.values())
            avg_coverage = sum(coverages) / len(coverages) if coverages else 0
            min_coverage = min(coverages) if coverages else 0
            max_coverage = max(coverages) if coverages else 0
            
            # Varianza
            if len(coverages) > 1:
                variance = sum((c - avg_coverage) ** 2 for c in coverages) / len(coverages)
            else:
                variance = 0
            
            # Classifica il modulo
            is_core = min_coverage >= self.core_threshold
            
            # Distintivo: alta varianza, alcune classi molto sopra la media
            distinctive_for = []
            gap_for = []
            
            for classe, cov in coverage_by_class.items():
                if cov >= avg_coverage + self.distinctive_delta and cov >= self.core_threshold:
                    distinctive_for.append(classe)
                if cov < self.gap_threshold:
                    gap_for.append(classe)
            
            is_distinctive = len(distinctive_for) > 0 and len(distinctive_for) < len(classes)
            
            module_analyses[mod_id] = ModuleMulticlassAnalysis(
                module_id=mod_id,
                module_name=mod_name,
                core_contents=core_contents,
                coverage_by_class=coverage_by_class,
                concepts_by_class=concepts_by_class,
                is_core=is_core,
                is_distinctive=is_distinctive,
                distinctive_for=distinctive_for,
                gap_for=gap_for,
                avg_coverage=avg_coverage,
                min_coverage=min_coverage,
                max_coverage=max_coverage,
                coverage_variance=variance
            )
        
        # Classifica moduli
        core_modules = [m for m in module_analyses.values() if m.is_core]
        distinctive_modules = [m for m in module_analyses.values() if m.is_distinctive]
        
        # Gap per classe
        gap_modules: Dict[str, List[ModuleMulticlassAnalysis]] = defaultdict(list)
        for m in module_analyses.values():
            for classe in m.gap_for:
                gap_modules[classe].append(m)
        
        # Copertura complessiva per classe
        overall_coverage_by_class = {
            classe: result.overall_coverage
            for classe, result in class_results.items()
        }
        
        # Debug
        print(f"[INFO] Moduli CORE (≥{self.core_threshold}% in tutte le classi): {len(core_modules)}")
        for m in core_modules:
            print(f"       - {m.module_name}: {m.min_coverage:.0f}%-{m.max_coverage:.0f}%")
        
        print(f"[INFO] Moduli DISTINTIVI: {len(distinctive_modules)}")
        for m in distinctive_modules:
            print(f"       - {m.module_name}: distintivo per {m.distinctive_for}")
        
        print(f"[INFO] GAP per classe:")
        for classe, gaps in gap_modules.items():
            print(f"       - {classe}: {len(gaps)} moduli sotto {self.gap_threshold}%")
        
        framework_name = self.ideal_framework.get("framework", {}).get("name", "Framework Ideale")
        
        return MulticlassResult(
            materia=self.materia,
            classes=classes,
            framework_name=framework_name,
            class_results=class_results,
            module_analyses=module_analyses,
            core_modules=core_modules,
            distinctive_modules=distinctive_modules,
            gap_modules=dict(gap_modules),
            n_modules_total=len(self.modules),
            n_modules_core=len(core_modules),
            n_modules_distinctive=len(distinctive_modules),
            overall_coverage_by_class=overall_coverage_by_class,
            core_threshold=self.core_threshold,
            gap_threshold=self.gap_threshold
        )
