"""
CoreX - Manual Analyzer v2.0
Analizza manuali rispetto a framework IDEALE e REALE
Confronta più manuali tra loro
UPGRADE: Matching semantico tramite LLM (universale per qualsiasi materia)
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
    
    Usa LLM per matching semantico avanzato (universale per qualsiasi materia).
    """
    
    def __init__(self, manuali_dir: Path = None, frameworks_dir: Path = None, use_llm: bool = True):
        self.manuali_dir = manuali_dir or Path("data/manuali")
        self.frameworks_dir = frameworks_dir or Path("frameworks")
        self.archivio_dir = Path("archivio")
        self.use_llm = use_llm
    
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
        """Restituisce i manuali disponibili per una materia, divisi per tipo."""
        subject_dir = self.manuali_dir / subject / "indici"
        result = {"zanichelli": [], "competitor": []}
        
        if not subject_dir.exists():
            return result
        
        for type_dir in subject_dir.iterdir():
            if type_dir.is_dir():
                dir_name_lower = type_dir.name.lower()
                
                if "zanichelli" in dir_name_lower:
                    manual_type = "zanichelli"
                else:
                    manual_type = "competitor"
                
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
        
        for json_file in subject_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    manual_type = "zanichelli" if "zanichelli" in data.get("type", "").lower() else "competitor"
                    
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
        """Estrae tutti gli argomenti (capitoli + sezioni + subsections) da un manuale."""
        topics = []
        
        for chapter in manual.get("chapters", []):
            # Livello 1: Chapter/Focus
            topics.append({
                "text": chapter.get("title", ""),
                "type": "chapter",
                "chapter_num": chapter.get("number", 0),
                "section_num": None,
                "subsection_num": None,
                "page_start": chapter.get("page_start", None)
            })
            
            for section in chapter.get("sections", []):
                # Livello 2: Section/Capitolo
                topics.append({
                    "text": section.get("title", ""),
                    "type": "section",
                    "chapter_num": chapter.get("number", 0),
                    "section_num": section.get("number", ""),
                    "subsection_num": None,
                    "page_start": section.get("page_start", None)
                })
                
                # Livello 3: Subsection/Paragrafo (NUOVO)
                for subsection in section.get("subsections", []):
                    topics.append({
                        "text": subsection.get("title", ""),
                        "type": "subsection",
                        "chapter_num": chapter.get("number", 0),
                        "section_num": section.get("number", ""),
                        "subsection_num": subsection.get("number", ""),
                        "page_start": subsection.get("page_start", None)
                    })
        
        return topics

    
    # =========================================================
    # MATCHING SEMANTICO CON LLM (UNIVERSALE)
    # =========================================================
    
    def _match_manual_to_framework_llm(
        self, 
        manual: Dict,
        manual_topics: List[Dict], 
        modules: List[Dict],
        subject: str,
        provider_id: str = "openai",
        model: str = "gpt-4o-mini"
    ) -> Optional[Dict]:
        """
        Usa LLM per matching semantico tra titoli manuale e moduli framework.
        Funziona per QUALSIASI materia.
        """
        try:
            from app.llm_provider import get_llm_client
        except ImportError:
            print("LLM provider non disponibile")
            return None
        
        # Prepara i titoli del manuale
        manual_structure = []
        for chapter in manual.get("chapters", []):
            chapter_info = {
                "chapter_num": chapter.get("number", 0),
                "chapter_title": chapter.get("title", ""),
                "sections": [s.get("title", "") for s in chapter.get("sections", [])]
            }
            manual_structure.append(chapter_info)
        
        # Prepara i moduli del framework
        framework_modules = []
        for mod in modules:
            framework_modules.append({
                "id": mod.get("id", 0),
                "name": mod.get("name", ""),
                "core_contents": mod.get("core_contents", [])
            })
        
        # Prompt universale
        prompt = f"""Sei un esperto di didattica universitaria. 
Devi analizzare quanto un manuale universitario di "{subject.replace('_', ' ').title()}" copre i contenuti di un framework didattico.

STRUTTURA DEL MANUALE:
{json.dumps(manual_structure, indent=2, ensure_ascii=False)}

MODULI DEL FRAMEWORK DA VALUTARE:
{json.dumps(framework_modules, indent=2, ensure_ascii=False)}

ISTRUZIONI:
Per OGNI modulo del framework, determina:
1. Quali capitoli/sezioni del manuale coprono i core_contents di quel modulo
2. La percentuale di copertura (0-100%)

REGOLE DI MATCHING:
- Sii GENEROSO: se un capitolo tratta l'argomento anche con terminologia diversa, consideralo coperto
- Considera sinonimi e varianti terminologiche
- Un capitolo può coprire più moduli
- Una sezione specifica è preferibile a un capitolo generico

Rispondi SOLO con un JSON valido (senza markdown) in questo formato:
{{
    "modules_coverage": [
        {{
            "module_id": 1,
            "module_name": "nome modulo",
            "coverage_percent": 85,
            "matched_contents": [
                {{
                    "content": "contenuto del framework coperto",
                    "matched_by": "titolo capitolo o sezione che lo copre",
                    "chapter_num": 1
                }}
            ],
            "missing_contents": ["contenuti non coperti dal manuale"]
        }}
    ],
    "overall_assessment": {{
        "total_coverage": 75,
        "strengths": ["punti di forza del manuale"],
        "gaps": ["lacune principali"]
    }}
}}"""

        try:
            client = get_llm_client(provider_id)
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Sei un analista esperto di manuali universitari. Rispondi SOLO con JSON valido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Pulisci eventuale markdown
            if "```" in response_text:
                parts = response_text.split("```")
                for part in parts:
                    if part.strip().startswith("json"):
                        response_text = part.strip()[4:].strip()
                        break
                    elif part.strip().startswith("{"):
                        response_text = part.strip()
                        break
            
            result = json.loads(response_text)
            return result
            
        except json.JSONDecodeError as e:
            print(f"Errore parsing JSON risposta LLM: {e}")
            return None
        except Exception as e:
            print(f"Errore LLM matching: {e}")
            return None
    
    # =========================================================
    # MATCHING FALLBACK (senza LLM)
    # =========================================================
    
    def _normalize_text(self, text: str) -> str:
        """Normalizza testo per matching"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s\-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _text_matches_content_fallback(self, text: str, content: str, threshold: float = 0.3) -> Tuple[bool, float]:
        """
        Matching fallback basato su parole chiave comuni.
        Funziona per qualsiasi materia senza dizionari specifici.
        """
        text_norm = self._normalize_text(text)
        content_norm = self._normalize_text(content)
        
        # Match diretto
        if content_norm in text_norm or text_norm in content_norm:
            return True, 1.0
        
        # Match per parole significative (>3 caratteri)
        text_words = set(w for w in text_norm.split() if len(w) > 3)
        content_words = set(w for w in content_norm.split() if len(w) > 3)
        
        if not content_words:
            return False, 0.0
        
        # Calcola sovrapposizione
        common = text_words & content_words
        
        if common:
            score = len(common) / len(content_words)
            if score >= threshold:
                return True, min(score, 1.0)
        
        # Match parziale: cerca se almeno una parola chiave del contenuto è nel testo
        for word in content_words:
            if len(word) > 4 and word in text_norm:
                return True, 0.5
        
        return False, 0.0
    # =========================================================
    # HELPER METHODS
    # =========================================================
    
    def _coverage_to_status(self, coverage: float) -> str:
        """Converte copertura in status"""
        if coverage >= 80:
            return "completo"
        elif coverage >= 60:
            return "buono"
        elif coverage >= 40:
            return "parziale"
        else:
            return "carente"
    
    def _coverage_to_judgment(self, coverage: float) -> str:
        """Converte copertura in giudizio"""
        if coverage >= 80:
            return "Eccellente"
        elif coverage >= 60:
            return "Buono"
        elif coverage >= 40:
            return "Sufficiente"
        else:
            return "Insufficiente"
    
    def _get_recommendation(self, coverage: float, framework_type: str) -> str:
        """Genera raccomandazione basata sulla copertura"""
        if coverage >= 80:
            return "Il manuale copre ampiamente i contenuti richiesti. Adozione consigliata."
        elif coverage >= 60:
            return "Il manuale copre la maggior parte dei contenuti con alcune lacune. Adozione con integrazioni."
        elif coverage >= 40:
            return "Il manuale copre solo parzialmente i contenuti. Richiede integrazioni significative."
        else:
            return "Il manuale presenta lacune importanti. Valutare alternative."
    
    def _judgment_to_class(self, judgment: str) -> str:
        """Converte giudizio in classe CSS"""
        judgment_lower = judgment.lower()
        if "eccellente" in judgment_lower:
            return "judgment-eccellente"
        elif "buono" in judgment_lower:
            return "judgment-buono"
        elif "sufficiente" in judgment_lower:
            return "judgment-sufficiente"
        else:
            return "judgment-insufficiente"
    
    # =========================================================
    # ANALISI VS FRAMEWORK IDEALE
    # =========================================================
    
    def analyze_manual_vs_ideal(
        self, 
        manual: Dict, 
        ideal_framework: Dict, 
        provider_id: str = "openai", 
        model: str = "gpt-4o-mini"
    ) -> Dict:
        """
        Confronta un manuale con il framework IDEALE.
        Usa LLM per matching semantico, con fallback keyword-based.
        """
        manual_topics = self.extract_manual_topics(manual)
        modules = ideal_framework.get("syllabus_modules", [])
        subject = manual.get("subject", "materia")
        
        # Prova matching con LLM
        llm_result = None
        if self.use_llm:
            llm_result = self._match_manual_to_framework_llm(
                manual, manual_topics, modules, subject, provider_id, model
            )
        
        modules_analysis = []
        all_matched_topics = set()
        method_used = "fallback"
        
        if llm_result and "modules_coverage" in llm_result:
            # === USA RISULTATI LLM ===
            method_used = "llm"
            
            for mod_cov in llm_result["modules_coverage"]:
                module_id = mod_cov.get("module_id", 0)
                module_name = mod_cov.get("module_name", "")
                coverage_pct = mod_cov.get("coverage_percent", 0)
                
                # Trova modulo originale
                original_module = next((m for m in modules if m.get("id") == module_id), {})
                core_contents = original_module.get("core_contents", [])
                
                content_matches = []
                chapters_involved = []
                
                for matched in mod_cov.get("matched_contents", []):
                    content_matches.append({
                        "content": matched.get("content", ""),
                        "matched_by": matched.get("matched_by", ""),
                        "chapter": matched.get("chapter_num", 0),
                        "score": 1.0
                    })
                    if matched.get("matched_by"):
                        all_matched_topics.add(matched.get("matched_by"))
                    if matched.get("chapter_num"):
                        chapters_involved.append(matched.get("chapter_num"))
                
                for missing in mod_cov.get("missing_contents", []):
                    content_matches.append({
                        "content": missing,
                        "matched_by": None,
                        "score": 0
                    })
                
                covered = len([c for c in content_matches if c.get("matched_by")])
                
                modules_analysis.append({
                    "module_id": module_id,
                    "module_name": module_name,
                    "coverage_percentage": round(coverage_pct, 1),
                    "contents_covered": covered,
                    "contents_total": len(core_contents),
                    "content_matches": content_matches,
                    "chapters_involved": list(set(chapters_involved)),
                    "status": self._coverage_to_status(coverage_pct)
                })
        
        else:
            # === FALLBACK: MATCHING KEYWORD-BASED ===
            method_used = "fallback"
            
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
                        is_match, score = self._text_matches_content_fallback(topic["text"], content)
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
                
                covered = sum(1 for cm in content_matches if cm["matched_by"])
                coverage_pct = (covered / len(core_contents) * 100) if core_contents else 0
                
                chapters_involved = list(set(
                    t["chapter_num"] for t in matched_topics_for_module
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
        
        # Calcola copertura complessiva
        if modules_analysis:
            overall_coverage = sum(m["coverage_percentage"] for m in modules_analysis) / len(modules_analysis)
        else:
            overall_coverage = 0
        
        # Gap analysis
        missing_contents = []
        for m in modules_analysis:
            for cm in m["content_matches"]:
                if not cm.get("matched_by"):
                    missing_contents.append({
                        "content": cm["content"],
                        "module": m["module_name"]
                    })
        
        # Capitoli extra (nel manuale ma non matchati)
        uncovered_chapters = []
        for topic in manual_topics:
            if topic["type"] == "chapter" and topic["text"] not in all_matched_topics:
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
                "total_contents": sum(len(m.get("core_contents", [])) for m in modules)
            },
            "overall_coverage": round(overall_coverage, 1),
            "judgment": self._coverage_to_judgment(overall_coverage),
            "recommendation": self._get_recommendation(overall_coverage, "ideal"),
            "modules_analysis": modules_analysis,
            "uncovered_chapters": uncovered_chapters,
            "gaps": {
                "missing_in_manual": missing_contents,
                "extra_in_manual": uncovered_chapters
            },
            "method": method_used,
            "analysis_date": datetime.now().isoformat()
        }
    
    # =========================================================
    # FRAMEWORK REALE - CON SUPPORTO MULTICLASSE
    # =========================================================
    
    def get_available_real_frameworks(self, subject: str = None) -> List[Dict]:
        """
        Restituisce le analisi archiviate che contengono framework reali.
        Supporta sia framework_aggiornato.json che framework_multiclasse.json
        """
        analyses = []
        
        archivio_dir = Path("archivio")
        if archivio_dir.exists():
            for d in sorted(archivio_dir.iterdir(), reverse=True):
                if d.is_dir():
                    # Cerca entrambi i tipi di framework
                    fw_file = d / "framework_aggiornato.json"
                    if not fw_file.exists():
                        fw_file = d / "framework_multiclasse.json"
                    
                    meta_file = d / "analisi.json"
                    
                    if fw_file.exists() and meta_file.exists():
                        try:
                            with open(meta_file, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            
                            # Normalizza per confronto case-insensitive
                            meta_materia = meta.get("materia", "").lower().replace(" ", "_")
                            subject_normalized = subject.lower().replace(" ", "_") if subject else ""
                            
                            if subject and meta_materia != subject_normalized:
                                continue
                            
                            analysis_type = meta.get("type", "single")
                            type_label = "Multiclasse" if analysis_type == "multiclass" else "Singola classe"
                            
                            if analysis_type == "multiclass":
                                coverage_by_class = meta.get("coverage_by_class", {})
                                classi = meta.get("classi", [])
                                coverage = coverage_by_class.get(classi[0], 0) if classi else 0
                                n_syllabus = meta.get("n_syllabus_total", 0)
                            else:
                                coverage = meta.get("coverage", 0)
                                n_syllabus = meta.get("n_syllabus", 0)
                            
                            analyses.append({
                                "id": d.name,
                                "name": meta.get("name", d.name),
                                "materia": meta.get("materia", "N/D"),
                                "classi": meta.get("classi", []),
                                "coverage": coverage,
                                "n_syllabus": n_syllabus,
                                "date": meta.get("created", "")[:10],
                                "framework_path": fw_file,
                                "path": d,
                                "type": analysis_type,
                                "type_label": type_label
                            })
                        except Exception as e:
                            print(f"Errore lettura {meta_file}: {e}")
        
        # Cerca anche in analisi_corrente
        current_dir = Path("data/analisi_corrente")
        fw_current = current_dir / "framework_aggiornato.json"
        if not fw_current.exists():
            fw_current = current_dir / "framework_multiclasse.json"
        
        meta_current = current_dir / "analisi.json"
        
        if fw_current.exists() and meta_current.exists():
            try:
                with open(meta_current, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                
                meta_materia = meta.get("materia", "").lower().replace(" ", "_")
                subject_normalized = subject.lower().replace(" ", "_") if subject else ""
                
                if not subject or meta_materia == subject_normalized:
                    analysis_type = meta.get("type", "single")
                    type_label = "Multiclasse" if analysis_type == "multiclass" else "Singola classe"
                    
                    if analysis_type == "multiclass":
                        coverage_by_class = meta.get("coverage_by_class", {})
                        classi = meta.get("classi", [])
                        coverage = coverage_by_class.get(classi[0], 0) if classi else 0
                        n_syllabus = meta.get("n_syllabus_total", 0)
                    else:
                        coverage = meta.get("coverage", 0)
                        n_syllabus = meta.get("n_syllabus", 0)
                    
                    analyses.insert(0, {
                        "id": "current",
                        "name": f"[CORRENTE] {meta.get('name', 'Analisi')}",
                        "materia": meta.get("materia", "N/D"),
                        "classi": meta.get("classi", []),
                        "coverage": coverage,
                        "n_syllabus": n_syllabus,
                        "date": meta.get("created", "")[:10],
                        "framework_path": fw_current,
                        "path": current_dir,
                        "type": analysis_type,
                        "type_label": type_label
                    })
            except Exception as e:
                print(f"Errore lettura analisi corrente: {e}")
        
        return analyses
    
    def load_real_framework(self, path: Path) -> Optional[Dict]:
        """Carica un framework reale da un'analisi"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore caricamento framework reale {path}: {e}")
            return None
    
    def analyze_manual_vs_real(
        self, 
        manual: Dict, 
        real_framework: Dict,
        provider_id: str = "openai",
        model: str = "gpt-4o-mini"
    ) -> Dict:
        """
        Confronta un manuale con il framework REALE (generato da analisi programmi).
        Supporta sia framework singola-classe che multiclasse.
        """
        manual_topics = self.extract_manual_topics(manual)
        
        # SUPPORTO MULTICLASSE: cerca moduli in "modules" o "syllabus_modules"
        modules = real_framework.get("modules", real_framework.get("syllabus_modules", []))
        
        # Info framework
        framework_info = real_framework.get("framework", {})
        classes_analyzed = framework_info.get("classes_analyzed", [])
        is_multiclass = len(classes_analyzed) > 1 or real_framework.get("summary", {}).get("n_classes", 1) > 1
        
        modules_analysis = []
        subject = manual.get("subject", framework_info.get("materia", "materia"))
        
        # Prova matching con LLM se disponibile
        llm_result = None
        if self.use_llm and modules:
            llm_result = self._match_manual_to_framework_llm(
                manual, manual_topics, modules, subject, provider_id, model
            )
        
        method_used = "fallback"
        
        if llm_result and "modules_coverage" in llm_result:
            # === USA RISULTATI LLM ===
            method_used = "llm"
            
            for mod_cov in llm_result["modules_coverage"]:
                module_id = mod_cov.get("module_id", 0)
                module_name = mod_cov.get("module_name", "")
                coverage_pct = mod_cov.get("coverage_percent", 0)
                
                # Trova modulo originale per dati aggiuntivi
                original_module = next((m for m in modules if m.get("id") == module_id), {})
                
                # Info multiclasse
                avg_coverage_real = original_module.get("avg_coverage", 0)
                coverage_by_class = original_module.get("coverage_by_class", {})
                is_core = original_module.get("is_core", False)
                
                content_matches = []
                for matched in mod_cov.get("matched_contents", []):
                    content_matches.append({
                        "content": matched.get("content", ""),
                        "matched_by": matched.get("matched_by", ""),
                        "chapter": matched.get("chapter_num", 0),
                        "score": 1.0
                    })
                
                for missing in mod_cov.get("missing_contents", []):
                    content_matches.append({
                        "content": missing,
                        "matched_by": None,
                        "score": 0
                    })
                
                covered = len([c for c in content_matches if c.get("matched_by")])
                total = len(content_matches) if content_matches else len(original_module.get("core_contents", []))
                
                modules_analysis.append({
                    "module_id": module_id,
                    "module_name": module_name,
                    "manual_coverage": round(coverage_pct, 1),
                    "real_avg_coverage": round(avg_coverage_real, 1),
                    "coverage_by_class": coverage_by_class,
                    "is_core": is_core,
                    "contents_covered": covered,
                    "contents_total": total,
                    "content_matches": content_matches,
                    "status": self._coverage_to_status(coverage_pct)
                })
        
        else:
            # === FALLBACK: MATCHING BASATO SU CORE_CONTENTS E CONCEPTS_BY_CLASS ===
            method_used = "fallback"
            
            for module in modules:
                module_id = module.get("id", 0)
                module_name = module.get("name", "")
                core_contents = module.get("core_contents", [])
                concepts_by_class = module.get("concepts_by_class", {})
                avg_coverage_real = module.get("avg_coverage", 0)
                coverage_by_class = module.get("coverage_by_class", {})
                is_core = module.get("is_core", False)
                
                # Raccogli tutti i concetti reali da tutte le classi
                all_real_concepts = set()
                for classe, concepts in concepts_by_class.items():
                    for c in concepts:
                        all_real_concepts.add(c.lower() if isinstance(c, str) else str(c).lower())
                
                content_matches = []
                matched_count = 0
                
                # Match sui core_contents (come per framework ideale)
                for content in core_contents:
                    best_match = None
                    best_score = 0
                    
                    for topic in manual_topics:
                        is_match, score = self._text_matches_content_fallback(topic["text"], content)
                        if is_match and score > best_score:
                            best_score = score
                            best_match = topic
                    
                    if best_match:
                        content_matches.append({
                            "content": content,
                            "matched_by": best_match["text"],
                            "chapter": best_match["chapter_num"],
                            "score": round(best_score, 2)
                        })
                        matched_count += 1
                    else:
                        content_matches.append({
                            "content": content,
                            "matched_by": None,
                            "score": 0
                        })
                
                # Match aggiuntivo sui concetti estratti (concepts_by_class)
                concepts_matched = 0
                for concept in list(all_real_concepts)[:15]:  # Top 15 concetti
                    for topic in manual_topics:
                        is_match, _ = self._text_matches_content_fallback(topic["text"], concept)
                        if is_match:
                            concepts_matched += 1
                            break
                
                # Calcola coverage combinata
                core_coverage = (matched_count / len(core_contents) * 100) if core_contents else 0
                concept_coverage = (concepts_matched / min(len(all_real_concepts), 15) * 100) if all_real_concepts else 0
                
                # Media pesata: 60% core_contents, 40% concepts reali
                combined_coverage = (core_coverage * 0.6 + concept_coverage * 0.4) if all_real_concepts else core_coverage
                
                modules_analysis.append({
                    "module_id": module_id,
                    "module_name": module_name,
                    "manual_coverage": round(combined_coverage, 1),
                    "core_coverage": round(core_coverage, 1),
                    "concept_coverage": round(concept_coverage, 1),
                    "real_avg_coverage": round(avg_coverage_real, 1),
                    "coverage_by_class": coverage_by_class,
                    "is_core": is_core,
                    "contents_covered": matched_count,
                    "contents_total": len(core_contents),
                    "concepts_matched": concepts_matched,
                    "concepts_checked": min(len(all_real_concepts), 15),
                    "content_matches": content_matches,
                    "status": self._coverage_to_status(combined_coverage)
                })
        
        # Calcola coperture complessive
        if modules_analysis:
            overall_coverage = sum(m["manual_coverage"] for m in modules_analysis) / len(modules_analysis)
            
            # Core modules coverage (solo moduli CORE)
            core_modules = [m for m in modules_analysis if m.get("is_core", False)]
            core_coverage = sum(m["manual_coverage"] for m in core_modules) / len(core_modules) if core_modules else overall_coverage
        else:
            overall_coverage = 0
            core_coverage = 0
        
        # Gap analysis
        missing_contents = []
        for m in modules_analysis:
            for cm in m.get("content_matches", []):
                if not cm.get("matched_by"):
                    missing_contents.append({
                        "content": cm["content"],
                        "module": m["module_name"],
                        "is_core_module": m.get("is_core", False)
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
            "real_framework_info": {
                "name": framework_info.get("name", "N/D"),
                "type": "multiclass" if is_multiclass else "single",
                "classes_analyzed": classes_analyzed,
                "n_modules": len(modules),
                "n_core_modules": len([m for m in modules if m.get("is_core", False)])
            },
            "overall_coverage": round(overall_coverage, 1),
            "core_modules_coverage": round(core_coverage, 1),
            "judgment": self._coverage_to_judgment(overall_coverage),
            "recommendation": self._get_recommendation(overall_coverage, "real"),
            "modules_analysis": modules_analysis,
            "gaps": {
                "missing_in_manual": missing_contents,
                "priority_gaps": [g for g in missing_contents if g.get("is_core_module", False)]
            },
            "method": method_used,
            "analysis_date": datetime.now().isoformat()
        }

    # =========================================================
    # CONFRONTO TRA MANUALI
    # =========================================================
    
    def compare_manuals(
        self, 
        manuals: List[Dict], 
        reference_framework: Dict = None,
        framework_type: str = "ideal",
        provider_id: str = "openai",
        model: str = "gpt-4o-mini"
    ) -> Dict:
        """Confronta più manuali tra loro rispetto a un framework."""
        if not manuals:
            return {"error": "Nessun manuale da confrontare"}
        
        comparisons = []
        
        for manual in manuals:
            if reference_framework:
                if framework_type == "ideal":
                    analysis = self.analyze_manual_vs_ideal(manual, reference_framework, provider_id, model)
                else:
                    analysis = self.analyze_manual_vs_real(manual, reference_framework, provider_id, model)
            else:
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
        
        if reference_framework:
            comparisons.sort(
                key=lambda x: x.get("weighted_coverage") or x.get("coverage") or 0, 
                reverse=True
            )
        
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
    # SALVATAGGIO E RECUPERO ANALISI
    # =========================================================

    def save_analysis(
        self, 
        analysis: Dict, 
        materia: str, 
        manual_name: str,
        manual_type: str = "zanichelli"
    ) -> Path:
        """
        Salva l'analisi in archivio/analisi_manuali/{materia}/
        
        Args:
            analysis: Risultato dell'analisi (da analyze_manual_vs_ideal o analyze_manual_vs_real)
            materia: Nome della materia
            manual_name: Nome del manuale
            manual_type: "zanichelli" o "competitor"
        
        Returns:
            Path del file salvato
        """
        # Crea directory se non esiste
        save_dir = Path("archivio/analisi_manuali") / materia.replace(" ", "_")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Nome file con timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        safe_name = manual_name.replace(" ", "_").replace("/", "-")[:50]
        filename = f"{safe_name}_{manual_type}_{timestamp}.json"
        
        filepath = save_dir / filename
        
        # Aggiungi metadati
        analysis_with_meta = {
            "metadata": {
                "manual_name": manual_name,
                "manual_type": manual_type,
                "materia": materia,
                "saved_at": datetime.now().isoformat(),
                "analysis_version": "2.0"
            },
            "analysis": analysis
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(analysis_with_meta, f, indent=2, ensure_ascii=False)
        
        return filepath


    def get_saved_analyses(self, materia: str = None) -> List[Dict]:
        """
        Restituisce le analisi salvate, opzionalmente filtrate per materia.
        
        Args:
            materia: Se specificata, filtra per questa materia
        
        Returns:
            Lista di dict con info sulle analisi salvate
        """
        base_dir = Path("archivio/analisi_manuali")
        if not base_dir.exists():
            return []
        
        analyses = []
        
        if materia:
            materia_dir = base_dir / materia.replace(" ", "_")
            dirs_to_search = [materia_dir] if materia_dir.exists() else []
        else:
            dirs_to_search = [d for d in base_dir.iterdir() if d.is_dir()]
        
        for materia_dir in dirs_to_search:
            for json_file in materia_dir.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    meta = data.get("metadata", {})
                    analysis = data.get("analysis", {})
                    
                    analyses.append({
                        "path": json_file,
                        "filename": json_file.name,
                        "materia": meta.get("materia", materia_dir.name),
                        "manual_name": meta.get("manual_name", json_file.stem),
                        "manual_type": meta.get("manual_type", "unknown"),
                        "saved_at": meta.get("saved_at", ""),
                        "coverage": analysis.get("overall_coverage", 0),
                        "judgment": analysis.get("judgment", "N/D")
                    })
                except Exception as e:
                    print(f"Errore lettura {json_file}: {e}")
        
        analyses.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
        return analyses


    def load_saved_analysis(self, path: Path) -> Optional[Dict]:
        """
        Carica un'analisi salvata.
        
        Args:
            path: Path del file JSON
        
        Returns:
            Dict con metadata e analysis, o None se errore
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore caricamento {path}: {e}")
            return None
        
    # =========================================================
    # GENERAZIONE REPORT HTML
    # =========================================================
    
    def generate_single_analysis_report_html(self, analysis: Dict, framework_type: str = "ideal") -> str:
        """Genera report HTML per analisi singolo manuale"""
        
        manual_info = analysis.get("manual_info", {})
        modules = analysis.get("modules_analysis", [])
        overall = analysis.get("overall_coverage", 0)
        judgment = analysis.get("judgment", "N/D")
        gaps = analysis.get("gaps", {})
        method = analysis.get("method", "N/D")
        
        overall_color = "#4caf50" if overall >= 70 else ("#ff9800" if overall >= 50 else "#f44336")
        judgment_class = self._judgment_to_class(judgment)
        
        # Genera righe moduli
        modules_html = ""
        for mod in modules:
            cov = mod.get("coverage_percentage", mod.get("manual_coverage", 0))
            status = mod.get("status", "N/D")
            fill_class = "fill-high" if cov >= 70 else ("fill-medium" if cov >= 50 else "fill-low")
            status_icon = "🟢" if cov >= 70 else ("🟡" if cov >= 50 else "🔴")
            
            modules_html += f"""
            <tr>
                <td>{status_icon} <strong>{mod.get('module_name', 'N/D')}</strong></td>
                <td>
                    <div class="coverage-bar" style="height:15px;">
                        <div class="coverage-fill {fill_class}" style="width:{cov}%;"></div>
                    </div>
                </td>
                <td style="text-align:center; font-weight:bold;">{cov:.1f}%</td>
                <td>{status}</td>
            </tr>"""
        
        # Genera lista gap
        gaps_html = ""
        missing = gaps.get("missing_in_manual", [])
        if missing:
            gaps_html = "<ul>"
            for gap in missing[:15]:
                gaps_html += f"<li><strong>{gap.get('module', 'N/D')}</strong>: {gap.get('content', 'N/D')}</li>"
            if len(missing) > 15:
                gaps_html += f"<li><em>... e altri {len(missing) - 15} contenuti</em></li>"
            gaps_html += "</ul>"
        else:
            gaps_html = "<p>✅ Nessun gap significativo rilevato.</p>"
        
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
        .subtitle {{ color: #666; margin-bottom: 25px; }}
        .method-badge {{ background: #e3f2fd; color: #1565c0; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; }}
        
        .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 25px 0; }}
        .summary-card {{ 
            background: #f8f9ff; padding: 20px; border-radius: 10px; text-align: center;
            border-top: 4px solid #3949ab;
        }}
        .summary-card .value {{ font-size: 2.5em; font-weight: bold; color: #1a237e; }}
        .summary-card .label {{ color: #666; font-size: 0.9em; }}
        
        .modules-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .modules-table th {{ background: #3949ab; color: white; padding: 12px; text-align: left; }}
        .modules-table td {{ padding: 12px; border-bottom: 1px solid #e0e0e0; }}
        
        .coverage-bar {{ width: 100%; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; }}
        .coverage-fill {{ height: 100%; border-radius: 10px; }}
        .fill-high {{ background: linear-gradient(90deg, #4caf50, #8bc34a); }}
        .fill-medium {{ background: linear-gradient(90deg, #ff9800, #ffc107); }}
        .fill-low {{ background: linear-gradient(90deg, #f44336, #ff5722); }}
        
        .judgment-badge {{ display: inline-block; padding: 8px 20px; border-radius: 20px; font-size: 1.1em; font-weight: 600; }}
        .judgment-eccellente {{ background: #c8e6c9; color: #2e7d32; }}
        .judgment-buono {{ background: #dcedc8; color: #558b2f; }}
        .judgment-sufficiente {{ background: #fff3e0; color: #e65100; }}
        .judgment-insufficiente {{ background: #ffcdd2; color: #c62828; }}
        
        .gaps-section {{ background: #fff8e1; padding: 20px; border-radius: 10px; margin-top: 20px; }}
        .gaps-section h3 {{ color: #e65100; margin-top: 0; }}
        .gaps-section ul {{ margin: 10px 0; padding-left: 25px; }}
        .gaps-section li {{ margin: 8px 0; }}
        
        .recommendation {{ background: #e8f5e9; padding: 15px 20px; border-radius: 10px; margin-top: 20px; border-left: 4px solid #4caf50; }}
        
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #888; font-size: 0.85em; text-align: center; }}
    </style>
</head>
<body>
<div class="container">
    <h1>📖 Analisi Manuale</h1>
    <p class="subtitle">
        <strong>{manual_info.get('title', 'N/D')}</strong> — {manual_info.get('author', 'N/D')} ({manual_info.get('publisher', 'N/D')})<br>
        Confronto vs Framework {framework_type.upper()} 
        <span class="method-badge">Metodo: {method.upper()}</span>
    </p>
    
    <div class="summary-grid">
        <div class="summary-card">
            <div class="value" style="color: {overall_color};">{overall:.1f}%</div>
            <div class="label">Copertura Complessiva</div>
        </div>
        <div class="summary-card">
            <div class="value">{manual_info.get('n_chapters', 0)}</div>
            <div class="label">Capitoli</div>
        </div>
        <div class="summary-card">
            <div class="value">{manual_info.get('n_sections', 0)}</div>
            <div class="label">Sezioni</div>
        </div>
        <div class="summary-card">
            <span class="judgment-badge {judgment_class}">{judgment}</span>
            <div class="label" style="margin-top:10px;">Giudizio</div>
        </div>
    </div>
    
    <div class="recommendation">
        <strong>📋 Raccomandazione:</strong> {analysis.get('recommendation', 'N/D')}
    </div>
    
    <h2>📊 Copertura per Modulo</h2>
    <table class="modules-table">
        <thead>
            <tr>
                <th>Modulo</th>
                <th style="width:300px;">Copertura</th>
                <th style="width:80px;">%</th>
                <th style="width:120px;">Status</th>
            </tr>
        </thead>
        <tbody>
            {modules_html}
        </tbody>
    </table>
    
    <div class="gaps-section">
        <h3>⚠️ Gap Rilevati</h3>
        {gaps_html}
    </div>
    
    <div class="footer">
        Report generato da <strong>CoreX - Manual Analyzer v2.0</strong> | Zanichelli<br>
        {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    </div>
</div>
</body>
</html>"""
        
        return html
    
    def generate_comparison_report_html(self, comparison_result: Dict) -> str:
        """Genera report HTML per confronto manuali"""
        
        ranking = comparison_result.get("ranking", [])
        modules_comparison = comparison_result.get("modules_comparison", [])
        framework_name = comparison_result.get("framework_name", "N/D")
        framework_type = comparison_result.get("framework_type", "none")
        
        # Genera righe ranking
        ranking_html = ""
        for i, manual in enumerate(ranking):
            rank = i + 1
            rank_class = f"rank-{rank}" if rank <= 3 else "rank-other"
            row_class = "winner" if rank == 1 else ""
            coverage = manual.get("weighted_coverage") or manual.get("coverage") or 0
            fill_class = "fill-high" if coverage >= 70 else ("fill-medium" if coverage >= 50 else "fill-low")
            judgment = manual.get("judgment", "N/D")
            judgment_class = self._judgment_to_class(judgment)
            
            ranking_html += f"""
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
        
        # Genera cards moduli
        modules_html = ""
        for module in modules_comparison:
            module_bars = ""
            for ms in module.get("manual_scores", [])[:5]:
                cov = ms['coverage']
                fill_class = "fill-high" if cov >= 70 else ("fill-medium" if cov >= 50 else "fill-low")
                module_bars += f"""
                <div class="manual-bar">
                    <span class="name" title="{ms['manual']}">{ms['manual'][:20]}</span>
                    <div class="bar">
                        <div class="coverage-bar" style="height:10px;">
                            <div class="coverage-fill {fill_class}" style="width:{cov}%;"></div>
                        </div>
                    </div>
                    <span class="value">{cov:.0f}%</span>
                </div>"""
            
            modules_html += f"""
            <div class="module-card">
                <h4>{module['module_name']}</h4>
                <div style="font-size:0.85em; color:#666; margin-bottom:10px;">
                    Media: {module['avg_coverage']:.1f}% | Migliore: {module.get('best_manual', 'N/D')}
                </div>
                {module_bars}
            </div>"""
        
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
        
        .coverage-bar {{ width: 100%; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; }}
        .coverage-fill {{ height: 100%; border-radius: 10px; }}
        .fill-high {{ background: linear-gradient(90deg, #4caf50, #8bc34a); }}
        .fill-medium {{ background: linear-gradient(90deg, #ff9800, #ffc107); }}
        .fill-low {{ background: linear-gradient(90deg, #f44336, #ff5722); }}
        
        .judgment-badge {{ display: inline-block; padding: 4px 12px; border-radius: 15px; font-size: 0.85em; font-weight: 500; }}
        .judgment-eccellente {{ background: #c8e6c9; color: #2e7d32; }}
        .judgment-buono {{ background: #dcedc8; color: #558b2f; }}
        .judgment-sufficiente {{ background: #fff3e0; color: #e65100; }}
        .judgment-insufficiente {{ background: #ffcdd2; color: #c62828; }}
        
        .module-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }}
        .module-card {{ background: #f8f9ff; border-radius: 10px; padding: 15px; border-left: 4px solid #3949ab; }}
        .module-card h4 {{ margin: 0 0 10px 0; color: #1a237e; }}
        
        .manual-bar {{ display: flex; align-items: center; margin: 5px 0; font-size: 0.9em; }}
        .manual-bar .name {{ width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .manual-bar .bar {{ flex: 1; margin: 0 10px; }}
        .manual-bar .value {{ width: 50px; text-align: right; font-weight: bold; }}
        
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #888; font-size: 0.85em; text-align: center; }}
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
        <tbody>
            {ranking_html}
        </tbody>
    </table>
    
    <h2>📊 Confronto per Modulo</h2>
    <div class="module-grid">
        {modules_html}
    </div>
    
    <div class="footer">
        Report generato da <strong>CoreX - Manual Analyzer v2.0</strong> | Zanichelli<br>
        {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    </div>
</div>
</body>
</html>"""
        
        return html
