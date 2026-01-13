"""
Framework Adapter per CoreX v3.2
Mappa i concetti estratti sui MODULI del framework IDEALE
Calcola copertura individuale per ogni syllabus
Supporta sia formato vecchio (moduli/criteri) che nuovo (syllabus_modules/criteria)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict
import re


class FrameworkAdapter:
    """
    Mappa i concetti estratti dai programmi reali sulla struttura del framework ideale.
    Il framework ideale definisce la struttura, quello reale misura quanto è coperta.
    Supporta due formati di framework:
    - Formato A (vecchio): {"materia": ..., "moduli": [...], "criteri": [...]}
    - Formato B (nuovo): {"framework": {...}, "syllabus_modules": [...], "criteria": [...]}
    """
    
    def __init__(self, frameworks_dir: Path = None):
        self.frameworks_dir = frameworks_dir or Path("frameworks")
        
        # Espansione semantica: sinonimi e varianti per migliorare il matching
        self.semantic_expansions = {
            # Struttura atomi e legami
            "orbitale atomici e ibridazione": ["orbitali", "ibridazione", "sp3", "sp2", "sp", "orbitale"],
            "legami covalenti, sigma/pi": ["legame covalente", "legame sigma", "legame pi", "legame chimico", "legami"],
            "polarità molecolare": ["polarità", "momento dipolare", "dipolo", "molecola polare"],
            "forze intermolecolari": ["forze di van der waals", "legame idrogeno", "forze di london", "interazioni intermolecolari"],
            
            # Idrocarburi
            "alcani, alceni, alchini": ["alcani", "alceni", "alchini", "idrocarburi saturi", "idrocarburi insaturi"],
            "isomeria strutturale e spaziale": ["isomeria", "isomeri", "isomeria di struttura", "isomeria geometrica", "isomeri di catena"],
            "regole nomenclatura iupac": ["nomenclatura", "iupac", "nomenclatura iupac"],
            "proprietà fisiche e reattività": ["proprietà fisiche", "reattività", "punto di ebollizione", "solubilità"],
            
            # Gruppi funzionali
            "alcoli, eteri, fenoli": ["alcoli", "eteri", "fenoli", "gruppo ossidrile", "oh"],
            "aldeidi, chetoni": ["aldeidi", "chetoni", "gruppo carbonilico", "carbonile"],
            "acidi carbossilici e derivati": ["acidi carbossilici", "esteri", "ammidi", "anidridi", "alogenuri acilici", "gruppo carbossilico"],
            "ammine e altri gruppi": ["ammine", "ammidi", "nitrili", "gruppo amminico"],
            
            # Meccanismi di reazione
            "reazioni di sostituzione nucleofila/elettrofila": ["sostituzione nucleofila", "sn1", "sn2", "sostituzione elettrofila", "reazioni di sostituzione"],
            "addizione e eliminazione": ["addizione", "eliminazione", "e1", "e2", "reazioni di addizione", "reazioni di eliminazione", "addizione nucleofila", "addizione elettrofila"],
            "radicali liberi": ["radicali", "radicali liberi", "reazioni radicaliche"],
            "meccanismi di reazione comuni": ["meccanismo", "meccanismi", "frecce curve", "intermedi di reazione"],
            
            # Stereochimica
            "isomeria ottica, enantiomeri": ["enantiomeri", "isomeria ottica", "attività ottica", "potere rotatorio"],
            "carbonio chirale, centri stereogenici": ["chiralità", "carbonio chirale", "centro stereogenico", "stereocentro", "carbonio asimmetrico"],
            "proiezioni di fischer e newman": ["fischer", "newman", "proiezioni", "conformazioni"],
            "attività ottica e miscugli racemici": ["racemico", "racemizzazione", "miscela racemica", "attività ottica"],
            
            # Composti aromatici
            "struttura benzene e aromaticità": ["benzene", "aromaticità", "aromatici", "anello aromatico", "regola di hückel"],
            "reazioni di sostituzione aromatica": ["sostituzione aromatica", "sostituzione elettrofila aromatica", "sea"],
            "composti aromatici sostituiti": ["sostituenti", "effetto induttivo", "effetto mesomerico", "orto", "meta", "para"],
            "composti eterociclici": ["eterocicli", "eterociclici", "piridina", "pirrolo", "furano", "tiofene"],
            
            # Polimeri
            "polimerizzazione additiva/condensazione": ["polimerizzazione", "polimeri", "monomeri", "poliaddizione", "policondensazione"],
            "proprietà meccaniche polimeri": ["proprietà polimeri", "plasticità", "elasticità"],
            "polimeri naturali/sintetici": ["polimeri naturali", "polimeri sintetici", "gomma", "plastica", "nylon"],
            "applicazioni agrochimiche/biotecnologiche": ["applicazioni", "biotecnologie", "agrochimica"],
            
            # Bio-organica
            "strutture aminoacidi, proteine": ["amminoacidi", "aminoacidi", "proteine", "struttura proteica", "legame peptidico"],
            "carboidrati e lipidi": ["carboidrati", "zuccheri", "lipidi", "grassi", "monosaccaridi", "disaccaridi", "polisaccaridi", "glucosio"],
            "enzimi e meccanismi catalitici": ["enzimi", "catalisi enzimatica", "sito attivo"],
            "acidi nucleici e replicazione": ["acidi nucleici", "dna", "rna", "nucleotidi", "nucleosidi", "replicazione"],
            
            # Spettroscopia
            "spettroscopia ir": ["infrarosso", "ir", "spettroscopia ir", "assorbimento ir"],
            "spettroscopia nmr": ["nmr", "risonanza magnetica nucleare", "spettroscopia nmr", "chemical shift"],
            "mass spectrometry": ["spettrometria di massa", "mass spectrometry", "ms", "frammentazione"],
            "cromatografia": ["cromatografia", "hplc", "gc", "tlc", "separazione cromatografica"],
            
            # Sintesi avanzata
            "sintesi multistep": ["sintesi", "sintesi organica", "strategia sintetica", "retrosintesi"],
            "protezione/deprotezione gruppi funzionali": ["gruppi protettori", "protezione", "deprotezione"],
            "sintesi asimmetrica": ["sintesi asimmetrica", "enantioselettiva", "stereoselettiva"],
            "catalisi organica": ["catalisi", "catalizzatore", "organocatalisi"],
            
            # Organometallica
            "composti metallo-organici": ["organometallici", "composti organometallici", "metallo-carbonio"],
            "catalisi omogenea": ["catalisi omogenea", "complessi metallici"],
            "reazioni di coupling": ["coupling", "cross-coupling", "suzuki", "heck", "grignard"],
            "applicazioni industriali/farmaceutiche": ["applicazioni farmaceutiche", "sintesi farmaceutica", "industria chimica"],
            
            # Laboratorio
            "metodi analitici chimica organica": ["analisi", "metodi analitici", "caratterizzazione"],
            "separazioni e purificazioni": ["purificazione", "distillazione", "cristallizzazione", "estrazione", "separazione"],
            "sicurezza e gestione rifiuti": ["sicurezza", "rifiuti", "smaltimento", "norme sicurezza"],
            "progettazione esperimenti/report": ["esperimenti", "laboratorio", "relazione", "report"]
        }
    
    def find_framework(self, materia: str) -> Optional[Path]:
        """
        Trova il framework ideale corrispondente alla materia.
        Cerca automaticamente tutti i file JSON nella cartella frameworks.
        """
        if not self.frameworks_dir.exists():
            return None
        
        materia_lower = materia.lower().replace(" ", "_")
        
        # Cerca corrispondenza esatta (case-insensitive)
        for fw_file in self.frameworks_dir.glob("*.json"):
            filename_lower = fw_file.stem.lower()
            if filename_lower == materia_lower:
                return fw_file
        
        # Cerca corrispondenza parziale
        for fw_file in self.frameworks_dir.glob("*.json"):
            filename_lower = fw_file.stem.lower()
            if filename_lower in materia_lower or materia_lower in filename_lower:
                return fw_file
        
        # Cerca dentro i file JSON per il campo materia/name
        for fw_file in self.frameworks_dir.glob("*.json"):
            try:
                with open(fw_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Formato A: campo "materia" al primo livello
                if "materia" in data:
                    if materia_lower in data["materia"].lower().replace(" ", "_"):
                        return fw_file
                
                # Formato B: campo "framework.name"
                if "framework" in data and "name" in data["framework"]:
                    fw_name = data["framework"]["name"].lower()
                    if materia_lower in fw_name.replace(" ", "_"):
                        return fw_file
            except:
                continue
        
        return None
    
    def load_framework(self, materia: str) -> Optional[Dict]:
        """
        Carica il framework ideale JSON per una materia.
        Normalizza automaticamente la struttura per supportare entrambi i formati.
        """
        fw_path = self.find_framework(materia)
        if not fw_path:
            return None
        
        with open(fw_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Normalizza la struttura
        return self._normalize_framework(data)
    
    def _normalize_framework(self, data: Dict) -> Dict:
        """
        Normalizza il framework per avere una struttura consistente.
        Converte Formato B (nuovo) in struttura compatibile con il resto del codice.
        """
        # Se ha già "syllabus_modules", è già nel formato che ci aspettiamo internamente
        if "syllabus_modules" in data:
            # Assicuriamoci che i moduli abbiano "core_contents"
            for mod in data.get("syllabus_modules", []):
                if "core_contents" not in mod and "contents" in mod:
                    mod["core_contents"] = mod["contents"]
            return data
        
        # Se ha "moduli" (Formato A vecchio), converti a "syllabus_modules"
        if "moduli" in data:
            normalized = data.copy()
            
            # Converti moduli -> syllabus_modules
            syllabus_modules = []
            for mod in data.get("moduli", []):
                new_mod = {
                    "id": mod.get("id"),
                    "name": mod.get("nome", mod.get("name", "")),
                    "core_contents": mod.get("sottoargomenti", mod.get("core_contents", []))
                }
                syllabus_modules.append(new_mod)
            
            normalized["syllabus_modules"] = syllabus_modules
            
            # Crea struttura framework se non esiste
            if "framework" not in normalized:
                normalized["framework"] = {
                    "name": data.get("materia", "Framework"),
                    "version": data.get("versione", "1.0"),
                    "description": "",
                    "date": data.get("data_aggiornamento", "")
                }
            
            return normalized
        
        # Se ha "framework" ma non syllabus_modules (struttura parziale)
        if "framework" in data and "modules" in data:
            data["syllabus_modules"] = data["modules"]
            return data
        
        # Ritorna i dati così come sono se non riconosciamo la struttura
        return data
    
    def _normalize_text(self, text: str) -> str:
        """Normalizza il testo per il matching"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _concept_matches_content(self, concept: str, content: str) -> bool:
        """Verifica se un concetto estratto corrisponde a un contenuto del framework ideale"""
        concept_norm = self._normalize_text(concept)
        content_norm = self._normalize_text(content)
        
        # Match diretto
        if concept_norm in content_norm or content_norm in concept_norm:
            return True
        
        # Match tramite espansione semantica
        if content_norm in self.semantic_expansions:
            variants = self.semantic_expansions[content_norm]
            for variant in variants:
                variant_norm = self._normalize_text(variant)
                if concept_norm == variant_norm or concept_norm in variant_norm or variant_norm in concept_norm:
                    return True
        
        # Match per parole chiave (almeno 2 parole significative in comune)
        concept_words = set(w for w in concept_norm.split() if len(w) > 3)
        content_words = set(w for w in content_norm.split() if len(w) > 3)
        
        # Cerca anche nelle espansioni
        for content_key, variants in self.semantic_expansions.items():
            if any(w in content_key for w in content_words):
                for variant in variants:
                    variant_words = set(w for w in self._normalize_text(variant).split() if len(w) > 3)
                    if len(concept_words & variant_words) >= 1:
                        return True
        
        common_words = concept_words & content_words
        if len(common_words) >= 1 and len(concept_words) <= 3:
            return True
        if len(common_words) >= 2:
            return True
        
        return False
    
    def map_concepts_to_ideal_modules(
        self,
        concepts: List[Dict],
        ideal_framework: Dict
    ) -> Dict[int, Dict]:
        """
        Mappa i concetti estratti sui moduli del framework ideale.
        """
        modules = ideal_framework.get("syllabus_modules", [])
        module_mapping = {}
        
        for module in modules:
            module_id = module.get("id", 0)
            module_name = module.get("name", "")
            core_contents = module.get("core_contents", [])
            
            matched_concepts = []
            covered_contents = set()
            
            for content in core_contents:
                for concept in concepts:
                    concept_name = concept.get("name", concept.get("canonical_name", ""))
                    concept_freq = concept.get("frequency", 0)
                    
                    if self._concept_matches_content(concept_name, content):
                        already_added = any(mc["name"] == concept_name for mc in matched_concepts)
                        if not already_added:
                            matched_concepts.append({
                                "name": concept_name,
                                "frequency": concept_freq,
                                "matched_content": content
                            })
                        covered_contents.add(content)
            
            missing_contents = [c for c in core_contents if c not in covered_contents]
            coverage_pct = (len(covered_contents) / len(core_contents) * 100) if core_contents else 0
            
            avg_freq = 0
            if matched_concepts:
                avg_freq = sum(c["frequency"] for c in matched_concepts) / len(matched_concepts)
            
            matched_concepts.sort(key=lambda x: x["frequency"], reverse=True)
            
            module_mapping[module_id] = {
                "module_id": module_id,
                "module_name": module_name,
                "core_contents": core_contents,
                "matched_concepts": matched_concepts,
                "covered_contents": list(covered_contents),
                "missing_contents": missing_contents,
                "n_contents_total": len(core_contents),
                "n_contents_covered": len(covered_contents),
                "coverage_percentage": round(coverage_pct, 1),
                "avg_frequency": round(avg_freq, 1)
            }
        
        return module_mapping
    
    def calculate_overall_coverage(self, module_mapping: Dict[int, Dict]) -> Dict:
        """Calcola la copertura complessiva del framework ideale"""
        if not module_mapping:
            return {"percentage": 0, "judgment": "N/D", "recommendation": ""}
        
        total_contents = sum(m["n_contents_total"] for m in module_mapping.values())
        covered_contents = sum(m["n_contents_covered"] for m in module_mapping.values())
        
        overall_pct = (covered_contents / total_contents * 100) if total_contents > 0 else 0
        
        all_frequencies = []
        for m in module_mapping.values():
            for c in m["matched_concepts"]:
                all_frequencies.append(c["frequency"])
        
        avg_frequency = sum(all_frequencies) / len(all_frequencies) if all_frequencies else 0
        combined_score = (overall_pct * 0.6) + (avg_frequency * 0.4)
        
        if combined_score >= 75:
            judgment = "Eccellente allineamento"
            recommendation = "Il framework ideale è molto ben rappresentato nei programmi reali"
        elif combined_score >= 55:
            judgment = "Buon allineamento"
            recommendation = "Il framework ideale è sostanzialmente coperto, con alcune lacune"
        elif combined_score >= 35:
            judgment = "Allineamento parziale"
            recommendation = "Significative differenze tra ideale e realtà - valutare aggiornamenti"
        else:
            judgment = "Allineamento basso"
            recommendation = "Il framework ideale è poco rappresentato nei programmi reali"
        
        return {
            "percentage": round(overall_pct, 1),
            "avg_frequency": round(avg_frequency, 1),
            "combined_score": round(combined_score, 1),
            "judgment": judgment,
            "recommendation": recommendation,
            "total_contents": total_contents,
            "covered_contents": covered_contents
        }
    
    def identify_gaps(
        self,
        concepts: List[Dict],
        module_mapping: Dict[int, Dict],
        ideal_framework: Dict
    ) -> Dict:
        """Identifica gap tra realtà e ideale"""
        
        all_matched_concepts = set()
        for m in module_mapping.values():
            for c in m["matched_concepts"]:
                all_matched_concepts.add(c["name"].lower())
        
        reality_not_in_ideal = []
        for concept in concepts:
            concept_name = concept.get("name", "")
            concept_freq = concept.get("frequency", 0)
            if concept_freq >= 40 and concept_name.lower() not in all_matched_concepts:
                reality_not_in_ideal.append({
                    "name": concept_name,
                    "frequency": concept_freq
                })
        
        reality_not_in_ideal.sort(key=lambda x: x["frequency"], reverse=True)
        
        ideal_not_in_reality = []
        for m in module_mapping.values():
            for content in m["missing_contents"]:
                ideal_not_in_reality.append({
                    "content": content,
                    "module": m["module_name"]
                })
        
        return {
            "reality_not_in_ideal": {
                "title": "Argomenti frequenti nei programmi ma NON nel framework ideale",
                "description": "Questi argomenti sono insegnati frequentemente ma non previsti nel modello",
                "action": "Valutare se aggiungere al framework ideale",
                "items": reality_not_in_ideal[:20]
            },
            "ideal_not_in_reality": {
                "title": "Contenuti del framework ideale NON trovati nei programmi",
                "description": "Questi contenuti sono previsti nel modello ma raramente insegnati",
                "action": "Valutare se il framework è troppo ambizioso o se i programmi sono carenti",
                "items": ideal_not_in_reality
            }
        }
    
    def calculate_syllabus_ideal_coverage(
        self,
        syllabus_concepts: Set[str],
        module_mapping: Dict[int, Dict]
    ) -> Tuple[float, int, int]:
        """
        Calcola la copertura del framework ideale per un singolo syllabus.
        """
        contents_covered = 0
        total_contents = 0
        
        for mod_id, mod_data in module_mapping.items():
            total_contents += mod_data["n_contents_total"]
            
            for content in mod_data["core_contents"]:
                for concept in syllabus_concepts:
                    if self._concept_matches_content(concept, content):
                        contents_covered += 1
                        break
        
        coverage_pct = (contents_covered / total_contents * 100) if total_contents > 0 else 0
        
        return coverage_pct, contents_covered, total_contents
    
    def generate_zanichelli_output(
        self,
        materia: str,
        concepts: List[Dict],
        syllabus_data: List[Dict],
        classi_analizzate: List[str],
        modules_from_clustering: List[Dict] = None
    ) -> Dict:
        """
        Genera output strutturato mappando i concetti reali sul framework ideale.
        Calcola copertura individuale per ogni syllabus.
        """
        
        # Carica framework ideale
        ideal_framework = self.load_framework(materia)
        
        if not ideal_framework:
            return self._generate_output_without_ideal(
                materia, concepts, syllabus_data, classi_analizzate
            )
        
        # Mappa concetti aggregati sui moduli ideali
        module_mapping = self.map_concepts_to_ideal_modules(concepts, ideal_framework)
        
        # Calcola copertura complessiva
        overall_coverage = self.calculate_overall_coverage(module_mapping)
        
        # Identifica gap
        gaps = self.identify_gaps(concepts, module_mapping, ideal_framework)
        
        # Classifica moduli per copertura
        modules_by_coverage = {
            "well_covered": [],
            "partially_covered": [],
            "poorly_covered": []
        }
        
        for mod_id, mod_data in module_mapping.items():
            cov = mod_data["coverage_percentage"]
            entry = {
                "module_id": mod_id,
                "module_name": mod_data["module_name"],
                "coverage_percentage": cov,
                "avg_frequency": mod_data["avg_frequency"],
                "n_concepts_found": len(mod_data["matched_concepts"]),
                "n_contents_covered": mod_data["n_contents_covered"],
                "n_contents_total": mod_data["n_contents_total"],
                "matched_concepts": mod_data["matched_concepts"][:10],
                "missing_contents": mod_data["missing_contents"]
            }
            
            if cov >= 70:
                modules_by_coverage["well_covered"].append(entry)
            elif cov >= 40:
                modules_by_coverage["partially_covered"].append(entry)
            else:
                modules_by_coverage["poorly_covered"].append(entry)
        
        for key in modules_by_coverage:
            modules_by_coverage[key].sort(key=lambda x: x["coverage_percentage"], reverse=True)
        
        # Calcolo copertura individuale per ogni syllabus
        syllabus_details = []
        
        all_n_concepts = [s.get("n_concepts", 0) for s in syllabus_data]
        avg_concepts = sum(all_n_concepts) / len(all_n_concepts) if all_n_concepts else 0
        
        for i, s in enumerate(syllabus_data):
            syllabus_concepts = set(c.lower() for c in s.get("concepts", []))
            n_concepts = s.get("n_concepts", len(syllabus_concepts))
            
            ideal_coverage, contents_covered, total_contents = self.calculate_syllabus_ideal_coverage(
                syllabus_concepts, 
                module_mapping
            )
            
            if ideal_coverage >= 55:
                judgment = "Programma completo"
            elif ideal_coverage >= 40:
                judgment = "Programma standard"
            elif ideal_coverage >= 25:
                judgment = "Programma essenziale"
            else:
                judgment = "Programma ridotto"
            
            syllabus_details.append({
                "id": s.get("id", f"syl_{i}"),
                "university": s.get("university", "N/D"),
                "professor": s.get("professor", "N/D"),
                "classe": s.get("classe", "N/D"),
                "n_concepts": n_concepts,
                "ideal_coverage": round(ideal_coverage, 1),
                "contents_covered": contents_covered,
                "total_ideal_contents": total_contents,
                "judgment": judgment
            })
        
        # Estrai info framework (compatibile con entrambi i formati)
        framework_info = ideal_framework.get("framework", {})
        framework_name = framework_info.get("name", ideal_framework.get("materia", "N/D"))
        
        output = {
            "meta": {
                "generated_by": "CoreX v3.2",
                "date": datetime.now().isoformat(),
                "materia": materia,
                "classes_analyzed": classi_analizzate,
                "analysis_type": "mapping_to_ideal_framework"
            },
            "ideal_framework_info": {
                "name": framework_name,
                "n_modules": len(ideal_framework.get("syllabus_modules", [])),
                "total_core_contents": sum(
                    len(m.get("core_contents", []))
                    for m in ideal_framework.get("syllabus_modules", [])
                )
            },
            "analysis_summary": {
                "n_syllabus_analyzed": len(syllabus_data),
                "n_concepts_extracted": len(concepts),
                "n_concepts_mapped": sum(
                    len(m["matched_concepts"]) for m in module_mapping.values()
                )
            },
            "overall_assessment": {
                "coverage_percentage": overall_coverage["percentage"],
                "avg_frequency": overall_coverage["avg_frequency"],
                "combined_score": overall_coverage["combined_score"],
                "judgment": overall_coverage["judgment"],
                "recommendation": overall_coverage["recommendation"],
                "contents_covered": f"{overall_coverage['covered_contents']}/{overall_coverage['total_contents']}"
            },
            "modules_analysis": module_mapping,
            "modules_by_coverage": modules_by_coverage,
            "gaps_analysis": gaps,
            "syllabus_details": syllabus_details,
            "syllabus_modules_analysis": [
                {
                    "id": m["module_id"],
                    "name": m["module_name"],
                    "coverage": {
                        "percentage": m["coverage_percentage"],
                        "frequency": m["avg_frequency"],
                        "level": self._coverage_to_level(m["coverage_percentage"]),
                        "level_description": self._get_level_description(m["coverage_percentage"]),
                        "concepts_found": len(m["matched_concepts"]),
                        "contents_covered": m["n_contents_covered"],
                        "contents_total": m["n_contents_total"]
                    },
                    "top_concepts": m["matched_concepts"][:8],
                    "missing_contents": m["missing_contents"]
                }
                for m in module_mapping.values()
            ]
        }
        
        return output
    
    def _coverage_to_level(self, coverage: float) -> int:
        """Converte copertura in livello 1-5"""
        if coverage >= 80:
            return 5
        elif coverage >= 60:
            return 4
        elif coverage >= 40:
            return 3
        elif coverage >= 20:
            return 2
        else:
            return 1
    
    def _get_level_description(self, coverage: float) -> str:
        """Descrizione testuale del livello di copertura"""
        if coverage >= 80:
            return "Eccellente - Modulo ben rappresentato"
        elif coverage >= 60:
            return "Buono - Copertura solida"
        elif coverage >= 40:
            return "Sufficiente - Copertura parziale"
        elif coverage >= 20:
            return "Basso - Pochi contenuti coperti"
        else:
            return "Minimo - Modulo quasi assente"
    
    def _generate_output_without_ideal(
        self,
        materia: str,
        concepts: List[Dict],
        syllabus_data: List[Dict],
        classi_analizzate: List[str]
    ) -> Dict:
        """Genera output quando non esiste un framework ideale"""
        
        core = [c for c in concepts if c.get("frequency", 0) >= 60]
        common = [c for c in concepts if 30 <= c.get("frequency", 0) < 60]
        specific = [c for c in concepts if c.get("frequency", 0) < 30]
        
        return {
            "meta": {
                "generated_by": "CoreX v3.2",
                "date": datetime.now().isoformat(),
                "materia": materia,
                "classes_analyzed": classi_analizzate,
                "analysis_type": "no_ideal_framework"
            },
            "warning": "Nessun framework ideale disponibile per questa materia. Output basato solo sui dati estratti.",
            "analysis_summary": {
                "n_syllabus_analyzed": len(syllabus_data),
                "n_concepts_extracted": len(concepts),
                "n_core_concepts": len(core),
                "n_common_concepts": len(common),
                "n_specific_concepts": len(specific)
            },
            "concepts_by_frequency": {
                "core": sorted(core, key=lambda x: x.get("frequency", 0), reverse=True)[:30],
                "common": sorted(common, key=lambda x: x.get("frequency", 0), reverse=True)[:30],
                "specific": sorted(specific, key=lambda x: x.get("frequency", 0), reverse=True)[:20]
            },
            "syllabus_details": [
                {
                    "id": s.get("id", f"syl_{i}"),
                    "university": s.get("university", "N/D"),
                    "professor": s.get("professor", "N/D"),
                    "classe": s.get("classe", "N/D"),
                    "n_concepts": s.get("n_concepts", 0),
                    "ideal_coverage": 0,
                    "judgment": "N/D - Nessun framework ideale"
                }
                for i, s in enumerate(syllabus_data)
            ]
        }


def get_available_frameworks(frameworks_dir: Path = None) -> List[str]:
    """Ritorna lista delle materie con framework ideale disponibile"""
    fw_dir = frameworks_dir or Path("frameworks")
    if not fw_dir.exists():
        return []
    
    available = []
    for f in fw_dir.glob("*.json"):
        name = f.stem.replace("_", " ").title()
        available.append(name)
    
    return sorted(available)