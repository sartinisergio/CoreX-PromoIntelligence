"""
CoreX - Promo LLM Analyzer v2.1
Analisi commerciale REALE con LLM per report promotore
QUESTA VERSIONE LEGGE DAVVERO GLI INDICI DEI MANUALI
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import openai


@dataclass
class ModuleCoverage:
    """Copertura di un singolo modulo"""
    nome: str
    copertura_percentuale: int
    rilevanza: str
    argomenti_coperti: List[str] = field(default_factory=list)
    argomenti_mancanti: List[str] = field(default_factory=list)
    argomenti_extra: List[str] = field(default_factory=list)
    note: str = ""


@dataclass
class GapItem:
    """Singolo gap identificato"""
    tipo: str
    priorita: str
    titolo: str
    descrizione: str
    modulo: str
    evidenza: str
    impatto_commerciale: str


@dataclass
class ManualAnalysis:
    """Analisi di un singolo manuale"""
    titolo: str
    autore: str
    editore: str
    n_capitoli: int = 0
    allineamento_score: float = 0
    punti_forza: List[str] = field(default_factory=list)
    punti_deboli: List[str] = field(default_factory=list)
    copertura_moduli: List[ModuleCoverage] = field(default_factory=list)
    note_comparative: str = ""
    indice_caricato: bool = False


@dataclass
class PromoAnalysisResult:
    """Risultato completo dell'analisi commerciale"""
    materia: str
    universita: str
    docente: str
    data_analisi: str
    
    profilo_docente: Dict
    insight_principale: str
    filosofia_didattica: str
    
    copertura_ideale: Dict
    copertura_reale: Optional[Dict]
    moduli_analisi: List[ModuleCoverage]
    
    manuale_competitor: Optional[ManualAnalysis]
    posizione_zanichelli: str
    
    manuale_zanichelli: ManualAnalysis
    
    gap_analysis: List[GapItem]
    punti_forza_vs_competitor: List[Dict]
    
    postit: Dict
    argomenti_vendita: List[str]
    domande_discovery: List[str]
    strategia: Dict
    email: Dict
    
    punteggio_opportunita: int


