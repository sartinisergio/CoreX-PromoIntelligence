"""
CoreX - Framework Triple Comparator v2.0
Confronta Framework Ideale, Reale e Evidence-Based con algoritmo
di Coverage Mapping avanzato per gestire granularità diverse.

NOVITÀ v2.0:
- Matching semantico basato su parole chiave (non stringhe esatte)
- Supporto relazioni 1:N e N:1 tra moduli
- Confronto sui nomi dei moduli oltre ai contenuti
- Calcolo copertura reale basato su concetti effettivamente coperti
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
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
        
        # Keywords per matching semantico (espandibile)
        self.keyword_synonyms = {
            "atomico": ["atomica", "atomo", "atomi", "atomici"],
            "struttura": ["strutture", "strutturale"],
            "equilibrio": ["equilibri", "equilibrata"],
            "reazione": ["reazioni", "reagenti", "reattivi"],
            "legame": ["legami", "legante"],
            "termodinamica": ["termodinamiche", "termodinamico", "termochimico", "termochimica"],
            "cinetica": ["cinetiche", "cinetico", "velocità"],
            "acido": ["acidi", "acidità", "acida"],
            "base": ["basi", "basico", "basica", "basicità"],
            "ossido": ["ossidi", "ossidazione", "ossidante"],
            "riduzione": ["riducente", "redox", "ossidoriduzione"],
            "soluzione": ["soluzioni", "soluto", "solvente"],
            "gas": ["gassoso", "gassosi", "aeriforme"],
            "elettro": ["elettrochimica", "elettrolitico", "elettrolisi"],
            "quantico": ["quantici", "quantistica", "quantistico"],
            "orbitale": ["orbitali"],
            "periodico": ["periodica", "periodicità", "periodiche"],
            "molare": ["mole", "moli", "molarità"],
            "entalpia": ["entalpico", "entalpiche", "enthalpie"],
            "entropia": ["entropico", "entropiche"],
            "gibbs": ["energia libera"],
            "colligativo": ["colligative", "colligativi"],
            "stechiometria": ["stechiometrico", "stechiometrica", "stechiometrici"],
            "isotopo": ["isotopi", "isotopica", "isotopico"],
        }
        
    # =========================================================================
    # METODI DI CARICAMENTO (invariati)
    # =========================================================================
    
    def load_ideal_framework(self) -> Optional[Dict]:
        """Carica il framework ideale Zanichelli."""
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
        return None
    
    def load_real_framework(self, analysis_path: Path = None) -> Optional[Dict]:
        """Carica il framework reale (analisi multiclasse con framework ideale)."""
        search_paths = []
        
        if analysis_path:
            search_paths.append(analysis_path / "framework_multiclasse.json")
        
        search_paths.append(self.data_dir / "analisi_corrente" / "framework_multiclasse.json")
        
        if self.archivio_dir.exists():
            for d in self.archivio_dir.iterdir():
                if d.is_dir():
                    meta_file = d / "analisi.json"
                    if meta_file.exists():
                        try:
                            with open(meta_file, "r", encoding="utf-8") as f:
                                meta = json.load(f)
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
                    if data.get("meta", {}).get("type") != "evidence_based":
                        return data
                except Exception as e:
                    print(f"[WARN] Errore lettura {path}: {e}")
        
        print(f"[WARN] Framework reale non trovato per {self.materia}")
        return None
    
    def load_evidence_based_framework(self, analysis_path: Path = None) -> Optional[Dict]:
        """Carica il framework evidence-based."""
        search_paths = []
        
        if analysis_path:
            search_paths.append(analysis_path / "framework_multiclasse.json")
        
        search_paths.append(self.data_dir / "analisi_corrente" / "framework_multiclasse.json")
        
        if self.archivio_dir.exists():
            for d in sorted(self.archivio_dir.iterdir(), reverse=True):
                if d.is_dir():
                    meta_file = d / "analisi.json"
                    if meta_file.exists():
                        try:
                            with open(meta_file, "r", encoding="utf-8") as f:
                                meta = json.load(f)
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
                    if data.get("meta", {}).get("type") == "evidence_based":
                        return data
                except Exception as e:
                    print(f"[WARN] Errore lettura {path}: {e}")
        
        print(f"[WARN] Framework evidence-based non trovato per {self.materia}")
        return None
    
    # =========================================================================
    # NUOVO: ALGORITMO DI MATCHING SEMANTICO
    # =========================================================================
    
    def _normalize_text(self, text: str) -> str:
        """Normalizza il testo per il confronto."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Estrae parole chiave significative da un testo."""
        normalized = self._normalize_text(text)
        words = set(normalized.split())
        
        # Rimuovi stopwords italiane comuni
        stopwords = {
            'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra', 
            'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una',
            'e', 'o', 'ma', 'che', 'del', 'della', 'dei', 'degli', 'delle',
            'al', 'alla', 'ai', 'agli', 'alle', 'dal', 'dalla', 'nel', 'nella',
            'sul', 'sulla', 'è', 'sono', 'essere', 'come', 'anche', 'più',
            'molto', 'poco', 'tutto', 'tutti', 'ogni', 'quale', 'quali'
        }
        words = words - stopwords
        
        # Espandi con sinonimi
        expanded = set()
        for word in words:
            expanded.add(word)
            # Cerca il termine base nei sinonimi
            for base, synonyms in self.keyword_synonyms.items():
                if word == base or word in synonyms:
                    expanded.add(base)
                    expanded.update(synonyms)
                    break
        
        return expanded
    
    def _keywords_from_contents(self, contents: List[str]) -> Set[str]:
        """Estrae tutte le keywords da una lista di contenuti."""
        all_keywords = set()
        for content in contents:
            all_keywords.update(self._extract_keywords(content))
        return all_keywords
    
    def _calculate_keyword_overlap(self, keywords1: Set[str], keywords2: Set[str]) -> Tuple[float, Set[str]]:
        """
        Calcola la sovrapposizione tra due set di keywords.
        Ritorna (percentuale, keywords in comune).
        """
        if not keywords1 or not keywords2:
            return 0.0, set()
        
        intersection = keywords1 & keywords2
        # Usiamo la media delle due percentuali per bilanciare
        pct1 = len(intersection) / len(keywords1) * 100 if keywords1 else 0
        pct2 = len(intersection) / len(keywords2) * 100 if keywords2 else 0
        
        return (pct1 + pct2) / 2, intersection
    
    def _calculate_semantic_similarity(
        self, 
        module1: Dict, 
        module2: Dict
    ) -> Dict:
        """
        Calcola similarità semantica tra due moduli considerando:
        1. Nome del modulo
        2. Contenuti
        
        Returns:
            Dict con dettagli del matching
        """
        # Keywords dal nome
        name1_kw = self._extract_keywords(module1.get("name", ""))
        name2_kw = self._extract_keywords(module2.get("name", ""))
        
        # Keywords dai contenuti
        contents1_kw = self._keywords_from_contents(module1.get("contents", []))
        contents2_kw = self._keywords_from_contents(module2.get("contents", []))
        
        # Calcola overlap nomi
        name_overlap, name_common = self._calculate_keyword_overlap(name1_kw, name2_kw)
        
        # Calcola overlap contenuti
        content_overlap, content_common = self._calculate_keyword_overlap(contents1_kw, contents2_kw)
        
        # Score combinato (nome pesa 30%, contenuti 70%)
        combined_score = name_overlap * 0.3 + content_overlap * 0.7
        
        return {
            "combined_score": round(combined_score, 1),
            "name_similarity": round(name_overlap, 1),
            "content_similarity": round(content_overlap, 1),
            "common_keywords": list(name_common | content_common)[:15],
            "name_keywords_matched": list(name_common),
            "content_keywords_matched": list(content_common)[:10]
        }
    
    # =========================================================================
    # NUOVO: COVERAGE MAPPING (relazioni 1:N e N:1)
    # =========================================================================
    
    def _build_coverage_map(
        self, 
        source_modules: List[Dict], 
        target_modules: List[Dict],
        threshold: float = 15.0
    ) -> Dict:
        """
        Costruisce una mappa di copertura tra moduli source e target.
        Gestisce relazioni 1:N (un source copre più target) e N:1 (più source coprono un target).
        
        Args:
            source_modules: Moduli di riferimento (es. Ideale)
            target_modules: Moduli da mappare (es. Evidence-Based)
            threshold: Soglia minima di similarità per considerare un match
            
        Returns:
            Dict con mapping dettagliato
        """
        coverage_map = {
            "source_to_target": {},  # 1:N - un source quali target copre
            "target_to_source": {},  # N:1 - un target da quali source è coperto
            "uncovered_sources": [],  # Source senza match
            "unmapped_targets": [],   # Target senza match (emergenti)
            "matrix": []  # Matrice completa delle similarità
        }
        
        # Calcola matrice di similarità completa
        similarity_matrix = []
        for s_idx, source in enumerate(source_modules):
            row = {"source": source["name"], "matches": []}
            for t_idx, target in enumerate(target_modules):
                sim = self._calculate_semantic_similarity(source, target)
                row["matches"].append({
                    "target": target["name"],
                    "target_idx": t_idx,
                    **sim
                })
            similarity_matrix.append(row)
        
        coverage_map["matrix"] = similarity_matrix
        
        # Costruisci mapping source -> target (1:N)
        for s_idx, source in enumerate(source_modules):
            source_name = source["name"]
            matches = []
            
            for match in similarity_matrix[s_idx]["matches"]:
                if match["combined_score"] >= threshold:
                    matches.append({
                        "target": match["target"],
                        "score": match["combined_score"],
                        "name_sim": match["name_similarity"],
                        "content_sim": match["content_similarity"],
                        "common_keywords": match["common_keywords"]
                    })
            
            # Ordina per score decrescente
            matches.sort(key=lambda x: x["score"], reverse=True)
            
            if matches:
                coverage_map["source_to_target"][source_name] = {
                    "matches": matches,
                    "best_match": matches[0]["target"],
                    "best_score": matches[0]["score"],
                    "total_matches": len(matches),
                    "coverage_type": "1:N" if len(matches) > 1 else "1:1"
                }
            else:
                coverage_map["uncovered_sources"].append({
                    "module": source_name,
                    "contents": source.get("contents", [])[:5]
                })
        
        # Costruisci mapping target -> source (N:1)
        for t_idx, target in enumerate(target_modules):
            target_name = target["name"]
            sources_covering = []
            
            for s_idx, source in enumerate(source_modules):
                match = similarity_matrix[s_idx]["matches"][t_idx]
                if match["combined_score"] >= threshold:
                    sources_covering.append({
                        "source": source["name"],
                        "score": match["combined_score"],
                        "common_keywords": match["common_keywords"]
                    })
            
            sources_covering.sort(key=lambda x: x["score"], reverse=True)
            
            if sources_covering:
                coverage_map["target_to_source"][target_name] = {
                    "covered_by": sources_covering,
                    "primary_source": sources_covering[0]["source"],
                    "primary_score": sources_covering[0]["score"],
                    "total_sources": len(sources_covering),
                    "coverage_type": "N:1" if len(sources_covering) > 1 else "1:1"
                }
            else:
                coverage_map["unmapped_targets"].append({
                    "module": target_name,
                    "category": target.get("category", "N/D"),
                    "presence": target.get("presence_percentage", 0),
                    "contents": target.get("contents", [])[:5]
                })
        
        return coverage_map
    
    # =========================================================================
    # METODI CONFRONTO AGGIORNATI
    # =========================================================================
    
    def compare(
        self,
        ideal: Dict = None,
        real: Dict = None,
        evidence_based: Dict = None
    ) -> Dict:
        """Esegue il confronto tra i tre framework."""
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
        
        # Estrai moduli
        ideal_modules = self._extract_modules(ideal, "ideal") if ideal else []
        real_modules = self._extract_modules(real, "real") if real else []
        eb_modules = self._extract_modules(evidence_based, "evidence_based") if evidence_based else []
        
        result["modules_count"] = {
            "ideal": len(ideal_modules),
            "real": len(real_modules),
            "evidence_based": len(eb_modules)
        }
        
        # NUOVO: Coverage Map Ideale vs Evidence-Based
        if ideal and evidence_based:
            coverage_map = self._build_coverage_map(ideal_modules, eb_modules, threshold=15.0)
            result["coverage_map_ideal_eb"] = coverage_map
            
            # Analisi Gap Formativi (basata su coverage map)
            result["analysis"]["gap_formativi"] = self._analyze_gaps_from_coverage(
                coverage_map, ideal_modules, eb_modules
            )
            
            # Analisi Contenuti Emergenti (basata su coverage map)
            result["analysis"]["contenuti_emergenti"] = self._analyze_emergent_from_coverage(
                coverage_map, eb_modules
            )
        
        # Validazione Reale vs Evidence-Based
        if real and evidence_based:
            result["analysis"]["validazione"] = self._validate_mapping(
                real_modules, eb_modules
            )
        
        # Copertura Ideale vs Reale
        if ideal and real:
            result["analysis"]["copertura_ideale"] = self._analyze_ideal_coverage(
                ideal_modules, real_modules
            )
        
        # Opportunità Commerciali
        result["analysis"]["opportunita_commerciali"] = self._identify_opportunities(
            ideal_modules, real_modules, eb_modules,
            result.get("coverage_map_ideal_eb", {})
        )
        
        # Matrice di confronto
        result["comparison_matrix"] = self._build_comparison_matrix_v2(
            ideal_modules, real_modules, eb_modules
        )
        
        return result
    
    def _extract_modules(self, framework: Dict, source: str) -> List[Dict]:
        """Estrae i moduli da un framework normalizzandoli."""
        modules = []
        
        if source == "ideal":
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
            raw_modules = framework.get("syllabus_modules", framework.get("modules", []))
            for mod in raw_modules:
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
            for mod in framework.get("modules", []):
                modules.append({
                    "name": mod.get("name", ""),
                    "contents": [c.lower() for c in mod.get("core_contents", [])],
                    "source": "evidence_based",
                    "category": mod.get("category", ""),
                    "is_core": mod.get("is_core", False),
                    "is_transversal": mod.get("is_transversal", False),
                    "is_specific": mod.get("is_specific", False),
                    "presence_percentage": mod.get("stats", {}).get("presence_percentage", 0),
                    "distinctive_for": mod.get("distinctive_for", [])
                })
        
        return modules
    
    def _analyze_gaps_from_coverage(
        self, 
        coverage_map: Dict, 
        ideal_modules: List[Dict],
        eb_modules: List[Dict]
    ) -> Dict:
        """Analizza gap formativi dalla coverage map."""
        
        source_to_target = coverage_map.get("source_to_target", {})
        uncovered = coverage_map.get("uncovered_sources", [])
        
        # Moduli coperti con dettagli
        covered = []
        partial_coverage = []
        
        for ideal_name, mapping in source_to_target.items():
            best_score = mapping["best_score"]
            
            entry = {
                "ideal_module": ideal_name,
                "eb_matches": [m["target"] for m in mapping["matches"]],
                "best_match": mapping["best_match"],
                "best_score": best_score,
                "coverage_type": mapping["coverage_type"],
                "common_keywords": mapping["matches"][0]["common_keywords"] if mapping["matches"] else []
            }
            
            # Trova la categoria del best match
            for eb in eb_modules:
                if eb["name"] == mapping["best_match"]:
                    entry["eb_category"] = eb.get("category", "N/D")
                    break
            
            if best_score >= 40:
                covered.append(entry)
            else:
                partial_coverage.append(entry)
        
        # Calcola statistiche
        total = len(ideal_modules)
        fully_covered = len([c for c in covered if c["best_score"] >= 40])
        partially_covered = len(partial_coverage)
        not_covered = len(uncovered)
        
        coverage_pct = (fully_covered / total * 100) if total > 0 else 0
        
        # Formatta gap per severità
        gaps = []
        for gap in uncovered:
            gaps.append({
                "module": gap["module"],
                "contents": gap["contents"],
                "severity": "alta",
                "reason": "Nessun modulo EB corrisponde"
            })
        
        for partial in partial_coverage:
            gaps.append({
                "module": partial["ideal_module"],
                "best_eb_match": partial["best_match"],
                "score": partial["best_score"],
                "severity": "media" if partial["best_score"] >= 25 else "alta",
                "reason": f"Match parziale ({partial['best_score']:.0f}%) con '{partial['best_match']}'"
            })
        
        return {
            "description": "Moduli del framework ideale e loro copertura nei programmi reali",
            "total_ideal": total,
            "fully_covered": fully_covered,
            "partially_covered": partially_covered,
            "not_covered": not_covered,
            "coverage_percentage": round(coverage_pct, 1),
            "gaps": gaps,
            "covered": covered,
            "partial": partial_coverage
        }
    
    def _analyze_emergent_from_coverage(
        self, 
        coverage_map: Dict,
        eb_modules: List[Dict]
    ) -> Dict:
        """Analizza contenuti emergenti dalla coverage map."""
        
        target_to_source = coverage_map.get("target_to_source", {})
        unmapped = coverage_map.get("unmapped_targets", [])
        
        # Moduli mappati
        mapped = []
        for eb_name, mapping in target_to_source.items():
            # Trova il modulo EB completo
            eb_mod = None
            for eb in eb_modules:
                if eb["name"] == eb_name:
                    eb_mod = eb
                    break
            
            mapped.append({
                "eb_module": eb_name,
                "ideal_matches": [s["source"] for s in mapping["covered_by"]],
                "primary_source": mapping["primary_source"],
                "primary_score": mapping["primary_score"],
                "coverage_type": mapping["coverage_type"],
                "category": eb_mod.get("category", "N/D") if eb_mod else "N/D"
            })
        
        # Moduli emergenti (non nel framework ideale)
        emergent = []
        for em in unmapped:
            # Trova il modulo EB completo per più dettagli
            eb_mod = None
            for eb in eb_modules:
                if eb["name"] == em["module"]:
                    eb_mod = eb
                    break
            
            interpretation = self._interpret_emergent_v2(eb_mod) if eb_mod else "Analisi non disponibile"
            
            emergent.append({
                "module": em["module"],
                "category": em.get("category", "N/D"),
                "presence": em.get("presence", 0),
                "contents": em["contents"],
                "interpretation": interpretation,
                "is_core": eb_mod.get("is_core", False) if eb_mod else False,
                "distinctive_for": eb_mod.get("distinctive_for", []) if eb_mod else []
            })
        
        return {
            "description": "Moduli evidence-based e loro corrispondenza con il framework ideale",
            "total_eb": len(eb_modules),
            "mapped_count": len(mapped),
            "emergent_count": len(emergent),
            "mapped": mapped,
            "emergent": emergent
        }
    
    def _interpret_emergent_v2(self, module: Dict) -> str:
        """Interpreta il significato di un modulo emergente (v2)."""
        if module.get("is_core"):
            return "⚠️ ATTENZIONE: Tema insegnato universalmente ma ASSENTE nel framework ideale - LACUNA CRITICA nel framework Zanichelli"
        elif module.get("is_transversal"):
            presence = module.get("presence_percentage", 0)
            return f"📊 Tema diffuso ({presence:.0f}% classi) - Candidato per inclusione nel framework ideale"
        else:
            distinctive = module.get("distinctive_for", [])
            if distinctive:
                return f"🎯 Tema di nicchia, distintivo per: {', '.join(distinctive)}"
            return "📌 Tema specifico per alcune classi di laurea"
    
    def _validate_mapping(self, real_modules: List[Dict], eb_modules: List[Dict]) -> Dict:
        """Valida coerenza tra framework reale e evidence-based."""
        concordances = []
        discrepancies = []
        
        for real_mod in real_modules:
            best_match = None
            best_sim = 0
            
            for eb_mod in eb_modules:
                sim = self._calculate_semantic_similarity(real_mod, eb_mod)
                if sim["combined_score"] > best_sim:
                    best_sim = sim["combined_score"]
                    best_match = {
                        "module": eb_mod,
                        "similarity": sim
                    }
            
            if best_match and best_sim >= 30:
                concordances.append({
                    "real_module": real_mod["name"],
                    "eb_module": best_match["module"]["name"],
                    "similarity": round(best_sim, 1),
                    "real_coverage": round(real_mod.get("coverage", 0), 1),
                    "eb_presence": best_match["module"].get("presence_percentage", 0),
                    "common_keywords": best_match["similarity"]["common_keywords"]
                })
            else:
                discrepancies.append({
                    "real_module": real_mod["name"],
                    "real_coverage": round(real_mod.get("coverage", 0), 1),
                    "best_eb_match": best_match["module"]["name"] if best_match else "Nessuno",
                    "similarity": round(best_sim, 1) if best_match else 0
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
            return "✅ Ottima concordanza - il mapping sul framework ideale riflette accuratamente i contenuti reali"
        elif rate >= 60:
            return "👍 Buona concordanza - il mapping è generalmente affidabile con alcune differenze"
        elif rate >= 40:
            return "⚠️ Concordanza moderata - ci sono differenze significative tra le due prospettive"
        else:
            return "❌ Bassa concordanza - le due analisi danno risultati molto diversi, rivedere il mapping"
    
    def _analyze_ideal_coverage(self, ideal_modules: List[Dict], real_modules: List[Dict]) -> Dict:
        """Analizza quanto del framework ideale è coperto dal reale."""
        coverage_data = []
        
        for ideal_mod in ideal_modules:
            best_match = None
            best_sim = 0
            
            for real_mod in real_modules:
                sim = self._calculate_semantic_similarity(ideal_mod, real_mod)
                if sim["combined_score"] > best_sim:
                    best_sim = sim["combined_score"]
                    best_match = real_mod
            
            coverage_data.append({
                "module": ideal_mod["name"],
                "has_match": best_match is not None and best_sim >= 20,
                "match_name": best_match["name"] if best_match and best_sim >= 20 else None,
                "similarity": round(best_sim, 1),
                "real_coverage": round(best_match.get("coverage", 0), 1) if best_match else 0
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
        eb_modules: List[Dict],
        coverage_map: Dict = None
    ) -> Dict:
        """Identifica opportunità commerciali basate sul confronto."""
        opportunities = []
        
        if coverage_map:
            # Gap formativi dalla coverage map
            for gap in coverage_map.get("uncovered_sources", []):
                opportunities.append({
                    "type": "gap_formativo",
                    "priority": "alta",
                    "module": gap["module"],
                    "description": f"Il modulo '{gap['module']}' del framework Zanichelli NON ha corrispondenza nei programmi reali",
                    "action": "Verificare se il modulo è obsoleto o se serve materiale didattico aggiuntivo"
                })
            
            # Contenuti emergenti CORE
            for em in coverage_map.get("unmapped_targets", []):
                is_core = em.get("category", "").upper() == "CORE"
                if is_core or em.get("presence", 0) >= 50:
                    opportunities.append({
                        "type": "contenuto_emergente",
                        "priority": "alta" if is_core else "media",
                        "module": em["module"],
                        "presence": em.get("presence", 0),
                        "description": f"Il tema '{em['module']}' è insegnato nel {em.get('presence', 0):.0f}% delle classi ma NON è nel framework Zanichelli",
                        "action": "AZIONE PRIORITARIA: Valutare aggiunta al framework o creazione materiale supplementare"
                    })
        
        # Nicchie specifiche dagli EB
        for eb_mod in eb_modules:
            if eb_mod.get("is_specific") and eb_mod.get("presence_percentage", 0) >= 20:
                distinctive = eb_mod.get("distinctive_for", [])
                if distinctive:
                    opportunities.append({
                        "type": "nicchia_specifica",
                        "priority": "media",
                        "module": eb_mod["name"],
                        "target_classes": distinctive,
                        "description": f"Il tema '{eb_mod['name']}' è distintivo per: {', '.join(distinctive)}",
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
    
    def _build_comparison_matrix_v2(
        self,
        ideal_modules: List[Dict],
        real_modules: List[Dict],
        eb_modules: List[Dict]
    ) -> List[Dict]:
        """Costruisce matrice di confronto con nuovo algoritmo semantico."""
        matrix = []
        
        for ideal_mod in ideal_modules:
            row = {
                "ideal_module": ideal_mod["name"],
                "ideal_contents_count": len(ideal_mod.get("contents", [])),
                "real_match": None,
                "real_similarity": 0,
                "real_coverage": 0,
                "eb_matches": [],  # Può avere più match (1:N)
                "eb_best_match": None,
                "eb_best_similarity": 0,
                "eb_category": None,
                "common_keywords": []
            }
            
            # Match con reale
            best_real_sim = 0
            for real_mod in real_modules:
                sim = self._calculate_semantic_similarity(ideal_mod, real_mod)
                if sim["combined_score"] > best_real_sim:
                    best_real_sim = sim["combined_score"]
                    row["real_match"] = real_mod["name"]
                    row["real_similarity"] = round(sim["combined_score"], 1)
                    row["real_coverage"] = round(real_mod.get("coverage", 0), 1)
            
            # Match con evidence-based (può essere multiplo)
            eb_matches = []
            for eb_mod in eb_modules:
                sim = self._calculate_semantic_similarity(ideal_mod, eb_mod)
                if sim["combined_score"] >= 15:  # Soglia minima
                    eb_matches.append({
                        "name": eb_mod["name"],
                        "score": round(sim["combined_score"], 1),
                        "category": eb_mod.get("category", "N/D"),
                        "keywords": sim["common_keywords"][:5]
                    })
            
            eb_matches.sort(key=lambda x: x["score"], reverse=True)
            
            if eb_matches:
                row["eb_matches"] = eb_matches[:3]  # Top 3
                row["eb_best_match"] = eb_matches[0]["name"]
                row["eb_best_similarity"] = eb_matches[0]["score"]
                row["eb_category"] = eb_matches[0]["category"]
                row["common_keywords"] = eb_matches[0]["keywords"]
            
            matrix.append(row)
        
        return matrix
    
    # =========================================================================
    # GENERAZIONE REPORT HTML (aggiornato per v2)
    # =========================================================================
    
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
        .version-badge {{ background: #673ab7; color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.8em; margin-left: 10px; }}
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
        .gap-item.media {{ background: #fff8e1; border-left-color: #ff9800; }}
        .emergent-item {{ background: #fff3e0; border-left: 4px solid #ff9800; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0; }}
        .emergent-item.core {{ background: #ffebee; border-left-color: #f44336; }}
        .covered-item {{ background: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0; }}
        .opportunity {{ background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin: 10px 0; }}
        .opportunity.alta {{ border-left: 4px solid #f44336; }}
        .opportunity.media {{ border-left: 4px solid #ff9800; }}
        .opportunity.bassa {{ border-left: 4px solid #4caf50; }}
        .priority-badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; font-weight: 500; }}
        .priority-badge.alta {{ background: #ffcdd2; color: #c62828; }}
        .priority-badge.media {{ background: #ffe0b2; color: #e65100; }}
        .priority-badge.bassa {{ background: #c8e6c9; color: #2e7d32; }}
        .type-badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; margin-left: 10px; background: #e3f2fd; color: #1565c0; }}
        .keyword-tag {{ display: inline-block; background: #e8eaf6; padding: 2px 8px; margin: 2px; border-radius: 10px; font-size: 0.8em; color: #3f51b5; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 0.9em; }}
        th, td {{ padding: 12px 8px; text-align: left; border-bottom: 1px solid #e0e0e0; }}
        th {{ background: #f5f5f5; font-weight: 600; color: #333; }}
        tr:hover {{ background: #fafafa; }}
        .match-high {{ color: #2e7d32; font-weight: 500; }}
        .match-medium {{ color: #f57c00; }}
        .match-low {{ color: #c62828; }}
        .concordance-bar {{ height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .concordance-fill {{ height: 100%; border-radius: 10px; }}
        .concordance-fill.high {{ background: linear-gradient(90deg, #4caf50, #81c784); }}
        .concordance-fill.medium {{ background: linear-gradient(90deg, #ff9800, #ffb74d); }}
        .concordance-fill.low {{ background: linear-gradient(90deg, #f44336, #e57373); }}
        .multi-match {{ font-size: 0.85em; color: #666; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #888; text-align: center; }}
    </style>
</head>
<body>
<div class="container">
    <h1>Confronto Framework - {self.materia.replace('_', ' ').title()} <span class="version-badge">v2.0</span></h1>
    <p>Analisi comparativa con <strong>Coverage Mapping Semantico</strong> tra Framework Ideale, Reale e Evidence-Based</p>
    <p><small>Generato il {comparison.get('generated_at', '')[:16].replace('T', ' ')}</small></p>
    
    <div class="summary">
        <div class="summary-card ideal">
            <div class="number">{comparison.get('modules_count', {}).get('ideal', 0)}</div>
            <div class="label">Moduli Framework Ideale</div>
            <div class="status">{'✓ Caricato' if comparison.get('frameworks_found', {}).get('ideal') else '✗ Non trovato'}</div>
        </div>
        <div class="summary-card real">
            <div class="number">{comparison.get('modules_count', {}).get('real', 0)}</div>
            <div class="label">Moduli Framework Reale</div>
            <div class="status">{'✓ Caricato' if comparison.get('frameworks_found', {}).get('real') else '✗ Non trovato'}</div>
        </div>
        <div class="summary-card evidence">
            <div class="number">{comparison.get('modules_count', {}).get('evidence_based', 0)}</div>
            <div class="label">Moduli Evidence-Based</div>
            <div class="status">{'✓ Caricato' if comparison.get('frameworks_found', {}).get('evidence_based') else '✗ Non trovato'}</div>
        </div>
    </div>
"""
        
        # Sezione Gap Formativi (aggiornata)
        gaps = comparison.get("analysis", {}).get("gap_formativi", {})
        if gaps:
            coverage_pct = gaps.get("coverage_percentage", 0)
            bar_class = "high" if coverage_pct >= 70 else ("medium" if coverage_pct >= 50 else "low")
            
            html += f"""
    <h2>📊 Gap Formativi - Copertura Framework Ideale</h2>
    <p>{gaps.get('description', '')}</p>
    
    <div class="metric-row">
        <div class="metric">
            <div class="value">{gaps.get('total_ideal', 0)}</div>
            <div class="label">Moduli Ideali</div>
        </div>
        <div class="metric">
            <div class="value" style="color: #2e7d32;">{gaps.get('fully_covered', 0)}</div>
            <div class="label">Coperti (&ge;40%)</div>
        </div>
        <div class="metric">
            <div class="value" style="color: #ff9800;">{gaps.get('partially_covered', 0)}</div>
            <div class="label">Parziali (15-40%)</div>
        </div>
        <div class="metric">
            <div class="value" style="color: #f44336;">{gaps.get('not_covered', 0)}</div>
            <div class="label">Non Coperti</div>
        </div>
    </div>
    
    <div class="concordance-bar">
        <div class="concordance-fill {bar_class}" style="width: {min(coverage_pct, 100)}%;"></div>
    </div>
    <p style="text-align: center; font-weight: bold; color: {'#2e7d32' if coverage_pct >= 70 else ('#ff9800' if coverage_pct >= 50 else '#f44336')};">
        Copertura: {coverage_pct:.0f}%
    </p>
"""
            
            # Moduli coperti
            if gaps.get("covered"):
                html += """
    <h3>✅ Moduli Ideali Coperti</h3>
"""
                for cov in gaps.get("covered", [])[:5]:  # Top 5
                    html += f"""
    <div class="covered-item">
        <strong>{cov.get('ideal_module', 'N/D')}</strong> → <em>{cov.get('best_match', 'N/D')}</em>
        <span class="priority-badge {'alta' if cov.get('best_score', 0) >= 60 else 'media'}">{cov.get('best_score', 0):.0f}%</span>
        <span class="type-badge">{cov.get('eb_category', 'N/D')}</span>
        <span class="type-badge">{cov.get('coverage_type', '1:1')}</span>
        <br><small>Keywords comuni: {', '.join(cov.get('common_keywords', [])[:5])}</small>
    </div>
"""
            
            # Gap (non coperti)
            if gaps.get("gaps"):
                html += """
    <h3>❌ Moduli Non Coperti o Parziali</h3>
"""
                for gap in gaps.get("gaps", []):
                    severity = gap.get('severity', 'media')
                    html += f"""
    <div class="gap-item {severity}">
        <strong>{gap.get('module', 'N/D')}</strong>
        <span class="priority-badge {severity}">{severity.upper()}</span>
        <br><small>{gap.get('reason', '')}</small>
    </div>
"""
        
        # Sezione Contenuti Emergenti (aggiornata)
        emergent = comparison.get("analysis", {}).get("contenuti_emergenti", {})
        if emergent:
            html += f"""
    <h2>🆕 Contenuti Emergenti</h2>
    <p>{emergent.get('description', '')}</p>
    
    <div class="metric-row">
        <div class="metric">
            <div class="value">{emergent.get('total_eb', 0)}</div>
            <div class="label">Moduli Evidence-Based</div>
        </div>
        <div class="metric">
            <div class="value" style="color: #2e7d32;">{emergent.get('mapped_count', 0)}</div>
            <div class="label">Mappati su Ideale</div>
        </div>
        <div class="metric">
            <div class="value" style="color: #ff9800;">{emergent.get('emergent_count', 0)}</div>
            <div class="label">Emergenti (nuovi)</div>
        </div>
    </div>
"""
            
            if emergent.get("emergent"):
                html += """
    <h3>⚠️ Moduli Emergenti (NON nel framework ideale)</h3>
"""
                for em in emergent.get("emergent", []):
                    is_core = em.get("is_core", False) or "CORE" in em.get("category", "").upper()
                    html += f"""
    <div class="emergent-item {'core' if is_core else ''}">
        <strong>{em.get('module', 'N/D')}</strong>
        <span class="type-badge">{em.get('category', 'N/D')}</span>
        <span class="priority-badge {'alta' if is_core else 'media'}">{em.get('presence', 0):.0f}% classi</span>
        <br><em>{em.get('interpretation', '')}</em>
        <br><small>Contenuti: {', '.join(em.get('contents', [])[:5])}</small>
        {f"<br><small>Distintivo per: {', '.join(em.get('distinctive_for', []))}</small>" if em.get('distinctive_for') else ""}
    </div>
"""
        
        # Sezione Validazione
        validation = comparison.get("analysis", {}).get("validazione", {})
        if validation:
            conc_rate = validation.get("concordance_rate", 0)
            bar_class = "high" if conc_rate >= 70 else ("medium" if conc_rate >= 50 else "low")
            
            html += f"""
    <h2>🔍 Validazione Mapping</h2>
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
    <h2>💼 Opportunità Commerciali</h2>
    <p>{opportunities.get('description', '')}</p>
    
    <div class="metric-row">
        <div class="metric">
            <div class="value">{opportunities.get('total', 0)}</div>
            <div class="label">Totale</div>
        </div>
        <div class="metric">
            <div class="value" style="color: #f44336;">{opportunities.get('by_type', {}).get('gap_formativo', 0)}</div>
            <div class="label">Gap Formativi</div>
        </div>
        <div class="metric">
            <div class="value" style="color: #ff9800;">{opportunities.get('by_type', {}).get('contenuto_emergente', 0)}</div>
            <div class="label">Contenuti Emergenti</div>
        </div>
        <div class="metric">
            <div class="value" style="color: #2196f3;">{opportunities.get('by_type', {}).get('nicchia_specifica', 0)}</div>
            <div class="label">Nicchie</div>
        </div>
    </div>
"""
            
            for opp in opportunities.get("opportunities", [])[:10]:  # Top 10
                html += f"""
    <div class="opportunity {opp.get('priority', 'media')}">
        <span class="priority-badge {opp.get('priority', 'media')}">{opp.get('priority', 'N/D').upper()}</span>
        <span class="type-badge">{opp.get('type', '').replace('_', ' ').title()}</span>
        <h4 style="margin: 10px 0 5px 0;">{opp.get('module', 'N/D')}</h4>
        <p style="margin: 5px 0;">{opp.get('description', '')}</p>
        <p style="margin: 5px 0; color: #1565c0;"><strong>Azione:</strong> {opp.get('action', '')}</p>
    </div>
"""
        
        # Matrice di Confronto (aggiornata per v2)
        matrix = comparison.get("comparison_matrix", [])
        if matrix:
            html += """
    <h2>📋 Matrice di Confronto Dettagliata</h2>
    <table>
        <thead>
            <tr>
                <th style="width: 20%;">Modulo Ideale</th>
                <th style="width: 15%;">Match Reale</th>
                <th style="width: 8%;">Sim.</th>
                <th style="width: 20%;">Match Evidence-Based</th>
                <th style="width: 8%;">Sim.</th>
                <th style="width: 10%;">Categoria</th>
                <th style="width: 19%;">Keywords Comuni</th>
            </tr>
        </thead>
        <tbody>
"""
            for row in matrix:
                real_sim = row.get("real_similarity", 0)
                eb_sim = row.get("eb_best_similarity", 0)
                real_class = "match-high" if real_sim >= 50 else ("match-medium" if real_sim >= 25 else "match-low")
                eb_class = "match-high" if eb_sim >= 50 else ("match-medium" if eb_sim >= 25 else "match-low")
                
                # Multi-match indicator
                eb_matches = row.get("eb_matches", [])
                multi_match = f"<br><span class='multi-match'>+{len(eb_matches)-1} altri</span>" if len(eb_matches) > 1 else ""
                
                keywords_html = " ".join([f"<span class='keyword-tag'>{kw}</span>" for kw in row.get("common_keywords", [])[:3]])
                
                html += f"""
            <tr>
                <td><strong>{row.get('ideal_module', 'N/D')}</strong></td>
                <td>{row.get('real_match', '-') or '-'}</td>
                <td class="{real_class}">{real_sim:.0f}%</td>
                <td>{row.get('eb_best_match', '-') or '-'}{multi_match}</td>
                <td class="{eb_class}">{eb_sim:.0f}%</td>
                <td>{row.get('eb_category', '-') or '-'}</td>
                <td>{keywords_html}</td>
            </tr>
"""
            html += """
        </tbody>
    </table>
"""
        
        # Footer
        html += f"""
    <div class="footer">
        <p><strong>CoreX PromoIntelligence - Framework Comparator v2.0</strong></p>
        <p>Algoritmo: Coverage Mapping Semantico con supporto relazioni 1:N / N:1</p>
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
    """
    comparator = FrameworkComparator(materia)
    
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
    """
    comparator = FrameworkComparator(materia)
    comparison = comparator.compare()
    html = comparator.generate_html_report(comparison)
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    
    return comparison, html
