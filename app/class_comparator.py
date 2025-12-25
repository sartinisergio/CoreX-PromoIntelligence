"""
CoreX - Class Comparator
Confronto framework tra classi di laurea diverse
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime


@dataclass
class ConceptPresence:
    """Presenza di un concetto nelle diverse classi"""
    concept_name: str
    classes_present: Dict[str, float] = field(default_factory=dict)
    classes_absent: List[str] = field(default_factory=list)
    
    @property
    def is_core(self) -> bool:
        """Concetto presente in tutte le classi con freq >= 50%"""
        if not self.classes_present:
            return False
        return all(freq >= 50 for freq in self.classes_present.values())
    
    @property
    def is_distinctive(self) -> bool:
        """Presente in una sola classe con freq >= 60%"""
        high_freq = [c for c, f in self.classes_present.items() if f >= 60]
        return len(high_freq) == 1 and len(self.classes_absent) >= 1
    
    @property
    def variance(self) -> float:
        """Varianza della frequenza tra classi (0 = uniforme)"""
        if len(self.classes_present) <= 1:
            return 0
        values = list(self.classes_present.values())
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)


@dataclass 
class ModuleComparison:
    """Confronto di un modulo tra classi"""
    module_name: str
    concepts: List[ConceptPresence]
    class_coverages: Dict[str, float]
    
    @property
    def core_concepts(self) -> List[ConceptPresence]:
        return [c for c in self.concepts if c.is_core]
    
    @property
    def distinctive_concepts(self) -> Dict[str, List[str]]:
        """Concetti distintivi per classe"""
        result = defaultdict(list)
        for c in self.concepts:
            if c.is_distinctive:
                high_class = max(c.classes_present.items(), key=lambda x: x[1])[0]
                result[high_class].append(c.concept_name)
        return dict(result)
    
    @property
    def gap_concepts(self) -> Dict[str, List[str]]:
        """Concetti mancanti per classe (presenti altrove con freq >= 40%)"""
        result = defaultdict(list)
        for c in self.concepts:
            if c.classes_absent:
                avg_present = sum(c.classes_present.values()) / len(c.classes_present) if c.classes_present else 0
                if avg_present >= 40:
                    for classe in c.classes_absent:
                        result[classe].append(c.concept_name)
        return dict(result)


@dataclass
class ClassComparisonResult:
    """Risultato completo del confronto tra classi"""
    classes_compared: List[str]
    materia: str
    modules: List[ModuleComparison]
    total_concepts: int = 0
    core_concepts_count: int = 0
    class_specific_counts: Dict[str, int] = field(default_factory=dict)
    
    def get_class_profile(self, classe: str) -> Dict:
        """Profilo riassuntivo di una classe"""
        distinctive = []
        gaps = []
        coverage_by_module = {}
        
        for mod in self.modules:
            if classe in mod.class_coverages:
                coverage_by_module[mod.module_name] = mod.class_coverages[classe]
            
            if classe in mod.distinctive_concepts:
                distinctive.extend(mod.distinctive_concepts[classe])
            
            if classe in mod.gap_concepts:
                gaps.extend(mod.gap_concepts[classe])
        
        avg_coverage = sum(coverage_by_module.values()) / len(coverage_by_module) if coverage_by_module else 0
        
        return {
            "classe": classe,
            "average_coverage": avg_coverage,
            "coverage_by_module": coverage_by_module,
            "distinctive_concepts": distinctive,
            "gap_concepts": gaps,
            "n_distinctive": len(distinctive),
            "n_gaps": len(gaps)
        }
    
    def get_comparison_matrix(self) -> Dict:
        """Matrice di confronto per visualizzazione"""
        matrix = {
            "classes": self.classes_compared,
            "modules": []
        }
        
        for mod in self.modules:
            mod_data = {
                "name": mod.module_name,
                "coverages": mod.class_coverages,
                "core_concepts": [c.concept_name for c in mod.core_concepts],
                "distinctive": mod.distinctive_concepts,
                "gaps": mod.gap_concepts
            }
            matrix["modules"].append(mod_data)
        
        return matrix


class ClassComparator:
    """Confronta framework/analisi tra classi di laurea"""
    
    def __init__(self):
        self.analyses_cache: Dict[str, Dict] = {}
    
    def load_analysis(self, analysis_path: Path) -> Optional[Dict]:
        """Carica un'analisi salvata"""
        meta_file = analysis_path / "analisi.json"
        framework_file = analysis_path / "framework_aggiornato.json"
        
        if not meta_file.exists():
            print(f"[WARN] Meta file non trovato: {meta_file}")
            return None
            
        if not framework_file.exists():
            print(f"[WARN] Framework file non trovato: {framework_file}")
            return None
        
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            
            with open(framework_file, "r", encoding="utf-8") as f:
                framework = json.load(f)
            
            print(f"[OK] Caricata analisi: {meta.get('name', 'N/D')}")
            return {
                "meta": meta,
                "framework": framework,
                "path": analysis_path
            }
        except Exception as e:
            print(f"[ERR] Errore caricamento: {e}")
            return None
    
    def compare_analyses(
        self, 
        analyses: List[Dict],
        reference_framework: Optional[Dict] = None
    ) -> ClassComparisonResult:
        """
        Confronta multiple analisi (una per classe)
        """
        classes = []
        class_data = {}
        
        for analysis in analyses:
            meta = analysis["meta"]
            fw = analysis["framework"]
            
            # Estrai nome classe dal framework stesso (più affidabile)
            fw_classes = fw.get("framework", {}).get("classes_analyzed", [])
            if fw_classes:
                classe_name = fw_classes[0]
            else:
                # Fallback ai metadati
                classi = meta.get("classi", [])
                classe_name = classi[0] if len(classi) == 1 else "_".join(classi)
            
            classes.append(classe_name)
            class_data[classe_name] = fw
            print(f"[DEBUG] Classe '{classe_name}' caricata con {len(fw.get('syllabus_modules', []))} moduli")
        
        # Raccogli tutti i moduli (unione)
        all_modules = set()
        for fw in class_data.values():
            for mod in fw.get("syllabus_modules", []):
                all_modules.add(mod.get("name", ""))
        
        print(f"[DEBUG] Moduli totali da confrontare: {len(all_modules)}")
        
        # Costruisci confronto per modulo
        module_comparisons = []
        total_concepts = 0
        core_count = 0
        class_specific = defaultdict(int)
        
        for module_name in sorted(all_modules):
            concepts_map = defaultdict(lambda: {"present": {}, "absent": []})
            class_coverages = {}
            
            for classe, fw in class_data.items():
                module_data = None
                for mod in fw.get("syllabus_modules", []):
                    if mod.get("name") == module_name:
                        module_data = mod
                        break
                
                if module_data:
                    # CORREZIONE: leggi coverage_percentage dal modulo
                    coverage = module_data.get("coverage_percentage", 0)
                    class_coverages[classe] = coverage
                    
                    # CORREZIONE: leggi matched_concepts dal modulo (non da class_data)
                    matched_concepts = module_data.get("matched_concepts", [])
                    
                    for c in matched_concepts:
                        if isinstance(c, dict):
                            cname = c.get("name", "")
                            freq = c.get("frequency", 50)
                        else:
                            cname = str(c)
                            freq = 50
                        
                        if cname:  # Ignora nomi vuoti
                            concepts_map[cname]["present"][classe] = freq
                else:
                    class_coverages[classe] = 0
            
            # Determina assenze
            for cname, data in concepts_map.items():
                for classe in classes:
                    if classe not in data["present"]:
                        data["absent"].append(classe)
            
            # Costruisci ConceptPresence
            concept_presences = []
            for cname, data in concepts_map.items():
                cp = ConceptPresence(
                    concept_name=cname,
                    classes_present=data["present"],
                    classes_absent=data["absent"]
                )
                concept_presences.append(cp)
                total_concepts += 1
                
                if cp.is_core:
                    core_count += 1
                elif cp.is_distinctive:
                    high_class = max(cp.classes_present.items(), key=lambda x: x[1])[0]
                    class_specific[high_class] += 1
            
            module_comparisons.append(ModuleComparison(
                module_name=module_name,
                concepts=concept_presences,
                class_coverages=class_coverages
            ))
            
            print(f"[DEBUG] Modulo '{module_name}': {len(concept_presences)} concetti, coperture: {class_coverages}")
        
        materia = analyses[0]["meta"].get("materia", "N/D") if analyses else "N/D"
        
        result = ClassComparisonResult(
            classes_compared=classes,
            materia=materia,
            modules=module_comparisons,
            total_concepts=total_concepts,
            core_concepts_count=core_count,
            class_specific_counts=dict(class_specific)
        )
        
        print(f"[DEBUG] Confronto completato: {total_concepts} concetti, {core_count} core")
        
        return result
    
    def generate_comparison_report(self, comparison: ClassComparisonResult) -> str:
        """Genera report HTML del confronto"""
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Confronto Classi - {comparison.materia}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a237e; border-bottom: 3px solid #3949ab; padding-bottom: 10px; }}
        h2 {{ color: #283593; margin-top: 30px; }}
        h3 {{ color: #3949ab; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #e8eaf6, #c5cae9); padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #1a237e; }}
        .stat-label {{ color: #5c6bc0; margin-top: 5px; }}
        .class-profile {{ background: #fafafa; border-left: 4px solid #3949ab; padding: 15px; margin: 15px 0; }}
        .profile-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .coverage-bar {{ height: 8px; background: #e0e0e0; border-radius: 4px; margin-top: 10px; }}
        .coverage-fill {{ height: 100%; border-radius: 4px; transition: width 0.3s; }}
        .high {{ background: #4caf50; }}
        .medium {{ background: #ff9800; }}
        .low {{ background: #f44336; }}
        .concept-list {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }}
        .concept-tag {{ padding: 4px 12px; border-radius: 15px; font-size: 0.85em; }}
        .core {{ background: #c8e6c9; color: #2e7d32; }}
        .distinctive {{ background: #fff3e0; color: #e65100; }}
        .gap {{ background: #ffcdd2; color: #c62828; }}
        .module-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .module-table th, .module-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }}
        .module-table th {{ background: #3949ab; color: white; }}
        .module-table tr:hover {{ background: #f5f5f5; }}
        .level-badge {{ display: inline-block; width: 24px; height: 24px; border-radius: 50%; text-align: center; line-height: 24px; color: white; font-weight: bold; font-size: 0.8em; }}
        .level-5 {{ background: #2e7d32; }}
        .level-4 {{ background: #689f38; }}
        .level-3 {{ background: #fbc02d; color: #333; }}
        .level-2 {{ background: #f57c00; }}
        .level-1 {{ background: #d32f2f; }}
        .level-0 {{ background: #9e9e9e; }}
    </style>
</head>
<body>
<div class="container">
    <h1>🔄 Confronto Framework: {comparison.materia.replace('_', ' ')}</h1>
    <p><strong>Classi analizzate:</strong> {', '.join(comparison.classes_compared)}</p>
    
    <div class="summary">
        <div class="stat-card">
            <div class="stat-value">{len(comparison.classes_compared)}</div>
            <div class="stat-label">Classi confrontate</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(comparison.modules)}</div>
            <div class="stat-label">Moduli totali</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{comparison.total_concepts}</div>
            <div class="stat-label">Concetti unici</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{comparison.core_concepts_count}</div>
            <div class="stat-label">Concetti core</div>
        </div>
    </div>
    
    <h2>📊 Profili per Classe</h2>
"""
        
        # Profili classi
        for classe in comparison.classes_compared:
            profile = comparison.get_class_profile(classe)
            cov = profile["average_coverage"]
            cov_class = "high" if cov >= 70 else "medium" if cov >= 40 else "low"
            
            html += f"""
    <div class="class-profile">
        <div class="profile-header">
            <h3>🎓 {classe}</h3>
            <span style="font-size: 1.2em; font-weight: bold;">{cov:.0f}% copertura media</span>
        </div>
        <div class="coverage-bar">
            <div class="coverage-fill {cov_class}" style="width: {min(cov, 100)}%;"></div>
        </div>
"""
            
            if profile["distinctive_concepts"]:
                html += """
        <p><strong>⭐ Concetti distintivi:</strong></p>
        <div class="concept-list">
"""
                for c in profile["distinctive_concepts"][:10]:
                    html += f'            <span class="concept-tag distinctive">{c}</span>\n'
                if len(profile["distinctive_concepts"]) > 10:
                    html += f'            <span class="concept-tag distinctive">+{len(profile["distinctive_concepts"])-10} altri</span>\n'
                html += "        </div>\n"
            
            if profile["gap_concepts"]:
                html += """
        <p><strong>⚠️ Gap rispetto ad altre classi:</strong></p>
        <div class="concept-list">
"""
                for c in profile["gap_concepts"][:10]:
                    html += f'            <span class="concept-tag gap">{c}</span>\n'
                if len(profile["gap_concepts"]) > 10:
                    html += f'            <span class="concept-tag gap">+{len(profile["gap_concepts"])-10} altri</span>\n'
                html += "        </div>\n"
            
            html += "    </div>\n"
        
        # Tabella moduli
        html += """
    <h2>📋 Confronto per Modulo</h2>
    <table class="module-table">
        <tr>
            <th>Modulo</th>
"""
        for classe in comparison.classes_compared:
            html += f"            <th>{classe}</th>\n"
        html += "            <th>Core</th>\n            <th>Note</th>\n        </tr>\n"
        
        for mod in comparison.modules:
            html += f"        <tr>\n            <td><strong>{mod.module_name}</strong></td>\n"
            
            for classe in comparison.classes_compared:
                cov = mod.class_coverages.get(classe, 0)
                level = min(5, max(0, int(cov / 20)))
                html += f'            <td><span class="level-badge level-{level}">{level}</span> {cov:.0f}%</td>\n'
            
            n_core = len(mod.core_concepts)
            html += f"            <td>{n_core} concetti</td>\n"
            
            notes = []
            for classe, concepts in mod.distinctive_concepts.items():
                if concepts:
                    notes.append(f"{classe}: {len(concepts)} distintivi")
            for classe, concepts in mod.gap_concepts.items():
                if concepts:
                    notes.append(f"{classe}: {len(concepts)} gap")
            
            html += f"            <td>{'; '.join(notes[:2]) if notes else '-'}</td>\n"
            html += "        </tr>\n"
        
        html += """
    </table>
    
    <h2>🎯 Core Concepts (trasversali)</h2>
    <p>Concetti presenti in tutte le classi con frequenza ≥50%:</p>
    <div class="concept-list">
"""
        
        core_found = False
        for mod in comparison.modules:
            for c in mod.core_concepts:
                html += f'        <span class="concept-tag core">{c.concept_name}</span>\n'
                core_found = True
        
        if not core_found:
            html += '        <span style="color: #666;">Nessun concetto core trovato (frequenza ≥50% in tutte le classi)</span>\n'
        
        html += f"""
    </div>
    
    <p style="margin-top: 40px; color: #666; font-size: 0.9em;">
        Report generato da CoreX - Zanichelli | {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </p>
</div>
</body>
</html>
"""
        
        return html
    
    def generate_unified_framework(
        self, 
        comparison: ClassComparisonResult,
        min_frequency: float = 30.0
    ) -> Dict:
        """
        Genera un framework unificato che include dati per tutte le classi
        """
        unified = {
            "framework": {
                "name": f"{comparison.materia} - Framework Multiclasse",
                "type": "unified_multiclass",
                "classes_analyzed": comparison.classes_compared,
                "generation_date": datetime.now().isoformat(),
                "stats": {
                    "total_modules": len(comparison.modules),
                    "total_concepts": comparison.total_concepts,
                    "core_concepts": comparison.core_concepts_count,
                    "class_specific": comparison.class_specific_counts
                }
            },
            "syllabus_modules": []
        }
        
        for mod in comparison.modules:
            module_entry = {
                "name": mod.module_name,
                "class_data": {},
                "concepts": {
                    "core": [],
                    "common": [],
                    "specific": {}
                }
            }
            
            # Dati per classe
            for classe in comparison.classes_compared:
                coverage = mod.class_coverages.get(classe, 0)
                level = min(5, max(0, int(coverage / 20)))
                
                if coverage >= 80:
                    status = "fondamentale"
                elif coverage >= 60:
                    status = "importante"
                elif coverage >= 40:
                    status = "presente"
                elif coverage > 0:
                    status = "marginale"
                else:
                    status = "assente"
                
                distintivi = mod.distinctive_concepts.get(classe, [])
                gaps = mod.gap_concepts.get(classe, [])
                
                module_entry["class_data"][classe] = {
                    "relevance_level": level,
                    "coverage_percentage": round(coverage, 1),
                    "status": status,
                    "distinctive_concepts": distintivi,
                    "gap_concepts": gaps
                }
            
            # Categorizza concetti
            for cp in mod.concepts:
                concept_info = {
                    "name": cp.concept_name,
                    "classes_present": list(cp.classes_present.keys()),
                    "frequencies": {k: round(v, 1) for k, v in cp.classes_present.items()},
                    "variance": round(cp.variance, 2)
                }
                
                if cp.is_core:
                    module_entry["concepts"]["core"].append(concept_info)
                elif len(cp.classes_present) > 1:
                    module_entry["concepts"]["common"].append(concept_info)
                else:
                    for classe in cp.classes_present:
                        if classe not in module_entry["concepts"]["specific"]:
                            module_entry["concepts"]["specific"][classe] = []
                        module_entry["concepts"]["specific"][classe].append(concept_info)
            
            unified["syllabus_modules"].append(module_entry)
        
        return unified
    def compare_analyses_direct(
        self, 
        analyses: List[Dict]
    ) -> ClassComparisonResult:
        """
        Confronto DIRETTO tra classi: analizza le differenze reali
        di insegnamento senza riferimento al framework ideale.
        """
        classes = []
        class_data = {}
        
        for analysis in analyses:
            meta = analysis["meta"]
            fw = analysis["framework"]
            
            # Estrai nome classe
            fw_classes = fw.get("framework", {}).get("classes_analyzed", [])
            if fw_classes:
                classe_name = fw_classes[0]
            else:
                classi = meta.get("classi", [])
                classe_name = classi[0] if len(classi) == 1 else "_".join(classi)
            
            classes.append(classe_name)
            class_data[classe_name] = fw
            print(f"[DEBUG-DIRECT] Classe '{classe_name}' caricata")
        
        # Raccogli TUTTI i concetti da tutte le classi (non solo quelli mappati sul framework ideale)
        all_modules = set()
        all_concepts_by_module = defaultdict(lambda: defaultdict(dict))
        
        for classe, fw in class_data.items():
            for mod in fw.get("syllabus_modules", []):
                module_name = mod.get("name", "")
                all_modules.add(module_name)
                
                # Raccogli tutti i matched_concepts
                for concept in mod.get("matched_concepts", []):
                    cname = concept.get("name", "") if isinstance(concept, dict) else str(concept)
                    freq = concept.get("frequency", 50) if isinstance(concept, dict) else 50
                    
                    if cname:
                        all_concepts_by_module[module_name][cname][classe] = freq
                
                # Raccogli anche i concetti dalla gaps_analysis (reality_not_in_ideal)
                # Questi sono concetti insegnati ma non nel framework ideale
            
            # Aggiungi concetti da gaps_analysis
            gaps = fw.get("gaps_analysis", {})
            reality_not_ideal = gaps.get("reality_not_in_ideal", [])
            
            for concept in reality_not_ideal:
                cname = concept.get("name", "")
                freq = concept.get("frequency", 50)
                
                if cname:
                    # Assegna a un modulo "Argomenti Aggiuntivi" o cerca di mappare
                    all_concepts_by_module["_Argomenti oltre framework ideale"][cname][classe] = freq
        
        # Costruisci confronto per modulo
        module_comparisons = []
        total_concepts = 0
        core_count = 0
        class_specific = defaultdict(int)
        
        for module_name in sorted(all_modules):
            concepts_in_module = all_concepts_by_module[module_name]
            class_coverages = {}
            
            # Calcola copertura come numero di concetti presenti
            for classe in classes:
                concepts_for_class = sum(1 for cname, class_freqs in concepts_in_module.items() if classe in class_freqs)
                total_in_module = len(concepts_in_module)
                coverage = (concepts_for_class / total_in_module * 100) if total_in_module > 0 else 0
                class_coverages[classe] = coverage
            
            # Costruisci ConceptPresence
            concept_presences = []
            for cname, class_freqs in concepts_in_module.items():
                classes_absent = [c for c in classes if c not in class_freqs]
                
                cp = ConceptPresence(
                    concept_name=cname,
                    classes_present=class_freqs,
                    classes_absent=classes_absent
                )
                concept_presences.append(cp)
                total_concepts += 1
                
                if cp.is_core:
                    core_count += 1
                elif cp.is_distinctive:
                    high_class = max(cp.classes_present.items(), key=lambda x: x[1])[0]
                    class_specific[high_class] += 1
            
            module_comparisons.append(ModuleComparison(
                module_name=module_name,
                concepts=concept_presences,
                class_coverages=class_coverages
            ))
        
        # Aggiungi modulo speciale per concetti extra
        if "_Argomenti oltre framework ideale" in all_concepts_by_module:
            extra_concepts = all_concepts_by_module["_Argomenti oltre framework ideale"]
            class_coverages = {}
            
            for classe in classes:
                concepts_for_class = sum(1 for cname, class_freqs in extra_concepts.items() if classe in class_freqs)
                total_extra = len(extra_concepts)
                coverage = (concepts_for_class / total_extra * 100) if total_extra > 0 else 0
                class_coverages[classe] = coverage
            
            concept_presences = []
            for cname, class_freqs in extra_concepts.items():
                classes_absent = [c for c in classes if c not in class_freqs]
                
                cp = ConceptPresence(
                    concept_name=cname,
                    classes_present=class_freqs,
                    classes_absent=classes_absent
                )
                concept_presences.append(cp)
                total_concepts += 1
                
                if cp.is_core:
                    core_count += 1
                elif cp.is_distinctive:
                    high_class = max(cp.classes_present.items(), key=lambda x: x[1])[0]
                    class_specific[high_class] += 1
            
            module_comparisons.append(ModuleComparison(
                module_name="📌 Argomenti oltre framework ideale",
                concepts=concept_presences,
                class_coverages=class_coverages
            ))
        
        materia = analyses[0]["meta"].get("materia", "N/D") if analyses else "N/D"
        
        result = ClassComparisonResult(
            classes_compared=classes,
            materia=materia,
            modules=module_comparisons,
            total_concepts=total_concepts,
            core_concepts_count=core_count,
            class_specific_counts=dict(class_specific)
        )
        
        print(f"[DEBUG-DIRECT] Confronto completato: {total_concepts} concetti, {core_count} core, specifici: {dict(class_specific)}")
        
        return result

    def generate_direct_comparison_report(self, comparison: ClassComparisonResult) -> str:
        """Genera report HTML per confronto DIRETTO tra classi"""
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Confronto Diretto Classi - {comparison.materia}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a237e; border-bottom: 3px solid #e91e63; padding-bottom: 10px; }}
        h2 {{ color: #283593; margin-top: 30px; }}
        h3 {{ color: #3949ab; }}
        .badge-direct {{ background: #e91e63; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.8em; margin-left: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #fce4ec, #f8bbd9); padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #880e4f; }}
        .stat-label {{ color: #ad1457; margin-top: 5px; }}
        .class-profile {{ background: #fafafa; border-left: 4px solid #e91e63; padding: 15px; margin: 15px 0; }}
        .profile-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .concept-list {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }}
        .concept-tag {{ padding: 4px 12px; border-radius: 15px; font-size: 0.85em; }}
        .core {{ background: #c8e6c9; color: #2e7d32; }}
        .distinctive {{ background: #fff3e0; color: #e65100; }}
        .shared {{ background: #e3f2fd; color: #1565c0; }}
        .exclusive {{ background: #fce4ec; color: #c2185b; }}
        .module-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .module-table th, .module-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }}
        .module-table th {{ background: #e91e63; color: white; }}
        .module-table tr:hover {{ background: #fce4ec; }}
        .insight-box {{ background: #fff8e1; border-left: 4px solid #ff9800; padding: 15px; margin: 20px 0; }}
        .insight-box h4 {{ color: #e65100; margin-top: 0; }}
        .comparison-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
        .class-box {{ background: #f5f5f5; padding: 15px; border-radius: 8px; }}
        .class-box h4 {{ margin-top: 0; color: #1a237e; }}
        .freq-high {{ color: #2e7d32; font-weight: bold; }}
        .freq-medium {{ color: #f57c00; }}
        .freq-low {{ color: #757575; }}
    </style>
</head>
<body>
<div class="container">
    <h1>🔄 Confronto Diretto: {comparison.materia.replace('_', ' ')} <span class="badge-direct">REAL vs REAL</span></h1>
    <p><strong>Classi analizzate:</strong> {', '.join(comparison.classes_compared)}</p>
    <p><em>Questo report confronta direttamente cosa viene insegnato nelle diverse classi, evidenziando sovrapposizioni e differenze reali.</em></p>
    
    <div class="summary">
        <div class="stat-card">
            <div class="stat-value">{len(comparison.classes_compared)}</div>
            <div class="stat-label">Classi confrontate</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(comparison.modules)}</div>
            <div class="stat-label">Aree tematiche</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{comparison.total_concepts}</div>
            <div class="stat-label">Concetti totali</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{comparison.core_concepts_count}</div>
            <div class="stat-label">Concetti condivisi (core)</div>
        </div>
    </div>
    
    <div class="insight-box">
        <h4>💡 Insight Strategico</h4>
        <p><strong>Concetti core ({comparison.core_concepts_count}):</strong> Insegnati in TUTTE le classi con alta frequenza. Questi sono imprescindibili per qualsiasi manuale.</p>
        <p><strong>Concetti esclusivi:</strong></p>
        <ul>
"""
        
        for classe, count in comparison.class_specific_counts.items():
            html += f"            <li><strong>{classe}:</strong> {count} concetti distintivi (insegnati solo/principalmente qui)</li>\n"
        
        html += """
        </ul>
    </div>
    
    <h2>📊 Profili per Classe</h2>
    <div class="comparison-grid">
"""
        
        # Profili classi affiancati
        for classe in comparison.classes_compared:
            profile = comparison.get_class_profile(classe)
            
            html += f"""
        <div class="class-box">
            <h4>🎓 {classe}</h4>
            <p><strong>Copertura media:</strong> {profile['average_coverage']:.0f}%</p>
            <p><strong>Concetti distintivi:</strong> {profile['n_distinctive']}</p>
"""
            
            if profile["distinctive_concepts"]:
                html += "            <p><strong>Top concetti esclusivi:</strong></p>\n            <div class='concept-list'>\n"
                for c in profile["distinctive_concepts"][:8]:
                    html += f"                <span class='concept-tag exclusive'>{c}</span>\n"
                if len(profile["distinctive_concepts"]) > 8:
                    html += f"                <span class='concept-tag exclusive'>+{len(profile['distinctive_concepts'])-8} altri</span>\n"
                html += "            </div>\n"
            
            html += "        </div>\n"
        
        html += """
    </div>
    
    <h2>📋 Confronto per Area Tematica</h2>
    <table class="module-table">
        <tr>
            <th>Area Tematica</th>
"""
        
        for classe in comparison.classes_compared:
            html += f"            <th>{classe}</th>\n"
        html += "            <th>Condivisi</th>\n            <th>Esclusivi</th>\n        </tr>\n"
        
        for mod in comparison.modules:
            html += f"        <tr>\n            <td><strong>{mod.module_name}</strong></td>\n"
            
            for classe in comparison.classes_compared:
                cov = mod.class_coverages.get(classe, 0)
                n_concepts = sum(1 for c in mod.concepts if classe in c.classes_present)
                html += f"            <td>{n_concepts} concetti ({cov:.0f}%)</td>\n"
            
            n_core = len(mod.core_concepts)
            
            # Conta esclusivi per classe
            exclusive_info = []
            for classe, concepts in mod.distinctive_concepts.items():
                if concepts:
                    exclusive_info.append(f"{classe}: {len(concepts)}")
            
            html += f"            <td>{n_core}</td>\n"
            html += f"            <td>{'; '.join(exclusive_info) if exclusive_info else '-'}</td>\n"
            html += "        </tr>\n"
        
        html += """
    </table>
    
    <h2>🎯 Concetti Core (condivisi da tutte le classi)</h2>
    <p>Questi concetti sono insegnati in tutte le classi con frequenza ≥50%. Rappresentano il nucleo comune imprescindibile.</p>
    <div class="concept-list">
"""
        
        core_found = set()
        for mod in comparison.modules:
            for c in mod.core_concepts:
                if c.concept_name not in core_found:
                    avg_freq = sum(c.classes_present.values()) / len(c.classes_present)
                    freq_class = "freq-high" if avg_freq >= 70 else "freq-medium" if avg_freq >= 50 else "freq-low"
                    html += f'        <span class="concept-tag core" title="Freq. media: {avg_freq:.0f}%">{c.concept_name}</span>\n'
                    core_found.add(c.concept_name)
        
        if not core_found:
            html += '        <span style="color: #666;">Nessun concetto condiviso con frequenza ≥50% in tutte le classi</span>\n'
        
        html += """
    </div>
    
    <h2>⚡ Concetti Esclusivi per Classe</h2>
    <p>Questi concetti sono insegnati principalmente o esclusivamente in una classe specifica.</p>
"""
        
        for classe in comparison.classes_compared:
            profile = comparison.get_class_profile(classe)
            
            if profile["distinctive_concepts"]:
                html += f"""
    <h3>🎓 {classe}</h3>
    <div class="concept-list">
"""
                for c in profile["distinctive_concepts"][:15]:
                    html += f'        <span class="concept-tag distinctive">{c}</span>\n'
                if len(profile["distinctive_concepts"]) > 15:
                    html += f'        <span class="concept-tag distinctive">+{len(profile["distinctive_concepts"])-15} altri</span>\n'
                html += "    </div>\n"
        
        html += f"""
    
    <div class="insight-box" style="background: #e8f5e9; border-left-color: #4caf50;">
        <h4>🎯 Implicazioni per la Promozione</h4>
        <ul>
            <li><strong>Per tutti i corsi:</strong> I {comparison.core_concepts_count} concetti core devono essere trattati in modo eccellente nel manuale</li>
"""
        
        for classe, count in comparison.class_specific_counts.items():
            if count > 5:
                html += f"            <li><strong>Per {classe}:</strong> Considera i {count} concetti esclusivi quando presenti il manuale a questi docenti</li>\n"
        
        html += f"""
        </ul>
    </div>
    
    <p style="margin-top: 40px; color: #666; font-size: 0.9em;">
        Report generato da CoreX - Zanichelli | {datetime.now().strftime('%d/%m/%Y %H:%M')} | Modalità: Confronto Diretto
    </p>
</div>
</body>
</html>
"""
        
        return html