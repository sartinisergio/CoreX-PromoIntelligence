"""
CoreX - Pedagogical Analyzer
Analisi del profilo pedagogico del docente dal programma d'esame
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class TeachingApproach(Enum):
    """Approccio didattico prevalente"""
    THEORETICAL = "teorico"
    PRACTICAL = "pratico"
    BALANCED = "bilanciato"
    

class DepthBreadth(Enum):
    """Preferenza profondità vs ampiezza"""
    DEEP_NARROW = "approfondito_focalizzato"
    BROAD_SURVEY = "ampio_panoramico"
    BALANCED = "bilanciato"


class RigorLevel(Enum):
    """Livello di rigore formale"""
    HIGH_FORMAL = "alto_formale"
    ACCESSIBLE = "accessibile"
    MIXED = "misto"


@dataclass
class TeachingPhilosophy:
    """Filosofia didattica del docente"""
    approach: TeachingApproach = TeachingApproach.BALANCED
    rigor_level: RigorLevel = RigorLevel.MIXED
    application_emphasis: int = 50
    interdisciplinarity: int = 50
    theory_indicators: List[str] = field(default_factory=list)
    practice_indicators: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "approach": self.approach.value,
            "rigor_level": self.rigor_level.value,
            "application_emphasis": self.application_emphasis,
            "interdisciplinarity": self.interdisciplinarity,
            "theory_indicators": self.theory_indicators,
            "practice_indicators": self.practice_indicators
        }


@dataclass
class PedagogicalPriorities:
    """Priorità pedagogiche del docente"""
    depth_breadth: DepthBreadth = DepthBreadth.BALANCED
    teaching_methods: List[str] = field(default_factory=list)
    assessment_methods: List[str] = field(default_factory=list)
    sequence_type: str = "non_specificato"
    n_topics: int = 0
    n_hours: int = 0
    lab_percentage: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "depth_breadth": self.depth_breadth.value,
            "teaching_methods": self.teaching_methods,
            "assessment_methods": self.assessment_methods,
            "sequence_type": self.sequence_type,
            "n_topics": self.n_topics,
            "n_hours": self.n_hours,
            "lab_percentage": self.lab_percentage
        }


@dataclass
class StudentTarget:
    """Target di studenti"""
    degree_program: str = ""
    degree_class: str = ""
    year: int = 0
    semester: str = ""
    prerequisites: List[str] = field(default_factory=list)
    expected_background: str = ""
    career_focus: bool = False
    research_focus: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "degree_program": self.degree_program,
            "degree_class": self.degree_class,
            "year": self.year,
            "semester": self.semester,
            "prerequisites": self.prerequisites,
            "expected_background": self.expected_background,
            "career_focus": self.career_focus,
            "research_focus": self.research_focus
        }


@dataclass
class PedagogicalProfile:
    """Profilo pedagogico completo del docente"""
    docente: str = ""
    corso: str = ""
    universita: str = ""
    anno_accademico: str = ""
    philosophy: TeachingPhilosophy = field(default_factory=TeachingPhilosophy)
    priorities: PedagogicalPriorities = field(default_factory=PedagogicalPriorities)
    target: StudentTarget = field(default_factory=StudentTarget)
    profile_summary: str = ""
    key_insights: List[str] = field(default_factory=list)
    suggested_approach: str = ""
    talking_points: List[str] = field(default_factory=list)
    analysis_confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "docente": self.docente,
            "corso": self.corso,
            "universita": self.universita,
            "anno_accademico": self.anno_accademico,
            "philosophy": self.philosophy.to_dict(),
            "priorities": self.priorities.to_dict(),
            "target": self.target.to_dict(),
            "profile_summary": self.profile_summary,
            "key_insights": self.key_insights,
            "suggested_approach": self.suggested_approach,
            "talking_points": self.talking_points,
            "analysis_confidence": self.analysis_confidence
        }


class PedagogicalAnalyzer:
    """Analizza il profilo pedagogico dal programma d'esame"""
    
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.llm_client = None
        
        if use_llm:
            try:
                # Prova a importare e inizializzare il client OpenAI
                import openai
                api_key = os.environ.get("OPENAI_API_KEY", "")
                if api_key:
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    self.use_llm = True
                    print("[OK] OpenAI client inizializzato")
                else:
                    print("[WARN] OPENAI_API_KEY non trovata")
                    self.use_llm = False
            except Exception as e:
                print(f"[WARN] LLM non disponibile: {e}")
                self.use_llm = False
    
    def analyze_program(self, program_text: str, metadata: Optional[Dict] = None) -> PedagogicalProfile:
        """
        Analizza un programma d'esame e genera il profilo pedagogico
        """
        profile = PedagogicalProfile()
        
        # Estrai metadati di base
        if metadata:
            profile.docente = metadata.get("docente", "")
            profile.corso = metadata.get("corso", "")
            profile.universita = metadata.get("universita", "")
            profile.anno_accademico = metadata.get("anno_accademico", "")
        
        # Analisi con LLM se disponibile
        if self.use_llm:
            profile = self._analyze_with_llm(program_text, profile)
        else:
            profile = self._analyze_with_heuristics(program_text, profile)
        
        return profile
    
    def _analyze_with_llm(self, program_text: str, profile: PedagogicalProfile) -> PedagogicalProfile:
        """Analisi approfondita con LLM"""
        
        prompt = f"""Analizza questo programma d'esame universitario ed estrai il profilo pedagogico del docente.

PROGRAMMA D'ESAME:
{program_text[:6000]}

Rispondi SOLO con un JSON valido (senza markdown, senza ```), con questa struttura:
{{
    "docente": "nome se presente nel testo, altrimenti stringa vuota",
    "corso": "nome del corso",
    "universita": "nome università se presente",
    
    "filosofia_didattica": {{
        "approccio": "teorico|pratico|bilanciato",
        "rigore": "alto_formale|accessibile|misto",
        "enfasi_applicazioni": 50,
        "interdisciplinarita": 50,
        "indicatori_teoria": ["lista di frasi che indicano approccio teorico"],
        "indicatori_pratica": ["lista di frasi che indicano approccio pratico"]
    }},
    
    "priorita_pedagogiche": {{
        "profondita_ampiezza": "approfondito_focalizzato|ampio_panoramico|bilanciato",
        "metodi_didattici": ["lezione frontale", "laboratorio", "esercitazioni"],
        "metodi_valutazione": ["scritto", "orale", "progetto"],
        "sequenza": "deduttivo|induttivo|misto",
        "n_argomenti_principali": 10,
        "ore_totali": 60,
        "percentuale_laboratorio": 20
    }},
    
    "target_studenti": {{
        "corso_laurea": "nome",
        "classe_laurea": "es. L-13",
        "anno": 2,
        "semestre": "primo|secondo",
        "prerequisiti": ["lista prerequisiti"],
        "background_atteso": "descrizione",
        "orientamento_lavoro": false,
        "orientamento_ricerca": true
    }},
    
    "sintesi_profilo": "2-3 frasi che descrivono il docente e il suo approccio",
    "insight_chiave": ["3-5 insight utili per il promotore editoriale"],
    "approccio_suggerito": "come dovrebbe presentarsi il promotore a questo docente",
    "punti_chiave_conversazione": ["3-5 argomenti da toccare nella conversazione col docente"],
    "confidence": 0.75
}}

Concentrati su elementi concreti del programma. Se un'informazione non è presente, usa valori neutri.
Rispondi SOLO con il JSON, niente altro."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Sei un analista esperto di didattica universitaria. Rispondi sempre e solo con JSON valido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Rimuovi eventuale markdown
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            profile = self._populate_profile_from_json(data, profile)
            
        except json.JSONDecodeError as e:
            print(f"[ERR] JSON non valido: {e}")
            profile = self._analyze_with_heuristics(program_text, profile)
        except Exception as e:
            print(f"[ERR] Errore analisi LLM: {e}")
            profile = self._analyze_with_heuristics(program_text, profile)
        
        return profile
    
    def _populate_profile_from_json(self, data: Dict, profile: PedagogicalProfile) -> PedagogicalProfile:
        """Popola il profilo dal JSON dell'LLM"""
        
        # Metadati
        profile.docente = data.get("docente", profile.docente) or profile.docente
        profile.corso = data.get("corso", profile.corso) or profile.corso
        profile.universita = data.get("universita", profile.universita) or profile.universita
        
        # Filosofia didattica
        fil = data.get("filosofia_didattica", {})
        
        approach_map = {
            "teorico": TeachingApproach.THEORETICAL,
            "pratico": TeachingApproach.PRACTICAL,
            "bilanciato": TeachingApproach.BALANCED
        }
        profile.philosophy.approach = approach_map.get(fil.get("approccio", ""), TeachingApproach.BALANCED)
        
        rigor_map = {
            "alto_formale": RigorLevel.HIGH_FORMAL,
            "accessibile": RigorLevel.ACCESSIBLE,
            "misto": RigorLevel.MIXED
        }
        profile.philosophy.rigor_level = rigor_map.get(fil.get("rigore", ""), RigorLevel.MIXED)
        
        profile.philosophy.application_emphasis = fil.get("enfasi_applicazioni", 50)
        profile.philosophy.interdisciplinarity = fil.get("interdisciplinarita", 50)
        profile.philosophy.theory_indicators = fil.get("indicatori_teoria", [])
        profile.philosophy.practice_indicators = fil.get("indicatori_pratica", [])
        
        # Priorità pedagogiche
        pri = data.get("priorita_pedagogiche", {})
        
        depth_map = {
            "approfondito_focalizzato": DepthBreadth.DEEP_NARROW,
            "ampio_panoramico": DepthBreadth.BROAD_SURVEY,
            "bilanciato": DepthBreadth.BALANCED
        }
        profile.priorities.depth_breadth = depth_map.get(pri.get("profondita_ampiezza", ""), DepthBreadth.BALANCED)
        
        profile.priorities.teaching_methods = pri.get("metodi_didattici", [])
        profile.priorities.assessment_methods = pri.get("metodi_valutazione", [])
        profile.priorities.sequence_type = pri.get("sequenza", "non_specificato")
        profile.priorities.n_topics = pri.get("n_argomenti_principali", 0)
        profile.priorities.n_hours = pri.get("ore_totali", 0)
        profile.priorities.lab_percentage = pri.get("percentuale_laboratorio", 0)
        
        # Target studenti
        tgt = data.get("target_studenti", {})
        
        profile.target.degree_program = tgt.get("corso_laurea", "")
        profile.target.degree_class = tgt.get("classe_laurea", "")
        profile.target.year = tgt.get("anno", 0)
        profile.target.semester = tgt.get("semestre", "")
        profile.target.prerequisites = tgt.get("prerequisiti", [])
        profile.target.expected_background = tgt.get("background_atteso", "")
        profile.target.career_focus = tgt.get("orientamento_lavoro", False)
        profile.target.research_focus = tgt.get("orientamento_ricerca", False)
        
        # Sintesi
        profile.profile_summary = data.get("sintesi_profilo", "")
        profile.key_insights = data.get("insight_chiave", [])
        profile.suggested_approach = data.get("approccio_suggerito", "")
        profile.talking_points = data.get("punti_chiave_conversazione", [])
        profile.analysis_confidence = data.get("confidence", 0.7)
        
        return profile
    
    def _analyze_with_heuristics(self, program_text: str, profile: PedagogicalProfile) -> PedagogicalProfile:
        """Analisi basata su euristiche quando LLM non è disponibile"""
        
        text_lower = program_text.lower()
        
        # Indicatori teoria vs pratica
        theory_keywords = ["teoria", "teorico", "teorema", "dimostrazione", "formale", "fondamenti", "principi", "definizione", "assioma"]
        practice_keywords = ["laboratorio", "esercitazione", "pratico", "applicazione", "caso studio", "progetto", "hands-on", "sperimentale", "esperimento"]
        
        theory_count = sum(text_lower.count(kw) for kw in theory_keywords)
        practice_count = sum(text_lower.count(kw) for kw in practice_keywords)
        
        if theory_count > practice_count * 1.5:
            profile.philosophy.approach = TeachingApproach.THEORETICAL
            profile.philosophy.application_emphasis = 30
        elif practice_count > theory_count * 1.5:
            profile.philosophy.approach = TeachingApproach.PRACTICAL
            profile.philosophy.application_emphasis = 70
        else:
            profile.philosophy.approach = TeachingApproach.BALANCED
            profile.philosophy.application_emphasis = 50
        
        # Metodi di valutazione
        if "scritto" in text_lower or "compito" in text_lower or "prova scritta" in text_lower:
            profile.priorities.assessment_methods.append("scritto")
        if "orale" in text_lower or "colloquio" in text_lower:
            profile.priorities.assessment_methods.append("orale")
        if "progetto" in text_lower or "elaborato" in text_lower or "tesina" in text_lower:
            profile.priorities.assessment_methods.append("progetto")
        if "itinere" in text_lower or "parzial" in text_lower:
            profile.priorities.assessment_methods.append("prove in itinere")
        
        # Metodi didattici
        if "lezione" in text_lower or "frontale" in text_lower:
            profile.priorities.teaching_methods.append("lezione frontale")
        if "laboratorio" in text_lower:
            profile.priorities.teaching_methods.append("laboratorio")
        if "seminari" in text_lower:
            profile.priorities.teaching_methods.append("seminari")
        if "esercitazione" in text_lower or "esercizi" in text_lower:
            profile.priorities.teaching_methods.append("esercitazioni")
        if "gruppo" in text_lower or "team" in text_lower:
            profile.priorities.teaching_methods.append("lavoro di gruppo")
        
        # Interdisciplinarità
        interdisciplinary_keywords = ["interdisciplin", "multidisciplin", "integrat", "trasversal"]
        interdisciplinary_count = sum(text_lower.count(kw) for kw in interdisciplinary_keywords)
        profile.philosophy.interdisciplinarity = min(80, 30 + interdisciplinary_count * 10)
        
        # Genera insight basici
        profile.key_insights = []
        if profile.philosophy.approach == TeachingApproach.THEORETICAL:
            profile.key_insights.append("Docente con approccio prevalentemente teorico - enfatizzare solidità scientifica del manuale")
        elif profile.philosophy.approach == TeachingApproach.PRACTICAL:
            profile.key_insights.append("Docente orientato alla pratica - evidenziare esercizi, casi studio e applicazioni")
        
        if "laboratorio" in profile.priorities.teaching_methods:
            profile.key_insights.append("Presenza di laboratorio - proporre eventuali materiali di supporto per attività pratiche")
        
        if "orale" in profile.priorities.assessment_methods:
            profile.key_insights.append("Esame orale previsto - il manuale dovrebbe favorire la comprensione concettuale")
        
        # Talking points
        profile.talking_points = [
            "Chiedere quali argomenti ritiene più importanti per gli studenti",
            "Informarsi su eventuali difficoltà degli studenti con i materiali attuali",
            "Proporre una copia saggio per valutazione"
        ]
        
        if practice_count > 5:
            profile.talking_points.append("Discutere le risorse per esercitazioni disponibili nel manuale")
        
        # Approccio suggerito
        if profile.philosophy.approach == TeachingApproach.THEORETICAL:
            profile.suggested_approach = "Approccio formale: enfatizzare il rigore scientifico, la completezza teorica e le basi concettuali solide del manuale Zanichelli."
        elif profile.philosophy.approach == TeachingApproach.PRACTICAL:
            profile.suggested_approach = "Approccio pratico: evidenziare gli esercizi svolti, i casi studio reali e le applicazioni concrete presenti nel manuale."
        else:
            profile.suggested_approach = "Approccio bilanciato: presentare sia la solidità teorica che le applicazioni pratiche, adattandosi alle preferenze che emergeranno dalla conversazione."
        
        profile.profile_summary = "Analisi basata su euristiche (LLM non disponibile)"
        profile.analysis_confidence = 0.3
        
        return profile
    
    def generate_profile_report_html(self, profile: PedagogicalProfile) -> str:
        """Genera un report HTML del profilo pedagogico"""
        
        approach_colors = {
            TeachingApproach.THEORETICAL: "#3f51b5",
            TeachingApproach.PRACTICAL: "#4caf50",
            TeachingApproach.BALANCED: "#ff9800"
        }
        main_color = approach_colors.get(profile.philosophy.approach, "#3f51b5")
        
        insights_html = "".join(f"<li>{insight}</li>" for insight in profile.key_insights) if profile.key_insights else "<li>Nessun insight disponibile</li>"
        talking_points_html = "".join(f'<div class="talking-point">💬 {point}</div>' for point in profile.talking_points) if profile.talking_points else '<div class="talking-point">Nessun punto suggerito</div>'
        teaching_methods_html = "".join(f'<span class="badge badge-secondary">{m}</span>' for m in profile.priorities.teaching_methods) if profile.priorities.teaching_methods else '<span class="badge badge-secondary">Non specificato</span>'
        assessment_methods_html = "".join(f'<span class="badge badge-warning">{m}</span>' for m in profile.priorities.assessment_methods) if profile.priorities.assessment_methods else '<span class="badge badge-warning">Non specificato</span>'
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Profilo Pedagogico - {profile.docente or profile.corso}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: {main_color}; border-bottom: 3px solid {main_color}; padding-bottom: 10px; }}
        h2 {{ color: #333; margin-top: 25px; }}
        .header-info {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .header-info p {{ margin: 5px 0; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 15px; font-size: 0.85em; margin-right: 8px; margin-bottom: 5px; }}
        .badge-primary {{ background: {main_color}; color: white; }}
        .badge-secondary {{ background: #e0e0e0; color: #333; }}
        .badge-warning {{ background: #fff3e0; color: #e65100; }}
        .meter {{ height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .meter-fill {{ height: 100%; border-radius: 10px; }}
        .meter-label {{ display: flex; justify-content: space-between; font-size: 0.85em; color: #666; }}
        .insight-box {{ background: #e3f2fd; border-left: 4px solid #1976d2; padding: 15px; margin: 15px 0; }}
        .talking-point {{ background: #fff8e1; border-left: 4px solid #ffa000; padding: 10px 15px; margin: 10px 0; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .card {{ background: #fafafa; padding: 15px; border-radius: 8px; }}
        .card h3 {{ margin-top: 0; color: #555; font-size: 1em; }}
        .confidence {{ text-align: right; color: #999; font-size: 0.85em; margin-top: 20px; }}
    </style>
</head>
<body>
<div class="container">
    <h1>📋 Profilo Pedagogico</h1>
    
    <div class="header-info">
        <p><strong>👨‍🏫 Docente:</strong> {profile.docente or "Non specificato"}</p>
        <p><strong>📚 Corso:</strong> {profile.corso or "Non specificato"}</p>
        <p><strong>🏛️ Università:</strong> {profile.universita or "Non specificata"}</p>
        <p><strong>🎓 Classe:</strong> {profile.target.degree_class} - {profile.target.degree_program}</p>
    </div>
    
    <h2>🎯 Sintesi</h2>
    <p style="font-size: 1.1em; line-height: 1.6;">{profile.profile_summary or "Sintesi non disponibile"}</p>
    
    <h2>📐 Filosofia Didattica</h2>
    <div class="grid">
        <div class="card">
            <h3>Approccio</h3>
            <span class="badge badge-primary">{profile.philosophy.approach.value.replace('_', ' ').title()}</span>
            <span class="badge badge-secondary">{profile.philosophy.rigor_level.value.replace('_', ' ').title()}</span>
        </div>
        <div class="card">
            <h3>Orientamento</h3>
            <span class="badge badge-secondary">{profile.priorities.depth_breadth.value.replace('_', ' ').title()}</span>
        </div>
    </div>
    
    <div style="margin-top: 20px;">
        <p><strong>Enfasi sulle Applicazioni:</strong></p>
        <div class="meter-label"><span>Teorico</span><span>Applicativo</span></div>
        <div class="meter"><div class="meter-fill" style="width: {profile.philosophy.application_emphasis}%; background: linear-gradient(90deg, #3f51b5, #4caf50);"></div></div>
        
        <p><strong>Interdisciplinarità:</strong></p>
        <div class="meter-label"><span>Disciplinare</span><span>Interdisciplinare</span></div>
        <div class="meter"><div class="meter-fill" style="width: {profile.philosophy.interdisciplinarity}%; background: linear-gradient(90deg, #9e9e9e, #ff9800);"></div></div>
    </div>
    
    <h2>🛠️ Metodi</h2>
    <div class="grid">
        <div class="card">
            <h3>Didattica</h3>
            {teaching_methods_html}
        </div>
        <div class="card">
            <h3>Valutazione</h3>
            {assessment_methods_html}
        </div>
    </div>
    
    <h2>💡 Insight per il Promotore</h2>
    <div class="insight-box">
        <ul>
            {insights_html}
        </ul>
    </div>
    
    <h2>🗣️ Punti Chiave per la Conversazione</h2>
    {talking_points_html}
    
    <h2>🎯 Approccio Suggerito</h2>
    <p style="font-size: 1.05em; background: #e8f5e9; padding: 15px; border-radius: 8px;">
        {profile.suggested_approach or "Approccio standard"}
    </p>
    
    <p class="confidence">Confidence analisi: {profile.analysis_confidence*100:.0f}%</p>
</div>
</body>
</html>
"""
        return html
