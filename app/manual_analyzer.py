"""
CoreX - Manual Analyzer v1.0
Analizza manuali rispetto a framework IDEALE e REALE
Confronta più manuali tra loro
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict
import re


class ManualAnalyzer:
    """
    Analizza indici di manuali e li confronta con:
    - Framework IDEALE (da frameworks/)
    - Framework REALE (da archivio analisi)
    - Altri manuali
    """
    
    def __init__(self, manuali_dir: Path = None, frameworks_dir: Path = None):
        self.manuali_dir = manuali_dir or Path("data/manuali")
        self.frameworks_dir = frameworks_dir or Path("frameworks")
        self.archivio_dir = Path("archivio")

        
        # Espansione semantica per matching (eredita da framework_adapter)
        self.semantic_expansions = self._load_semantic_expansions()
    
    def _load_semantic_expansions(self) -> Dict[str, List[str]]:
        """Carica espansioni semantiche per il matching"""
        return {
            # Struttura atomi e legami
            "orbitali atomici e ibridazione": ["orbitali", "ibridazione", "sp3", "sp2", "sp", "orbitale", "orbitali atomici"],
            "legami covalenti": ["legame covalente", "legame sigma", "legame pi", "legame chimico", "legami", "legame covalente polare"],
            "polarità molecolare": ["polarità", "momento dipolare", "dipolo", "molecola polare", "elettronegatività"],
            "forze intermolecolari": ["forze di van der waals", "legame idrogeno", "forze di london", "interazioni intermolecolari", "forze dipolo-dipolo"],
            
            # Idrocarburi
            "alcani": ["alcani", "metano", "etano", "propano", "idrocarburi saturi", "paraffine"],
            "alceni": ["alceni", "alcheni", "etene", "propene", "idrocarburi insaturi", "doppio legame"],
            "alchini": ["alchini", "acetilene", "etino", "triplo legame"],
            "cicloalcani": ["cicloalcani", "ciclopropano", "cicloesano", "conformazioni cicliche"],
            "isomeria": ["isomeria", "isomeri", "isomeria strutturale", "isomeria geometrica", "isomeri di catena", "isomeria di posizione"],
            "nomenclatura": ["nomenclatura", "iupac", "nomenclatura iupac", "regole di nomenclatura"],
            
            # Stereochimica
            "stereochimica": ["stereochimica", "stereoisomeri", "configurazione"],
            "chiralità": ["chiralità", "carbonio chirale", "centro stereogenico", "stereocentro", "carbonio asimmetrico", "chirale"],
            "enantiomeri": ["enantiomeri", "isomeria ottica", "attività ottica", "potere rotatorio", "configurazione r/s"],
            "diastereoisomeri": ["diastereoisomeri", "diastereomeri", "isomeri cis-trans"],
            "proiezioni di fischer": ["fischer", "proiezioni di fischer", "proiezione di fischer"],
            "proiezioni di newman": ["newman", "proiezioni di newman", "conformazioni"],
            "racemico": ["racemico", "racemizzazione", "miscela racemica"],
            
            # Gruppi funzionali
            "alcoli": ["alcoli", "alcool", "gruppo ossidrile", "oh", "etanolo", "metanolo"],
            "eteri": ["eteri", "etere", "legame etereo"],
            "fenoli": ["fenoli", "fenolo", "idrossibenzene"],
            "aldeidi": ["aldeidi", "aldeide", "gruppo aldeidico", "formile"],
            "chetoni": ["chetoni", "chetone", "gruppo chetonico", "carbonile"],
            "acidi carbossilici": ["acidi carbossilici", "acido carbossilico", "gruppo carbossilico", "cooh"],
            "esteri": ["esteri", "estere", "esterificazione"],
            "ammidi": ["ammidi", "ammide", "legame ammidico"],
            "ammine": ["ammine", "ammina", "gruppo amminico", "ammina primaria", "ammina secondaria", "ammina terziaria"],
            "alogenuri alchilici": ["alogenuri alchilici", "alogenoalcani", "cloroalcani"],
            
            # Meccanismi di reazione
            "sostituzione nucleofila": ["sostituzione nucleofila", "sn1", "sn2", "nucleofilo"],
            "sostituzione elettrofila": ["sostituzione elettrofila", "elettrofilo", "sea"],
            "addizione elettrofila": ["addizione elettrofila", "addizione ad alcheni"],
            "addizione nucleofila": ["addizione nucleofila", "addizione al carbonile"],
            "eliminazione": ["eliminazione", "e1", "e2", "beta-eliminazione", "deidroalogenazione"],
            "radicali": ["radicali", "radicali liberi", "reazioni radicaliche", "omolisi"],
            "meccanismo di reazione": ["meccanismo", "meccanismi", "frecce curve", "intermedi di reazione", "stato di transizione"],
            
            # Composti aromatici
            "benzene": ["benzene", "anello benzenico", "anello aromatico"],
            "aromaticità": ["aromaticità", "aromatici", "regola di hückel", "composti aromatici"],
            "sostituzione aromatica": ["sostituzione aromatica", "sostituzione elettrofila aromatica", "sea"],
            "eterocicli": ["eterocicli", "eterociclici", "piridina", "pirrolo", "furano", "tiofene", "composti eterociclici"],
            
            # Bio-organica
            "amminoacidi": ["amminoacidi", "aminoacidi", "alfa-amminoacidi"],
            "proteine": ["proteine", "struttura proteica", "legame peptidico", "polipeptidi"],
            "carboidrati": ["carboidrati", "zuccheri", "saccaridi", "glucidi"],
            "monosaccaridi": ["monosaccaridi", "glucosio", "fruttosio", "galattosio"],
            "disaccaridi": ["disaccaridi", "saccarosio", "maltosio", "lattosio"],
            "polisaccaridi": ["polisaccaridi", "amido", "cellulosa", "glicogeno"],
            "lipidi": ["lipidi", "grassi", "acidi grassi", "trigliceridi"],
            "acidi nucleici": ["acidi nucleici", "dna", "rna", "nucleotidi", "nucleosidi"],
            
            # Spettroscopia
            "spettroscopia ir": ["infrarosso", "ir", "spettroscopia ir", "spettroscopia infrarossa"],
            "spettroscopia nmr": ["nmr", "risonanza magnetica nucleare", "spettroscopia nmr", "chemical shift", "1h-nmr", "13c-nmr"],
            "spettrometria di massa": ["spettrometria di massa", "mass spectrometry", "ms", "frammentazione"],
            "spettroscopia uv-vis": ["uv-vis", "ultravioletto", "spettroscopia uv"],
            
            # Reazioni specifiche
            "grignard": ["grignard", "reattivo di grignard", "organomagnesio"],
            "aldolica": ["aldolica", "condensazione aldolica", "reazione aldolica"],
            "claisen": ["claisen", "condensazione di claisen"],
            "wittig": ["wittig", "reazione di wittig"],
            "diels-alder": ["diels-alder", "cicloaddizione"],
            
            # Polimeri
            "polimeri": ["polimeri", "polimerizzazione", "monomeri", "macromolecole"],
            "poliaddizione": ["poliaddizione", "polimerizzazione a catena", "polimerizzazione radicalica"],
            "policondensazione": ["policondensazione", "polimerizzazione a stadi"],
        }
    
    # =========================================================
    # GESTIONE MANUALI
    # =========================================================
    
    def get_available_subjects(self) -> List[str]:
        """Restituisce le materie disponibili nella cartella manuali"""
        if not self.manuali_dir.exists():
            return []
        
        subjects = []
        for d in sorted(self.manuali_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                subjects.append(d.name)
        return subjects
    
    def get_manuals_for_subject(self, subject: str) -> Dict[str, List[Dict]]:
        """
        Restituisce i manuali disponibili per una materia, divisi per tipo.
        
        Returns:
            {
                "zanichelli": [{"id": ..., "title": ..., "path": ...}, ...],
                "competitor": [{"id": ..., "title": ..., "path": ...}, ...]
            }
        """
        subject_dir = self.manuali_dir / subject / "indici"
        result = {"zanichelli": [], "competitor": []}
        
        if not subject_dir.exists():
            return result
        
        # Cerca in sottocartelle
        for type_dir in subject_dir.iterdir():
            if type_dir.is_dir():
                dir_name_lower = type_dir.name.lower()
                
                if "zanichelli" in dir_name_lower:
                    manual_type = "zanichelli"
                elif "competitor" in dir_name_lower:
                    manual_type = "competitor"
                else:
                    manual_type = "competitor"  # default
                
                for json_file in type_dir.glob("*.json"):
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            result[manual_type].append({
                                "id": data.get("id", json_file.stem),
                                "title": data.get("title", json_file.stem),
                                "author": data.get("author", "N/D"),
                                "publisher": data.get("publisher", "N/D"),
                                "path": json_file,
                                "n_chapters": len(data.get("chapters", []))
                            })
                    except Exception as e:
                        print(f"Errore caricamento {json_file}: {e}")
        
        # Cerca anche file JSON direttamente nella cartella indici
        for json_file in subject_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    manual_type = data.get("type", "competitor")
                    if manual_type not in result:
                        manual_type = "competitor"
                    
                    result[manual_type].append({
                        "id": data.get("id", json_file.stem),
                        "title": data.get("title", json_file.stem),
                        "author": data.get("author", "N/D"),
                        "publisher": data.get("publisher", "N/D"),
                        "path": json_file,
                        "n_chapters": len(data.get("chapters", []))
                    })
            except Exception as e:
                print(f"Errore caricamento {json_file}: {e}")
        
        return result
    
    def load_manual(self, path: Path) -> Optional[Dict]:
        """Carica un manuale JSON"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore caricamento manuale {path}: {e}")
            return None
    
    def extract_manual_topics(self, manual: Dict) -> List[Dict]:
        """
        Estrae tutti gli argomenti (capitoli + sezioni) da un manuale.
        
        Returns:
            Lista di {"text": ..., "type": "chapter"|"section", "chapter_num": ..., "section_num": ...}
        """
        topics = []
        
        for chapter in manual.get("chapters", []):
            # Aggiungi titolo capitolo
            topics.append({
                "text": chapter.get("title", ""),
                "type": "chapter",
                "chapter_num": chapter.get("number", 0),
                "section_num": None,
                "page_start": chapter.get("page_start", None)
            })
            
            # Aggiungi sezioni
            for section in chapter.get("sections", []):
                topics.append({
                    "text": section.get("title", ""),
                    "type": "section",
                    "chapter_num": chapter.get("number", 0),
                    "section_num": section.get("number", ""),
                    "page_start": section.get("page_start", None)
                })
        
        return topics
    
    # =========================================================
    # MATCHING SEMANTICO
    # =========================================================
    
    def _normalize_text(self, text: str) -> str:
        """Normalizza testo per matching"""
        text = text.lower().strip()
        # Rimuovi punteggiatura eccetto trattini
        text = re.sub(r'[^\w\s\-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _text_matches_content(self, text: str, content: str, threshold: float = 0.5) -> Tuple[bool, float]:
        """
        Verifica se un testo (titolo capitolo/sezione) corrisponde a un contenuto del framework.
        
        Returns:
            (match: bool, score: float 0-1)
        """
        text_norm = self._normalize_text(text)
        content_norm = self._normalize_text(content)
        
        # Match esatto
        if content_norm in text_norm or text_norm in content_norm:
            return True, 1.0
        
        # Match tramite espansione semantica
        for key, variants in self.semantic_expansions.items():
            key_norm = self._normalize_text(key)
            
            # Se il contenuto del framework matcha con una chiave
            if key_norm in content_norm or content_norm in key_norm:
                for variant in variants:
                    variant_norm = self._normalize_text(variant)
                    if variant_norm in text_norm or text_norm in variant_norm:
                        return True, 0.9
            
            # Se il testo del manuale contiene una variante
            for variant in variants:
                variant_norm = self._normalize_text(variant)
                if variant_norm in text_norm:
                    if key_norm in content_norm or content_norm in key_norm:
                        return True, 0.85
        
        # Match per parole chiave
        text_words = set(w for w in text_norm.split() if len(w) > 3)
        content_words = set(w for w in content_norm.split() if len(w) > 3)
        
        if text_words and content_words:
            common = text_words & content_words
            score = len(common) / max(len(content_words), 1)
            
            if score >= threshold:
                return True, score
        
        return False, 0.0
    
    # =========================================================
    # ANALISI VS FRAMEWORK IDEALE
    # =========================================================
    
    def analyze_manual_vs_ideal(self, manual: Dict, ideal_framework: Dict) -> Dict:
        """
        Confronta un manuale con il framework IDEALE.
        
        Returns:
            {
                "manual_info": {...},
                "framework_info": {...},
                "overall_coverage": float,
                "modules_analysis": [...],
                "uncovered_chapters": [...],
                "gaps": {...}
            }
        """
        manual_topics = self.extract_manual_topics(manual)
        modules = ideal_framework.get("syllabus_modules", [])
        
        modules_analysis = []
        all_matched_topics = set()  # Per tracciare quali topic sono stati matchati
        
        for module in modules:
            module_id = module.get("id", 0)
            module_name = module.get("name", "")
            core_contents = module.get("core_contents", [])
            
            content_matches = []
            matched_topics_for_module = []
            
            for content in core_contents:
                best_match = None
                best_score = 0
                
                for topic in manual_topics:
                    is_match, score = self._text_matches_content(topic["text"], content)
                    if is_match and score > best_score:
                        best_score = score
                        best_match = topic
                
                if best_match:
                    content_matches.append({
                        "content": content,
                        "matched_by": best_match["text"],
                        "type": best_match["type"],
                        "chapter": best_match["chapter_num"],
                        "section": best_match["section_num"],
                        "score": round(best_score, 2)
                    })
                    all_matched_topics.add(best_match["text"])
                    matched_topics_for_module.append(best_match)
                else:
                    content_matches.append({
                        "content": content,
                        "matched_by": None,
                        "score": 0
                    })
            
            # Calcola copertura modulo
            covered = sum(1 for cm in content_matches if cm["matched_by"])
            coverage_pct = (covered / len(core_contents) * 100) if core_contents else 0
            
            # Trova capitoli principali che coprono questo modulo
            chapters_involved = list(set(
                t["chapter_num"] for t in matched_topics_for_module if t["type"] == "chapter"
            ))
            
            modules_analysis.append({
                "module_id": module_id,
                "module_name": module_name,
                "coverage_percentage": round(coverage_pct, 1),
                "contents_covered": covered,
                "contents_total": len(core_contents),
                "content_matches": content_matches,
                "chapters_involved": chapters_involved,
                "status": self._coverage_to_status(coverage_pct)
            })
        
        # Trova capitoli del manuale NON matchati (contenuto extra)
        uncovered_chapters = []
        for topic in manual_topics:
            if topic["type"] == "chapter" and topic["text"] not in all_matched_topics:
                # Verifica se almeno una sezione del capitolo è matchata
                chapter_sections_matched = any(
                    t["text"] in all_matched_topics 
                    for t in manual_topics 
                    if t["type"] == "section" and t["chapter_num"] == topic["chapter_num"]
                )
                if not chapter_sections_matched:
                    uncovered_chapters.append({
                        "chapter_num": topic["chapter_num"],
                        "title": topic["text"]
                    })
        
        # Calcola copertura complessiva
        total_contents = sum(m["contents_total"] for m in modules_analysis)
        total_covered = sum(m["contents_covered"] for m in modules_analysis)
        overall_coverage = (total_covered / total_contents * 100) if total_contents > 0 else 0
        
        # Gap analysis
        missing_contents = []
        for m in modules_analysis:
            for cm in m["content_matches"]:
                if not cm["matched_by"]:
                    missing_contents.append({
                        "content": cm["content"],
                        "module": m["module_name"]
                    })
        
        return {
            "manual_info": {
                "id": manual.get("id", "N/D"),
                "title": manual.get("title", "N/D"),
                "author": manual.get("author", "N/D"),
                "publisher": manual.get("publisher", "N/D"),
                "n_chapters": len(manual.get("chapters", [])),
                "n_sections": sum(len(ch.get("sections", [])) for ch in manual.get("chapters", []))
            },
            "framework_info": {
                "name": ideal_framework.get("framework", {}).get("name", "N/D"),
                "n_modules": len(modules),
                "total_contents": total_contents
            },
            "overall_coverage": round(overall_coverage, 1),
            "judgment": self._coverage_to_judgment(overall_coverage),
            "modules_analysis": modules_analysis,
            "uncovered_chapters": uncovered_chapters,
            "gaps": {
                "missing_in_manual": missing_contents,
                "extra_in_manual": uncovered_chapters
            },
            "analysis_date": datetime.now().isoformat()
        }
    
    # =========================================================
    # ANALISI VS FRAMEWORK REALE
    # =========================================================
    
    def get_available_real_frameworks(self, subject: str = None) -> List[Dict]:
        """
        Restituisce le analisi archiviate che contengono framework reali.
        """
        analyses = []
        
        # Cerca nell'archivio
        archivio_dir = Path("archivio")
        if archivio_dir.exists():
            for d in sorted(archivio_dir.iterdir(), reverse=True):
                if d.is_dir():
                    fw_file = d / "framework_aggiornato.json"
                    meta_file = d / "analisi.json"
                    
                    if fw_file.exists() and meta_file.exists():
                        try:
                            with open(meta_file, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            
                            # Filtra per materia se specificata
                            if subject and meta.get("materia", "").lower() != subject.lower():
                                continue
                            
                            analyses.append({
                                "id": d.name,
                                "name": meta.get("name", d.name),
                                "materia": meta.get("materia", "N/D"),
                                "classi": meta.get("classi", []),
                                "coverage": meta.get("coverage", 0),
                                "n_syllabus": meta.get("n_syllabus", 0),
                                "date": meta.get("created", "")[:10],
                                "framework_path": fw_file,
                                "path": d
                            })
                        except Exception as e:
                            print(f"Errore lettura {meta_file}: {e}")
        
        # Cerca anche in analisi_corrente
        current_dir = Path("data/analisi_corrente")
        fw_current = current_dir / "framework_aggiornato.json"
        meta_current = current_dir / "analisi.json"
        
        if fw_current.exists() and meta_current.exists():
            try:
                with open(meta_current, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                
                if not subject or meta.get("materia", "").lower() == subject.lower():
                    analyses.insert(0, {
                        "id": "current",
                        "name": f"[CORRENTE] {meta.get('name', 'Analisi')}",
                        "materia": meta.get("materia", "N/D"),
                        "classi": meta.get("classi", []),
                        "coverage": meta.get("coverage", 0),
                        "n_syllabus": meta.get("n_syllabus", 0),
                        "date": meta.get("created", "")[:10],
                        "framework_path": fw_current,
                        "path": current_dir
                    })
            except:
                pass
        
        return analyses
    
    def load_real_framework(self, path: Path) -> Optional[Dict]:
        """Carica un framework reale da un'analisi"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore caricamento framework reale {path}: {e}")
            return None
    
    def analyze_manual_vs_real(self, manual: Dict, real_framework: Dict) -> Dict:
        """
        Confronta un manuale con il framework REALE (generato da analisi programmi).
        
        Mostra quanto il manuale copre ciò che viene EFFETTIVAMENTE insegnato.
        """
        manual_topics = self.extract_manual_topics(manual)
        modules = real_framework.get("syllabus_modules", [])
        
        modules_analysis = []
        
        for module in modules:
            module_name = module.get("name", "")
            # Nel framework reale, usiamo i matched_concepts come riferimento
            real_concepts = module.get("matched_concepts", [])
            module_coverage_real = module.get("coverage_percentage", 0)
            
            # Cerca match tra titoli manuale e concetti reali
            matched_concepts = []
            for concept in real_concepts[:20]:  # Top 20 concetti per modulo
                concept_name = concept.get("name", "")
                concept_freq = concept.get("frequency", 0)
                
                best_match = None
                best_score = 0
                
                for topic in manual_topics:
                    is_match, score = self._text_matches_content(topic["text"], concept_name)
                    if is_match and score > best_score:
                        best_score = score
                        best_match = topic
                
                matched_concepts.append({
                    "concept": concept_name,
                    "frequency_in_programs": round(concept_freq, 1),
                    "found_in_manual": best_match["text"] if best_match else None,
                    "chapter": best_match["chapter_num"] if best_match else None,
                    "match_score": round(best_score, 2)
                })
            
            # Calcola copertura
            covered = sum(1 for mc in matched_concepts if mc["found_in_manual"])
            coverage_pct = (covered / len(matched_concepts) * 100) if matched_concepts else 0
            
            # Calcola "importanza pesata" (concetti più frequenti pesano di più)
            weighted_coverage = 0
            total_weight = 0
            for mc in matched_concepts:
                weight = mc["frequency_in_programs"]
                total_weight += weight
                if mc["found_in_manual"]:
                    weighted_coverage += weight
            
            weighted_pct = (weighted_coverage / total_weight * 100) if total_weight > 0 else 0
            
            modules_analysis.append({
                "module_id": module.get("id", 0),
                "module_name": module_name,
                "real_coverage_in_programs": round(module_coverage_real, 1),
                "manual_coverage": round(coverage_pct, 1),
                "weighted_coverage": round(weighted_pct, 1),
                "concepts_matched": covered,
                "concepts_total": len(matched_concepts),
                "matched_concepts": matched_concepts,
                "status": module.get("status", "N/D")
            })
        
        # Calcolo complessivo
        total_concepts = sum(m["concepts_total"] for m in modules_analysis)
        total_matched = sum(m["concepts_matched"] for m in modules_analysis)
        overall_coverage = (total_matched / total_concepts * 100) if total_concepts > 0 else 0
        
        # Weighted overall
        all_weighted_cov = [m["weighted_coverage"] for m in modules_analysis if m["concepts_total"] > 0]
        overall_weighted = sum(all_weighted_cov) / len(all_weighted_cov) if all_weighted_cov else 0
        
        return {
            "manual_info": {
                "id": manual.get("id", "N/D"),
                "title": manual.get("title", "N/D"),
                "author": manual.get("author", "N/D"),
                "publisher": manual.get("publisher", "N/D"),
                "n_chapters": len(manual.get("chapters", [])),
                "n_sections": sum(len(ch.get("sections", [])) for ch in manual.get("chapters", []))
            },
            "real_framework_info": {
                "name": real_framework.get("framework", {}).get("name", "N/D"),
                "materia": real_framework.get("framework", {}).get("materia", "N/D"),
                "classes_analyzed": real_framework.get("framework", {}).get("classes_analyzed", []),
                "n_syllabus": real_framework.get("overall_statistics", {}).get("n_syllabus_analyzed", 0)
            },
            "overall_coverage": round(overall_coverage, 1),
            "overall_weighted_coverage": round(overall_weighted, 1),
            "judgment": self._coverage_to_judgment(overall_weighted),
            "recommendation": self._get_recommendation(overall_weighted, "real"),
            "modules_analysis": modules_analysis,
            "analysis_date": datetime.now().isoformat()
        }
    
    # =========================================================
    # CONFRONTO TRA MANUALI
    # =========================================================
    
    def compare_manuals(
        self, 
        manuals: List[Dict], 
        reference_framework: Dict = None,
        framework_type: str = "ideal"
    ) -> Dict:
        """
        Confronta più manuali tra loro.
        
        Args:
            manuals: Lista di dict manuali caricati
            reference_framework: Framework di riferimento (ideale o reale)
            framework_type: "ideal" o "real"
            
        Returns:
            Confronto con ranking e analisi comparativa
        """
        if not manuals:
            return {"error": "Nessun manuale da confrontare"}
        
        comparisons = []
        
        for manual in manuals:
            if reference_framework:
                if framework_type == "ideal":
                    analysis = self.analyze_manual_vs_ideal(manual, reference_framework)
                else:
                    analysis = self.analyze_manual_vs_real(manual, reference_framework)
            else:
                # Senza framework, analizza solo struttura
                analysis = self._analyze_manual_structure(manual)
            
            comparisons.append({
                "manual_id": manual.get("id", "N/D"),
                "manual_title": manual.get("title", "N/D"),
                "author": manual.get("author", "N/D"),
                "publisher": manual.get("publisher", "N/D"),
                "n_chapters": len(manual.get("chapters", [])),
                "n_sections": sum(len(ch.get("sections", [])) for ch in manual.get("chapters", [])),
                "coverage": analysis.get("overall_coverage", 0) if reference_framework else None,
                "weighted_coverage": analysis.get("overall_weighted_coverage", analysis.get("overall_coverage", 0)),
                "judgment": analysis.get("judgment", "N/D"),
                "modules_analysis": analysis.get("modules_analysis", []),
                "full_analysis": analysis
            })
        
        # Ordina per copertura (pesata se disponibile)
        if reference_framework:
            comparisons.sort(
                key=lambda x: x.get("weighted_coverage", x.get("coverage", 0)), 
                reverse=True
            )
        
        # Analisi comparativa per modulo
        modules_comparison = self._build_modules_comparison(comparisons, reference_framework)
        
        return {
            "n_manuals": len(manuals),
            "framework_type": framework_type if reference_framework else "none",
            "framework_name": reference_framework.get("framework", {}).get("name", "N/D") if reference_framework else None,
            "ranking": comparisons,
            "modules_comparison": modules_comparison,
            "best_manual": comparisons[0] if comparisons else None,
            "comparison_date": datetime.now().isoformat()
        }
    
    def _build_modules_comparison(self, comparisons: List[Dict], reference_framework: Dict) -> List[Dict]:
        """Costruisce tabella comparativa per modulo"""
        if not reference_framework or not comparisons:
            return []
        
        modules = reference_framework.get("syllabus_modules", [])
        result = []
        
        for module in modules:
            module_name = module.get("name", "")
            module_id = module.get("id", 0)
            
            manual_scores = []
            for comp in comparisons:
                # Trova l'analisi di questo modulo per questo manuale
                mod_analysis = next(
                    (m for m in comp.get("modules_analysis", []) if m.get("module_id") == module_id),
                    None
                )
                
                if mod_analysis:
                    manual_scores.append({
                        "manual": comp["manual_title"],
                        "publisher": comp["publisher"],
                        "coverage": mod_analysis.get("coverage_percentage", mod_analysis.get("manual_coverage", 0)),
                        "status": mod_analysis.get("status", "N/D")
                    })
            
            # Ordina per copertura
            manual_scores.sort(key=lambda x: x["coverage"], reverse=True)
            
            result.append({
                "module_id": module_id,
                "module_name": module_name,
                "manual_scores": manual_scores,
                "best_manual": manual_scores[0]["manual"] if manual_scores else None,
                "avg_coverage": sum(m["coverage"] for m in manual_scores) / len(manual_scores) if manual_scores else 0
            })
        
        return result
    
    def _analyze_manual_structure(self, manual: Dict) -> Dict:
        """Analisi base della struttura del manuale senza framework"""
        chapters = manual.get("chapters", [])
        
        return {
            "manual_info": {
                "id": manual.get("id", "N/D"),
                "title": manual.get("title", "N/D"),
                "author": manual.get("author", "N/D"),
                "publisher": manual.get("publisher", "N/D")
            },
            "structure": {
                "n_chapters": len(chapters),
                "n_sections": sum(len(ch.get("sections", [])) for ch in chapters),
                "chapters": [
                    {
                        "number": ch.get("number", 0),
                        "title": ch.get("title", ""),
                        "n_sections": len(ch.get("sections", []))
                    }
                    for ch in chapters
                ]
            },
            "overall_coverage": 0,
            "judgment": "Analisi strutturale"
        }
    
    # =========================================================
    # GENERAZIONE REPORT HTML
    # =========================================================
    
    def generate_comparison_report_html(self, comparison_result: Dict) -> str:
        """Genera report HTML per confronto manuali"""
        
        ranking = comparison_result.get("ranking", [])
        modules_comparison = comparison_result.get("modules_comparison", [])
        framework_name = comparison_result.get("framework_name", "N/D")
        framework_type = comparison_result.get("framework_type", "none")
        
        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Confronto Manuali - CoreX</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; padding: 20px 40px; 
            background: #f5f7fa; color: #333; line-height: 1.6;
        }}
        .container {{ 
            max-width: 1400px; margin: 0 auto; 
            background: white; padding: 30px 40px; 
            border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.07); 
        }}
        h1 {{ color: #1a237e; border-bottom: 3px solid #3949ab; padding-bottom: 15px; }}
        h2 {{ color: #283593; margin-top: 35px; border-left: 4px solid #3949ab; padding-left: 15px; }}
        .subtitle {{ color: #666; margin-bottom: 25px; }}
        
        .ranking-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .ranking-table th {{ background: #3949ab; color: white; padding: 12px; text-align: left; }}
        .ranking-table td {{ padding: 12px; border-bottom: 1px solid #e0e0e0; }}
        .ranking-table tr:hover {{ background: #f8f9ff; }}
        .ranking-table tr.winner {{ background: #e8f5e9; }}
        
        .rank-badge {{ 
            display: inline-flex; align-items: center; justify-content: center;
            width: 30px; height: 30px; border-radius: 50%; font-weight: bold;
        }}
        .rank-1 {{ background: gold; color: #333; }}
        .rank-2 {{ background: silver; color: #333; }}
        .rank-3 {{ background: #cd7f32; color: white; }}
        .rank-other {{ background: #e0e0e0; color: #666; }}
        
        .coverage-bar {{ 
            width: 100%; height: 20px; background: #e0e0e0; 
            border-radius: 10px; overflow: hidden; 
        }}
        .coverage-fill {{ height: 100%; border-radius: 10px; }}
        .fill-high {{ background: linear-gradient(90deg, #4caf50, #8bc34a); }}
        .fill-medium {{ background: linear-gradient(90deg, #ff9800, #ffc107); }}
        .fill-low {{ background: linear-gradient(90deg, #f44336, #ff5722); }}
        
        .judgment-badge {{
            display: inline-block; padding: 4px 12px; border-radius: 15px;
            font-size: 0.85em; font-weight: 500;
        }}
        .judgment-eccellente {{ background: #c8e6c9; color: #2e7d32; }}
        .judgment-buono {{ background: #dcedc8; color: #558b2f; }}
        .judgment-sufficiente {{ background: #fff3e0; color: #e65100; }}
        .judgment-insufficiente {{ background: #ffcdd2; color: #c62828; }}
        
        .module-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }}
        .module-card {{ 
            background: #f8f9ff; border-radius: 10px; padding: 15px;
            border-left: 4px solid #3949ab;
        }}
        .module-card h4 {{ margin: 0 0 10px 0; color: #1a237e; }}
        
        .manual-bar {{ 
            display: flex; align-items: center; margin: 5px 0;
            font-size: 0.9em;
        }}
        .manual-bar .name {{ width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .manual-bar .bar {{ flex: 1; margin: 0 10px; }}
        .manual-bar .value {{ width: 50px; text-align: right; font-weight: bold; }}
        
        .footer {{ 
            margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0;
            color: #888; font-size: 0.85em; text-align: center;
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>📚 Confronto Manuali</h1>
    <p class="subtitle">
        <strong>{len(ranking)} manuali confrontati</strong> | 
        Framework: {framework_name} ({framework_type.upper()}) |
        Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}
    </p>
    
    <h2>🏆 Ranking Manuali</h2>
    <table class="ranking-table">
        <thead>
            <tr>
                <th style="width:60px;">Rank</th>
                <th>Manuale</th>
                <th>Autore</th>
                <th>Editore</th>
                <th style="width:80px;">Cap.</th>
                <th style="width:200px;">Copertura</th>
                <th style="width:120px;">Giudizio</th>
            </tr>
        </thead>
        <tbody>"""
        
        for i, manual in enumerate(ranking):
            rank = i + 1
            rank_class = f"rank-{rank}" if rank <= 3 else "rank-other"
            row_class = "winner" if rank == 1 else ""
            coverage = manual.get("weighted_coverage", manual.get("coverage", 0)) or 0
            fill_class = "fill-high" if coverage >= 70 else ("fill-medium" if coverage >= 50 else "fill-low")
            judgment = manual.get("judgment", "N/D")
            judgment_class = self._judgment_to_class(judgment)
            
            html += f"""
            <tr class="{row_class}">
                <td><span class="rank-badge {rank_class}">{rank}</span></td>
                <td><strong>{manual['manual_title']}</strong></td>
                <td>{manual['author']}</td>
                <td>{manual['publisher']}</td>
                <td style="text-align:center;">{manual['n_chapters']}</td>
                <td>
                    <div class="coverage-bar">
                        <div class="coverage-fill {fill_class}" style="width:{coverage}%;"></div>
                    </div>
                    <div style="text-align:center; font-weight:bold; margin-top:3px;">{coverage:.1f}%</div>
                </td>
                <td><span class="judgment-badge {judgment_class}">{judgment}</span></td>
            </tr>"""
        
        html += """
        </tbody>
    </table>
    
    <h2>📊 Confronto per Modulo</h2>
    <div class="module-grid">"""
        
        for module in modules_comparison:
            html += f"""
        <div class="module-card">
            <h4>{module['module_name']}</h4>
            <div style="font-size:0.85em; color:#666; margin-bottom:10px;">
                Media: {module['avg_coverage']:.1f}% | Migliore: {module.get('best_manual', 'N/D')}
            </div>"""
            
            for ms in module.get("manual_scores", [])[:5]:
                coverage = ms['coverage']
                fill_class = "fill-high" if coverage >= 70 else ("fill-medium" if coverage >= 50 else "fill-low")
                html += f"""
            <div class="manual-bar">
                <span class="name" title="{ms['manual']}">{ms['manual'][:20]}</span>
                <div class="bar">
                    <div class="coverage-bar" style="height:10px;">
                        <div class="coverage-fill {fill_class}" style="width:{coverage}%;"></div>
                    </div>
                </div>
                <span class="value">{coverage:.0f}%</span>
            </div>"""
            
            html += "</div>"
        
        html += f"""
    </div>
    
    <div class="footer">
        Report generato da <strong>CoreX - Manual Analyzer v1.0</strong> | Zanichelli<br>
        {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    </div>
</div>
</body>
</html>"""
        
        return html
    
    def generate_single_analysis_report_html(self, analysis: Dict, framework_type: str = "ideal") -> str:
        """Genera report HTML per analisi singolo manuale"""
        
        manual_info = analysis.get("manual_info", {})
        modules = analysis.get("modules_analysis", [])
        overall = analysis.get("overall_coverage", 0)
        judgment = analysis.get("judgment", "N/D")
        
        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Analisi Manuale - {manual_info.get('title', 'N/D')}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; padding: 20px 40px; 
            background: #f5f7fa; color: #333; line-height: 1.6;
        }}
        .container {{ 
            max-width: 1200px; margin: 0 auto; 
            background: white; padding: 30px 40px; 
            border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.07); 
        }}
        h1 {{ color: #1a237e; border-bottom: 3px solid #3949ab; padding-bottom: 15px; }}
        h2 {{ color: #283593; margin-top: 35px; border-left: 4px solid #3949ab; padding-left: 15px; }}
        
        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .info-card {{ background: #f8f9ff; padding: 15px; border-radius: 10px; text-align: center; }}
        .info-value {{ font-size: 1.8em; font-weight: bold; color: #1a237e; }}
        .info-label {{ color: #666; font-size: 0.9em; }}
        
        .overall-box {{
            background: linear-gradient(135deg, #e8f5e9, #fff);
            border-left: 5px solid #4caf50;
            padding: 20px; border-radius: 10px; margin: 20px 0;
        }}
        .overall-score {{ font-size: 3em; font-weight: bold; }}
        .score-high {{ color: #2e7d32; }}
        .score-medium {{ color: #f57c00; }}
        .score-low {{ color: #d32f2f; }}
        
        .modules-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .modules-table th {{ background: #3949ab; color: white; padding: 12px; text-align: left; }}
        .modules-table td {{ padding: 12px; border-bottom: 1px solid #e0e0e0; vertical-align: top; }}
        .modules-table tr:hover {{ background: #f8f9ff; }}
        
        .progress-bar {{ width: 100%; height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden; }}
        .progress-fill {{ height: 100%; border-radius: 4px; }}
        .fill-high {{ background: #4caf50; }}
        .fill-medium {{ background: #ff9800; }}
        .fill-low {{ background: #f44336; }}
        
        .content-tag {{ 
            display: inline-block; padding: 3px 10px; margin: 2px; 
            border-radius: 12px; font-size: 0.85em; 
        }}
        .tag-found {{ background: #c8e6c9; color: #2e7d32; }}
        .tag-missing {{ background: #ffcdd2; color: #c62828; }}
        
        .footer {{ 
            margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0;
            color: #888; font-size: 0.85em; text-align: center;
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>📖 Analisi: {manual_info.get('title', 'N/D')}</h1>
    <p style="color:#666;">
        <strong>{manual_info.get('author', 'N/D')}</strong> | 
        {manual_info.get('publisher', 'N/D')} |
        Confronto con framework {framework_type.upper()}
    </p>
    
    <div class="info-grid">
        <div class="info-card">
            <div class="info-value">{manual_info.get('n_chapters', 0)}</div>
            <div class="info-label">Capitoli</div>
        </div>
        <div class="info-card">
            <div class="info-value">{manual_info.get('n_sections', 0)}</div>
            <div class="info-label">Sezioni</div>
        </div>
        <div class="info-card">
            <div class="info-value">{len(modules)}</div>
            <div class="info-label">Moduli Framework</div>
        </div>
    </div>
    
    <div class="overall-box">
        <div style="display:flex; align-items:center; gap:20px;">
            <div class="overall-score {self._score_class(overall)}">{overall:.1f}%</div>
            <div>
                <div style="font-size:1.3em; font-weight:bold;">{judgment}</div>
                <div style="color:#666;">{analysis.get('recommendation', '')}</div>
            </div>
        </div>
        <div class="progress-bar" style="margin-top:15px; height:12px;">
            <div class="progress-fill {self._fill_class(overall)}" style="width:{overall}%;"></div>
        </div>
    </div>
    
    <h2>📊 Analisi per Modulo</h2>
    <table class="modules-table">
        <thead>
            <tr>
                <th style="width:25%;">Modulo</th>
                <th style="width:15%;">Copertura</th>
                <th>Contenuti Trovati</th>
                <th>Mancanti</th>
            </tr>
        </thead>
        <tbody>"""
        
        for mod in modules:
            coverage = mod.get("coverage_percentage", mod.get("manual_coverage", 0))
            fill_class = self._fill_class(coverage)
            
            # Contenuti trovati
            found_html = ""
            missing_html = ""
            
            if "content_matches" in mod:
                for cm in mod["content_matches"]:
                    if cm.get("matched_by"):
                        found_html += f'<span class="content-tag tag-found" title="Cap. {cm.get("chapter", "")}">{cm["content"][:30]}</span> '
                    else:
                        missing_html += f'<span class="content-tag tag-missing">{cm["content"][:30]}</span> '
            elif "matched_concepts" in mod:
                for mc in mod["matched_concepts"][:8]:
                    if mc.get("found_in_manual"):
                        found_html += f'<span class="content-tag tag-found">{mc["concept"][:25]} ({mc["frequency_in_programs"]:.0f}%)</span> '
                    else:
                        missing_html += f'<span class="content-tag tag-missing">{mc["concept"][:25]}</span> '
            
            if not found_html:
                found_html = '<span style="color:#999;">Nessuno</span>'
            if not missing_html:
                missing_html = '<span style="color:#2e7d32;">✓ Tutti coperti</span>'
            
            html += f"""
            <tr>
                <td>
                    <strong>{mod.get('module_name', 'N/D')}</strong><br>
                    <small style="color:#666;">{mod.get('contents_covered', mod.get('concepts_matched', 0))}/{mod.get('contents_total', mod.get('concepts_total', 0))} contenuti</small>
                </td>
                <td style="text-align:center;">
                    <strong style="font-size:1.2em;">{coverage:.0f}%</strong>
                    <div class="progress-bar" style="margin-top:5px;">
                        <div class="progress-fill {fill_class}" style="width:{coverage}%;"></div>
                    </div>
                </td>
                <td>{found_html}</td>
                <td>{missing_html}</td>
            </tr>"""
        
        html += f"""
        </tbody>
    </table>
    
    <div class="footer">
        Report generato da <strong>CoreX - Manual Analyzer v1.0</strong> | Zanichelli<br>
        {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    </div>
</div>
</body>
</html>"""
        
        return html
    
    # =========================================================
    # UTILITY
    # =========================================================
    
    def _coverage_to_status(self, coverage: float) -> str:
        if coverage >= 80:
            return "eccellente"
        elif coverage >= 60:
            return "buono"
        elif coverage >= 40:
            return "sufficiente"
        elif coverage >= 20:
            return "basso"
        else:
            return "minimo"
    
    def _coverage_to_judgment(self, coverage: float) -> str:
        if coverage >= 85:
            return "Eccellente"
        elif coverage >= 70:
            return "Buono"
        elif coverage >= 55:
            return "Sufficiente"
        elif coverage >= 40:
            return "Parziale"
        else:
            return "Insufficiente"
    
    def _get_recommendation(self, coverage: float, framework_type: str) -> str:
        if framework_type == "real":
            if coverage >= 85:
                return "Manuale perfettamente allineato con i programmi universitari"
            elif coverage >= 70:
                return "Buona copertura degli argomenti effettivamente insegnati"
            elif coverage >= 55:
                return "Copertura accettabile, alcune integrazioni potrebbero essere utili"
            else:
                return "Copertura limitata rispetto ai programmi reali"
        else:
            if coverage >= 85:
                return "Copertura eccellente del framework ideale"
            elif coverage >= 70:
                return "Buona aderenza al framework di riferimento"
            elif coverage >= 55:
                return "Copertura parziale, valutare integrazioni"
            else:
                return "Significative lacune rispetto al framework ideale"
    
    def _judgment_to_class(self, judgment: str) -> str:
        j_lower = judgment.lower()
        if "eccellente" in j_lower:
            return "judgment-eccellente"
        elif "buono" in j_lower:
            return "judgment-buono"
        elif "sufficiente" in j_lower or "parziale" in j_lower:
            return "judgment-sufficiente"
        else:
            return "judgment-insufficiente"
    
    def _score_class(self, score: float) -> str:
        if score >= 70:
            return "score-high"
        elif score >= 50:
            return "score-medium"
        else:
            return "score-low"
    
    def _fill_class(self, coverage: float) -> str:
        if coverage >= 70:
            return "fill-high"
        elif coverage >= 50:
            return "fill-medium"
        else:
            return "fill-low"