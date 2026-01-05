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
    
    def __init__(self, manuali_dir: Path = None, frameworks_dir: Path = None, use_llm: bool = True):
        self.manuali_dir = manuali_dir or Path("data/manuali")
        self.frameworks_dir = frameworks_dir or Path("frameworks")
        self.archivio_dir = Path("archivio")
        self.use_llm = use_llm
    
    def get_available_subjects(self) -> List[str]:
        if not self.manuali_dir.exists():
            return []
        subjects = []
        for d in sorted(self.manuali_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                subjects.append(d.name)
        return subjects
    
    def get_manuals_for_subject(self, subject: str) -> Dict[str, List[Dict]]:
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
        return result
    
    def load_manual(self, path: Path) -> Optional[Dict]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore caricamento manuale {path}: {e}")
            return None
    
    def extract_manual_topics(self, manual: Dict) -> List[Dict]:
        topics = []
        for chapter in manual.get("chapters", []):
            topics.append({
                "text": chapter.get("title", ""),
                "type": "chapter",
                "chapter_num": chapter.get("number", 0),
                "section_num": None,
                "subsection_num": None,
                "page_start": chapter.get("page_start", None)
            })
            for section in chapter.get("sections", []):
                topics.append({
                    "text": section.get("title", ""),
                    "type": "section",
                    "chapter_num": chapter.get("number", 0),
                    "section_num": section.get("number", ""),
                    "subsection_num": None,
                    "page_start": section.get("page_start", None)
                })
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

    def _match_manual_to_framework_llm(self, manual: Dict, manual_topics: List[Dict], modules: List[Dict], subject: str, provider_id: str = "openai", model: str = "gpt-4o-mini") -> Optional[Dict]:
        try:
            from app.llm_provider import get_llm_client
        except ImportError:
            print("LLM provider non disponibile")
            return None
        
        manual_structure = []
        for chapter in manual.get("chapters", []):
            sections_list = []
            for section in chapter.get("sections", []):
                section_info = {"title": section.get("title", ""), "subsections": [sub.get("title", "") for sub in section.get("subsections", [])]}
                sections_list.append(section_info)
            chapter_info = {"chapter_num": chapter.get("number", 0), "chapter_title": chapter.get("title", ""), "sections": sections_list}
            manual_structure.append(chapter_info)
        
        framework_modules = []
        for mod in modules:
            framework_modules.append({"id": mod.get("id", 0), "name": mod.get("name", ""), "core_contents": mod.get("core_contents", [])})
        
        prompt = f"""Sei un esperto di didattica universitaria. 
Devi analizzare quanto un manuale universitario di "{subject.replace('_', ' ').title()}" copre i contenuti di un framework didattico.

STRUTTURA DEL MANUALE (3 livelli: Capitoli > Sezioni > Sottosezioni):
{json.dumps(manual_structure, indent=2, ensure_ascii=False)}

MODULI DEL FRAMEWORK DA VALUTARE:
{json.dumps(framework_modules, indent=2, ensure_ascii=False)}

ISTRUZIONI:
Per OGNI modulo del framework, determina:
1. Quali capitoli/sezioni/sottosezioni del manuale coprono i core_contents di quel modulo
2. La percentuale di copertura (0-100%)

REGOLE DI MATCHING:
- Analizza TUTTI I LIVELLI: capitoli, sezioni E sottosezioni
- Sii GENEROSO: se un contenuto è trattato anche con terminologia diversa, consideralo coperto
- Considera sinonimi e varianti terminologiche

Rispondi SOLO con un JSON valido (senza markdown) in questo formato:
{{
    "modules_coverage": [
        {{
            "module_id": 1,
            "module_name": "nome modulo",
            "coverage_percent": 85,
            "matched_contents": [
                {{"content": "contenuto coperto", "matched_by": "titolo sezione", "chapter_num": 1}}
            ],
            "missing_contents": ["contenuti non coperti"]
        }}
    ],
    "overall_assessment": {{
        "total_coverage": 75,
        "strengths": ["punti di forza"],
        "gaps": ["lacune"]
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
    def _generate_narrative_descriptions(self, analysis_result: Dict, manual: Dict, subject: str, provider_id: str = "openai", model: str = "gpt-4o-mini") -> Dict:
        """
        Genera descrizioni narrative UTILI per il promotore.
        v2.0 - Passa TUTTI i dati del matching per descrizioni specifiche.
        """
        try:
            from app.llm_provider import get_llm_client
        except ImportError:
            return analysis_result
        
        # Costruisce la struttura capitoli per riferimento rapido
        chapters_index = {}
        for ch in manual.get("chapters", []):
            ch_num = ch.get("number", 0)
            chapters_index[ch_num] = {
                "title": ch.get("title", ""),
                "sections": {s.get("number", ""): s.get("title", "") for s in ch.get("sections", [])}
            }
        
        # Prepara dati COMPLETI per ogni modulo (non riassunti!)
        modules_detailed = []
        for mod in analysis_result.get("modules_analysis", []):
            # Separa contenuti coperti da quelli mancanti CON DETTAGLI
            covered_details = []
            missing_details = []
            
            for cm in mod.get("content_matches", []):
                if cm.get("matched_by"):
                    ch_num = cm.get("chapter", 0)
                    ch_info = chapters_index.get(ch_num, {})
                    covered_details.append({
                        "content": cm.get("content", ""),
                        "where": cm.get("matched_by", ""),
                        "chapter_num": ch_num,
                        "chapter_title": ch_info.get("title", ""),
                        "section": cm.get("section", "")
                    })
                else:
                    missing_details.append(cm.get("content", ""))
            
            modules_detailed.append({
                "id": mod.get("module_id"),
                "name": mod.get("module_name"),
                "coverage_percent": mod.get("coverage_percentage", mod.get("manual_coverage", 0)),
                "is_core": mod.get("is_core", False),
                "covered": covered_details,
                "missing": missing_details,
                "chapters_involved": mod.get("chapters_involved", [])
            })
        
        manual_title = manual.get("title", "N/D")
        manual_author = manual.get("author", "N/D")
        overall_coverage = analysis_result.get("overall_coverage", 0)
        
        prompt = f"""Sei un PROMOTORE EDITORIALE ESPERTO di manuali universitari di {subject.replace('_', ' ').title()}.
Devi generare descrizioni che userai per ARGOMENTARE con i docenti.

MANUALE: "{manual_title}" di {manual_author}
COPERTURA COMPLESSIVA: {overall_coverage:.0f}%

ANALISI DETTAGLIATA PER MODULO:
{json.dumps(modules_detailed, indent=2, ensure_ascii=False)}

ISTRUZIONI PER LE DESCRIZIONI:
Per OGNI modulo genera una descrizione di 2-3 frasi che:

1. CITI ESATTAMENTE dove viene trattato:
   - "Nel Capitolo 3 'Cinetica chimica' (sezioni 3.1-3.4)" 
   - NON "viene trattato nel manuale" (troppo generico!)

2. SPECIFICHI i contenuti coperti:
   - "tratta velocità di reazione, ordine di reazione e meccanismi"
   - NON "copre i contenuti del modulo"

3. Per i CONTENUTI MANCANTI, valuta se sono:
   - LACUNA GRAVE: argomento fondamentale richiesto in quasi tutti i corsi
   - LACUNA MARGINALE: argomento avanzato/specialistico, spesso non richiesto nei corsi base
   - Spiega PERCHÉ in 5-10 parole

4. Se coverage > 90%, evidenzia il PUNTO DI FORZA per la vendita

TONO: Professionale ma diretto. Frasi utili in una visita commerciale.

GENERA ANCHE UN SUMMARY (3-4 frasi) che:
- Identifichi il POSIZIONAMENTO del manuale (base/intermedio/avanzato)
- Indichi i 2-3 PUNTI DI FORZA principali
- Segnali la LACUNA PIÙ CRITICA (se presente)
- Suggerisca il TARGET IDEALE (es: "Ottimo per corsi di Chimica Generale per Biologi")

Rispondi SOLO con JSON valido:
{{
    "module_descriptions": [
        {{
            "module_id": 1,
            "description": "Trattato nel Capitolo 2 'Struttura atomica' (sez. 2.1-2.5): modello atomico, numeri quantici, configurazioni elettroniche. Manca la trattazione degli spettri atomici - lacuna marginale, argomento raramente richiesto nei corsi base di Chimica Generale."
        }}
    ],
    "summary": "Manuale di livello intermedio, particolarmente forte sulla termodinamica (copertura 95%) e cinetica. Punto debole: elettrochimica trattata solo superficialmente. Target ideale: corsi di Chimica Generale per CTF e Farmacia."
}}"""

        try:
            client = get_llm_client(provider_id)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Sei un esperto commerciale editoriale. Genera descrizioni CONCRETE e UTILI per argomentare con i docenti. Cita sempre capitoli e sezioni specifiche. Rispondi SOLO con JSON valido."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=3500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Pulizia markdown se presente
            if "```" in response_text:
                for part in response_text.split("```"):
                    if part.strip().startswith("json"):
                        response_text = part.strip()[4:].strip()
                        break
                    elif part.strip().startswith("{"):
                        response_text = part.strip()
                        break
            
            narrative = json.loads(response_text)
            
            # Mappa descrizioni ai moduli
            desc_map = {d["module_id"]: d["description"] for d in narrative.get("module_descriptions", [])}
            for mod in analysis_result.get("modules_analysis", []):
                mod["description"] = desc_map.get(mod.get("module_id"), "")
            
            analysis_result["summary"] = narrative.get("summary", "")
            analysis_result["narrative_generated"] = True
            
        except json.JSONDecodeError as e:
            print(f"Errore parsing JSON narrative: {e}")
            print(f"Response raw: {response_text[:500]}")
            analysis_result["narrative_generated"] = False
        except Exception as e:
            print(f"Errore generazione narrative: {e}")
            analysis_result["narrative_generated"] = False
        
        return analysis_result
    
    def _normalize_text(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r'[^\w\s\-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _text_matches_content_fallback(self, text: str, content: str, threshold: float = 0.3) -> Tuple[bool, float]:
        text_norm = self._normalize_text(text)
        content_norm = self._normalize_text(content)
        if content_norm in text_norm or text_norm in content_norm:
            return True, 1.0
        text_words = set(w for w in text_norm.split() if len(w) > 3)
        content_words = set(w for w in content_norm.split() if len(w) > 3)
        if not content_words:
            return False, 0.0
        common = text_words & content_words
        if common:
            score = len(common) / len(content_words)
            if score >= threshold:
                return True, min(score, 1.0)
        for word in content_words:
            if len(word) > 4 and word in text_norm:
                return True, 0.5
        return False, 0.0

    def _coverage_to_status(self, coverage: float) -> str:
        if coverage >= 80:
            return "completo"
        elif coverage >= 60:
            return "buono"
        elif coverage >= 40:
            return "parziale"
        else:
            return "carente"
    
    def _coverage_to_judgment(self, coverage: float) -> str:
        if coverage >= 80:
            return "Eccellente"
        elif coverage >= 60:
            return "Buono"
        elif coverage >= 40:
            return "Sufficiente"
        else:
            return "Insufficiente"
    
    def _get_recommendation(self, coverage: float, framework_type: str) -> str:
        if coverage >= 80:
            return "Il manuale copre ampiamente i contenuti richiesti. Adozione consigliata."
        elif coverage >= 60:
            return "Il manuale copre la maggior parte dei contenuti con alcune lacune. Adozione con integrazioni."
        elif coverage >= 40:
            return "Il manuale copre solo parzialmente i contenuti. Richiede integrazioni significative."
        else:
            return "Il manuale presenta lacune importanti. Valutare alternative."
    
    def _judgment_to_class(self, judgment: str) -> str:
        judgment_lower = judgment.lower()
        if "eccellente" in judgment_lower:
            return "judgment-eccellente"
        elif "buono" in judgment_lower:
            return "judgment-buono"
        elif "sufficiente" in judgment_lower:
            return "judgment-sufficiente"
        else:
            return "judgment-insufficiente"

    def analyze_manual_vs_ideal(self, manual: Dict, ideal_framework: Dict, provider_id: str = "openai", model: str = "gpt-4o-mini") -> Dict:
        manual_topics = self.extract_manual_topics(manual)
        modules = ideal_framework.get("syllabus_modules", [])
        subject = manual.get("subject", "materia")
        
        llm_result = None
        if self.use_llm:
            llm_result = self._match_manual_to_framework_llm(manual, manual_topics, modules, subject, provider_id, model)
        
        modules_analysis = []
        all_matched_topics = set()
        method_used = "fallback"
        
        if llm_result and "modules_coverage" in llm_result:
            method_used = "llm"
            for mod_cov in llm_result["modules_coverage"]:
                module_id = mod_cov.get("module_id", 0)
                module_name = mod_cov.get("module_name", "")
                coverage_pct = mod_cov.get("coverage_percent", 0)
                original_module = next((m for m in modules if m.get("id") == module_id), {})
                core_contents = original_module.get("core_contents", [])
                content_matches = []
                chapters_involved = []
                for matched in mod_cov.get("matched_contents", []):
                    content_matches.append({"content": matched.get("content", ""), "matched_by": matched.get("matched_by", ""), "chapter": matched.get("chapter_num", 0), "score": 1.0})
                    if matched.get("matched_by"):
                        all_matched_topics.add(matched.get("matched_by"))
                    if matched.get("chapter_num"):
                        chapters_involved.append(matched.get("chapter_num"))
                for missing in mod_cov.get("missing_contents", []):
                    content_matches.append({"content": missing, "matched_by": None, "score": 0})
                covered = len([c for c in content_matches if c.get("matched_by")])
                modules_analysis.append({
                    "module_id": module_id, "module_name": module_name, "coverage_percentage": round(coverage_pct, 1),
                    "contents_covered": covered, "contents_total": len(core_contents), "content_matches": content_matches,
                    "chapters_involved": list(set(chapters_involved)), "status": self._coverage_to_status(coverage_pct), "description": ""
                })
        else:
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
                        content_matches.append({"content": content, "matched_by": best_match["text"], "type": best_match["type"], "chapter": best_match["chapter_num"], "section": best_match["section_num"], "score": round(best_score, 2)})
                        all_matched_topics.add(best_match["text"])
                        matched_topics_for_module.append(best_match)
                    else:
                        content_matches.append({"content": content, "matched_by": None, "score": 0})
                covered = sum(1 for cm in content_matches if cm["matched_by"])
                coverage_pct = (covered / len(core_contents) * 100) if core_contents else 0
                chapters_involved = list(set(t["chapter_num"] for t in matched_topics_for_module))
                modules_analysis.append({
                    "module_id": module_id, "module_name": module_name, "coverage_percentage": round(coverage_pct, 1),
                    "contents_covered": covered, "contents_total": len(core_contents), "content_matches": content_matches,
                    "chapters_involved": chapters_involved, "status": self._coverage_to_status(coverage_pct), "description": ""
                })
        
        if modules_analysis:
            overall_coverage = sum(m["coverage_percentage"] for m in modules_analysis) / len(modules_analysis)
        else:
            overall_coverage = 0
        
        missing_contents = []
        for m in modules_analysis:
            for cm in m["content_matches"]:
                if not cm.get("matched_by"):
                    missing_contents.append({"content": cm["content"], "module": m["module_name"]})
        
        uncovered_chapters = []
        for topic in manual_topics:
            if topic["type"] == "chapter" and topic["text"] not in all_matched_topics:
                chapter_sections_matched = any(t["text"] in all_matched_topics for t in manual_topics if t["type"] == "section" and t["chapter_num"] == topic["chapter_num"])
                if not chapter_sections_matched:
                    uncovered_chapters.append({"chapter_num": topic["chapter_num"], "title": topic["text"]})
        
        result = {
            "manual_info": {"id": manual.get("id", "N/D"), "title": manual.get("title", "N/D"), "author": manual.get("author", "N/D"), "publisher": manual.get("publisher", "N/D"), "n_chapters": len(manual.get("chapters", [])), "n_sections": sum(len(ch.get("sections", [])) for ch in manual.get("chapters", []))},
            "framework_info": {"name": ideal_framework.get("framework", {}).get("name", "N/D"), "n_modules": len(modules), "total_contents": sum(len(m.get("core_contents", [])) for m in modules)},
            "overall_coverage": round(overall_coverage, 1), "judgment": self._coverage_to_judgment(overall_coverage),
            "recommendation": self._get_recommendation(overall_coverage, "ideal"), "modules_analysis": modules_analysis,
            "uncovered_chapters": uncovered_chapters, "gaps": {"missing_in_manual": missing_contents, "extra_in_manual": uncovered_chapters},
            "method": method_used, "summary": "", "narrative_generated": False, "analysis_date": datetime.now().isoformat()
        }
        
        if self.use_llm and method_used == "llm":
            result = self._generate_narrative_descriptions(result, manual, subject, provider_id, model)
        
        return result

    def get_available_real_frameworks(self, subject: str = None) -> List[Dict]:
        analyses = []
        archivio_dir = Path("archivio")
        if archivio_dir.exists():
            for d in sorted(archivio_dir.iterdir(), reverse=True):
                if d.is_dir():
                    fw_file = d / "framework_aggiornato.json"
                    if not fw_file.exists():
                        fw_file = d / "framework_multiclasse.json"
                    meta_file = d / "analisi.json"
                    if fw_file.exists() and meta_file.exists():
                        try:
                            with open(meta_file, "r", encoding="utf-8") as f:
                                meta = json.load(f)
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
                            analyses.append({"id": d.name, "name": meta.get("name", d.name), "materia": meta.get("materia", "N/D"), "classi": meta.get("classi", []), "coverage": coverage, "n_syllabus": n_syllabus, "date": meta.get("created", "")[:10], "framework_path": fw_file, "path": d, "type": analysis_type, "type_label": type_label})
                        except Exception as e:
                            print(f"Errore lettura {meta_file}: {e}")
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
                    analyses.insert(0, {"id": "current", "name": f"[CORRENTE] {meta.get('name', 'Analisi')}", "materia": meta.get("materia", "N/D"), "classi": meta.get("classi", []), "coverage": coverage, "n_syllabus": n_syllabus, "date": meta.get("created", "")[:10], "framework_path": fw_current, "path": current_dir, "type": analysis_type, "type_label": type_label})
            except Exception as e:
                print(f"Errore lettura analisi corrente: {e}")
        return analyses
    
    def load_real_framework(self, path: Path) -> Optional[Dict]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore caricamento framework reale {path}: {e}")
            return None

    def analyze_manual_vs_real(self, manual: Dict, real_framework: Dict, provider_id: str = "openai", model: str = "gpt-4o-mini") -> Dict:
        manual_topics = self.extract_manual_topics(manual)
        modules = real_framework.get("modules", real_framework.get("syllabus_modules", []))
        framework_info = real_framework.get("framework", {})
        classes_analyzed = framework_info.get("classes_analyzed", [])
        is_multiclass = len(classes_analyzed) > 1 or real_framework.get("summary", {}).get("n_classes", 1) > 1
        modules_analysis = []
        subject = manual.get("subject", framework_info.get("materia", "materia"))
        
        llm_result = None
        if self.use_llm and modules:
            llm_result = self._match_manual_to_framework_llm(manual, manual_topics, modules, subject, provider_id, model)
        method_used = "fallback"
        
        if llm_result and "modules_coverage" in llm_result:
            method_used = "llm"
            for mod_cov in llm_result["modules_coverage"]:
                module_id = mod_cov.get("module_id", 0)
                module_name = mod_cov.get("module_name", "")
                coverage_pct = mod_cov.get("coverage_percent", 0)
                original_module = next((m for m in modules if m.get("id") == module_id), {})
                avg_coverage_real = original_module.get("avg_coverage", 0)
                coverage_by_class = original_module.get("coverage_by_class", {})
                is_core = original_module.get("is_core", False)
                content_matches = []
                for matched in mod_cov.get("matched_contents", []):
                    content_matches.append({"content": matched.get("content", ""), "matched_by": matched.get("matched_by", ""), "chapter": matched.get("chapter_num", 0), "score": 1.0})
                for missing in mod_cov.get("missing_contents", []):
                    content_matches.append({"content": missing, "matched_by": None, "score": 0})
                covered = len([c for c in content_matches if c.get("matched_by")])
                total = len(content_matches) if content_matches else len(original_module.get("core_contents", []))
                modules_analysis.append({"module_id": module_id, "module_name": module_name, "manual_coverage": round(coverage_pct, 1), "real_avg_coverage": round(avg_coverage_real, 1), "coverage_by_class": coverage_by_class, "is_core": is_core, "contents_covered": covered, "contents_total": total, "content_matches": content_matches, "status": self._coverage_to_status(coverage_pct), "description": ""})
        else:
            method_used = "fallback"
            for module in modules:
                module_id = module.get("id", 0)
                module_name = module.get("name", "")
                core_contents = module.get("core_contents", [])
                concepts_by_class = module.get("concepts_by_class", {})
                avg_coverage_real = module.get("avg_coverage", 0)
                coverage_by_class = module.get("coverage_by_class", {})
                is_core = module.get("is_core", False)
                all_real_concepts = set()
                for classe, concepts in concepts_by_class.items():
                    for c in concepts:
                        all_real_concepts.add(c.lower() if isinstance(c, str) else str(c).lower())
                content_matches = []
                matched_count = 0
                for content in core_contents:
                    best_match = None
                    best_score = 0
                    for topic in manual_topics:
                        is_match, score = self._text_matches_content_fallback(topic["text"], content)
                        if is_match and score > best_score:
                            best_score = score
                            best_match = topic
                    if best_match:
                        content_matches.append({"content": content, "matched_by": best_match["text"], "chapter": best_match["chapter_num"], "score": round(best_score, 2)})
                        matched_count += 1
                    else:
                        content_matches.append({"content": content, "matched_by": None, "score": 0})
                concepts_matched = 0
                for concept in list(all_real_concepts)[:15]:
                    for topic in manual_topics:
                        is_match, _ = self._text_matches_content_fallback(topic["text"], concept)
                        if is_match:
                            concepts_matched += 1
                            break
                core_coverage = (matched_count / len(core_contents) * 100) if core_contents else 0
                concept_coverage = (concepts_matched / min(len(all_real_concepts), 15) * 100) if all_real_concepts else 0
                combined_coverage = (core_coverage * 0.6 + concept_coverage * 0.4) if all_real_concepts else core_coverage
                modules_analysis.append({"module_id": module_id, "module_name": module_name, "manual_coverage": round(combined_coverage, 1), "core_coverage": round(core_coverage, 1), "concept_coverage": round(concept_coverage, 1), "real_avg_coverage": round(avg_coverage_real, 1), "coverage_by_class": coverage_by_class, "is_core": is_core, "contents_covered": matched_count, "contents_total": len(core_contents), "concepts_matched": concepts_matched, "concepts_checked": min(len(all_real_concepts), 15), "content_matches": content_matches, "status": self._coverage_to_status(combined_coverage), "description": ""})
        
        if modules_analysis:
            overall_coverage = sum(m["manual_coverage"] for m in modules_analysis) / len(modules_analysis)
            core_modules = [m for m in modules_analysis if m.get("is_core", False)]
            core_coverage = sum(m["manual_coverage"] for m in core_modules) / len(core_modules) if core_modules else overall_coverage
        else:
            overall_coverage = 0
            core_coverage = 0
        
        missing_contents = []
        for m in modules_analysis:
            for cm in m.get("content_matches", []):
                if not cm.get("matched_by"):
                    missing_contents.append({"content": cm["content"], "module": m["module_name"], "is_core_module": m.get("is_core", False)})
        
        result = {
            "manual_info": {"id": manual.get("id", "N/D"), "title": manual.get("title", "N/D"), "author": manual.get("author", "N/D"), "publisher": manual.get("publisher", "N/D"), "n_chapters": len(manual.get("chapters", [])), "n_sections": sum(len(ch.get("sections", [])) for ch in manual.get("chapters", []))},
            "real_framework_info": {"name": framework_info.get("name", "N/D"), "type": "multiclass" if is_multiclass else "single", "classes_analyzed": classes_analyzed, "n_modules": len(modules), "n_core_modules": len([m for m in modules if m.get("is_core", False)])},
            "overall_coverage": round(overall_coverage, 1), "core_modules_coverage": round(core_coverage, 1),
            "judgment": self._coverage_to_judgment(overall_coverage), "recommendation": self._get_recommendation(overall_coverage, "real"),
            "modules_analysis": modules_analysis, "gaps": {"missing_in_manual": missing_contents, "priority_gaps": [g for g in missing_contents if g.get("is_core_module", False)]},
            "method": method_used, "summary": "", "narrative_generated": False, "analysis_date": datetime.now().isoformat()
        }
        
        if self.use_llm and method_used == "llm":
            result = self._generate_narrative_descriptions(result, manual, subject, provider_id, model)
        return result

    def compare_manuals(self, manuals: List[Dict], reference_framework: Dict = None, framework_type: str = "ideal", provider_id: str = "openai", model: str = "gpt-4o-mini") -> Dict:
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
            comparisons.append({"manual_id": manual.get("id", "N/D"), "manual_title": manual.get("title", "N/D"), "author": manual.get("author", "N/D"), "publisher": manual.get("publisher", "N/D"), "n_chapters": len(manual.get("chapters", [])), "n_sections": sum(len(ch.get("sections", [])) for ch in manual.get("chapters", [])), "coverage": analysis.get("overall_coverage", 0) if reference_framework else None, "weighted_coverage": analysis.get("overall_weighted_coverage", analysis.get("overall_coverage", 0)), "judgment": analysis.get("judgment", "N/D"), "modules_analysis": analysis.get("modules_analysis", []), "full_analysis": analysis})
        if reference_framework:
            comparisons.sort(key=lambda x: x.get("weighted_coverage") or x.get("coverage") or 0, reverse=True)
        modules_comparison = self._build_modules_comparison(comparisons, reference_framework)
        return {"n_manuals": len(manuals), "framework_type": framework_type if reference_framework else "none", "framework_name": reference_framework.get("framework", {}).get("name", "N/D") if reference_framework else None, "ranking": comparisons, "modules_comparison": modules_comparison, "best_manual": comparisons[0] if comparisons else None, "comparison_date": datetime.now().isoformat()}
    
    def _build_modules_comparison(self, comparisons: List[Dict], reference_framework: Dict) -> List[Dict]:
        if not reference_framework or not comparisons:
            return []
        modules = reference_framework.get("syllabus_modules", [])
        result = []
        for module in modules:
            module_name = module.get("name", "")
            module_id = module.get("id", 0)
            manual_scores = []
            for comp in comparisons:
                mod_analysis = next((m for m in comp.get("modules_analysis", []) if m.get("module_id") == module_id), None)
                if mod_analysis:
                    manual_scores.append({"manual": comp["manual_title"], "publisher": comp["publisher"], "coverage": mod_analysis.get("coverage_percentage", mod_analysis.get("manual_coverage", 0)), "status": mod_analysis.get("status", "N/D")})
            manual_scores.sort(key=lambda x: x["coverage"], reverse=True)
            result.append({"module_id": module_id, "module_name": module_name, "manual_scores": manual_scores, "best_manual": manual_scores[0]["manual"] if manual_scores else None, "avg_coverage": sum(m["coverage"] for m in manual_scores) / len(manual_scores) if manual_scores else 0})
        return result
    
    def _analyze_manual_structure(self, manual: Dict) -> Dict:
        chapters = manual.get("chapters", [])
        return {"manual_info": {"id": manual.get("id", "N/D"), "title": manual.get("title", "N/D"), "author": manual.get("author", "N/D"), "publisher": manual.get("publisher", "N/D")}, "structure": {"n_chapters": len(chapters), "n_sections": sum(len(ch.get("sections", [])) for ch in chapters), "chapters": [{"number": ch.get("number", 0), "title": ch.get("title", ""), "n_sections": len(ch.get("sections", []))} for ch in chapters]}, "overall_coverage": 0, "judgment": "Analisi strutturale"}

    def save_analysis(self, analysis: Dict, materia: str, manual_name: str, manual_type: str = "zanichelli") -> Path:
        save_dir = Path("archivio/analisi_manuali") / materia.replace(" ", "_")
        save_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        safe_name = manual_name.replace(" ", "_").replace("/", "-")[:50]
        filename = f"{safe_name}_{manual_type}_{timestamp}.json"
        filepath = save_dir / filename
        analysis_with_meta = {"metadata": {"manual_name": manual_name, "manual_type": manual_type, "materia": materia, "saved_at": datetime.now().isoformat(), "analysis_version": "2.0"}, "analysis": analysis}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(analysis_with_meta, f, indent=2, ensure_ascii=False)
        return filepath

    def get_saved_analyses(self, materia: str = None) -> List[Dict]:
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
                    analyses.append({"path": json_file, "filename": json_file.name, "materia": meta.get("materia", materia_dir.name), "manual_name": meta.get("manual_name", json_file.stem), "manual_type": meta.get("manual_type", "unknown"), "saved_at": meta.get("saved_at", ""), "coverage": analysis.get("overall_coverage", 0), "judgment": analysis.get("judgment", "N/D")})
                except Exception as e:
                    print(f"Errore lettura {json_file}: {e}")
        analyses.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
        return analyses

    def load_saved_analysis(self, path: Path) -> Optional[Dict]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore caricamento analisi {path}: {e}")
            return None

    def generate_single_analysis_report_html(self, analysis: Dict, framework_type: str = "ideal") -> str:
        manual_info = analysis.get("manual_info", {})
        modules_analysis = analysis.get("modules_analysis", [])
        gaps = analysis.get("gaps", {})
        coverage = analysis.get("overall_coverage", 0)
        if coverage >= 70:
            coverage_color = "#4caf50"
        elif coverage >= 50:
            coverage_color = "#ff9800"
        else:
            coverage_color = "#f44336"
        judgment = analysis.get("judgment", "N/D")
        judgment_class = self._judgment_to_class(judgment)
        
        modules_html = ""
        for mod in modules_analysis:
            mod_coverage = mod.get("coverage_percentage", mod.get("manual_coverage", 0))
            if mod_coverage >= 70:
                mod_color = "#4caf50"
                fill_class = "fill-high"
                icon = "🟢"
            elif mod_coverage >= 40:
                mod_color = "#ff9800"
                fill_class = "fill-medium"
                icon = "🟡"
            else:
                mod_color = "#f44336"
                fill_class = "fill-low"
                icon = "🔴"
            description = mod.get("description", "")
            if not description:
                description = f"Copertura {mod.get('status', 'N/D')}"
            modules_html += f"""
            <div class="module-card" style="border-left: 4px solid {mod_color};">
                <div class="module-header">
                    <span class="module-title">{icon} {mod.get('module_name', 'N/D')}</span>
                    <span class="module-coverage" style="color: {mod_color};">{mod_coverage:.0f}%</span>
                </div>
                <div class="coverage-bar"><div class="coverage-fill {fill_class}" style="width:{mod_coverage}%;"></div></div>
                <div class="module-description"><em>{description}</em></div>
            </div>"""
        
        gaps_html = ""
        missing = gaps.get("missing_in_manual", [])[:15]
        if missing:
            gaps_items = "".join([f"<li><strong>{g.get('module', 'N/D')}</strong>: {g.get('content', 'N/D')}</li>" for g in missing])
            remaining = len(gaps.get("missing_in_manual", [])) - 15
            if remaining > 0:
                gaps_items += f"<li><em>... e altri {remaining} contenuti</em></li>"
            gaps_html = f"""<div class="gaps-section"><h3>⚠️ Gap Rilevati</h3><ul>{gaps_items}</ul></div>"""
        
        summary = analysis.get("summary", "")
        summary_html = f"""<div class="summary-narrative"><h3>📝 Sintesi</h3><p>{summary}</p></div>""" if summary else ""
        
        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Analisi Manuale - {manual_info.get('title', 'N/D')}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px 40px; background: #f5f7fa; color: #333; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.07); }}
        h1 {{ color: #1a237e; border-bottom: 3px solid #3949ab; padding-bottom: 15px; }}
        h2 {{ color: #283593; margin-top: 35px; border-left: 4px solid #3949ab; padding-left: 15px; }}
        h3 {{ color: #3949ab; }}
        .subtitle {{ color: #666; margin-bottom: 25px; }}
        .method-badge {{ background: #e3f2fd; color: #1565c0; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 25px 0; }}
        .summary-card {{ background: #f8f9ff; padding: 20px; border-radius: 10px; text-align: center; border-top: 4px solid #3949ab; }}
        .summary-card .value {{ font-size: 2.5em; font-weight: bold; color: #1a237e; }}
        .summary-card .label {{ color: #666; font-size: 0.9em; }}
        .summary-narrative {{ background: #e8eaf6; padding: 20px; border-radius: 10px; margin: 25px 0; }}
        .summary-narrative h3 {{ margin-top: 0; }}
        .module-card {{ background: #fafafa; padding: 20px; border-radius: 10px; margin: 15px 0; }}
        .module-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .module-title {{ font-size: 1.1em; font-weight: 600; }}
        .module-coverage {{ font-size: 1.4em; font-weight: bold; }}
        .module-description {{ margin-top: 15px; padding-top: 15px; border-top: 1px solid #e0e0e0; color: #444; font-size: 0.95em; }}
        .coverage-bar {{ width: 100%; height: 12px; background: #e0e0e0; border-radius: 6px; overflow: hidden; }}
        .coverage-fill {{ height: 100%; border-radius: 6px; }}
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
        .recommendation {{ background: #e8f5e9; padding: 15px 20px; border-radius: 10px; margin-top: 20px; border-left: 4px solid #4caf50; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #888; font-size: 0.85em; text-align: center; }}
    </style>
</head>
<body>
<div class="container">
    <h1>📖 Analisi Manuale</h1>
    <p class="subtitle"><strong>{manual_info.get('title', 'N/D')}</strong> — {manual_info.get('author', 'N/D')} ({manual_info.get('publisher', 'N/D')})<br>
        Confronto vs Framework {'IDEALE' if framework_type == 'ideal' else 'REALE'} <span class="method-badge">Metodo: {analysis.get('method', 'N/D').upper()}</span></p>
    <div class="summary-grid">
        <div class="summary-card"><div class="value" style="color: {coverage_color};">{coverage:.1f}%</div><div class="label">Copertura Complessiva</div></div>
        <div class="summary-card"><div class="value">{manual_info.get('n_chapters', 0)}</div><div class="label">Capitoli</div></div>
        <div class="summary-card"><div class="value">{manual_info.get('n_sections', 0)}</div><div class="label">Sezioni</div></div>
        <div class="summary-card"><span class="judgment-badge {judgment_class}">{judgment}</span><div class="label" style="margin-top:10px;">Giudizio</div></div>
    </div>
    {summary_html}
    <div class="recommendation"><strong>📋 Raccomandazione:</strong> {analysis.get('recommendation', 'N/D')}</div>
    <h2>📊 Analisi per Modulo</h2>
    {modules_html}
    {gaps_html}
    <div class="footer">Report generato da <strong>CoreX - Manual Analyzer v2.0</strong> | Zanichelli<br>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>
</div>
</body>
</html>"""
        return html

    def generate_comparison_report_html(self, comparison: Dict) -> str:
        """
        Genera report HTML per il confronto tra manuali.
        """
        ranking = comparison.get("ranking", [])
        modules_comparison = comparison.get("modules_comparison", [])
        framework_name = comparison.get("framework_name", "N/D")
        n_manuals = comparison.get("n_manuals", 0)
        
        # CSS styling
        css = """
        <style>
            body { font-family: 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
            .header h1 { margin: 0; }
            .header p { margin: 5px 0 0 0; opacity: 0.9; }
            .ranking-card { background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 20px; margin-bottom: 20px; }
            .ranking-card.winner { border-left: 5px solid #4caf50; }
            .ranking-position { font-size: 2em; font-weight: bold; color: #1e3c72; float: left; margin-right: 20px; width: 50px; text-align: center; }
            .ranking-position.first { color: #ffc107; }
            .ranking-details { overflow: hidden; }
            .ranking-title { font-size: 1.3em; font-weight: bold; margin-bottom: 5px; }
            .ranking-meta { color: #666; margin-bottom: 10px; }
            .ranking-coverage { font-size: 1.5em; font-weight: bold; }
            .coverage-high { color: #4caf50; }
            .coverage-medium { color: #ff9800; }
            .coverage-low { color: #f44336; }
            .modules-table { width: 100%; border-collapse: collapse; margin-top: 30px; }
            .modules-table th, .modules-table td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
            .modules-table th { background: #f5f5f5; font-weight: 600; }
            .modules-table tr:hover { background: #fafafa; }
            .badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.85em; }
            .badge-best { background: #e8f5e9; color: #2e7d32; }
            .section-title { font-size: 1.5em; margin: 30px 0 20px 0; padding-bottom: 10px; border-bottom: 2px solid #1e3c72; }
        </style>
        """
        
        # Header
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Confronto Manuali - {framework_name}</title>
    {css}
</head>
<body>
    <div class="header">
        <h1>📊 Confronto tra Manuali</h1>
        <p>Framework di riferimento: {framework_name} | {n_manuals} manuali confrontati</p>
        <p>Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    </div>
"""
        
        # Ranking
        html += '<h2 class="section-title">🏆 Classifica Manuali</h2>'
        
        for i, manual in enumerate(ranking):
            position = i + 1
            coverage = manual.get("coverage", manual.get("weighted_coverage", 0))
            
            if coverage >= 70:
                cov_class = "coverage-high"
            elif coverage >= 50:
                cov_class = "coverage-medium"
            else:
                cov_class = "coverage-low"
            
            winner_class = "winner" if position == 1 else ""
            pos_class = "first" if position == 1 else ""
            
            html += f"""
    <div class="ranking-card {winner_class}">
        <div class="ranking-position {pos_class}">#{position}</div>
        <div class="ranking-details">
            <div class="ranking-title">{manual.get('manual_title', 'N/D')}</div>
            <div class="ranking-meta">{manual.get('author', 'N/D')} • {manual.get('publisher', 'N/D')} • {manual.get('n_chapters', 0)} capitoli</div>
            <div class="ranking-coverage {cov_class}">{coverage:.0f}% copertura</div>
            <div style="margin-top: 5px; color: #666;">{manual.get('judgment', 'N/D')}</div>
        </div>
        <div style="clear: both;"></div>
    </div>
"""
        
        # Confronto per modulo
        if modules_comparison:
            html += '<h2 class="section-title">📋 Confronto per Modulo</h2>'
            html += """
    <table class="modules-table">
        <thead>
            <tr>
                <th>Modulo</th>
                <th>Miglior Manuale</th>
                <th>Copertura Media</th>
                <th>Dettaglio</th>
            </tr>
        </thead>
        <tbody>
"""
            
            for mod in modules_comparison:
                best = mod.get("best_manual", "N/D")
                avg = mod.get("avg_coverage", 0)
                
                # Dettaglio manuali per questo modulo
                detail_parts = []
                for score in mod.get("manual_scores", [])[:3]:
                    detail_parts.append(f"{score['manual'][:20]}: {score['coverage']:.0f}%")
                detail = " | ".join(detail_parts)
                
                html += f"""
            <tr>
                <td><strong>{mod.get('module_name', 'N/D')}</strong></td>
                <td><span class="badge badge-best">{best}</span></td>
                <td>{avg:.0f}%</td>
                <td style="font-size: 0.9em; color: #666;">{detail}</td>
            </tr>
"""
            
            html += """
        </tbody>
    </table>
"""
        
        # Footer
        html += """
    <div style="margin-top: 40px; padding: 20px; background: #f5f5f5; border-radius: 10px; text-align: center; color: #666;">
        <p>Report generato da <strong>CoreX - PromoIntelligence</strong></p>
    </div>
</body>
</html>
"""
        
        return html