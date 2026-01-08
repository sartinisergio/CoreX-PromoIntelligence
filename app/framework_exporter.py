"""
CoreX - Framework Exporter v1.0
Converte il Framework Reale di CoreX nel formato compatibile con UNI-SCAN,
arricchendolo con i dati di validazione empirica.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class FrameworkExporter:
    """
    Esporta il Framework Reale (multiclasse) di CoreX
    nel formato JSON compatibile con UNI-SCAN.
    """
    
    # Mappatura classi di laurea → indirizzi UNI-SCAN
    CLASS_TO_INDIRIZZO = {
        # Biologia/Biotecnologie
        "L-13_Biologia": "Bio",
        "L-2_Biotecnologie": "Bio",
        "LM-6_Biologia": "Bio",
        
        # Chimica
        "L-27_Scienze_chimiche": "Chim",
        "LM-54_Chimica": "Chim",
        
        # Farmacia
        "L-29_Scienze_farmaceutiche": "Farm",
        "LM-13_Farmacia": "Farm",
        
        # Fisica/Ingegneria
        "L-7-8-9_Ingegneria": "Fis",
        "L-30_Fisica": "Fis",
        "LM-17_Fisica": "Fis",
        
        # Scienze Naturali/Ambientali
        "L-32_Scienze_naturali_amb": "Amb",
        "L-34_Geologia": "Amb",
        "L-25_Scienze_e_tecnologie_agrarie": "Amb",
        "L-26_Scienze_e_tecnologie_alimentari": "Amb",
    }
    
    def __init__(self, materia: str):
        self.materia = materia
        self.data_dir = Path("data")
        self.frameworks_dir = Path("frameworks")
        self.export_dir = Path("export")
        self.export_dir.mkdir(exist_ok=True)
    
    def load_corex_framework(self, path: Path = None) -> Optional[Dict]:
        """Carica il Framework Reale generato da CoreX."""
        if path and path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # Cerca in analisi corrente
        default_path = self.data_dir / "analisi_corrente" / "framework_multiclasse.json"
        if default_path.exists():
            with open(default_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Verifica che sia un framework reale (non evidence-based)
                if data.get("framework", {}).get("type") == "multiclass_on_ideal_framework":
                    return data
        
        print(f"[WARN] Framework Reale CoreX non trovato per {self.materia}")
        return None
    
    def load_uniscan_template(self, path: Path = None) -> Optional[Dict]:
        """
        Carica il template UNI-SCAN esistente per mantenere
        criteri, prerequisiti, obiettivi, ecc.
        """
        if path and path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # Cerca nella cartella frameworks
        possible_names = [
            f"{self.materia}_uniscan.json",
            f"{self.materia.lower()}_uniscan.json",
            f"{self.materia.replace(' ', '_')}_uniscan.json",
        ]
        
        for name in possible_names:
            path = self.frameworks_dir / name
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        
        return None
    
    def export(
        self,
        corex_framework: Dict = None,
        uniscan_template: Dict = None,
        include_concepts: bool = True,
        top_concepts: int = 10
    ) -> Dict:
        """
        Esporta il Framework Reale CoreX nel formato UNI-SCAN.
        
        Args:
            corex_framework: Framework Reale CoreX (se None, lo carica)
            uniscan_template: Template UNI-SCAN esistente (per criteri, ecc.)
            include_concepts: Se includere i concetti reali frequenti
            top_concepts: Quanti concetti frequenti includere per modulo
            
        Returns:
            Dict nel formato UNI-SCAN arricchito
        """
        # Carica dati
        corex = corex_framework or self.load_corex_framework()
        template = uniscan_template or self.load_uniscan_template()
        
        if not corex:
            return {"error": "Framework CoreX non trovato"}
        
        # Estrai metadati CoreX
        framework_info = corex.get("framework", {})
        summary = corex.get("summary", {})
        classes_analyzed = framework_info.get("classes_analyzed", [])
        
        # Costruisci output UNI-SCAN
        output = {
            "materia": self.materia.replace("_", " "),
            "versione": "2.0-validated",
            "data_aggiornamento": datetime.now().strftime("%Y-%m-%d"),
            "validazione": {
                "fonte": "CoreX PromoIntelligence",
                "tipo_analisi": "multiclass_on_ideal_framework",
                "n_programmi": sum(
                    corex.get("class_details", {}).get(c, {}).get("n_syllabus", 0)
                    for c in classes_analyzed
                ),
                "n_classi": summary.get("n_classes", len(classes_analyzed)),
                "classi_analizzate": classes_analyzed,
                "copertura_media_globale": round(
                    sum(summary.get("overall_coverage_by_class", {}).values()) / 
                    len(summary.get("overall_coverage_by_class", {}))
                    if summary.get("overall_coverage_by_class") else 0,
                    1
                ),
                "data_analisi": framework_info.get("generation_date", "")[:10],
                "soglie": framework_info.get("thresholds", {})
            }
        }
        
        # Mantieni prerequisiti e obiettivi dal template se disponibile
        if template:
            output["prerequisiti"] = template.get("prerequisiti", [])
            output["obiettivi"] = template.get("obiettivi", [])
        else:
            output["prerequisiti"] = []
            output["obiettivi"] = []
        
        # Converti indirizzi
        output["indirizzi"] = self._convert_indirizzi(
            classes_analyzed, 
            summary.get("overall_coverage_by_class", {}),
            template
        )
        
        # Converti moduli
        output["moduli"] = self._convert_moduli(
            corex.get("modules", []),
            include_concepts,
            top_concepts
        )
        
        # Mantieni criteri dal template o genera default
        if template and template.get("criteri"):
            output["criteri"] = template["criteri"]
        else:
            output["criteri"] = self._generate_default_criteri(output["moduli"])
        
        # Scala interpretazione
        if template and template.get("scala_interpretazione"):
            output["scala_interpretazione"] = template["scala_interpretazione"]
        else:
            output["scala_interpretazione"] = {
                "85-100": {"giudizio": "Eccellente", "descrizione": "Copertura completa", "azione": "Adozione consigliata"},
                "70-84": {"giudizio": "Buono", "descrizione": "Copertura solida", "azione": "Raccomandato"},
                "55-69": {"giudizio": "Sufficiente", "descrizione": "Alcune lacune", "azione": "Con riserva"},
                "<55": {"giudizio": "Insufficiente", "descrizione": "Lacune significative", "azione": "Non adottare"}
            }
        
        # Istruzioni prompt (opzionale)
        if template and template.get("istruzioni_prompt"):
            output["istruzioni_prompt"] = template["istruzioni_prompt"]
        
        return output
    
    def _convert_indirizzi(
        self, 
        classes: List[str], 
        coverage_by_class: Dict,
        template: Dict = None
    ) -> List[Dict]:
        """Converte le classi CoreX in indirizzi UNI-SCAN."""
        
        # Raggruppa classi per indirizzo
        indirizzo_classes = {}
        for cls in classes:
            ind = self.CLASS_TO_INDIRIZZO.get(cls, "Altro")
            if ind not in indirizzo_classes:
                indirizzo_classes[ind] = []
            indirizzo_classes[ind].append(cls)
        
        # Nomi completi indirizzi
        indirizzo_names = {
            "Bio": "Biologia/Biotecnologie",
            "Chim": "Chimica",
            "Farm": "Farmacia",
            "Fis": "Fisica/Ingegneria",
            "Amb": "Scienze Naturali/Ambientali",
            "Altro": "Altro"
        }
        
        indirizzi = []
        for codice, cls_list in indirizzo_classes.items():
            # Calcola copertura media per indirizzo
            coverages = [coverage_by_class.get(c, 0) for c in cls_list]
            avg_coverage = sum(coverages) / len(coverages) if coverages else 0
            
            ind_data = {
                "nome": indirizzo_names.get(codice, codice),
                "codice": codice,
                "classi_corrispondenti": cls_list,
                "copertura_reale": round(avg_coverage, 1)
            }
            
            # Aggiungi focus e moduli_critici dal template se disponibile
            if template:
                for t_ind in template.get("indirizzi", []):
                    if t_ind.get("codice") == codice:
                        ind_data["focus"] = t_ind.get("focus", "")
                        ind_data["livello"] = t_ind.get("livello", "Avanzato")
                        ind_data["moduli_critici"] = t_ind.get("moduli_critici", [])
                        break
            
            indirizzi.append(ind_data)
        
        return indirizzi
    
    def _convert_moduli(
        self, 
        corex_modules: List[Dict],
        include_concepts: bool,
        top_concepts: int
    ) -> List[Dict]:
        """Converte i moduli CoreX nel formato UNI-SCAN."""
        
        moduli = []
        for mod in corex_modules:
            modulo = {
                "id": mod.get("id"),
                "nome": mod.get("name", ""),
                "sottoargomenti": mod.get("core_contents", [])
            }
            
            # Aggiungi dati di validazione
            modulo["validazione"] = {
                "copertura_media": mod.get("avg_coverage", 0),
                "copertura_min": mod.get("min_coverage", 0),
                "copertura_max": mod.get("max_coverage", 0),
                "is_core": mod.get("is_core", False),
                "is_distinctive": mod.get("is_distinctive", False),
                "distinctive_for": mod.get("distinctive_for", []),
                "gap_for": mod.get("gap_for", []),
                "copertura_per_classe": mod.get("coverage_by_class", {})
            }
            
            # Aggiungi concetti reali frequenti
            if include_concepts and mod.get("concepts_by_class"):
                frequent = self._extract_frequent_concepts(
                    mod["concepts_by_class"], 
                    top_concepts
                )
                modulo["validazione"]["concetti_reali_frequenti"] = frequent
            
            # Nota interpretativa
            avg_cov = mod.get("avg_coverage", 0)
            if avg_cov >= 90:
                modulo["validazione"]["nota"] = "Argomento fondamentale, presente in tutti i programmi"
            elif avg_cov >= 70:
                modulo["validazione"]["nota"] = "Argomento importante, ampiamente trattato"
            elif avg_cov >= 50:
                modulo["validazione"]["nota"] = "Copertura variabile tra le classi"
            else:
                modulo["validazione"]["nota"] = "Argomento specialistico o marginale in alcuni corsi"
            
            moduli.append(modulo)
        
        return moduli
    
    def _extract_frequent_concepts(
        self, 
        concepts_by_class: Dict, 
        top_n: int
    ) -> List[str]:
        """Estrae i concetti più frequenti tra tutte le classi."""
        
        concept_count = {}
        for cls, concepts in concepts_by_class.items():
            for concept in concepts:
                concept_count[concept] = concept_count.get(concept, 0) + 1
        
        # Ordina per frequenza
        sorted_concepts = sorted(
            concept_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [c[0] for c in sorted_concepts[:top_n]]
    
    def _generate_default_criteri(self, moduli: List[Dict]) -> List[Dict]:
        """Genera criteri di valutazione di default basati sui moduli."""
        
        criteri = []
        for i, mod in enumerate(moduli, 1):
            criterio = {
                "id": i,
                "nome": mod["nome"],
                "descrizione": f"Copertura del modulo {mod['nome']}",
                "scala": "5=Completo;3=Parziale;1=Assente",
                "pesi": {
                    "Bio": 10,
                    "Chim": 10,
                    "Farm": 10,
                    "Fis": 10,
                    "Amb": 10
                }
            }
            
            # Aggiusta pesi in base alla copertura reale
            if mod.get("validazione", {}).get("is_core"):
                for k in criterio["pesi"]:
                    criterio["pesi"][k] = 12
            
            criteri.append(criterio)
        
        return criteri
    
    def save(
        self, 
        output: Dict, 
        filename: str = None,
        output_dir: Path = None
    ) -> Path:
        """Salva il framework esportato."""
        
        if not filename:
            filename = f"{self.materia.replace(' ', '_')}_uniscan_validated.json"
        
        if not output_dir:
            output_dir = self.export_dir
        
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Framework esportato: {output_path}")
        return output_path
    
    def export_and_save(
        self,
        corex_path: Path = None,
        template_path: Path = None,
        output_filename: str = None
    ) -> tuple:
        """Esporta e salva in un unico passaggio."""
        
        corex = self.load_corex_framework(corex_path) if corex_path else None
        template = self.load_uniscan_template(template_path) if template_path else None
        
        output = self.export(corex, template)
        
        if "error" in output:
            return None, output
        
        path = self.save(output, output_filename)
        return path, output


# =============================================================================
# FUNZIONI HELPER
# =============================================================================

def export_framework_for_uniscan(
    materia: str,
    corex_path: Path = None,
    template_path: Path = None,
    output_path: Path = None
) -> Dict:
    """
    Funzione helper per esportare un framework.
    
    Args:
        materia: Nome della materia
        corex_path: Path al framework CoreX (opzionale)
        template_path: Path al template UNI-SCAN (opzionale)
        output_path: Path di output (opzionale)
    
    Returns:
        Dict con il framework nel formato UNI-SCAN
    """
    exporter = FrameworkExporter(materia)
    path, output = exporter.export_and_save(corex_path, template_path)
    return output


def batch_export(materie: List[str], output_dir: Path = None) -> Dict[str, Path]:
    """
    Esporta più framework in batch.
    
    Returns:
        Dict {materia: path_output}
    """
    results = {}
    for materia in materie:
        try:
            exporter = FrameworkExporter(materia)
            path, _ = exporter.export_and_save()
            results[materia] = path
        except Exception as e:
            print(f"[ERROR] {materia}: {e}")
            results[materia] = None
    
    return results


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    # Test export
    exporter = FrameworkExporter("Chimica_Generale")
    output = exporter.export()
    
    if "error" not in output:
        print(f"Materia: {output['materia']}")
        print(f"Versione: {output['versione']}")
        print(f"Validazione: {output['validazione']['n_programmi']} programmi, {output['validazione']['n_classi']} classi")
        print(f"Moduli: {len(output['moduli'])}")
        print(f"Indirizzi: {len(output['indirizzi'])}")
        
        # Salva
        path = exporter.save(output)
        print(f"Salvato in: {path}")
    else:
        print(f"Errore: {output['error']}")