class PromoLLMAnalyzer:
    """
    Analizzatore LLM per report commerciali promotore.
    LEGGE DAVVERO gli indici dei manuali e li passa all'LLM.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY non configurata")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = model
        
        print(f"[OK] PromoLLMAnalyzer inizializzato con modello: {self.model}")
        
        self.base_dir = Path(__file__).parent.parent
        self.frameworks_dir = self.base_dir / "frameworks"
        self.manuali_dir = self.base_dir / "data" / "manuali"
    
    # =========================================================
    # METODO PRINCIPALE
    # =========================================================
    
    def analizza_completo(
        self,
        testo_programma: str,
        materia: str,
        manuali_adottati: List[Dict],  # Contiene 'path' per ogni manuale!
        manuale_zanichelli_path: Optional[Path] = None,
        framework_ideale: Optional[Dict] = None,
        framework_reale: Optional[Dict] = None
    ) -> PromoAnalysisResult:
        """
        Esegue l'analisi completa multi-step.
        
        Args:
            testo_programma: Testo estratto dal PDF del programma
            materia: Nome della materia
            manuali_adottati: Lista manuali con PATH [{titolo, autore, editore, path, tipo}]
            manuale_zanichelli_path: Path al JSON dell'indice Zanichelli (se specificato)
            framework_ideale: Framework ideale (da frameworks/)
            framework_reale: Framework reale (da archivio analisi)
        """
        print(f"\n{'='*60}")
        print(f"[LLM] Inizio analisi multi-step per {materia}")
        print(f"{'='*60}")
        
        # STEP A: Estrazione strutturata programma
        print("\n[STEP A] Estrazione strutturata programma...")
        programma_strutturato = self._step_a_estrai_programma(testo_programma)
        
        # STEP B: Profilo pedagogico
        print("\n[STEP B] Analisi profilo pedagogico...")
        profilo = self._step_b_profilo_pedagogico(testo_programma, programma_strutturato)
        
        # STEP C: Mapping vs Framework Ideale
        print("\n[STEP C] Mapping vs Framework Ideale...")
        copertura_ideale = None
        if framework_ideale:
            copertura_ideale = self._step_c_mapping_ideale(programma_strutturato, framework_ideale)
        else:
            print("[WARN] Nessun framework ideale fornito")
        
        # STEP D: Mapping vs Framework Reale
        print("\n[STEP D] Mapping vs Framework Reale...")
        copertura_reale = None
        if framework_reale:
            copertura_reale = self._step_d_mapping_reale(programma_strutturato, framework_reale)
        else:
            print("[INFO] Nessun framework reale fornito")
        
        # STEP E: Carica e analizza TUTTI i manuali (competitor e Zanichelli presenti)
        print("\n[STEP E] Caricamento indici manuali adottati...")
        manuali_con_indice = self._carica_indici_manuali_adottati(manuali_adottati)
        
        # Identifica competitor principale (primo non-Zanichelli)
        competitor_analizzato = None
        zanichelli_gia_adottato = None
        
        for m in manuali_con_indice:
            if m["tipo"] == "competitor" and competitor_analizzato is None:
                competitor_analizzato = m
                print(f"[OK] Competitor principale: {m['titolo']} ({m['n_capitoli']} capitoli)")
            elif m["tipo"] == "zanichelli" and zanichelli_gia_adottato is None:
                zanichelli_gia_adottato = m
                print(f"[OK] Zanichelli già adottato: {m['titolo']}")
        
        # STEP F: Seleziona manuale Zanichelli da proporre
        print("\n[STEP F] Selezione manuale Zanichelli da proporre...")
        zanichelli_proposto = self._seleziona_zanichelli_appropriato(
            materia=materia,
            competitor=competitor_analizzato,
            manuale_specificato_path=manuale_zanichelli_path,
            zanichelli_gia_adottato=zanichelli_gia_adottato
        )
        
        # STEP G: Analisi comparativa con LLM
        print("\n[STEP G] Analisi comparativa LLM...")
        analisi_comparativa = self._step_g_analisi_comparativa_llm(
            programma=programma_strutturato,
            profilo=profilo,
            competitor=competitor_analizzato,
            zanichelli=zanichelli_proposto,
            copertura_ideale=copertura_ideale,
            copertura_reale=copertura_reale
        )
        
        # STEP H: Gap Analysis e Strategia
        print("\n[STEP H] Gap Analysis e Strategia commerciale...")
        gap_strategia = self._step_h_gap_strategia(
            programma=programma_strutturato,
            profilo=profilo,
            competitor=competitor_analizzato,
            zanichelli=zanichelli_proposto,
            analisi_comparativa=analisi_comparativa,
            copertura_ideale=copertura_ideale
        )
        
        # Assembla risultato finale
        result = self._assembla_risultato(
            materia=materia,
            programma=programma_strutturato,
            profilo=profilo,
            copertura_ideale=copertura_ideale,
            copertura_reale=copertura_reale,
            competitor=competitor_analizzato,
            zanichelli=zanichelli_proposto,
            analisi_comparativa=analisi_comparativa,
            gap_strategia=gap_strategia,
            zanichelli_gia_adottato=zanichelli_gia_adottato
        )
        
        print(f"\n{'='*60}")
        print(f"[OK] Analisi completata - Punteggio: {result.punteggio_opportunita}/100")
        print(f"{'='*60}\n")
        
        return result
    
    # =========================================================
    # STEP A: ESTRAZIONE STRUTTURATA PROGRAMMA
    # =========================================================
    
    def _step_a_estrai_programma(self, testo: str) -> Dict:
        """Estrae struttura del programma con LLM"""
        
        prompt = f"""Analizza questo programma d'esame universitario e estrai la struttura.

PROGRAMMA:
{testo[:8000]}

Rispondi SOLO con JSON valido:
{{
    "metadati": {{
        "docente": "nome cognome",
        "corso": "nome corso",
        "universita": "nome università",
        "cfu": 6,
        "ore": 48,
        "anno_accademico": "2024/2025",
        "classe_laurea": "L-XX",
        "corso_laurea": "nome corso di laurea"
    }},
    "obiettivi_formativi": ["lista obiettivi dichiarati"],
    "prerequisiti": ["lista prerequisiti"],
    "contenuti": [
        {{
            "titolo": "titolo argomento/modulo",
            "descrizione": "breve descrizione",
            "ore_stimate": 4,
            "livello": "base|intermedio|avanzato"
        }}
    ],
    "metodologie_didattiche": ["lezione frontale", "laboratorio", ...],
    "modalita_esame": ["scritto", "orale", ...],
    "bibliografia": [
        {{
            "titolo": "titolo libro",
            "autore": "autore",
            "editore": "editore",
            "ruolo": "principale|alternativo|consultazione"
        }}
    ],
    "note_particolari": "eventuali elementi distintivi del programma"
}}"""
        
        return self._call_llm_json(prompt)
    
    # =========================================================
    # STEP B: PROFILO PEDAGOGICO
    # =========================================================
    
    def _step_b_profilo_pedagogico(self, testo: str, programma: Dict) -> Dict:
        """Analizza il profilo pedagogico del docente"""
        
        contenuti_summary = json.dumps(programma.get("contenuti", [])[:10], ensure_ascii=False)
        
        prompt = f"""Analizza il profilo pedagogico di questo docente basandoti sul programma.

