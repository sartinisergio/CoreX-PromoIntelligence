"""
CoreX - Framework Comparator v1.0
Confronta Framework Ideale, Reale e Evidence-Based per identificare
gap formativi, contenuti emergenti e opportunità commerciali.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class FrameworkComparator:
    """
    Confronta tre tipi di framework per la stessa materia:
    - Ideale: struttura teorica Zanichelli
    - Reale: mapping dei programmi sul framework ideale
    - Evidence-Based: moduli emersi dai programmi senza struttura predefinita
    """
    
    def __init__(self, materia: str):
        self.materia = materia
        self.frameworks_dir = Path("frameworks")
        self.data_dir = Path("data")
        self.archivio_dir = Path("archivio")
        
    def load_ideal_framework(self) -> Optional[Dict]:
        """Carica il framework ideale Zanichelli."""
        # Genera tutte le possibili varianti del nome
        base_name = self.materia
        possible_names = [
            f"{base_name}.json",
            f"{base_name.lower()}.json",
            f"{base_name.upper()}.json",
            f"{base_name.replace(' ', '_')}.json",
            f"{base_name.replace(' ', '_').lower()}.json",
            f"{base_name.replace('_', ' ')}.json",
            f"{base_name.replace('_', ' ').lower()}.json",
            f"{base_name.replace('_', '-')}.json",
            f"{base_name.replace('_', '-').lower()}.json",
        ]
        
        # Rimuovi duplicati mantenendo l'ordine
        seen = set()
        unique_names = []
        for name in possible_names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)
        
        for name in unique_names:
            path = self.frameworks_dir / name
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    print(f"[ERROR] Errore caricamento framework ideale: {e}")
                    return None
        
        print(f"[WARN] Framework ideale non trovato per {self.materia}")
        print(f"[DEBUG] Cercato in: {', '.join(unique_names)}")
        return None
    
    def load_real_framework(self, analysis_path: Path = None) -> Optional[Dict]:
        """
        Carica il framework reale (analisi multiclasse con framework ideale).
        Cerca nell'analisi corrente o in un percorso specifico.
        """
        search_paths = []
        
        if analysis_path:
            search_paths.append(analysis_path / "framework_multiclasse.json")
        
        # Analisi corrente
        search_paths.append(self.data_dir / "analisi_corrente" / "framework_multiclasse.json")
        
        # Cerca nell'archivio analisi multiclass (non evidence-based)
        if self.archivio_dir.exists():
            for d in self.archivio_dir.iterdir():
                if d.is_dir():
                    meta_file = d / "analisi.json"
                    if meta_file.exists():
                        try:
                            with open(meta_file, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            # Solo analisi multiclass NON evidence-based per questa materia
                            if (meta.get("type") == "multiclass" and 
                                meta.get("materia", "").lower() == self.materia.lower()):
                                search_paths.append(d / "framework_multiclasse.json")
                        except:
                            pass
        
        for path in search_paths:
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Verifica che sia un framework reale (non evidence-based)
                    if data.get("meta", {}).get("type") != "evidence_based":
                        return data
                except Exception as e:
                    print(f"[WARN] Errore lettura {path}: {e}")
        
        print(f"[WARN] Framework reale non trovato per {self.materia}")
        return None
    
    def load_evidence_based_framework(self, analysis_path: Path = None) -> Optional[Dict]:
        """
        Carica il framework evidence-based.
        Cerca nell'analisi corrente o in un percorso specifico.
        """
        search_paths = []
        
        if analysis_path:
            search_paths.append(analysis_path / "framework_multiclasse.json")
        
        # Analisi corrente
        search_paths.append(self.data_dir / "analisi_corrente" / "framework_multiclasse.json")
        
        # Cerca nell'archivio analisi evidence-based
        if self.archivio_dir.exists():
            for d in sorted(self.archivio_dir.iterdir(), reverse=True):
                if d.is_dir():
                    meta_file = d / "analisi.json"
                    if meta_file.exists():
                        try:
                            with open(meta_file, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            # Solo analisi evidence-based per questa materia
                            if (meta.get("type") == "multiclass_evidence_based" and 
                                meta.get("materia", "").lower() == self.materia.lower()):
                                search_paths.append(d / "framework_multiclasse.json")
                        except:
                            pass
        
        for path in search_paths:
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Verifica che sia evidence-based
                    if data.get("meta", {}).get("type") == "evidence_based":
                        return data
                except Exception as e:
                    print(f"[WARN] Errore lettura {path}: {e}")
        
        print(f"[WARN] Framework evidence-based non trovato per {self.materia}")
        return None
    
    def compare(
        self,
        ideal: Dict = None,
        real: Dict = None,
        evidence_based: Dict = None
    ) -> Dict:
        """
        Esegue il confronto tra i tre framework.
        
        Returns:
            Dict con analisi comparativa completa
        """
        # Carica framework se non forniti
        ideal = ideal or self.load_ideal_framework()
        real = real or self.load_real_framework()
        evidence_based = evidence_based or self.load_evidence_based_framework()
        
        if not any([ideal, real, evidence_based]):
            return {"error": "Nessun framework trovato per il confronto"}
        
        result = {
            "materia": self.materia,
            "generated_at": datetime.now().isoformat(),
            "frameworks_found": {
                "ideal": ideal is not None,
                "real": real is not None,
                "evidence_based": evidence_based is not None
            },
            "analysis": {}
        }
        
        # Estrai moduli da ogni framework
        ideal_modules = self._extract_modules(ideal, "ideal") if ideal else []
        real_modules = self._extract_modules(real, "real") if real else []
        eb_modules = self._extract_modules(evidence_based, "evidence_based") if evidence_based else []
        
        result["modules_count"] = {
            "ideal": len(ideal_modules),
            "real": len(real_modules),
            "evidence_based": len(eb_modules)
        }
        
        # Analisi 1: Gap Formativi (nell'ideale ma non nell'evidence-based)
        if ideal and evidence_based:
            result["analysis"]["gap_formativi"] = self._find_gaps(
                ideal_modules, eb_modules
            )
        
        # Analisi 2: Contenuti Emergenti (nell'evidence-based ma non nell'ideale)
        if ideal and evidence_based:
            result["analysis"]["contenuti_emergenti"] = self._find_emergent(
                ideal_modules, eb_modules
            )
        
        # Analisi 3: Validazione (concordanza tra reale e evidence-based)
        if real and evidence_based:
            result["analysis"]["validazione"] = self._validate_mapping(
                real_modules, eb_modules
            )
        
        # Analisi 4: Copertura Ideale vs Reale
        if ideal and real:
            result["analysis"]["copertura_ideale"] = self._analyze_ideal_coverage(
                ideal_modules, real_modules
            )
        
        # Analisi 5: Sintesi Opportunità Commerciali
        result["analysis"]["opportunita_commerciali"] = self._identify_opportunities(
            ideal_modules, real_modules, eb_modules
        )
        
        # Matrice di confronto moduli
        result["comparison_matrix"] = self._build_comparison_matrix(
            ideal_modules, real_modules, eb_modules
        )
        
        return result
    
    def _extract_modules(self, framework: Dict, source: str) -> List[Dict]:
        """Estrae i moduli da un framework normalizzandoli."""
        modules = []
        
        if source == "ideal":
            # Framework ideale Zanichelli usa "syllabus_modules"
            raw_modules = framework.get("syllabus_modules", framework.get("modules", []))
            for mod in raw_modules:
                modules.append({
                    "name": mod.get("name", ""),
                    "contents": [c.lower() for c in mod.get("core_contents", [])],
                    "source": "ideal",
                    "coverage": None,
                    "id": mod.get("id")
                })
        
        elif source == "real":
            # Framework reale (da analisi multiclasse)
            raw_modules = framework.get("syllabus_modules", framework.get("modules", []))
            for mod in raw_modules:
                # Calcola copertura media
                class_data = mod.get("class_data", {})
                coverages = [cd.get("coverage", 0) for cd in class_data.values()]
                avg_coverage = sum(coverages) / len(coverages) if coverages else 0
                
                modules.append({
                    "name": mod.get("name", ""),
                    "contents": [c.lower() for c in mod.get("matched_contents", mod.get("core_contents", []))],
                    "source": "real",
                    "coverage": avg_coverage,
                    "status": mod.get("status", ""),
                    "id": mod.get("id")
                })
        
        elif source == "evidence_based":
            # Framework evidence-based
            for mod in framework.get("modules", []):
                modules.append({
                    "name": mod.get("name", ""),
                    "contents": [c.lower() for c in mod.get("core_contents", [])],
                    "source": "evidence_based",
                    "category": mod.get("category", ""),
                    "is_core": mod.get("is_core", False),
                    "is_transversal": mod.get("is_transversal", False),
                    "is_specific": mod.get("is_specific", False),
                    "presence_percentage": mod.get("stats", {}).get("presence_percentage", 0)
                })
        
        return modules
    
    def _calculate_similarity(self, contents1: List[str], contents2: List[str]) -> float:
        """Calcola similarità tra due liste di contenuti."""
        if not contents1 or not contents2:
            return 0.0
        
        set1 = set(contents1)
        set2 = set(contents2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return (intersection / union * 100) if union > 0 else 0.0
    
    def _find_best_match(self, module: Dict, candidates: List[Dict], threshold: float = 20.0) -> Optional[Dict]:
        """Trova il miglior match per un modulo tra i candidati."""
        best_match = None
        best_similarity = threshold
        
        for candidate in candidates:
            similarity = self._calculate_similarity(
                module.get("contents", []),
                candidate.get("contents", [])
            )
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    "module": candidate,
                    "similarity": similarity
                }
        
        return best_match
    
    def _find_gaps(self, ideal_modules: List[Dict], eb_modules: List[Dict]) -> Dict:
        """
        Trova gap formativi: moduli nell'ideale che non hanno corrispondenza
        significativa nell'evidence-based.
        """
        gaps = []
        covered = []
        
        for ideal_mod in ideal_modules:
            match = self._find_best_match(ideal_mod, eb_modules, threshold=25.0)
            
            if match:
                covered.append({
                    "ideal_module": ideal_mod["name"],
                    "eb_match": match["module"]["name"],
                    "similarity": round(match["similarity"], 1),
                    "eb_category": match["module"].get("category", "N/D")
                })
            else:
                gaps.append({
                    "module": ideal_mod["name"],
                    "contents": ideal_mod["contents"][:10],
                    "severity": "alta" if len(ideal_mod["contents"]) > 5 else "media"
                })
        
        return {
            "description": "Moduli del framework ideale non coperti dai programmi reali",
            "total_ideal": len(ideal_modules),
            "gaps_count": len(gaps),
            "covered_count": len(covered),
            "coverage_percentage": round(len(covered) / len(ideal_modules) * 100, 1) if ideal_modules else 0,
            "gaps": gaps,
            "covered": covered
        }
    
    def _find_emergent(self, ideal_modules: List[Dict], eb_modules: List[Dict]) -> Dict:
        """
        Trova contenuti emergenti: moduli nell'evidence-based che non hanno
        corrispondenza significativa nell'ideale.
        """
        emergent = []
        mapped = []
        
        for eb_mod in eb_modules:
            match = self._find_best_match(eb_mod, ideal_modules, threshold=25.0)
            
            if match:
                mapped.append({
                    "eb_module": eb_mod["name"],
                    "ideal_match": match["module"]["name"],
                    "similarity": round(match["similarity"], 1),
                    "category": eb_mod.get("category", "N/D")
                })
            else:
                emergent.append({
                    "module": eb_mod["name"],
                    "category": eb_mod.get("category", "N/D"),
                    "presence": eb_mod.get("presence_percentage", 0),
                    "contents": eb_mod["contents"][:10],
                    "interpretation": self._interpret_emergent(eb_mod)
                })
        
        return {
            "description": "Moduli insegnati che non sono nel framework ideale Zanichelli",
            "total_eb": len(eb_modules),
            "emergent_count": len(emergent),
            "mapped_count": len(mapped),
            "emergent": emergent,
            "mapped": mapped
        }
    
    def _interpret_emergent(self, module: Dict) -> str:
        """Interpreta il significato di un modulo emergente."""
        if module.get("is_core"):
            return "Tema universalmente insegnato ma non nel framework ideale - potenziale lacuna nel framework"
        elif module.get("is_transversal"):
            return "Tema diffuso - potrebbe meritare inclusione nel framework ideale"
        else:
            return "Tema di nicchia - specifico per alcune classi di laurea"
    
    def _validate_mapping(self, real_modules: List[Dict], eb_modules: List[Dict]) -> Dict:
        """
        Valida la coerenza tra framework reale e evidence-based.
        Alta concordanza = mapping affidabile.
        """
        concordances = []
        discrepancies = []
        
        for real_mod in real_modules:
            match = self._find_best_match(real_mod, eb_modules, threshold=20.0)
            
            if match and match["similarity"] >= 40:
                concordances.append({
                    "real_module": real_mod["name"],
                    "eb_module": match["module"]["name"],
                    "similarity": round(match["similarity"], 1),
                    "real_coverage": round(real_mod.get("coverage", 0), 1),
                    "eb_presence": match["module"].get("presence_percentage", 0)
                })
            else:
                discrepancies.append({
                    "real_module": real_mod["name"],
                    "real_coverage": round(real_mod.get("coverage", 0), 1),
                    "best_eb_match": match["module"]["name"] if match else "Nessuno",
                    "similarity": round(match["similarity"], 1) if match else 0
                })
        
        concordance_rate = len(concordances) / len(real_modules) * 100 if real_modules else 0
        
        return {
            "description": "Verifica coerenza tra analisi con framework ideale e analisi bottom-up",
            "concordance_rate": round(concordance_rate, 1),
            "interpretation": self._interpret_concordance(concordance_rate),
            "concordances": concordances,
            "discrepancies": discrepancies
        }
    
    def _interpret_concordance(self, rate: float) -> str:
        """Interpreta il tasso di concordanza."""
        if rate >= 80:
            return "Ottima concordanza - il mapping sul framework ideale riflette accuratamente i contenuti reali"
        elif rate >= 60:
            return "Buona concordanza - il mapping è generalmente affidabile con alcune differenze"
        elif rate >= 40:
            return "Concordanza moderata - ci sono differenze significative tra le due prospettive"
        else:
            return "Bassa concordanza - le due analisi danno risultati molto diversi, rivedere il mapping"
    
    def _analyze_ideal_coverage(self, ideal_modules: List[Dict], real_modules: List[Dict]) -> Dict:
        """Analizza quanto del framework ideale è coperto dal reale."""
        coverage_data = []
        
        for ideal_mod in ideal_modules:
            match = self._find_best_match(ideal_mod, real_modules, threshold=20.0)
            
            coverage_data.append({
                "module": ideal_mod["name"],
                "has_match": match is not None,
                "match_name": match["module"]["name"] if match else None,
                "similarity": round(match["similarity"], 1) if match else 0,
                "real_coverage": round(match["module"].get("coverage", 0), 1) if match else 0
            })
        
        covered = [c for c in coverage_data if c["has_match"]]
        avg_coverage = sum(c["real_coverage"] for c in covered) / len(covered) if covered else 0
        
        return {
            "description": "Quanto del framework ideale viene effettivamente insegnato",
            "modules_covered": len(covered),
            "modules_total": len(ideal_modules),
            "coverage_rate": round(len(covered) / len(ideal_modules) * 100, 1) if ideal_modules else 0,
            "avg_coverage_depth": round(avg_coverage, 1),
            "details": coverage_data
        }
    
    def _identify_opportunities(
        self,
        ideal_modules: List[Dict],
        real_modules: List[Dict],
        eb_modules: List[Dict]
    ) -> Dict:
        """Identifica opportunità commerciali basate sul confronto."""
        opportunities = []
        
        # Opportunità 1: Gap nell'ideale (moduli ideali poco coperti)
        if ideal_modules and eb_modules:
            for ideal_mod in ideal_modules:
                match = self._find_best_match(ideal_mod, eb_modules, threshold=25.0)
                if not match:
                    opportunities.append({
                        "type": "gap_formativo",
                        "priority": "alta",
                        "module": ideal_mod["name"],
                        "description": f"Il modulo '{ideal_mod['name']}' del framework Zanichelli non viene insegnato significativamente",
                        "action": "Valutare materiale didattico specifico o integrazione nei manuali esistenti"
                    })
        
        # Opportunità 2: Contenuti emergenti CORE (molto insegnati ma non nel framework)
        if eb_modules and ideal_modules:
            for eb_mod in eb_modules:
                if eb_mod.get("is_core") or eb_mod.get("is_transversal"):
                    match = self._find_best_match(eb_mod, ideal_modules, threshold=25.0)
                    if not match:
                        opportunities.append({
                            "type": "contenuto_emergente",
                            "priority": "alta" if eb_mod.get("is_core") else "media",
                            "module": eb_mod["name"],
                            "presence": eb_mod.get("presence_percentage", 0),
                            "description": f"Il tema '{eb_mod['name']}' è insegnato nel {eb_mod.get('presence_percentage', 0):.0f}% delle classi ma non è nel framework Zanichelli",
                            "action": "Considerare aggiunta al framework o creazione di materiale supplementare"
                        })
        
        # Opportunità 3: Moduli specifici per nicchie
        if eb_modules:
            for eb_mod in eb_modules:
                if eb_mod.get("is_specific") and eb_mod.get("presence_percentage", 0) >= 20:
                    distinctive_for = eb_mod.get("distinctive_for", [])
                    if distinctive_for:
                        opportunities.append({
                            "type": "nicchia_specifica",
                            "priority": "media",
                            "module": eb_mod["name"],
                            "target_classes": distinctive_for,
                            "description": f"Il tema '{eb_mod['name']}' è distintivo per: {', '.join(distinctive_for)}",
                            "action": "Valutare materiale specifico per queste classi di laurea"
                        })
        
        # Ordina per priorità
        priority_order = {"alta": 0, "media": 1, "bassa": 2}
        opportunities.sort(key=lambda x: priority_order.get(x.get("priority", "bassa"), 2))
        
        return {
            "description": "Opportunità commerciali identificate dal confronto",
            "total": len(opportunities),
            "by_type": {
                "gap_formativo": len([o for o in opportunities if o["type"] == "gap_formativo"]),
                "contenuto_emergente": len([o for o in opportunities if o["type"] == "contenuto_emergente"]),
                "nicchia_specifica": len([o for o in opportunities if o["type"] == "nicchia_specifica"])
            },
            "opportunities": opportunities
        }
    
    def _build_comparison_matrix(
        self,
        ideal_modules: List[Dict],
        real_modules: List[Dict],
        eb_modules: List[Dict]
    ) -> List[Dict]:
        """Costruisce una matrice di confronto tra tutti i moduli."""
        matrix = []
        
        # Parti dai moduli ideali
        all_module_names = set()
        
        for mod in ideal_modules:
            all_module_names.add(("ideal", mod["name"]))
        for mod in real_modules:
            all_module_names.add(("real", mod["name"]))
        for mod in eb_modules:
            all_module_names.add(("eb", mod["name"]))
        
        # Per ogni modulo ideale, trova corrispondenze
        for ideal_mod in ideal_modules:
            row = {
                "ideal_module": ideal_mod["name"],
                "ideal_contents_count": len(ideal_mod.get("contents", [])),
                "real_match": None,
                "real_similarity": 0,
                "real_coverage": 0,
                "eb_match": None,
                "eb_similarity": 0,
                "eb_category": None
            }
            
            # Match con reale
            real_match = self._find_best_match(ideal_mod, real_modules, threshold=15.0)
            if real_match:
                row["real_match"] = real_match["module"]["name"]
                row["real_similarity"] = round(real_match["similarity"], 1)
                row["real_coverage"] = round(real_match["module"].get("coverage", 0), 1)
            
            # Match con evidence-based
            eb_match = self._find_best_match(ideal_mod, eb_modules, threshold=15.0)
            if eb_match:
                row["eb_match"] = eb_match["module"]["name"]
                row["eb_similarity"] = round(eb_match["similarity"], 1)
                row["eb_category"] = eb_match["module"].get("category", "N/D")
            
            matrix.append(row)
        
        return matrix
    
    def generate_html_report(self, comparison: Dict) -> str:
        """Genera un report HTML del confronto."""
        
        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Confronto Framework - {self.materia}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a237e; border-bottom: 3px solid #673ab7; padding-bottom: 15px; }}
        h2 {{ color: #4527a0; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; }}
        h3 {{ color: #5e35b1; margin-top: 25px; }}
        .summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 30px 0; }}
        .summary-card {{ padding: 25px; border-radius: 12px; text-align: center; color: white; }}
        .summary-card.ideal {{ background: linear-gradient(135deg, #3f51b5, #1a237e); }}
        .summary-card.real {{ background: linear-gradient(135deg, #4caf50, #2e7d32); }}
        .summary-card.evidence {{ background: linear-gradient(135deg, #ff9800, #e65100); }}
        .summary-card .number {{ font-size: 3em; font-weight: bold; }}
        .summary-card .label {{ font-size: 1.1em; opacity: 0.9; }}
        .summary-card .status {{ font-size: 0.9em; margin-top: 5px; opacity: 0.8; }}
        .metric-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
        .metric {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .metric .value {{ font-size: 2em; font-weight: bold; color: #1a237e; }}
        .metric .label {{ color: #666; font-size: 0.9em; }}
        .section {{ background: #fafafa; border-radius: 10px; padding: 20px; margin: 20px 0; }}
        .gap-item {{ background: #ffebee; border-left: 4px solid #f44336; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0; }}
        .emergent-item {{ background: #fff3e0; border-left: 4px solid #ff9800; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0; }}
        .emergent-item.core {{ background: #e8f5e9; border-left-color: #4caf50; }}
        .opportunity {{ background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin: 10px 0; }}
        .opportunity.alta {{ border-left: 4px solid #f44336; }}
        .opportunity.media {{ border-left: 4px solid #ff9800; }}
        .opportunity.bassa {{ border-left: 4px solid #4caf50; }}
        .priority-badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; font-weight: 500; }}
        .priority-badge.alta {{ background: #ffcdd2; color: #c62828; }}
        .priority-badge.media {{ background: #ffe0b2; color: #e65100; }}
        .priority-badge.bassa {{ background: #c8e6c9; color: #2e7d32; }}
        .type-badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; margin-left: 10px; background: #e3f2fd; color: #1565c0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }}
        th {{ background: #f5f5f5; font-weight: 600; color: #333; }}
        tr:hover {{ background: #fafafa; }}
        .match-high {{ color: #2e7d32; font-weight: 500; }}
        .match-medium {{ color: #f57c00; }}
        .match-low {{ color: #c62828; }}
        .concordance-bar {{ height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .concordance-fill {{ height: 100%; border-radius: 10px; }}
        .concordance-fill.high {{ background: #4caf50; }}
        .concordance-fill.medium {{ background: #ff9800; }}
        .concordance-fill.low {{ background: #f44336; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #888; text-align: center; }}
        .tag {{ display: inline-block; background: #e8eaf6; padding: 2px 8px; margin: 2px; border-radius: 10px; font-size: 0.85em; }}
    </style>
</head>
<body>
<div class="container">
    <h1>Confronto Framework - {self.materia.replace('_', ' ').title()}</h1>
    <p>Analisi comparativa tra Framework Ideale, Reale e Evidence-Based</p>
    <p><small>Generato il {comparison.get('generated_at', '')[:16].replace('T', ' ')}</small></p>
    
    <div class="summary">
        <div class="summary-card ideal">
            <div class="number">{comparison.get('modules_count', {}).get('ideal', 0)}</div>
            <div class="label">Moduli Framework Ideale</div>
            <div class="status">{'Caricato' if comparison.get('frameworks_found', {}).get('ideal') else 'Non trovato'}</div>
        </div>
        <div class="summary-card real">
            <div class="number">{comparison.get('modules_count', {}).get('real', 0)}</div>
            <div class="label">Moduli Framework Reale</div>
            <div class="status">{'Caricato' if comparison.get('frameworks_found', {}).get('real') else 'Non trovato'}</div>
        </div>
        <div class="summary-card evidence">
            <div class="number">{comparison.get('modules_count', {}).get('evidence_based', 0)}</div>
            <div class="label">Moduli Evidence-Based</div>
            <div class="status">{'Caricato' if comparison.get('frameworks_found', {}).get('evidence_based') else 'Non trovato'}</div>
        </div>
    </div>
"""
        
        # Sezione Gap Formativi
        gaps = comparison.get("analysis", {}).get("gap_formativi", {})
        if gaps:
            coverage_pct = gaps.get("coverage_percentage", 0)
            bar_class = "high" if coverage_pct >= 70 else ("medium" if coverage_pct >= 50 else "low")
            
            html += f"""
    <h2>Gap Formativi</h2>
    <p>{gaps.get('description', '')}</p>
    
    <div class="metric-row">
        <div class="metric">
            <div class="value">{gaps.get('total_ideal', 0)}</div>
            <div class="label">Moduli Ideali</div>
        </div>
        <div class="metric">
            <div class="value">{gaps.get('covered_count', 0)}</div>
            <div class="label">Coperti</div>
        </div>
        <div class="metric">
            <div class="value">{gaps.get('gaps_count', 0)}</div>
            <div class="label">Gap</div>
        </div>
        <div class="metric">
            <div class="value">{coverage_pct:.0f}%</div>
            <div class="label">Copertura</div>
        </div>
    </div>
    
    <div class="concordance-bar">
        <div class="concordance-fill {bar_class}" style="width: {min(coverage_pct, 100)}%;"></div>
    </div>
"""
            
            if gaps.get("gaps"):
                html += """
    <h3>Moduli Non Coperti</h3>
"""
                for gap in gaps.get("gaps", []):
                    html += f"""
    <div class="gap-item">
        <strong>{gap.get('module', 'N/D')}</strong>
        <span class="priority-badge {gap.get('severity', 'media')}">{gap.get('severity', 'N/D').upper()}</span>
        <br><small>Contenuti: {', '.join(gap.get('contents', [])[:5])}...</small>
    </div>
"""
        
        # Sezione Contenuti Emergenti
        emergent = comparison.get("analysis", {}).get("contenuti_emergenti", {})
        if emergent:
            html += f"""
    <h2>Contenuti Emergenti</h2>
    <p>{emergent.get('description', '')}</p>
    
    <div class="metric-row">
        <div class="metric">
            <div class="value">{emergent.get('total_eb', 0)}</div>
            <div class="label">Moduli Evidence-Based</div>
        </div>
        <div class="metric">
            <div class="value">{emergent.get('mapped_count', 0)}</div>
            <div class="label">Mappati su Ideale</div>
        </div>
        <div class="metric">
            <div class="value">{emergent.get('emergent_count', 0)}</div>
            <div class="label">Emergenti</div>
        </div>
    </div>
"""
            
            if emergent.get("emergent"):
                html += """
    <h3>Moduli Emergenti (non nel framework ideale)</h3>
"""
                for em in emergent.get("emergent", []):
                    is_core = "CORE" in em.get("category", "").upper()
                    html += f"""
    <div class="emergent-item {'core' if is_core else ''}">
        <strong>{em.get('module', 'N/D')}</strong>
        <span class="type-badge">{em.get('category', 'N/D')}</span>
        <span class="priority-badge {'alta' if is_core else 'media'}">{em.get('presence', 0):.0f}% classi</span>
        <br><small>{em.get('interpretation', '')}</small>
        <br><small>Contenuti: {', '.join(em.get('contents', [])[:5])}...</small>
    </div>
"""
        
        # Sezione Validazione
        validation = comparison.get("analysis", {}).get("validazione", {})
        if validation:
            conc_rate = validation.get("concordance_rate", 0)
            bar_class = "high" if conc_rate >= 70 else ("medium" if conc_rate >= 50 else "low")
            
            html += f"""
    <h2>Validazione Mapping</h2>
    <p>{validation.get('description', '')}</p>
    
    <div class="section">
        <div class="metric-row">
            <div class="metric">
                <div class="value">{conc_rate:.0f}%</div>
                <div class="label">Tasso Concordanza</div>
            </div>
        </div>
        <div class="concordance-bar">
            <div class="concordance-fill {bar_class}" style="width: {min(conc_rate, 100)}%;"></div>
        </div>
        <p><strong>Interpretazione:</strong> {validation.get('interpretation', '')}</p>
    </div>
"""
        
        # Sezione Opportunità Commerciali
        opportunities = comparison.get("analysis", {}).get("opportunita_commerciali", {})
        if opportunities:
            html += f"""
    <h2>Opportunità Commerciali</h2>
    <p>{opportunities.get('description', '')}</p>
    
    <div class="metric-row">
        <div class="metric">
            <div class="value">{opportunities.get('total', 0)}</div>
            <div class="label">Totale Opportunità</div>
        </div>
        <div class="metric">
            <div class="value">{opportunities.get('by_type', {}).get('gap_formativo', 0)}</div>
            <div class="label">Gap Formativi</div>
        </div>
        <div class="metric">
            <div class="value">{opportunities.get('by_type', {}).get('contenuto_emergente', 0)}</div>
            <div class="label">Contenuti Emergenti</div>
        </div>
        <div class="metric">
            <div class="value">{opportunities.get('by_type', {}).get('nicchia_specifica', 0)}</div>
            <div class="label">Nicchie Specifiche</div>
        </div>
    </div>
"""
            
            for opp in opportunities.get("opportunities", []):
                html += f"""
    <div class="opportunity {opp.get('priority', 'media')}">
        <span class="priority-badge {opp.get('priority', 'media')}">{opp.get('priority', 'N/D').upper()}</span>
        <span class="type-badge">{opp.get('type', '').replace('_', ' ').title()}</span>
        <h4 style="margin: 10px 0 5px 0;">{opp.get('module', 'N/D')}</h4>
        <p style="margin: 5px 0;">{opp.get('description', '')}</p>
        <p style="margin: 5px 0; color: #1565c0;"><strong>Azione:</strong> {opp.get('action', '')}</p>
    </div>
"""
        
        # Matrice di Confronto
        matrix = comparison.get("comparison_matrix", [])
        if matrix:
            html += """
    <h2>Matrice di Confronto</h2>
    <table>
        <thead>
            <tr>
                <th>Modulo Ideale</th>
                <th>Match Reale</th>
                <th>Similarità</th>
                <th>Copertura</th>
                <th>Match Evidence-Based</th>
                <th>Similarità</th>
                <th>Categoria</th>
            </tr>
        </thead>
        <tbody>
"""
            for row in matrix:
                real_sim = row.get("real_similarity", 0)
                eb_sim = row.get("eb_similarity", 0)
                real_class = "match-high" if real_sim >= 50 else ("match-medium" if real_sim >= 25 else "match-low")
                eb_class = "match-high" if eb_sim >= 50 else ("match-medium" if eb_sim >= 25 else "match-low")
                
                html += f"""
            <tr>
                <td><strong>{row.get('ideal_module', 'N/D')}</strong></td>
                <td>{row.get('real_match', '-') or '-'}</td>
                <td class="{real_class}">{real_sim:.0f}%</td>
                <td>{row.get('real_coverage', 0):.0f}%</td>
                <td>{row.get('eb_match', '-') or '-'}</td>
                <td class="{eb_class}">{eb_sim:.0f}%</td>
                <td>{row.get('eb_category', '-') or '-'}</td>
            </tr>
"""
            html += """
        </tbody>
    </table>
"""
        
        # Footer
        html += f"""
    <div class="footer">
        <p><strong>CoreX PromoIntelligence - Framework Comparator v1.0</strong></p>
        <p>Generato il {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
</div>
</body>
</html>
"""
        
        return html


