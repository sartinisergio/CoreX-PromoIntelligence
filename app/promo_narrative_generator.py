"""
CoreX PromoIntelligence - Generatore Narrative LLM v1.0
Genera Executive Summary per il report di promozione.
Materia-agnostico: funziona con qualsiasi disciplina.
"""

import json
from typing import Dict, List, Any


class PromoNarrativeGenerator:
    """
    Genera Executive Summary narrativo per arricchire il report promozione.
    Una sola chiamata LLM, parametri conservativi per risultati ripetibili.
    """
    
    # Limiti per sicurezza prompt
    MAX_PUNTI_FORZA = 3
    MAX_GAP = 2
    MAX_CLASSI_TARGET = 3
    MAX_CLASSI_CRITICHE = 2
    MAX_NOME_LENGTH = 50
    
    def __init__(self, 
                 nome_manuale: str,
                 autore_manuale: str,
                 editore: str,
                 materia: str,
                 copertura_globale: float,
                 tipo_analisi: str = "zanichelli"):
        self.nome_manuale = nome_manuale
        self.autore_manuale = autore_manuale
        self.editore = editore
        self.materia = materia
        self.copertura_globale = copertura_globale
        self.tipo_analisi = tipo_analisi
    
    def generate_executive_summary(self, 
                                   punti_forza: List[Dict], 
                                   gap: List[Dict], 
                                   classificazione_classi: Dict,
                                   provider_id: str = "openai", 
                                   model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """
        Genera Executive Summary narrativo tramite LLM.
        
        Args:
            punti_forza: Lista moduli dove il manuale eccelle
            gap: Lista moduli con copertura insufficiente
            classificazione_classi: Dict con classi suddivise per categoria
            provider_id: Provider LLM da usare
            model: Modello LLM
            
        Returns:
            Dict con:
                - text: Il testo narrativo dell'executive summary
                - generated_by_llm: True se generato da LLM, False se fallback
        """
        try:
            from app.llm_provider import get_llm_client
        except ImportError:
            print("LLM provider non disponibile, uso fallback")
            return self._fallback_executive_summary(punti_forza, gap, classificazione_classi)
        
        # Prepara dati LIMITATI per il prompt
        top_punti_forza = self._prepare_punti_forza(punti_forza)
        top_gap = self._prepare_gap(gap)
        classi_target, classi_critiche = self._prepare_classi(classificazione_classi)
        
        # Costruisci prompt MATERIA-AGNOSTICO (nessun esempio specifico)
        prompt = self._build_prompt(top_punti_forza, top_gap, classi_target, classi_critiche)
        
        # Verifica lunghezza prompt
        if len(prompt) > 3000:
            print(f"Warning: prompt lungo ({len(prompt)} chars), potrebbe essere troncato")
        
        try:
            client = get_llm_client(provider_id)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Sei un consulente editoriale esperto. Genera testi professionali e oggettivi per promotori editoriali universitari. Rispondi sempre in italiano."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.15,  # Bassa per risultati ripetibili
                max_tokens=800     # Sufficiente per 6-8 frasi
            )
            
            response_text = response.choices[0].message.content.strip()
            
            return {
                "text": response_text,
                "generated_by_llm": True
            }
            
        except Exception as e:
            print(f"Errore generazione executive summary: {e}")
            return self._fallback_executive_summary(punti_forza, gap, classificazione_classi)
    
    def _prepare_punti_forza(self, punti_forza: List[Dict]) -> List[Dict]:
        """Prepara lista punti forza limitata e pulita."""
        result = []
        for p in punti_forza[:self.MAX_PUNTI_FORZA]:
            result.append({
                "modulo": p.get("name", "")[:self.MAX_NOME_LENGTH],
                "copertura": p.get("copertura", 0),
                "vs_media": p.get("differenza", 0)
            })
        return result
    
    def _prepare_gap(self, gap: List[Dict]) -> List[Dict]:
        """Prepara lista gap limitata e pulita."""
        result = []
        for g in gap[:self.MAX_GAP]:
            result.append({
                "modulo": g.get("name", "")[:self.MAX_NOME_LENGTH],
                "copertura": g.get("copertura_manuale", 0),
                "is_core": g.get("is_core", False)
            })
        return result
    
    def _prepare_classi(self, classificazione_classi: Dict) -> tuple:
        """Estrae classi target e critiche dalla classificazione."""
        classi_target = []
        classi_critiche = []
        
        if self.tipo_analisi == "zanichelli":
            # Per Zanichelli: spingere = target, attenzione = critiche
            for c in classificazione_classi.get("spingere", [])[:self.MAX_CLASSI_TARGET]:
                classi_target.append({
                    "classe": c.get("classe", "")[:self.MAX_NOME_LENGTH],
                    "fit": c.get("fit", 0)
                })
            for c in classificazione_classi.get("attenzione", [])[:self.MAX_CLASSI_CRITICHE]:
                classi_critiche.append({
                    "classe": c.get("classe", "")[:self.MAX_NOME_LENGTH],
                    "fit": c.get("fit", 0)
                })
        else:
            # Per Competitor: vulnerabile = opportunità, forte = evitare
            for c in classificazione_classi.get("vulnerabile", [])[:self.MAX_CLASSI_TARGET]:
                classi_target.append({
                    "classe": c.get("classe", "")[:self.MAX_NOME_LENGTH],
                    "fit": c.get("fit", 0)
                })
            for c in classificazione_classi.get("forte", [])[:self.MAX_CLASSI_CRITICHE]:
                classi_critiche.append({
                    "classe": c.get("classe", "")[:self.MAX_NOME_LENGTH],
                    "fit": c.get("fit", 0)
                })
        
        return classi_target, classi_critiche
    
    def _build_prompt(self, punti_forza: List, gap: List, classi_target: List, classi_critiche: List) -> str:
        """
        Costruisce il prompt per l'LLM.
        MATERIA-AGNOSTICO: nessun esempio specifico di discipline.
        """
        
        # Formatta punti forza
        if punti_forza:
            pf_text = "\n".join([
                f"- {p['modulo']}: copertura {p['copertura']:.0f}%, {p['vs_media']:+.0f}% vs media programmi"
                for p in punti_forza
            ])
        else:
            pf_text = "Nessun punto di forza significativo identificato"
        
        # Formatta gap
        if gap:
            gap_text = "\n".join([
                f"- {g['modulo']}: copertura {g['copertura']:.0f}%{' (modulo core)' if g['is_core'] else ''}"
                for g in gap
            ])
        else:
            gap_text = "Nessun gap critico identificato"
        
        # Formatta classi target
        if classi_target:
            target_text = ", ".join([f"{c['classe']} ({c['fit']:.0f}%)" for c in classi_target])
        else:
            target_text = "Da valutare caso per caso"
        
        # Formatta classi critiche
        if classi_critiche:
            critiche_text = ", ".join([f"{c['classe']} ({c['fit']:.0f}%)" for c in classi_critiche])
        else:
            critiche_text = "Nessuna criticità particolare"
        
        # Calcola giudizio sintetico
        if self.copertura_globale >= 80:
            giudizio = "eccellente"
        elif self.copertura_globale >= 65:
            giudizio = "buona"
        elif self.copertura_globale >= 50:
            giudizio = "sufficiente"
        else:
            giudizio = "parziale"
        
        prompt = f"""Genera un Executive Summary per un report di promozione editoriale universitaria.

INFORMAZIONI MANUALE:
- Titolo: "{self.nome_manuale}"
- Autore: {self.autore_manuale if self.autore_manuale else "N/D"}
- Editore: {self.editore}
- Materia: {self.materia}
- Copertura globale rispetto ai programmi universitari: {self.copertura_globale:.0f}% ({giudizio})

PUNTI DI FORZA (moduli dove il manuale supera le richieste medie):
{pf_text}

GAP CRITICI (moduli con copertura insufficiente):
{gap_text}

CLASSI DI LAUREA - TARGET OTTIMALE:
{target_text}

CLASSI DI LAUREA - CRITICITÀ:
{critiche_text}

ISTRUZIONI:
Scrivi un Executive Summary di 6-8 frasi suddiviso in 4 parti:

1. POSIZIONAMENTO (1-2 frasi): Descrivi il livello del manuale (base/intermedio/avanzato) e il suo approccio didattico, basandoti sulla copertura e sui punti di forza.

2. PUNTI DI FORZA (2 frasi): Evidenzia i moduli dove il manuale eccelle, citando i dati numerici forniti.

3. CRITICITÀ (1-2 frasi): Segnala i gap in modo oggettivo. Se i gap riguardano moduli non-core o specialistici, specificalo.

4. TARGET (1 frase): Indica le classi di laurea ideali e quelle dove prestare attenzione.

TONO: Professionale, oggettivo, utile per un promotore editoriale. Non usare elenchi puntati, scrivi in prosa fluida.

Rispondi SOLO con il testo dell'Executive Summary, senza titoli di sezione o formattazione."""

        return prompt
    
    def _fallback_executive_summary(self, punti_forza: List, gap: List, classificazione_classi: Dict) -> Dict[str, Any]:
        """
        Genera executive summary senza LLM.
        Usato come fallback in caso di errori.
        """
        # Estrai nomi
        pf_nomi = [p.get("name", "N/D") for p in punti_forza[:3]]
        gap_nomi = [g.get("name", "N/D") for g in gap[:2]]
        
        # Estrai classi target
        if self.tipo_analisi == "zanichelli":
            target = classificazione_classi.get("spingere", [])[:2]
        else:
            target = classificazione_classi.get("vulnerabile", [])[:2]
        target_nomi = [c.get("classe", "N/D") for c in target]
        
        # Costruisci testo
        parti = []
        
        # Posizionamento
        if self.copertura_globale >= 70:
            parti.append(f'"{self.nome_manuale}" presenta una copertura globale del {self.copertura_globale:.0f}% rispetto ai programmi universitari analizzati, collocandosi come testo di riferimento per la materia.')
        else:
            parti.append(f'"{self.nome_manuale}" presenta una copertura del {self.copertura_globale:.0f}% rispetto ai programmi universitari analizzati.')
        
        # Punti forza
        if pf_nomi:
            parti.append(f"I punti di forza principali sono: {', '.join(pf_nomi)}.")
        
        # Gap
        if gap_nomi:
            parti.append(f"Presenta gap su: {', '.join(gap_nomi)}.")
        else:
            parti.append("Non presenta gap critici significativi.")
        
        # Target
        if target_nomi:
            parti.append(f"Target consigliato: {', '.join(target_nomi)}.")
        
        return {
            "text": " ".join(parti),
            "generated_by_llm": False
        }