METADATI:
{json.dumps(programma.get('metadati', {}), ensure_ascii=False)}

OBIETTIVI:
{json.dumps(programma.get('obiettivi_formativi', []), ensure_ascii=False)}

CONTENUTI:
{contenuti_summary}

METODOLOGIE:
{json.dumps(programma.get('metodologie_didattiche', []), ensure_ascii=False)}

MODALITA ESAME:
{json.dumps(programma.get('modalita_esame', []), ensure_ascii=False)}

Rispondi SOLO con JSON:
{{
    "approccio_principale": "Teorico|Pratico|Bilanciato",
    "bilanciamento_teoria_pratica": 50,
    "livello_rigore": "Alto|Medio|Accessibile",
    "accessibilita": "Alta|Media|Bassa",
    "enfasi_applicazioni": "Alta|Media|Bassa",
    "interdisciplinarita": "Alta|Media|Bassa",
    "scuola_pensiero": "descrizione o 'Non applicabile'",
    "insight_principale": "2-3 frasi con l'insight principale per il promotore",
    "filosofia_didattica": "descrizione della filosofia didattica in 2-3 frasi",
    "argomenti_chiave": ["lista 3-5 argomenti su cui il docente punta di più"],
    "punti_forza_programma": ["lista punti di forza"],
    "aree_potenzialmente_deboli": ["aree che potrebbero essere migliorate"],
    "approccio_consigliato_promotore": "come dovrebbe presentarsi il promotore"
}}"""
        
        return self._call_llm_json(prompt)
    
    # =========================================================
    # STEP C: MAPPING VS FRAMEWORK IDEALE
    # =========================================================
    
    def _step_c_mapping_ideale(self, programma: Dict, framework: Dict) -> Dict:
        """Mappa il programma sul framework ideale"""
        
        moduli_fw = framework.get("syllabus_modules", [])
        contenuti_prog = programma.get("contenuti", [])
        
        moduli_list = []
        for m in moduli_fw[:15]:
            moduli_list.append({
                "nome": m.get("name", ""),
                "contenuti_core": m.get("core_contents", [])[:5]
            })
        
        prompt = f"""Confronta il programma del docente con il framework ideale della disciplina.
Per ogni modulo del framework, indica quanto è coperto dal programma.

CONTENUTI DEL PROGRAMMA DOCENTE:
{json.dumps(contenuti_prog, ensure_ascii=False, indent=2)}

MODULI DEL FRAMEWORK IDEALE:
{json.dumps(moduli_list, ensure_ascii=False, indent=2)}

Rispondi SOLO con JSON:
{{
    "percentuale_globale": 75,
    "sintesi": "breve sintesi della copertura",
    "moduli": [
        {{
            "nome": "nome modulo",
            "copertura": 80,
            "rilevanza": "alto|medio|basso",
            "argomenti_coperti": ["lista argomenti del modulo presenti nel programma"],
            "argomenti_mancanti": ["lista argomenti del modulo NON presenti"],
            "argomenti_extra": ["argomenti del programma che vanno oltre il framework"],
            "note": "eventuali note"
        }}
    ],
    "punti_forza": ["dove il programma eccelle"],
    "aree_approfondire": ["dove il programma è carente"]
}}"""
        
        return self._call_llm_json(prompt)
    
    # =========================================================
    # STEP D: MAPPING VS FRAMEWORK REALE
    # =========================================================
    
    def _step_d_mapping_reale(self, programma: Dict, framework: Dict) -> Dict:
        """Mappa il programma sul framework reale"""
        
        moduli_fw = framework.get("syllabus_modules", [])
        contenuti_prog = programma.get("contenuti", [])
        
        moduli_list = []
        for m in moduli_fw[:15]:
            moduli_list.append({
                "nome": m.get("name", ""),
                "contenuti_core": m.get("core_contents", [])[:5],
                "copertura_media_classi": m.get("coverage_percentage", 50)
            })
        
        prompt = f"""Confronta il programma con il framework reale (ciò che si insegna effettivamente).

CONTENUTI DEL PROGRAMMA:
{json.dumps(contenuti_prog, ensure_ascii=False, indent=2)}