# =============================================================================
# FUNZIONI HELPER
# =============================================================================

def compare_frameworks(
    materia: str,
    ideal_path: Path = None,
    real_path: Path = None,
    evidence_based_path: Path = None
) -> Dict:
    """
    Funzione helper per confrontare i framework.
    
    Args:
        materia: Nome della materia
        ideal_path: Path opzionale al framework ideale
        real_path: Path opzionale all'analisi reale
        evidence_based_path: Path opzionale all'analisi evidence-based
    
    Returns:
        Dict con risultati del confronto
    """
    comparator = FrameworkComparator(materia)
    
    # Carica framework personalizzati se specificati
    ideal = None
    real = None
    evidence_based = None
    
    if ideal_path and ideal_path.exists():
        with open(ideal_path, "r", encoding="utf-8") as f:
            ideal = json.load(f)
    
    if real_path and real_path.exists():
        with open(real_path, "r", encoding="utf-8") as f:
            real = json.load(f)
    
    if evidence_based_path and evidence_based_path.exists():
        with open(evidence_based_path, "r", encoding="utf-8") as f:
            evidence_based = json.load(f)
    
    return comparator.compare(ideal, real, evidence_based)


def generate_comparison_report(materia: str, output_path: Path = None) -> Tuple[Dict, str]:
    """
    Genera confronto e report HTML.
    
    Returns:
        Tuple (comparison_data, html_report)
    """
    comparator = FrameworkComparator(materia)
    comparison = comparator.compare()
    html = comparator.generate_html_report(comparison)
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    
    return comparison, html