# =============================================================================
# FUNZIONE HELPER PER INTEGRAZIONE
# =============================================================================

def generate_executive_summary_for_report(
    punti_forza: List[Dict],
    gap: List[Dict],
    classificazione_classi: Dict,
    nome_manuale: str,
    autore_manuale: str,
    editore: str,
    materia: str,
    copertura_globale: float,
    tipo_analisi: str = "zanichelli",
    provider_id: str = "openai",
    model: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    """
    Funzione helper per generare l'executive summary.
    Può essere chiamata direttamente da promo_report_generator.py
    
    Returns:
        Dict con 'text' (il summary) e 'generated_by_llm' (bool)
    """
    generator = PromoNarrativeGenerator(
        nome_manuale=nome_manuale,
        autore_manuale=autore_manuale,
        editore=editore,
        materia=materia,
        copertura_globale=copertura_globale,
        tipo_analisi=tipo_analisi
    )
    
    return generator.generate_executive_summary(
        punti_forza=punti_forza,
        gap=gap,
        classificazione_classi=classificazione_classi,
        provider_id=provider_id,
        model=model
    )


# =============================================================================
# GENERATORE HTML EXECUTIVE SUMMARY
# =============================================================================

def generate_executive_summary_html(executive_summary: Dict[str, Any]) -> str:
    """
    Genera HTML per la sezione Executive Summary.
    Da inserire nel report HTML dopo l'header.
    
    Args:
        executive_summary: Dict con 'text' e 'generated_by_llm'
        
    Returns:
        Stringa HTML
    """
    if not executive_summary or not executive_summary.get("text"):
        return ""
    
    text = executive_summary.get("text", "")
    is_llm = executive_summary.get("generated_by_llm", False)
    
    badge = ""
    if not is_llm:
        badge = '<span style="font-size: 0.75em; background: #fff3e0; color: #e65100; padding: 2px 8px; border-radius: 10px; margin-left: 10px;">Generato automaticamente</span>'
    
    html = f"""
    <div class="executive-summary" style="background: linear-gradient(135deg, #e3f2fd, #ffffff); padding: 25px 30px; border-radius: 12px; margin: 25px 0; border-left: 5px solid #1976d2; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
        <h2 style="margin-top: 0; color: #1565c0; font-size: 1.3em;">
            📋 Executive Summary {badge}
        </h2>
        <p style="margin: 0; line-height: 1.8; font-size: 1.05em; color: #333; text-align: justify;">
            {text}
        </p>
    </div>
"""
    return html


# =============================================================================
# CALCOLO ALLINEAMENTI E CRITICITÀ PER CLASSE (SENZA LLM)
# =============================================================================

def calcola_dettagli_classe(
    classe_data: Dict,
    copertura_manuale: Dict,
    copertura_reale: Dict,
    soglia_allineamento: float = 80.0,
    soglia_criticita: float = 40.0
) -> Dict[str, Any]:
    """
    Calcola allineamenti e criticità per una classe specifica.
    SENZA LLM - pura logica deterministica.
    
    Args:
        classe_data: Dati della classe (fit, classe_completa, etc.)
        copertura_manuale: Dict modulo_id -> {name, coverage}
        copertura_reale: Dict modulo_id -> {coverage_by_class, ...}
        soglia_allineamento: Soglia % per considerare un modulo "allineato"
        soglia_criticita: Soglia % sotto cui il modulo è "critico"
        
    Returns:
        Dict con allineamenti e criticità dettagliate
    """
    classe_nome = classe_data.get("classe_completa", classe_data.get("classe", ""))
    
    allineamenti = []
    criticita = []
    
    for mod_id, mod_data in copertura_manuale.items():
        copertura_man = mod_data.get("coverage", 0)
        nome_modulo = mod_data.get("name", "N/D")
        
        if mod_id not in copertura_reale:
            continue
        
        copertura_classe = copertura_reale[mod_id].get("coverage_by_class", {}).get(classe_nome, 0)
        
        # Allineamento: manuale >= soglia E classe richiede >= soglia
        if copertura_man >= soglia_allineamento and copertura_classe >= soglia_allineamento:
            allineamenti.append({
                "modulo": nome_modulo,
                "copertura_manuale": copertura_man,
                "richiesta_classe": copertura_classe
            })
        
        # Criticità: manuale < soglia MA classe richiede >= 50%
        elif copertura_man < soglia_criticita and copertura_classe >= 50:
            criticita.append({
                "modulo": nome_modulo,
                "copertura_manuale": copertura_man,
                "richiesta_classe": copertura_classe,
                "gap": copertura_classe - copertura_man
            })
    
    # Ordina criticità per gap decrescente
    criticita.sort(key=lambda x: x["gap"], reverse=True)
    
    return {
        "classe": classe_data.get("classe", ""),
        "classe_completa": classe_nome,
        "fit": classe_data.get("fit", 0),
        "allineamenti": allineamenti[:5],  # Max 5
        "criticita": criticita[:3],         # Max 3
        "n_allineamenti": len(allineamenti),
        "n_criticita": len(criticita)
    }
