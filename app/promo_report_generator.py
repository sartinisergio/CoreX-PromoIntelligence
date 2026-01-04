"""
CoreX PromoIntelligence - Generatore Report Promozione v3.0
Due modalità: ZANICHELLI (promuovere) e COMPETITOR (attaccare)
Con Executive Summary generato da LLM
"""

from datetime import datetime
from typing import Dict, List, Any, Literal
from pathlib import Path
import json


class PromoReportGenerator:
    """
    Genera report orientati alla promozione con due modalità:
    - ZANICHELLI: evidenzia punti di forza, gestisce gap
    - COMPETITOR: evidenzia vulnerabilità, opportunità di attacco
    """
    
    # Soglie
    SOGLIA_FIT_ALTO = 80
    SOGLIA_FIT_MEDIO = 75
    SOGLIA_GAP_CRITICO = 40
    SOGLIA_PUNTO_FORZA = 80
    SOGLIA_SOPRA_MEDIA = 5

    def __init__(self, 
                 analisi_manuale: Dict[str, Any],
                 framework_reale: Dict[str, Any],
                 framework_ideale: Dict[str, Any],
                 nome_manuale: str,
                 autore_manuale: str = "",
                 editore: str = "",
                 tipo_analisi: Literal["zanichelli", "competitor"] = "zanichelli"):
        """
        Args:
            analisi_manuale: Output dell'analisi LLM del manuale
            framework_reale: Framework multiclasse generato da CoreX
            framework_ideale: Framework ideale della materia
            nome_manuale: Nome del manuale analizzato
            autore_manuale: Autore del manuale
            editore: Casa editrice (Zanichelli, McGraw-Hill, etc.)
            tipo_analisi: "zanichelli" o "competitor"
        """
        self.analisi_manuale = analisi_manuale
        self.framework_reale = framework_reale
        self.framework_ideale = framework_ideale
        self.nome_manuale = nome_manuale
        self.autore_manuale = autore_manuale
        self.editore = editore if editore else ("Zanichelli" if tipo_analisi == "zanichelli" else "Competitor")
        self.tipo_analisi = tipo_analisi
        self.materia = framework_ideale.get("framework", {}).get("name", "N/D")
        
        self._parse_data()
    
    def _parse_data(self):
        """Estrae e prepara i dati per la generazione del report."""
        
        # Copertura manuale per modulo
        self.copertura_manuale = {}
        if "modules" in self.analisi_manuale:
            for mod in self.analisi_manuale["modules"]:
                self.copertura_manuale[mod["id"]] = {
                    "name": mod["name"],
                    "coverage": mod.get("coverage", 0),
                    "status": mod.get("status", "")
                }
        
        # Copertura framework reale per modulo e classe
        self.copertura_reale = {}
        self.moduli_core = []
        self.moduli_distintivi = []
        
        if "modules" in self.framework_reale:
            for mod in self.framework_reale["modules"]:
                mod_id = mod["id"]
                self.copertura_reale[mod_id] = {
                    "name": mod["name"],
                    "coverage_by_class": mod.get("coverage_by_class", {}),
                    "avg_coverage": mod.get("avg_coverage", 0),
                    "is_core": mod.get("is_core", False),
                    "is_distinctive": mod.get("is_distinctive", False),
                    "distinctive_for": mod.get("distinctive_for", [])
                }
                if mod.get("is_core"):
                    self.moduli_core.append(mod_id)
                if mod.get("is_distinctive"):
                    self.moduli_distintivi.append(mod_id)
        
        # Copertura per classe dal framework reale
        self.copertura_classi = self.framework_reale.get("summary", {}).get(
            "overall_coverage_by_class", {}
        )
        
        # Lista classi ordinate per copertura
        self.classi_ordinate = sorted(
            self.copertura_classi.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Calcola copertura globale manuale
        if self.copertura_manuale:
            coverages = [m["coverage"] for m in self.copertura_manuale.values()]
            self.copertura_globale = sum(coverages) / len(coverages)
        else:
            self.copertura_globale = 0
        
        # Conteggi moduli
        self.n_moduli_totali = len(self.copertura_manuale)
        self.n_moduli_coperti = sum(
            1 for m in self.copertura_manuale.values() 
            if m["coverage"] >= 80
        )

    def _calcola_giudizio(self, copertura: float) -> str:
        """Restituisce il giudizio testuale basato sulla copertura."""
        if copertura >= 85:
            return "ECCELLENTE"
        elif copertura >= 70:
            return "BUONO"
        elif copertura >= 55:
            return "SUFFICIENTE"
        else:
            return "INSUFFICIENTE"

    def _calcola_fit_classe(self, classe: str) -> float:
        """Calcola il fit del manuale per una specifica classe."""
        fit_scores = []
        
        for mod_id, mod_data in self.copertura_manuale.items():
            copertura_manuale = mod_data["coverage"]
            
            if mod_id in self.copertura_reale:
                copertura_classe = self.copertura_reale[mod_id]["coverage_by_class"].get(
                    classe, 0
                )
            else:
                copertura_classe = 0
            
            if copertura_classe > 0:
                peso = copertura_classe / 100
                score = min(copertura_manuale / copertura_classe, 1.0) * 100
                fit_scores.append((score, peso))
        
        if not fit_scores:
            return self.copertura_classi.get(classe, 0)
        
        totale_peso = sum(p for _, p in fit_scores)
        if totale_peso == 0:
            return 0
        
        fit = sum(s * p for s, p in fit_scores) / totale_peso
        return round(fit, 1)

    def _identifica_punti_forza(self) -> List[Dict[str, Any]]:
        """Identifica i moduli dove il manuale eccelle."""
        punti_forza = []
        
        for mod_id, mod_data in self.copertura_manuale.items():
            copertura = mod_data["coverage"]
            nome = mod_data["name"]
            
            if mod_id not in self.copertura_reale:
                continue
            
            media_classi = self.copertura_reale[mod_id]["avg_coverage"]
            is_core = self.copertura_reale[mod_id]["is_core"]
            
            if copertura >= self.SOGLIA_PUNTO_FORZA:
                differenza = copertura - media_classi
                
                if differenza >= self.SOGLIA_SOPRA_MEDIA:
                    vantaggio = "sopra_media"
                elif copertura >= 85 and media_classi >= 80:
                    vantaggio = "allineato_top"
                else:
                    vantaggio = "buono"
                
                punti_forza.append({
                    "id": mod_id,
                    "name": nome,
                    "copertura": copertura,
                    "media_classi": media_classi,
                    "differenza": round(differenza, 1),
                    "is_core": is_core,
                    "vantaggio": vantaggio
                })
        
        punti_forza.sort(key=lambda x: x["differenza"], reverse=True)
        return punti_forza

    def _identifica_gap(self) -> List[Dict[str, Any]]:
        """Identifica i moduli con gap critici."""
        gap_critici = []
        
        for mod_id, mod_data in self.copertura_manuale.items():
            copertura = mod_data["coverage"]
            nome = mod_data["name"]
            
            if copertura >= self.SOGLIA_GAP_CRITICO:
                continue
            
            if mod_id not in self.copertura_reale:
                continue
            
            coverage_by_class = self.copertura_reale[mod_id]["coverage_by_class"]
            media_classi = self.copertura_reale[mod_id]["avg_coverage"]
            is_core = self.copertura_reale[mod_id]["is_core"]
            
            classi_impattate = [
                {"classe": self._short_class_name(classe), "classe_completa": classe, "richiesta": cov}
                for classe, cov in coverage_by_class.items()
                if cov >= 50
            ]
            classi_impattate.sort(key=lambda x: x["richiesta"], reverse=True)
            
            gap_critici.append({
                "id": mod_id,
                "name": nome,
                "copertura_manuale": copertura,
                "media_classi": round(media_classi, 1),
                "is_core": is_core,
                "classi_impattate": classi_impattate[:5],
                "n_classi_impattate": len(classi_impattate),
                "impatto": round(media_classi - copertura, 1)
            })
        
        gap_critici.sort(key=lambda x: x["impatto"], reverse=True)
        return gap_critici

    def _classifica_classi(self) -> Dict[str, List[Dict[str, Any]]]:
        """Classifica le classi in base al fit con il manuale."""
        tutte_classi = []
        
        for classe, _ in self.classi_ordinate:
            fit = self._calcola_fit_classe(classe)
            classe_short = self._short_class_name(classe)
            moduli_forti = self._get_moduli_forti_classe(classe)
            gap_classe = self._get_gap_classe(classe)
            
            tutte_classi.append({
                "classe": classe_short,
                "classe_completa": classe,
                "fit": fit,
                "moduli_forti": moduli_forti,
                "gap": gap_classe
            })
        
        tutte_classi.sort(key=lambda x: x["fit"], reverse=True)
        
        if self.tipo_analisi == "zanichelli":
            return self._classifica_per_zanichelli(tutte_classi)
        else:
            return self._classifica_per_competitor(tutte_classi)

    def _classifica_per_zanichelli(self, classi: List[Dict]) -> Dict[str, List[Dict]]:
        """Classificazione per report Zanichelli: dove spingere."""
        classificazione = {
            "spingere": [],
            "valutare": [],
            "attenzione": []
        }
        
        for c in classi:
            if c["fit"] >= self.SOGLIA_FIT_ALTO:
                classificazione["spingere"].append(c)
            elif c["fit"] >= self.SOGLIA_FIT_MEDIO:
                classificazione["valutare"].append(c)
            else:
                classificazione["attenzione"].append(c)
        
        return classificazione

    def _classifica_per_competitor(self, classi: List[Dict]) -> Dict[str, List[Dict]]:
        """Classificazione per report Competitor: dove attaccare."""
        classificazione = {
            "vulnerabile": [],
            "contendibile": [],
            "forte": []
        }
        
        for c in classi:
            if c["fit"] < self.SOGLIA_FIT_MEDIO:
                classificazione["vulnerabile"].append(c)
            elif c["fit"] < self.SOGLIA_FIT_ALTO:
                classificazione["contendibile"].append(c)
            else:
                classificazione["forte"].append(c)
        
        classificazione["vulnerabile"].sort(key=lambda x: x["fit"])
        
        return classificazione

    def _short_class_name(self, classe: str) -> str:
        """Abbrevia il nome della classe per display."""
        short = classe.replace("_", " ")
        if len(short) > 30:
            short = short[:27] + "..."
        return short

    def _get_moduli_forti_classe(self, classe: str) -> List[str]:
        """Trova i moduli dove manuale e classe matchano bene."""
        moduli_forti = []
        
        for mod_id, mod_data in self.copertura_manuale.items():
            if mod_data["coverage"] < 80:
                continue
            
            if mod_id in self.copertura_reale:
                cov_classe = self.copertura_reale[mod_id]["coverage_by_class"].get(classe, 0)
                if cov_classe >= 80:
                    moduli_forti.append(mod_data["name"])
        
        return moduli_forti[:4]

    def _get_gap_classe(self, classe: str) -> List[str]:
        """Trova i gap del manuale rilevanti per questa classe."""
        gap = []
        
        for mod_id, mod_data in self.copertura_manuale.items():
            if mod_data["coverage"] >= 40:
                continue
            
            if mod_id in self.copertura_reale:
                cov_classe = self.copertura_reale[mod_id]["coverage_by_class"].get(classe, 0)
                if cov_classe >= 60:
                    gap.append(mod_data["name"])
        
        return gap[:3]

    def genera_report(self) -> Dict[str, Any]:
        """Genera il report in base al tipo di analisi."""
        
        punti_forza = self._identifica_punti_forza()
        gap = self._identifica_gap()
        classificazione_classi = self._classifica_classi()
        
        if self.tipo_analisi == "zanichelli":
            report = self._genera_report_zanichelli(punti_forza, gap, classificazione_classi)
        else:
            report = self._genera_report_competitor(punti_forza, gap, classificazione_classi)
        
        # ============================================================
        # NUOVO: Genera Executive Summary con LLM
        # ============================================================
        try:
            from app.promo_narrative_generator import generate_executive_summary_for_report
            
            exec_summary = generate_executive_summary_for_report(
                punti_forza=punti_forza,
                gap=gap,
                classificazione_classi=classificazione_classi,
                nome_manuale=self.nome_manuale,
                autore_manuale=self.autore_manuale,
                editore=self.editore,
                materia=self.materia,
                copertura_globale=self.copertura_globale,
                tipo_analisi=self.tipo_analisi
            )
            report["executive_summary"] = exec_summary
        except Exception as e:
            print(f"Executive summary non generato: {e}")
            report["executive_summary"] = {"text": "", "generated_by_llm": False}
        # ============================================================
        
        return report

    def _genera_report_zanichelli(self, punti_forza, gap, classificazione_classi) -> Dict[str, Any]:
        """Report per promuovere un manuale Zanichelli."""
        
        target_primario = [
            f"{c['classe']} ({c['fit']}%)" 
            for c in classificazione_classi["spingere"][:3]
        ]
        target_secondario = [
            f"{c['classe']} ({c['fit']}%)" 
            for c in classificazione_classi["valutare"][:3]
        ]
        attenzione = [
            f"{c['classe']} ({c['fit']}%)" 
            for c in classificazione_classi["attenzione"][:2]
        ]
        
        n_gap = len(gap)
        if n_gap == 0:
            posizionamento = "Copertura completa su tutti i moduli"
        elif n_gap == 1:
            posizionamento = f"Solido, con un gap su: {gap[0]['name']}"
        elif n_gap <= 3:
            nomi_gap = ", ".join([g["name"] for g in gap[:2]])
            posizionamento = f"Buona copertura, gap su: {nomi_gap}"
        else:
            posizionamento = f"Copertura parziale, {n_gap} moduli con gap significativi"
        
        return {
            "metadata": {
                "manuale": self.nome_manuale,
                "autore": self.autore_manuale,
                "editore": self.editore,
                "materia": self.materia,
                "tipo_report": "ZANICHELLI",
                "data_analisi": datetime.now().isoformat(),
                "copertura_globale": round(self.copertura_globale, 1),
                "giudizio": self._calcola_giudizio(self.copertura_globale),
                "versione_report": "3.0"
            },
            
            "quick_card": {
                "titolo": "Target di promozione",
                "target_primario": target_primario,
                "target_secondario": target_secondario,
                "attenzione": attenzione,
                "posizionamento": posizionamento,
                "moduli_coperti": f"{self.n_moduli_coperti}/{self.n_moduli_totali} moduli ≥80%"
            },
            
            "punti_forza": {
                "titolo": "Punti di Forza — Da evidenziare al docente",
                "descrizione": "Moduli dove il manuale eccelle rispetto alla media delle richieste",
                "items": [
                    {
                        "modulo": p["name"],
                        "copertura_manuale": p["copertura"],
                        "media_classi": round(p["media_classi"], 1),
                        "differenza": p["differenza"],
                        "is_core": p["is_core"],
                        "vantaggio": p["vantaggio"]
                    }
                    for p in punti_forza
                ]
            },
            
            "gap": {
                "titolo": "Gap — Essere preparati a gestire",
                "descrizione": "Moduli con copertura insufficiente che potrebbero generare obiezioni",
                "items": [
                    {
                        "modulo": g["name"],
                        "copertura_manuale": g["copertura_manuale"],
                        "media_classi": g["media_classi"],
                        "impatto": g["impatto"],
                        "is_core": g["is_core"],
                        "classi_impattate": g["classi_impattate"]
                    }
                    for g in gap
                ]
            },
            
            "strategia_classi": {
                "titolo": "Strategia per Classe",
                "categorie": {
                    "spingere": {
                        "label": "🟢 SPINGERE",
                        "descrizione": "Alto fit, target primario",
                        "items": classificazione_classi["spingere"]
                    },
                    "valutare": {
                        "label": "🟡 VALUTARE", 
                        "descrizione": "Medio fit, verificare esigenze docente",
                        "items": classificazione_classi["valutare"]
                    },
                    "attenzione": {
                        "label": "🔴 ATTENZIONE",
                        "descrizione": "Basso fit, potrebbero esserci alternative migliori",
                        "items": classificazione_classi["attenzione"]
                    }
                }
            },
            
            "dettaglio_tecnico": self._genera_dettaglio_tecnico()
        }

    def _genera_report_competitor(self, punti_forza, gap, classificazione_classi) -> Dict[str, Any]:
        """Report per analizzare un manuale competitor."""
        
        vulnerabili = [
            f"{c['classe']} ({c['fit']}%)" 
            for c in classificazione_classi["vulnerabile"][:3]
        ]
        contendibili = [
            f"{c['classe']} ({c['fit']}%)" 
            for c in classificazione_classi["contendibile"][:3]
        ]
        forte = [
            f"{c['classe']} ({c['fit']}%)" 
            for c in classificazione_classi["forte"][:2]
        ]
        
        n_gap = len(gap)
        n_forza = len(punti_forza)
        
        if n_gap >= 3:
            posizionamento = f"Competitor debole: {n_gap} gap significativi, buone opportunità"
        elif n_gap >= 1 and n_forza <= 5:
            posizionamento = f"Competitor con debolezze: attaccabile su {n_gap} moduli"
        elif n_forza >= 8:
            posizionamento = "Competitor solido: poche opportunità di attacco diretto"
        else:
            posizionamento = "Competitor nella media: cercare nicchie specifiche"
        
        return {
            "metadata": {
                "manuale": self.nome_manuale,
                "autore": self.autore_manuale,
                "editore": self.editore,
                "materia": self.materia,
                "tipo_report": "COMPETITOR",
                "data_analisi": datetime.now().isoformat(),
                "copertura_globale": round(self.copertura_globale, 1),
                "giudizio": self._calcola_giudizio(self.copertura_globale),
                "versione_report": "3.0"
            },
            
            "quick_card": {
                "titolo": "Analisi Competitiva",
                "classi_vulnerabili": vulnerabili,
                "classi_contendibili": contendibili,
                "classi_forte": forte,
                "posizionamento": posizionamento,
                "sintesi": f"{n_gap} vulnerabilità, {n_forza} punti di forza"
            },
            
            "vulnerabilita": {
                "titolo": "Vulnerabilità — Opportunità di attacco",
                "descrizione": "Gap del competitor dove proporre alternativa Zanichelli",
                "items": [
                    {
                        "modulo": g["name"],
                        "copertura_competitor": g["copertura_manuale"],
                        "richiesta_media": g["media_classi"],
                        "gap": g["impatto"],
                        "is_core": g["is_core"],
                        "classi_target": g["classi_impattate"],
                        "opportunita": "ALTA" if g["impatto"] >= 50 and g["is_core"] else 
                                       "MEDIA" if g["impatto"] >= 30 else "BASSA"
                    }
                    for g in gap
                ]
            },
            
            "punti_forza_competitor": {
                "titolo": "Punti di Forza Competitor — Evitare confronto",
                "descrizione": "Moduli dove il competitor è forte, non attaccare su questi temi",
                "items": [
                    {
                        "modulo": p["name"],
                        "copertura_competitor": p["copertura"],
                        "media_classi": round(p["media_classi"], 1),
                        "vantaggio": p["vantaggio"],
                        "is_core": p["is_core"]
                    }
                    for p in punti_forza
                ]
            },
            
            "strategia_classi": {
                "titolo": "Strategia Competitiva per Classe",
                "categorie": {
                    "vulnerabile": {
                        "label": "🎯 VULNERABILE",
                        "descrizione": "Competitor debole, proporre alternativa Zanichelli",
                        "items": classificazione_classi["vulnerabile"]
                    },
                    "contendibile": {
                        "label": "⚔️ CONTENDIBILE",
                        "descrizione": "Possibile competere, dipende dal docente",
                        "items": classificazione_classi["contendibile"]
                    },
                    "forte": {
                        "label": "🛡️ FORTE",
                        "descrizione": "Competitor solido, evitare scontro frontale",
                        "items": classificazione_classi["forte"]
                    }
                }
            },
            
            "dettaglio_tecnico": self._genera_dettaglio_tecnico()
        }

    def _genera_dettaglio_tecnico(self) -> Dict[str, Any]:
        """Genera sezione dettaglio tecnico comune."""
        return {
            "moduli": [
                {
                    "id": mod_id,
                    "nome": mod_data["name"],
                    "copertura": mod_data["coverage"],
                    "status": "gap" if mod_data["coverage"] < 40 else 
                              "attenzione" if mod_data["coverage"] < 70 else "ok"
                }
                for mod_id, mod_data in self.copertura_manuale.items()
            ],
            "n_moduli_totali": self.n_moduli_totali,
            "n_moduli_coperti_80": self.n_moduli_coperti,
            "n_moduli_core": len(self.moduli_core),
            "n_classi_analizzate": len(self.copertura_classi)
        }
# =============================================================================
# GENERAZIONE HTML
# =============================================================================

def genera_html_report(report: Dict[str, Any]) -> str:
    """Genera HTML in base al tipo di report."""
    
    if report["metadata"]["tipo_report"] == "ZANICHELLI":
        return _genera_html_zanichelli(report)
    else:
        return _genera_html_competitor(report)


def _genera_html_zanichelli(report: Dict[str, Any]) -> str:
    """HTML per report Zanichelli."""
    
    giudizio_class = report['metadata']['giudizio'].lower()
    
    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Report Promozione - {report['metadata']['manuale']}</title>
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
        
        .badge-zanichelli {{
            display: inline-block; background: #1a237e; color: white;
            padding: 5px 15px; border-radius: 15px; font-weight: bold; margin-left: 10px;
        }}
        
        .header-info {{
            background: #e8eaf6; padding: 15px 20px; border-radius: 8px; margin-bottom: 25px;
        }}
        .giudizio {{
            display: inline-block; padding: 5px 15px; border-radius: 15px; font-weight: bold; margin-left: 15px;
        }}
        .giudizio-eccellente {{ background: #c8e6c9; color: #2e7d32; }}
        .giudizio-buono {{ background: #dcedc8; color: #558b2f; }}
        .giudizio-sufficiente {{ background: #fff3e0; color: #e65100; }}
        .giudizio-insufficiente {{ background: #ffcdd2; color: #c62828; }}
        
        .executive-summary {{
            background: linear-gradient(135deg, #e3f2fd, #ffffff); 
            padding: 25px 30px; 
            border-radius: 12px; 
            margin: 25px 0; 
            border-left: 5px solid #1976d2; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .executive-summary h2 {{
            margin-top: 0; 
            color: #1565c0; 
            font-size: 1.3em;
            border: none;
            padding-left: 0;
        }}
        .executive-summary p {{
            margin: 0; 
            line-height: 1.8; 
            font-size: 1.05em; 
            color: #333; 
            text-align: justify;
        }}
        
        .quick-card {{
            display: grid; grid-template-columns: 160px 1fr; gap: 10px 20px;
            background: #fafafa; padding: 20px; border-radius: 10px; border-left: 4px solid #3949ab;
        }}
        .quick-card dt {{ font-weight: 600; color: #3949ab; }}
        .quick-card dd {{ margin: 0; }}
        
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #3949ab; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 12px; border-bottom: 1px solid #e0e0e0; }}
        tr:hover {{ background: #f5f5f5; }}
        
        .tag {{
            display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.85em; font-weight: 500;
        }}
        .tag-core {{ background: #e3f2fd; color: #1565c0; }}
        .tag-gap {{ background: #ffcdd2; color: #c62828; }}
        .tag-ok {{ background: #c8e6c9; color: #2e7d32; }}
        .tag-attenzione {{ background: #fff3e0; color: #e65100; }}
        .tag-sopra {{ background: #c8e6c9; color: #2e7d32; }}
        .tag-allineato {{ background: #e3f2fd; color: #1565c0; }}
        
        .strategia-section {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .strategia-card {{ padding: 15px; border-radius: 10px; }}
        .strategia-card h3 {{ margin-top: 0; font-size: 1.1em; }}
        .strategia-card.spingere {{ background: #e8f5e9; border: 2px solid #4caf50; }}
        .strategia-card.spingere h3 {{ color: #2e7d32; }}
        .strategia-card.valutare {{ background: #fff3e0; border: 2px solid #ff9800; }}
        .strategia-card.valutare h3 {{ color: #e65100; }}
        .strategia-card.attenzione {{ background: #ffebee; border: 2px solid #f44336; }}
        .strategia-card.attenzione h3 {{ color: #c62828; }}
        
        .classe-item {{ background: white; padding: 10px; border-radius: 6px; margin: 8px 0; }}
        .classe-item strong {{ color: #1a237e; }}
        .classe-item .fit {{ float: right; font-weight: bold; }}
        .classe-item .dettagli {{ font-size: 0.85em; color: #666; margin-top: 5px; }}
        
        .section-desc {{ color: #666; font-style: italic; margin-bottom: 15px; }}
        
        details {{ margin: 20px 0; padding: 15px; background: #fafafa; border-radius: 8px; }}
        summary {{ cursor: pointer; font-weight: 600; color: #3949ab; }}
        
        .footer {{
            margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0;
            color: #888; font-size: 0.85em; text-align: center;
        }}
        
        @media (max-width: 900px) {{
            .strategia-section {{ grid-template-columns: 1fr; }}
            body {{ padding: 10px; }}
            .container {{ padding: 15px; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>📊 Report Promozione <span class="badge-zanichelli">ZANICHELLI</span></h1>
    
    <div class="header-info">
        <strong>{report['metadata']['manuale']}</strong>
        {f" — {report['metadata']['autore']}" if report['metadata']['autore'] else ""}
        ({report['metadata']['editore']})<br>
        <strong>Materia:</strong> {report['metadata']['materia']}<br>
        <strong>Copertura globale:</strong> {report['metadata']['copertura_globale']}%
        <span class="giudizio giudizio-{giudizio_class}">{report['metadata']['giudizio']}</span>
    </div>
"""
    
    # ============================================================
    # NUOVO: Executive Summary
    # ============================================================
    exec_summary = report.get('executive_summary', {})
    if exec_summary and exec_summary.get('text'):
        badge_html = ""
        if not exec_summary.get('generated_by_llm', False):
            badge_html = '<span style="font-size: 0.75em; background: #fff3e0; color: #e65100; padding: 2px 8px; border-radius: 10px; margin-left: 10px;">Generato automaticamente</span>'
        
        html += f"""
    <div class="executive-summary">
        <h2>📋 Executive Summary {badge_html}</h2>
        <p>{exec_summary.get('text', '')}</p>
    </div>
"""
    # ============================================================
    
    html += f"""
    <h2>⚡ {report['quick_card']['titolo']}</h2>
    <dl class="quick-card">
        <dt>Target primario</dt>
        <dd>{', '.join(report['quick_card']['target_primario']) or 'Nessuno identificato'}</dd>
        <dt>Target secondario</dt>
        <dd>{', '.join(report['quick_card']['target_secondario']) or 'Nessuno identificato'}</dd>
        <dt>Attenzione</dt>
        <dd>{', '.join(report['quick_card']['attenzione']) or 'Nessuna criticità'}</dd>
        <dt>Posizionamento</dt>
        <dd>{report['quick_card']['posizionamento']}</dd>
        <dt>Copertura moduli</dt>
        <dd>{report['quick_card']['moduli_coperti']}</dd>
    </dl>
    
    <h2>💪 {report['punti_forza']['titolo']}</h2>
    <p class="section-desc">{report['punti_forza']['descrizione']}</p>
"""
    
    if report['punti_forza']['items']:
        html += """
    <table>
        <thead><tr><th>Modulo</th><th>Copertura</th><th>Media Classi</th><th>Δ</th><th>Note</th></tr></thead>
        <tbody>
"""
        for pf in report['punti_forza']['items']:
            core_badge = '<span class="tag tag-core">CORE</span>' if pf['is_core'] else ''
            vantaggio_badge = {
                'sopra_media': '<span class="tag tag-sopra">Sopra media</span>',
                'allineato_top': '<span class="tag tag-allineato">Top</span>'
            }.get(pf['vantaggio'], '')
            diff = f"+{pf['differenza']}" if pf['differenza'] > 0 else str(pf['differenza'])
            html += f"""
            <tr>
                <td><strong>{pf['modulo']}</strong> {core_badge}</td>
                <td>{pf['copertura_manuale']}%</td>
                <td>{pf['media_classi']}%</td>
                <td>{diff}%</td>
                <td>{vantaggio_badge}</td>
            </tr>
"""
        html += "</tbody></table>"
    else:
        html += "<p>Nessun modulo con copertura ≥80%</p>"
    
    # Gap
    html += f"""
    <h2>⚠️ {report['gap']['titolo']}</h2>
    <p class="section-desc">{report['gap']['descrizione']}</p>
"""
    
    if report['gap']['items']:
        html += """
    <table>
        <thead><tr><th>Modulo</th><th>Copertura</th><th>Richiesta media</th><th>Classi impattate</th></tr></thead>
        <tbody>
"""
        for g in report['gap']['items']:
            classi_str = ", ".join([f"{c['classe']} ({c['richiesta']}%)" for c in g['classi_impattate'][:3]])
            core_badge = '<span class="tag tag-core">CORE</span>' if g['is_core'] else ''
            html += f"""
            <tr>
                <td><strong>{g['modulo']}</strong> {core_badge}</td>
                <td><span class="tag tag-gap">{g['copertura_manuale']}%</span></td>
                <td>{g['media_classi']}%</td>
                <td>{classi_str}</td>
            </tr>
"""
        html += "</tbody></table>"
    else:
        html += "<p>✅ Nessun gap critico</p>"
    
    # Strategia classi
    html += f"""
    <h2>🎯 {report['strategia_classi']['titolo']}</h2>
    <div class="strategia-section">
"""
    
    for cat_key, cat_class in [("spingere", "spingere"), ("valutare", "valutare"), ("attenzione", "attenzione")]:
        cat = report['strategia_classi']['categorie'][cat_key]
        html += f"""
        <div class="strategia-card {cat_class}">
            <h3>{cat['label']}</h3>
            <p class="section-desc" style="font-size:0.85em; margin:0 0 10px 0;">{cat['descrizione']}</p>
"""
        if cat['items']:
            for c in cat['items']:
                moduli = ", ".join(c['moduli_forti'][:2]) if c['moduli_forti'] else "—"
                gap_str = ", ".join(c['gap'][:2]) if c['gap'] else "Nessuno"
                html += f"""
            <div class="classe-item">
                <strong>{c['classe']}</strong><span class="fit">{c['fit']}%</span>
                <div class="dettagli">Forti: {moduli}<br>Gap: {gap_str}</div>
            </div>
"""
        else:
            html += "<p style='color:#888;'>Nessuna classe</p>"
        html += "</div>"
    
    html += "</div>"
    
    # Dettaglio tecnico
    html += _genera_html_dettaglio_tecnico(report)
    
    # Footer
    html += f"""
    <div class="footer">
        <strong>CoreX PromoIntelligence v{report['metadata']['versione_report']}</strong> | {report['metadata']['editore']}<br>
        Report generato il {report['metadata']['data_analisi'][:10]}
    </div>
</div>
</body>
</html>
"""
    return html
def _genera_html_competitor(report: Dict[str, Any]) -> str:
    """HTML per report Competitor."""
    
    giudizio_class = report['metadata']['giudizio'].lower()
    
    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analisi Competitor - {report['metadata']['manuale']}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; padding: 20px 40px; 
            background: #fff8f0; color: #333; line-height: 1.6;
        }}
        .container {{ 
            max-width: 1200px; margin: 0 auto; 
            background: white; padding: 30px 40px; 
            border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.07); 
        }}
        h1 {{ color: #bf360c; border-bottom: 3px solid #e65100; padding-bottom: 15px; }}
        h2 {{ color: #e65100; margin-top: 35px; border-left: 4px solid #ff9800; padding-left: 15px; }}
        
        .badge-competitor {{
            display: inline-block; background: #e65100; color: white;
            padding: 5px 15px; border-radius: 15px; font-weight: bold; margin-left: 10px;
        }}
        
        .header-info {{
            background: #fff3e0; padding: 15px 20px; border-radius: 8px; margin-bottom: 25px;
            border-left: 4px solid #e65100;
        }}
        .giudizio {{
            display: inline-block; padding: 5px 15px; border-radius: 15px; font-weight: bold; margin-left: 15px;
        }}
        .giudizio-eccellente {{ background: #c8e6c9; color: #2e7d32; }}
        .giudizio-buono {{ background: #dcedc8; color: #558b2f; }}
        .giudizio-sufficiente {{ background: #fff3e0; color: #e65100; }}
        .giudizio-insufficiente {{ background: #ffcdd2; color: #c62828; }}
        
        .executive-summary {{
            background: linear-gradient(135deg, #fff3e0, #ffffff); 
            padding: 25px 30px; 
            border-radius: 12px; 
            margin: 25px 0; 
            border-left: 5px solid #e65100; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .executive-summary h2 {{
            margin-top: 0; 
            color: #e65100; 
            font-size: 1.3em;
            border: none;
            padding-left: 0;
        }}
        .executive-summary p {{
            margin: 0; 
            line-height: 1.8; 
            font-size: 1.05em; 
            color: #333; 
            text-align: justify;
        }}
        
        .quick-card {{
            display: grid; grid-template-columns: 180px 1fr; gap: 10px 20px;
            background: #fafafa; padding: 20px; border-radius: 10px; border-left: 4px solid #e65100;
        }}
        .quick-card dt {{ font-weight: 600; color: #e65100; }}
        .quick-card dd {{ margin: 0; }}
        
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #e65100; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 12px; border-bottom: 1px solid #e0e0e0; }}
        tr:hover {{ background: #fff8f0; }}
        
        .tag {{
            display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.85em; font-weight: 500;
        }}
        .tag-core {{ background: #e3f2fd; color: #1565c0; }}
        .tag-alta {{ background: #c8e6c9; color: #2e7d32; }}
        .tag-media {{ background: #fff3e0; color: #e65100; }}
        .tag-bassa {{ background: #ffcdd2; color: #c62828; }}
        .tag-ok {{ background: #c8e6c9; color: #2e7d32; }}
        .tag-attenzione {{ background: #fff3e0; color: #e65100; }}
        .tag-gap {{ background: #ffcdd2; color: #c62828; }}
        
        .strategia-section {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .strategia-card {{ padding: 15px; border-radius: 10px; }}
        .strategia-card h3 {{ margin-top: 0; font-size: 1.1em; }}
        .strategia-card.vulnerabile {{ background: #e8f5e9; border: 2px solid #4caf50; }}
        .strategia-card.vulnerabile h3 {{ color: #2e7d32; }}
        .strategia-card.contendibile {{ background: #fff3e0; border: 2px solid #ff9800; }}
        .strategia-card.contendibile h3 {{ color: #e65100; }}
        .strategia-card.forte {{ background: #ffebee; border: 2px solid #f44336; }}
        .strategia-card.forte h3 {{ color: #c62828; }}
        
        .classe-item {{ background: white; padding: 10px; border-radius: 6px; margin: 8px 0; }}
        .classe-item strong {{ color: #bf360c; }}
        .classe-item .fit {{ float: right; font-weight: bold; }}
        .classe-item .dettagli {{ font-size: 0.85em; color: #666; margin-top: 5px; }}
        
        .section-desc {{ color: #666; font-style: italic; margin-bottom: 15px; }}
        
        details {{ margin: 20px 0; padding: 15px; background: #fafafa; border-radius: 8px; }}
        summary {{ cursor: pointer; font-weight: 600; color: #e65100; }}
        
        .footer {{
            margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0;
            color: #888; font-size: 0.85em; text-align: center;
        }}
        
        @media (max-width: 900px) {{
            .strategia-section {{ grid-template-columns: 1fr; }}
            body {{ padding: 10px; }}
            .container {{ padding: 15px; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>🔍 Analisi Competitor <span class="badge-competitor">COMPETITOR</span></h1>
    
    <div class="header-info">
        <strong>{report['metadata']['manuale']}</strong>
        {f" — {report['metadata']['autore']}" if report['metadata']['autore'] else ""}
        ({report['metadata']['editore']})<br>
        <strong>Materia:</strong> {report['metadata']['materia']}<br>
        <strong>Copertura globale:</strong> {report['metadata']['copertura_globale']}%
        <span class="giudizio giudizio-{giudizio_class}">{report['metadata']['giudizio']}</span>
    </div>
"""
    
    # ============================================================
    # NUOVO: Executive Summary
    # ============================================================
    exec_summary = report.get('executive_summary', {})
    if exec_summary and exec_summary.get('text'):
        badge_html = ""
        if not exec_summary.get('generated_by_llm', False):
            badge_html = '<span style="font-size: 0.75em; background: #fff3e0; color: #e65100; padding: 2px 8px; border-radius: 10px; margin-left: 10px;">Generato automaticamente</span>'
        
        html += f"""
    <div class="executive-summary">
        <h2>📋 Executive Summary {badge_html}</h2>
        <p>{exec_summary.get('text', '')}</p>
    </div>
"""
    # ============================================================
    
    html += f"""
    <h2>⚡ {report['quick_card']['titolo']}</h2>
    <dl class="quick-card">
        <dt>Classi vulnerabili</dt>
        <dd>{', '.join(report['quick_card']['classi_vulnerabili']) or 'Nessuna identificata'}</dd>
        <dt>Classi contendibili</dt>
        <dd>{', '.join(report['quick_card']['classi_contendibili']) or 'Nessuna identificata'}</dd>
        <dt>Classi dove è forte</dt>
        <dd>{', '.join(report['quick_card']['classi_forte']) or 'Nessuna'}</dd>
        <dt>Posizionamento</dt>
        <dd>{report['quick_card']['posizionamento']}</dd>
        <dt>Sintesi</dt>
        <dd>{report['quick_card']['sintesi']}</dd>
    </dl>
    
    <h2>🎯 {report['vulnerabilita']['titolo']}</h2>
    <p class="section-desc">{report['vulnerabilita']['descrizione']}</p>
"""
    
    if report['vulnerabilita']['items']:
        html += """
    <table>
        <thead><tr><th>Modulo</th><th>Copertura Competitor</th><th>Richiesta media</th><th>Opportunità</th><th>Classi target</th></tr></thead>
        <tbody>
"""
        for v in report['vulnerabilita']['items']:
            core_badge = '<span class="tag tag-core">CORE</span>' if v['is_core'] else ''
            opp_class = {'ALTA': 'tag-alta', 'MEDIA': 'tag-media', 'BASSA': 'tag-bassa'}.get(v['opportunita'], 'tag-media')
            classi_str = ", ".join([f"{c['classe']}" for c in v['classi_target'][:3]])
            html += f"""
            <tr>
                <td><strong>{v['modulo']}</strong> {core_badge}</td>
                <td><span class="tag tag-gap">{v['copertura_competitor']}%</span></td>
                <td>{v['richiesta_media']}%</td>
                <td><span class="tag {opp_class}">{v['opportunita']}</span></td>
                <td>{classi_str}</td>
            </tr>
"""
        html += "</tbody></table>"
    else:
        html += "<p>Nessuna vulnerabilità significativa identificata</p>"
    
    # Punti forza competitor
    html += f"""
    <h2>🛡️ {report['punti_forza_competitor']['titolo']}</h2>
    <p class="section-desc">{report['punti_forza_competitor']['descrizione']}</p>
"""
    
    if report['punti_forza_competitor']['items']:
        html += """
    <table>
        <thead><tr><th>Modulo</th><th>Copertura Competitor</th><th>Media Classi</th><th>Note</th></tr></thead>
        <tbody>
"""
        for pf in report['punti_forza_competitor']['items']:
            core_badge = '<span class="tag tag-core">CORE</span>' if pf['is_core'] else ''
            vantaggio_badge = {
                'sopra_media': '<span class="tag tag-ok">Sopra media</span>',
                'allineato_top': '<span class="tag tag-ok">Top</span>'
            }.get(pf['vantaggio'], '')
            html += f"""
            <tr>
                <td><strong>{pf['modulo']}</strong> {core_badge}</td>
                <td><span class="tag tag-ok">{pf['copertura_competitor']}%</span></td>
                <td>{pf['media_classi']}%</td>
                <td>{vantaggio_badge}</td>
            </tr>
"""
        html += "</tbody></table>"
    else:
        html += "<p>Nessun punto di forza significativo</p>"
    
    # Strategia classi
    html += f"""
    <h2>⚔️ {report['strategia_classi']['titolo']}</h2>
    <div class="strategia-section">
"""
    
    for cat_key, cat_class in [("vulnerabile", "vulnerabile"), ("contendibile", "contendibile"), ("forte", "forte")]:
        cat = report['strategia_classi']['categorie'][cat_key]
        html += f"""
        <div class="strategia-card {cat_class}">
            <h3>{cat['label']}</h3>
            <p class="section-desc" style="font-size:0.85em; margin:0 0 10px 0;">{cat['descrizione']}</p>
"""
        if cat['items']:
            for c in cat['items']:
                moduli = ", ".join(c['moduli_forti'][:2]) if c['moduli_forti'] else "—"
                gap_str = ", ".join(c['gap'][:2]) if c['gap'] else "Nessuno"
                html += f"""
            <div class="classe-item">
                <strong>{c['classe']}</strong><span class="fit">{c['fit']}%</span>
                <div class="dettagli">Forti: {moduli}<br>Gap: {gap_str}</div>
            </div>
"""
        else:
            html += "<p style='color:#888;'>Nessuna classe</p>"
        html += "</div>"
    
    html += "</div>"
    
    # Dettaglio tecnico
    html += _genera_html_dettaglio_tecnico(report)
    
    # Footer
    html += f"""
    <div class="footer">
        <strong>CoreX PromoIntelligence v{report['metadata']['versione_report']}</strong> | Analisi Competitor<br>
        Report generato il {report['metadata']['data_analisi'][:10]}
    </div>
</div>
</body>
</html>
"""
    return html


def _genera_html_dettaglio_tecnico(report: Dict[str, Any]) -> str:
    """Genera HTML per sezione dettaglio tecnico (espandibile)."""
    
    dettaglio = report.get('dettaglio_tecnico', {})
    moduli = dettaglio.get('moduli', [])
    
    html = """
    <details>
        <summary>📊 Dettaglio Tecnico (clicca per espandere)</summary>
        <div style="margin-top: 15px;">
"""
    
    html += f"""
            <p>
                <strong>Moduli totali:</strong> {dettaglio.get('n_moduli_totali', 0)} |
                <strong>Moduli ≥80%:</strong> {dettaglio.get('n_moduli_coperti_80', 0)} |
                <strong>Moduli core:</strong> {dettaglio.get('n_moduli_core', 0)} |
                <strong>Classi analizzate:</strong> {dettaglio.get('n_classi_analizzate', 0)}
            </p>
"""
    
    if moduli:
        html += """
            <table style="font-size: 0.9em;">
                <thead><tr><th>ID</th><th>Modulo</th><th>Copertura</th><th>Status</th></tr></thead>
                <tbody>
"""
        for m in moduli:
            status_class = {
                'ok': 'tag-ok',
                'attenzione': 'tag-attenzione',
                'gap': 'tag-gap'
            }.get(m['status'], '')
            status_label = {
                'ok': 'OK',
                'attenzione': 'Attenzione',
                'gap': 'Gap'
            }.get(m['status'], m['status'])
            html += f"""
                <tr>
                    <td>{m['id']}</td>
                    <td>{m['nome']}</td>
                    <td>{m['copertura']}%</td>
                    <td><span class="tag {status_class}">{status_label}</span></td>
                </tr>
"""
        html += """
                </tbody>
            </table>
"""
    
    html += """
        </div>
    </details>
"""
    return html
