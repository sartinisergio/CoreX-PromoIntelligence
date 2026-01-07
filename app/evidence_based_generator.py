"""
CoreX - Evidence-Based Framework Generator v1.1
Genera framework dai programmi reali senza riferimento a framework ideali.
I moduli emergono naturalmente dall'analisi dei contenuti.
Distingue moduli CORE, TRASVERSALE e SPECIFICI.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class EvidenceBasedFrameworkGenerator:
    """
    Genera un framework basato esclusivamente sui dati reali estratti dai programmi.
    Approccio bottom-up: i moduli emergono dai contenuti, non da strutture predefinite.
    """
    
    # Soglie default AGGIORNATE (v1.1)
    DEFAULT_CORE_THRESHOLD = 60.0       # % classi per considerare un modulo CORE
    DEFAULT_SPECIFIC_THRESHOLD = 40.0   # Sotto questa % è SPECIFICO
    
    def __init__(
        self, 
        cache_dir: Path = None,
        core_threshold: float = None,
        specific_threshold: float = None
    ):
        self.cache_dir = cache_dir or Path("cache/evidence_based_frameworks")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.core_threshold = core_threshold if core_threshold is not None else self.DEFAULT_CORE_THRESHOLD
        self.specific_threshold = specific_threshold if specific_threshold is not None else self.DEFAULT_SPECIFIC_THRESHOLD
    
    def generate(
        self,
        concepts_by_class: Dict[str, List[Dict]],
        materia: str,
        provider_id: str = "openai",
        model: str = "gpt-4o-mini",
        force_refresh: bool = False
    ) -> Dict:
        """
        Genera un Evidence-Based Framework dai concetti estratti.
        
        Args:
            concepts_by_class: Dict con {classe: [lista concetti con frequenze]}
                Ogni concetto è {"name": "...", "frequency": X, ...}
            materia: Nome della materia
            provider_id: Provider LLM da usare
            model: Modello LLM
            force_refresh: Se True, ignora la cache
            
        Returns:
            Dict con il framework generato, struttura compatibile con il resto di CoreX
        """
        
        # Controlla cache
        cache_key = self._generate_cache_key(concepts_by_class, materia, model)
        if not force_refresh:
            cached = self._get_from_cache(cache_key)
            if cached:
                print(f"[CACHE HIT] Evidence-Based Framework trovato in cache: {cache_key}")
                return cached
        
        # Prepara dati per LLM
        all_concepts = self._aggregate_concepts(concepts_by_class)
        classes = list(concepts_by_class.keys())
        
        # Genera framework tramite LLM
        print(f"[INFO] Generazione Evidence-Based Framework per {materia}...")
        print(f"[INFO] Classi analizzate: {', '.join(classes)}")
        print(f"[INFO] Concetti totali: {len(all_concepts)}")
        
        llm_result = self._call_llm_for_clustering(
            all_concepts, 
            concepts_by_class,
            materia, 
            classes,
            provider_id, 
            model
        )
        
        if not llm_result:
            return {"error": "Errore nella generazione del framework", "success": False}
        
        # Arricchisci con classificazione CORE/TRASVERSALE/SPECIFICO
        framework = self._enrich_with_class_analysis(
            llm_result, 
            concepts_by_class, 
            classes
        )
        
        # Aggiungi metadata
        framework["meta"] = {
            "type": "evidence_based",
            "name": f"Evidence-Based Framework - {materia}",
            "materia": materia,
            "classes_analyzed": classes,
            "n_classes": len(classes),
            "generated_at": datetime.now().isoformat(),
            "generator_version": "1.1",
            "thresholds": {
                "core": self.core_threshold,
                "specific": self.specific_threshold
            }
        }
        
        framework["summary"] = {
            "n_modules": len(framework.get("modules", [])),
            "n_core_modules": len([m for m in framework.get("modules", []) if m.get("is_core")]),
            "n_transversal_modules": len([m for m in framework.get("modules", []) if m.get("is_transversal")]),
            "n_specific_modules": len([m for m in framework.get("modules", []) if m.get("is_specific")]),
            "total_concepts_analyzed": len(all_concepts)
        }
        
        # Salva in cache
        self._save_to_cache(cache_key, framework)
        
        return framework
    
    def _aggregate_concepts(self, concepts_by_class: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Aggrega i concetti da tutte le classi, calcolando frequenza globale.
        """
        concept_stats = defaultdict(lambda: {
            "total_frequency": 0,
            "class_count": 0,
            "classes": [],
            "max_frequency": 0
        })
        
        for classe, concepts in concepts_by_class.items():
            for concept in concepts:
                name = concept.get("name", "").lower().strip()
                if not name:
                    continue
                
                freq = concept.get("frequency", 0)
                concept_stats[name]["total_frequency"] += freq
                concept_stats[name]["class_count"] += 1
                concept_stats[name]["classes"].append(classe)
                concept_stats[name]["max_frequency"] = max(
                    concept_stats[name]["max_frequency"], 
                    freq
                )
        
        # Converti in lista
        aggregated = []
        n_classes = len(concepts_by_class)
        
        for name, stats in concept_stats.items():
            aggregated.append({
                "name": name,
                "avg_frequency": round(stats["total_frequency"] / stats["class_count"], 1),
                "max_frequency": stats["max_frequency"],
                "class_coverage": round(stats["class_count"] / n_classes * 100, 1),
                "classes": stats["classes"],
                "n_classes": stats["class_count"]
            })
        
        # Ordina per frequenza media
        aggregated.sort(key=lambda x: x["avg_frequency"], reverse=True)
        
        return aggregated
    
    def _call_llm_for_clustering(
        self,
        all_concepts: List[Dict],
        concepts_by_class: Dict[str, List[Dict]],
        materia: str,
        classes: List[str],
        provider_id: str,
        model: str
    ) -> Optional[Dict]:
        """
        Chiama LLM per clusterizzare i concetti in moduli tematici.
        Il numero di moduli emerge naturalmente dall'analisi.
        """
        try:
            from app.llm_provider import get_llm_client
        except ImportError:
            print("[ERROR] LLM provider non disponibile")
            return None
        
        # Prepara concetti per il prompt (top 150 per non superare limiti token)
        top_concepts = all_concepts[:150]
        
        # Formatta concetti con info sulla distribuzione per classe
        concepts_formatted = []
        for c in top_concepts:
            concepts_formatted.append({
                "concetto": c["name"],
                "frequenza_media": c["avg_frequency"],
                "presente_in_classi": f"{c['n_classes']}/{len(classes)}",
                "classi": c["classes"][:5]  # Max 5 per brevità
            })
        
        prompt = f"""Sei un esperto di didattica universitaria di {materia}.

Hai analizzato {len(classes)} classi di laurea diverse e estratto i concetti che i docenti effettivamente insegnano.

CLASSI ANALIZZATE:
{json.dumps(classes, ensure_ascii=False)}

CONCETTI ESTRATTI (ordinati per frequenza):
{json.dumps(concepts_formatted, indent=2, ensure_ascii=False)}

COMPITO:
Raggruppa questi concetti in MODULI TEMATICI coerenti.

REGOLE IMPORTANTI:
1. Il NUMERO DI MODULI deve emergere naturalmente dalla struttura dei contenuti
   - Non forzare un numero predefinito
   - Crea tanti moduli quanti ne servono per raggruppare coerentemente i concetti
   - Tipicamente saranno tra 6 e 15, ma dipende dalla materia

2. Ogni modulo deve avere:
   - Un nome chiaro e descrittivo
   - I concetti che lo compongono (core_contents)
   - Una stima di quanto è presente nei programmi (avg_frequency)

3. Considera la DISTRIBUZIONE PER CLASSE:
   - Alcuni concetti sono universali (presenti in tutte le classi)
   - Altri sono specifici di alcune classi
   - Questa informazione è nel campo "presente_in_classi"

4. Sii FEDELE AI DATI:
   - Non inventare moduli che non emergono dai concetti
   - Se un tema ha pochi concetti, può essere un modulo piccolo
   - Se un tema è molto ricco, può essere un modulo grande

Rispondi SOLO con JSON valido:
{{
    "modules": [
        {{
            "id": 1,
            "name": "Nome del modulo",
            "core_contents": ["concetto1", "concetto2", "concetto3"],
            "avg_frequency": 75.5,
            "description": "Breve descrizione del modulo (1 frase)"
        }}
    ],
    "clustering_notes": "Breve spiegazione delle scelte di raggruppamento"
}}"""

        try:
            client = get_llm_client(provider_id)
            
            call_params = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Sei un esperto di curriculum design universitario. Analizza i dati e raggruppa i concetti in moduli tematici coerenti. Rispondi SOLO con JSON valido."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.0,
                "max_tokens": 4000
            }
            
            # Seed per determinismo (solo OpenAI)
            if provider_id == "openai":
                call_params["seed"] = 42
            
            response = client.chat.completions.create(**call_params)
            response_text = response.choices[0].message.content.strip()
            
            # Pulizia risposta
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
            print(f"[INFO] LLM ha generato {len(result.get('modules', []))} moduli")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Errore parsing JSON risposta LLM: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Errore chiamata LLM: {e}")
            return None
    
    def _enrich_with_class_analysis(
        self,
        llm_result: Dict,
        concepts_by_class: Dict[str, List[Dict]],
        classes: List[str]
    ) -> Dict:
        """
        Arricchisce il framework con analisi per classe.
        Determina quali moduli sono CORE, TRASVERSALI o SPECIFICI.
        
        Logica classificazione (v1.1):
        - CORE: presente in >= core_threshold% delle classi (default 60%)
        - TRASVERSALE: presente tra specific_threshold% e core_threshold%
        - SPECIFICO: presente in < specific_threshold% delle classi (default 40%)
        """
        modules = llm_result.get("modules", [])
        n_classes = len(classes)
        
        # Per ogni modulo, calcola presenza per classe
        enriched_modules = []
        
        for module in modules:
            module_contents = set(c.lower() for c in module.get("core_contents", []))
            
            # Calcola copertura per ogni classe
            coverage_by_class = {}
            concepts_by_class_for_module = {}
            
            for classe in classes:
                class_concepts = concepts_by_class.get(classe, [])
                class_concept_names = set(c.get("name", "").lower() for c in class_concepts)
                
                # Quanti contenuti del modulo sono presenti in questa classe
                matched = module_contents & class_concept_names
                coverage = (len(matched) / len(module_contents) * 100) if module_contents else 0
                
                coverage_by_class[classe] = round(coverage, 1)
                concepts_by_class_for_module[classe] = list(matched)
            
            # Determina classificazione
            coverages = list(coverage_by_class.values())
            avg_coverage = sum(coverages) / len(coverages) if coverages else 0
            min_coverage = min(coverages) if coverages else 0
            max_coverage = max(coverages) if coverages else 0
            
            # Conta in quante classi è presente significativamente (>30%)
            classes_with_presence = sum(1 for c in coverages if c >= 30)
            presence_percentage = (classes_with_presence / n_classes * 100)
            
            # Classificazione a 3 livelli
            is_core = presence_percentage >= self.core_threshold
            is_specific = presence_percentage < self.specific_threshold
            is_transversal = (not is_core) and (not is_specific)
            
            # Determina categoria testuale
            if is_core:
                category = "CORE"
            elif is_transversal:
                category = "TRASVERSALE"
            else:
                category = "SPECIFICO"
            
            # Identifica per quali classi è distintivo (se specifico o trasversale)
            distinctive_for = []
            if not is_core:
                for classe, cov in coverage_by_class.items():
                    if cov >= 50:  # Alta presenza in questa classe
                        distinctive_for.append(classe)
            
            enriched_module = {
                "id": module.get("id"),
                "name": module.get("name"),
                "core_contents": module.get("core_contents", []),
                "description": module.get("description", ""),
                "avg_frequency": module.get("avg_frequency", 0),
                "coverage_by_class": coverage_by_class,
                "concepts_by_class": concepts_by_class_for_module,
                "category": category,
                "is_core": is_core,
                "is_transversal": is_transversal,
                "is_specific": is_specific,
                "distinctive_for": distinctive_for,
                "stats": {
                    "avg_coverage": round(avg_coverage, 1),
                    "min_coverage": round(min_coverage, 1),
                    "max_coverage": round(max_coverage, 1),
                    "presence_in_classes": f"{classes_with_presence}/{n_classes}",
                    "presence_percentage": round(presence_percentage, 1)
                }
            }
            
            enriched_modules.append(enriched_module)
        
        # Ordina: prima CORE, poi TRASVERSALE, poi SPECIFICO, poi per frequenza
        category_order = {"CORE": 0, "TRASVERSALE": 1, "SPECIFICO": 2}
        enriched_modules.sort(key=lambda x: (category_order.get(x["category"], 3), -x["avg_frequency"]))
        
        # Ri-numera gli ID
        for i, mod in enumerate(enriched_modules, 1):
            mod["id"] = i
        
        return {
            "modules": enriched_modules,
            "clustering_notes": llm_result.get("clustering_notes", ""),
            "framework": {
                "name": "Evidence-Based Framework",
                "type": "evidence_based",
                "classes_analyzed": classes
            }
        }
    
    def _generate_cache_key(
        self, 
        concepts_by_class: Dict[str, List[Dict]], 
        materia: str, 
        model: str
    ) -> str:
        """Genera chiave univoca per la cache."""
        signature = {
            "materia": materia,
            "model": model,
            "classes": sorted(concepts_by_class.keys()),
            "n_concepts_per_class": {
                k: len(v) for k, v in concepts_by_class.items()
            },
            "version": "1.1"
        }
        content = json.dumps(signature, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:20]
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Recupera framework dalla cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("framework")
            except Exception as e:
                print(f"[WARN] Errore lettura cache: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, framework: Dict) -> bool:
        """Salva framework in cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            cache_entry = {
                "cache_key": cache_key,
                "cached_at": datetime.now().isoformat(),
                "framework": framework
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f, indent=2, ensure_ascii=False)
            print(f"[CACHE] Evidence-Based Framework salvato: {cache_key}")
            return True
        except Exception as e:
            print(f"[ERROR] Errore salvataggio cache: {e}")
            return False
    
    def clear_cache(self) -> int:
        """Svuota la cache. Ritorna numero di file rimossi."""
        count = 0
        for f in self.cache_dir.glob("*.json"):
            try:
                f.unlink()
                count += 1
            except:
                pass
        return count
    
    def update_thresholds(self, core_threshold: float = None, specific_threshold: float = None):
        """Aggiorna le soglie di classificazione."""
        if core_threshold is not None:
            self.core_threshold = core_threshold
        if specific_threshold is not None:
            self.specific_threshold = specific_threshold


# =============================================================================
# FUNZIONI HELPER PER INTEGRAZIONE
# =============================================================================

def generate_evidence_based_framework(
    concepts_by_class: Dict[str, List[Dict]],
    materia: str,
    provider_id: str = "openai",
    model: str = "gpt-4o-mini",
    core_threshold: float = 60.0,
    specific_threshold: float = 40.0,
    force_refresh: bool = False
) -> Dict:
    """
    Funzione helper per generare un Evidence-Based Framework.
    Può essere chiamata direttamente senza istanziare la classe.
    
    Args:
        concepts_by_class: {classe: [lista concetti]}
        materia: Nome materia
        provider_id: Provider LLM
        model: Modello LLM
        core_threshold: Soglia % per moduli CORE (default 60%)
        specific_threshold: Soglia % per moduli SPECIFICI (default 40%)
        force_refresh: Ignora cache se True
        
    Returns:
        Dict con il framework generato
    """
    generator = EvidenceBasedFrameworkGenerator(
        core_threshold=core_threshold,
        specific_threshold=specific_threshold
    )
    
    return generator.generate(
        concepts_by_class=concepts_by_class,
        materia=materia,
        provider_id=provider_id,
        model=model,
        force_refresh=force_refresh
    )