FRAMEWORK REALE (con copertura media):
{json.dumps(moduli_list, ensure_ascii=False, indent=2)}

Rispondi SOLO con JSON:
{{
    "percentuale_globale": 77,
    "allineamento_medio": "sopra|nella media|sotto",
    "sintesi": "come si posiziona questo programma rispetto agli altri",
    "moduli": [
        {{
            "nome": "nome modulo",
            "copertura": 85,
            "rispetto_media": "sopra|nella media|sotto",
            "rilevanza": "alto|medio|basso",
            "argomenti_coperti": ["lista"],
            "argomenti_mancanti": ["lista"],
            "note": "note"
        }}
    ],
    "differenze_significative": ["dove questo programma si discosta dalla media"],
    "punti_forza": ["dove eccelle rispetto alla media"],
    "aree_sotto_media": ["dove è sotto la media"]
}}"""
        
        return self._call_llm_json(prompt)
    
    # =========================================================
    # CARICAMENTO INDICI MANUALI - IL CUORE DEL SISTEMA
    # =========================================================
    
    def _carica_indici_manuali_adottati(self, manuali_adottati: List[Dict]) -> List[Dict]:
        """
        Carica gli indici JSON dei manuali adottati.
        Usa il PATH fornito dalla UI.
        """
        manuali_con_indice = []
        
        for manuale in manuali_adottati:
            path_str = manuale.get("path")
            
            risultato = {
                "titolo": manuale.get("titolo", ""),
                "autore": manuale.get("autore", ""),
                "editore": manuale.get("editore", ""),
                "tipo": manuale.get("tipo", "competitor"),
                "path": path_str,
                "indice": None,
                "n_capitoli": 0,
                "capitoli_summary": []
            }
            
            if path_str:
                path = Path(path_str)
                if path.exists():
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            indice = json.load(f)
                        
                        risultato["indice"] = indice
                        capitoli = indice.get("chapters", [])
                        risultato["n_capitoli"] = len(capitoli)
                        
                        # Crea summary dei capitoli per l'LLM
                        risultato["capitoli_summary"] = [
                            {
                                "numero": c.get("number", i+1),
                                "titolo": c.get("title", ""),
                                "sezioni": len(c.get("sections", []))
                            }
                            for i, c in enumerate(capitoli)
                        ]
                        
                        print(f"[OK] Caricato indice: {risultato['titolo']} - {risultato['n_capitoli']} capitoli")
                        
                    except Exception as e:
                        print(f"[ERR] Errore caricamento {path}: {e}")
                else:
                    print(f"[WARN] File non trovato: {path}")
            else:
                print(f"[WARN] Nessun path per: {risultato['titolo']}")
            
            manuali_con_indice.append(risultato)
        
        return manuali_con_indice
    
    # =========================================================
    # SELEZIONE ZANICHELLI APPROPRIATO - LOGICA INTELLIGENTE
    # =========================================================
    
    def _seleziona_zanichelli_appropriato(
        self,
        materia: str,
        competitor: Optional[Dict],
        manuale_specificato_path: Optional[Path],
        zanichelli_gia_adottato: Optional[Dict]
    ) -> Dict:
        """
        Seleziona il manuale Zanichelli più appropriato.
        
        Logica:
        1. Se l'utente ha specificato un manuale, usa quello
        2. Se Zanichelli è già adottato, proponi upselling (manuale più completo)
        3. Altrimenti, scegli in base al LIVELLO del competitor (numero capitoli)
        """
        
        # Caso 1: Manuale specificato dall'utente
        if manuale_specificato_path and manuale_specificato_path.exists():
            print(f"[INFO] Uso manuale Zanichelli specificato: {manuale_specificato_path.name}")
            return self._carica_singolo_manuale_zanichelli(manuale_specificato_path)
        
        # Carica tutti i manuali Zanichelli disponibili per la materia
        zanichelli_disponibili = self._carica_tutti_zanichelli(materia)
        
        if not zanichelli_disponibili:
            print("[WARN] Nessun manuale Zanichelli trovato per questa materia")
            return {
                "titolo": "Nessun manuale disponibile",
                "autore": "",
                "editore": "Zanichelli",
                "n_capitoli": 0,
                "indice": None,
                "capitoli_summary": []
            }
        
        # Ordina per numero di capitoli (dal più completo al meno)
        zanichelli_disponibili.sort(key=lambda x: x["n_capitoli"], reverse=True)
        
        # Log manuali disponibili
        print(f"[INFO] Manuali Zanichelli disponibili ({len(zanichelli_disponibili)}):")
        for z in zanichelli_disponibili:
            print(f"       - {z['titolo']}: {z['n_capitoli']} capitoli")
        
        # Caso 2: Zanichelli già adottato - proponi upgrade
        if zanichelli_gia_adottato:
            n_cap_attuale = zanichelli_gia_adottato.get("n_capitoli", 0)
            for z in zanichelli_disponibili:
                if z["n_capitoli"] > n_cap_attuale:
                    print(f"[OK] Proposta upselling: {z['titolo']} ({z['n_capitoli']} cap) vs attuale ({n_cap_attuale} cap)")
                    return z
            # Se non c'è upgrade, mantieni l'attuale
            print("[INFO] Nessun upgrade disponibile, mantengo attuale")
            return zanichelli_gia_adottato
        
        # Caso 3: Scegli in base al livello del competitor
        if competitor and competitor.get("n_capitoli", 0) > 0:
            n_cap_competitor = competitor["n_capitoli"]
            print(f"[INFO] Competitor ha {n_cap_competitor} capitoli")
            
            # Trova il Zanichelli con numero capitoli più simile (ma >= competitor)
            migliore = None
            for z in zanichelli_disponibili:
                if z["n_capitoli"] >= n_cap_competitor * 0.8:  # Almeno 80% dei capitoli
                    if migliore is None or z["n_capitoli"] < migliore["n_capitoli"]:
                        # Preferisci il più piccolo che sia comunque adeguato
                        migliore = z
            
            if migliore:
                print(f"[OK] Selezionato: {migliore['titolo']} ({migliore['n_capitoli']} cap) per competere con {competitor['titolo']} ({n_cap_competitor} cap)")
                return migliore
            else:
                # Se nessuno è adeguato, prendi il più completo
                print(f"[OK] Selezionato il più completo: {zanichelli_disponibili[0]['titolo']}")
                return zanichelli_disponibili[0]
        
        # Fallback: prendi il più completo
        print(f"[OK] Fallback - selezionato: {zanichelli_disponibili[0]['titolo']}")
        return zanichelli_disponibili[0]
    
    def _carica_singolo_manuale_zanichelli(self, path: Path) -> Dict:
        """Carica un singolo manuale Zanichelli da path"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                indice = json.load(f)
            
            capitoli = indice.get("chapters", [])
            
            return {
                "titolo": indice.get("title", path.stem),
                "autore": indice.get("author", ""),
                "editore": "Zanichelli",
                "n_capitoli": len(capitoli),
                "indice": indice,
                "capitoli_summary": [
                    {
                        "numero": c.get("number", i+1),
                        "titolo": c.get("title", ""),
                        "sezioni": len(c.get("sections", []))
                    }
                    for i, c in enumerate(capitoli)
                ],
                "path": str(path)
            }
        except Exception as e:
            print(f"[ERR] Errore caricamento {path}: {e}")
            return {
                "titolo": path.stem,
                "autore": "",
                "editore": "Zanichelli",
                "n_capitoli": 0,
                "indice": None,
                "capitoli_summary": []
            }
    
    def _carica_tutti_zanichelli(self, materia: str) -> List[Dict]:
        """Carica tutti i manuali Zanichelli per una materia"""
        
        materia_safe = materia.replace(" ", "_")
        search_paths = [
            self.manuali_dir / materia_safe / "indici" / "Manuali_Zanichelli",
            self.manuali_dir / materia_safe / "indici" / "manuali_zanichelli",
            self.manuali_dir / materia_safe / "indici" / "manuali Zanichelli",
        ]
        
        search_dir = None
        for p in search_paths:
            if p.exists():
                search_dir = p
                break
        
        if not search_dir:
            print(f"[WARN] Cartella Zanichelli non trovata per {materia}")
            return []
        
        manuali = []
        for json_file in search_dir.glob("*.json"):
            manuale = self._carica_singolo_manuale_zanichelli(json_file)
            if manuale["n_capitoli"] > 0:
                manuali.append(manuale)
        
        return manuali
    
    # =========================================================
    # STEP G: ANALISI COMPARATIVA CON LLM
    # =========================================================
    
    def _step_g_analisi_comparativa_llm(
        self,
        programma: Dict,
        profilo: Dict,
        competitor: Optional[Dict],
        zanichelli: Dict,
        copertura_ideale: Optional[Dict],
        copertura_reale: Optional[Dict]
    ) -> Dict:
        """
        Analisi comparativa REALE tra competitor e Zanichelli.
        Passa gli indici effettivi all'LLM.
        """
        
        contenuti_prog = programma.get("contenuti", [])
        
        # Prepara dati competitor
        competitor_info = "Nessun competitor identificato"
        competitor_capitoli = []
        if competitor and competitor.get("indice"):
            competitor_info = f"{competitor['titolo']} di {competitor['autore']} ({competitor['editore']}) - {competitor['n_capitoli']} capitoli"
            competitor_capitoli = competitor.get("capitoli_summary", [])[:25]
        
        # Prepara dati Zanichelli
        zanichelli_info = f"{zanichelli['titolo']} di {zanichelli['autore']} - {zanichelli['n_capitoli']} capitoli"
        zanichelli_capitoli = zanichelli.get("capitoli_summary", [])[:25]
        
        prompt = f"""Sei un esperto analista editoriale. Confronta questi due manuali rispetto al programma del docente.

PROGRAMMA DEL DOCENTE (contenuti richiesti):
{json.dumps(contenuti_prog[:15], ensure_ascii=False, indent=2)}

MANUALE ATTUALMENTE ADOTTATO (COMPETITOR):
{competitor_info}
Capitoli:
{json.dumps(competitor_capitoli, ensure_ascii=False, indent=2)}

MANUALE ZANICHELLI DA PROPORRE:
{zanichelli_info}
Capitoli:
{json.dumps(zanichelli_capitoli, ensure_ascii=False, indent=2)}

Analizza REALMENTE gli indici e rispondi con JSON:
{{
    "competitor_analisi": {{
        "copertura_programma": 85,
        "punti_forza": ["lista punti di forza REALI del competitor basati sull'indice"],
        "punti_deboli": ["lista punti deboli REALI del competitor"],
        "capitoli_rilevanti": ["lista capitoli del competitor che coprono il programma"],
        "argomenti_mancanti": ["argomenti del programma NON coperti dal competitor"]
    }},
    "zanichelli_analisi": {{
        "copertura_programma": 88,
        "punti_forza": ["lista punti di forza REALI del Zanichelli basati sull'indice"],
        "punti_deboli": ["eventuali limiti del Zanichelli"],
        "capitoli_rilevanti": ["lista capitoli Zanichelli che coprono il programma"],
        "vantaggi_vs_competitor": ["vantaggi SPECIFICI e VERIFICABILI rispetto al competitor"]
    }},
    "confronto_diretto": {{
        "vincitore_copertura": "zanichelli|competitor|pari",
        "vincitore_livello": "zanichelli|competitor|pari",
        "aree_zanichelli_superiore": ["aree dove Zanichelli è oggettivamente migliore"],
        "aree_competitor_superiore": ["aree dove il competitor è oggettivamente migliore"],
        "raccomandazione": "sintesi della raccomandazione per il promotore"
    }}
}}

IMPORTANTE: Basa l'analisi SOLO sugli indici forniti, non inventare contenuti."""
        
        return self._call_llm_json(prompt)
    
    # =========================================================
    # STEP H: GAP ANALYSIS E STRATEGIA
    # =========================================================
    
    def _step_h_gap_strategia(
        self,
        programma: Dict,
        profilo: Dict,
        competitor: Optional[Dict],
        zanichelli: Dict,
        analisi_comparativa: Dict,
        copertura_ideale: Optional[Dict]
    ) -> Dict:
        """Genera gap analysis e strategia commerciale basata sull'analisi reale"""
        
        metadati = programma.get("metadati", {})
        
        # Costruisci contesto con dati REALI
        context = {
            "docente": metadati.get("docente", ""),
            "corso": metadati.get("corso", ""),
            "universita": metadati.get("universita", ""),
            "approccio_docente": profilo.get("approccio_principale", "Bilanciato"),
            "insight_docente": profilo.get("insight_principale", ""),
            
            "competitor_titolo": competitor.get("titolo", "") if competitor else "Nessuno",
            "competitor_editore": competitor.get("editore", "") if competitor else "",
            "competitor_capitoli": competitor.get("n_capitoli", 0) if competitor else 0,
            "competitor_punti_deboli": analisi_comparativa.get("competitor_analisi", {}).get("punti_deboli", []),
            "competitor_argomenti_mancanti": analisi_comparativa.get("competitor_analisi", {}).get("argomenti_mancanti", []),
            
            "zanichelli_titolo": zanichelli.get("titolo", ""),
            "zanichelli_autore": zanichelli.get("autore", ""),
            "zanichelli_capitoli": zanichelli.get("n_capitoli", 0),
            "zanichelli_vantaggi": analisi_comparativa.get("zanichelli_analisi", {}).get("vantaggi_vs_competitor", []),
            "zanichelli_punti_forza": analisi_comparativa.get("zanichelli_analisi", {}).get("punti_forza", []),
            
            "aree_zanichelli_superiore": analisi_comparativa.get("confronto_diretto", {}).get("aree_zanichelli_superiore", []),
            "raccomandazione_analisi": analisi_comparativa.get("confronto_diretto", {}).get("raccomandazione", ""),
            
            "aree_carenti_programma": copertura_ideale.get("aree_approfondire", []) if copertura_ideale else []
        }
        
        prompt = f"""Genera la strategia commerciale per il promotore Zanichelli basandoti su questa analisi REALE.

CONTESTO VERIFICATO:
{json.dumps(context, ensure_ascii=False, indent=2)}

Rispondi SOLO con JSON:
{{
    "gap_analysis": [
        {{
            "tipo": "Contenuto Mancante|Risorse Carenti|Profondità Insufficiente",
            "priorita": "alta|media|bassa",
            "titolo": "titolo del gap (DEVE essere basato sui dati reali)",
            "descrizione": "descrizione dettagliata basata sull'analisi degli indici",
            "modulo": "modulo di riferimento",
            "evidenza": "evidenza CONCRETA dall'analisi (es. 'Il competitor non ha capitoli su X, mentre Zanichelli ha il Cap. Y')",
            "impatto_commerciale": "come sfruttare questo gap"
        }}
    ],
    "punti_forza_vs_competitor": [
        {{
            "area": "nome area",
            "vantaggio_zanichelli": "descrizione CONCRETA del vantaggio",
            "capitolo_zanichelli": "riferimento al capitolo Zanichelli",
            "rilevanza_programma": "perché è rilevante per questo docente"
        }}
    ],
    "postit": {{
        "docente_sintesi": "sintesi del docente in 1 riga",
        "usa_attualmente": "titolo manuale attuale (editore)",
        "obiettivo": "obiettivo specifico del promotore",
        "leva_principale": "la leva principale CONCRETA basata sull'analisi",
        "argomentazione": "argomentazione in 2-3 righe basata su fatti verificabili"
    }},
    "argomenti_vendita": [
        "5 argomenti di vendita CONCRETI basati sull'analisi degli indici"
    ],
    "domande_discovery": [
        "3-4 domande per il docente"
    ],
    "strategia": {{
        "fase1": {{
            "nome": "Apertura",
            "descrizione": "cosa fare",
            "obiettivo": "obiettivo fase"
        }},
        "fase2": {{
            "nome": "Discovery",
            "descrizione": "cosa fare",
            "obiettivo": "obiettivo fase"
        }},
        "fase3": {{
            "nome": "Proposta",
            "descrizione": "cosa fare",
            "obiettivo": "obiettivo fase"
        }}
    }},
    "email": {{
        "oggetto": "oggetto email",
        "corpo": "testo email completo e professionale che cita vantaggi SPECIFICI"
    }},
    "punteggio_opportunita": 75
}}

IMPORTANTE: 
- Ogni affermazione DEVE essere basata sui dati forniti
- Non inventare vantaggi non supportati dall'analisi
- Se il competitor è superiore in alcune aree, ammettilo"""
        
        return self._call_llm_json(prompt)
    
    # =========================================================
    # UTILITY: CHIAMATA LLM
    # =========================================================
    
    def _call_llm_json(self, prompt: str, max_retries: int = 2) -> Dict:
        """Chiama LLM e parsea risposta JSON"""
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system", 
                            "content": "Sei un esperto analista editoriale. Rispondi SEMPRE e SOLO con JSON valido, senza markdown, senza ```."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=4000
                )
                
                text = response.choices[0].message.content.strip()
                
                # Pulisci markdown se presente
                if text.startswith("```"):
                    lines = text.split("\n")
                    text = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
                
                return json.loads(text)
                
            except json.JSONDecodeError as e:
                print(f"[WARN] JSON decode error (attempt {attempt+1}): {e}")
                if attempt == max_retries:
                    print(f"[ERR] Risposta non parsabile: {text[:500]}")
                    return {}
            except Exception as e:
                print(f"[ERR] LLM call failed: {e}")
                return {}
        
        return {}
    
    # =========================================================
    # ASSEMBLA RISULTATO FINALE
    # =========================================================
    
    def _assembla_risultato(self, **kwargs) -> PromoAnalysisResult:
        """Assembla il risultato finale"""
        
        materia = kwargs.get("materia", "")
        programma = kwargs.get("programma", {})
        profilo = kwargs.get("profilo", {})
        copertura_ideale = kwargs.get("copertura_ideale")
        copertura_reale = kwargs.get("copertura_reale")
        competitor = kwargs.get("competitor")
        zanichelli = kwargs.get("zanichelli", {})
        analisi_comparativa = kwargs.get("analisi_comparativa", {})
        gap_strategia = kwargs.get("gap_strategia", {})
        zanichelli_gia_adottato = kwargs.get("zanichelli_gia_adottato")
        
        metadati = programma.get("metadati", {})
        
        # Determina posizione Zanichelli
        if zanichelli_gia_adottato:
            posizione = "presente"
        elif competitor:
            posizione = "assente"
        else:
            posizione = "da_valutare"
        
        # Costruisci moduli analisi da copertura ideale
        moduli_analisi = []
        if copertura_ideale:
            for m in copertura_ideale.get("moduli", []):
                moduli_analisi.append(ModuleCoverage(
                    nome=m.get("nome", ""),
                    copertura_percentuale=m.get("copertura", 0),
                    rilevanza=m.get("rilevanza", "medio"),
                    argomenti_coperti=m.get("argomenti_coperti", []),
                    argomenti_mancanti=m.get("argomenti_mancanti", []),
                    argomenti_extra=m.get("argomenti_extra", []),
                    note=m.get("note", "")
                ))
        
        # Costruisci gap items
        gap_items = []
        for g in gap_strategia.get("gap_analysis", []):
            gap_items.append(GapItem(
                tipo=g.get("tipo", ""),
                priorita=g.get("priorita", "media"),
                titolo=g.get("titolo", ""),
                descrizione=g.get("descrizione", ""),
                modulo=g.get("modulo", ""),
                evidenza=g.get("evidenza", ""),
                impatto_commerciale=g.get("impatto_commerciale", "")
            ))
        
        # Costruisci ManualAnalysis per competitor
        competitor_analysis = None
        if competitor:
            comp_data = analisi_comparativa.get("competitor_analisi", {})
            competitor_analysis = ManualAnalysis(
                titolo=competitor.get("titolo", ""),
                autore=competitor.get("autore", ""),
                editore=competitor.get("editore", ""),
                n_capitoli=competitor.get("n_capitoli", 0),
                allineamento_score=comp_data.get("copertura_programma", 0),
                punti_forza=comp_data.get("punti_forza", []),
                punti_deboli=comp_data.get("punti_deboli", []),
                indice_caricato=competitor.get("indice") is not None
            )
        
        # Costruisci ManualAnalysis per Zanichelli
        zan_data = analisi_comparativa.get("zanichelli_analisi", {})
        zanichelli_analysis = ManualAnalysis(
            titolo=zanichelli.get("titolo", ""),
            autore=zanichelli.get("autore", ""),
            editore="Zanichelli",
            n_capitoli=zanichelli.get("n_capitoli", 0),
            allineamento_score=zan_data.get("copertura_programma", 0),
            punti_forza=zan_data.get("punti_forza", []),
            punti_deboli=zan_data.get("punti_deboli", []),
            note_comparative="; ".join(zan_data.get("vantaggi_vs_competitor", [])),
            indice_caricato=zanichelli.get("indice") is not None
        )
        
        return PromoAnalysisResult(
            materia=materia,
            universita=metadati.get("universita", ""),
            docente=metadati.get("docente", ""),
            data_analisi=datetime.now().strftime("%d/%m/%Y"),
            profilo_docente=profilo,
            insight_principale=profilo.get("insight_principale", ""),
            filosofia_didattica=profilo.get("filosofia_didattica", ""),
            copertura_ideale=copertura_ideale,
            copertura_reale=copertura_reale,
            moduli_analisi=moduli_analisi,
            manuale_competitor=competitor_analysis,
            posizione_zanichelli=posizione,
            manuale_zanichelli=zanichelli_analysis,
            gap_analysis=gap_items,
            punti_forza_vs_competitor=gap_strategia.get("punti_forza_vs_competitor", []),
            postit=gap_strategia.get("postit", {}),
            argomenti_vendita=gap_strategia.get("argomenti_vendita", []),
            domande_discovery=gap_strategia.get("domande_discovery", []),
            strategia=gap_strategia.get("strategia", {}),
            email=gap_strategia.get("email", {}),
            punteggio_opportunita=gap_strategia.get("punteggio_opportunita", 50)
        )
