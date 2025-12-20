"""
framework_comparator.py
Confronto framework generato vs esistente (formato Zanichelli)
"""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ModuleComparison:
    generated_name: str
    generated_concepts: int
    matched_name: Optional[str] = None
    matched_id: Optional[int] = None
    similarity: float = 0.0
    shared_concepts: list[str] = field(default_factory=list)
    only_in_generated: list[str] = field(default_factory=list)
    only_in_existing: list[str] = field(default_factory=list)
    status: str = "unmatched"  # matched, partial, new


@dataclass
class FrameworkComparison:
    generated_name: str
    existing_name: str
    n_generated: int = 0
    n_existing: int = 0
    n_matched: int = 0
    n_partial: int = 0
    n_new: int = 0
    overall_similarity: float = 0.0
    module_comparisons: list[ModuleComparison] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    existing_modules_not_found: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "generated_name": self.generated_name,
            "existing_name": self.existing_name,
            "statistics": {
                "n_generated_modules": self.n_generated,
                "n_existing_modules": self.n_existing,
                "n_matched": self.n_matched,
                "n_partial": self.n_partial,
                "n_new": self.n_new,
                "overall_similarity": round(self.overall_similarity * 100, 1)
            },
            "module_comparisons": [
                {
                    "generated": mc.generated_name,
                    "generated_concepts": mc.generated_concepts,
                    "matched_existing": mc.matched_name,
                    "matched_id": mc.matched_id,
                    "similarity": round(mc.similarity * 100, 1),
                    "status": mc.status,
                    "shared_concepts": mc.shared_concepts[:10],
                    "only_in_generated": mc.only_in_generated[:5],
                    "only_in_existing": mc.only_in_existing[:5]
                }
                for mc in self.module_comparisons
            ],
            "existing_modules_not_covered": self.existing_modules_not_found,
            "recommendations": self.recommendations
        }


class FrameworkComparator:
    """Confronta framework generato con formato Zanichelli."""
    
    def __init__(self, existing_path: Optional[Path] = None):
        self.existing = None
        self.existing_modules = []
        if existing_path:
            self.load_existing(existing_path)
    
    def load_existing(self, path: Path | str):
        """Carica framework esistente in formato Zanichelli."""
        with open(path, "r", encoding="utf-8") as f:
            self.existing = json.load(f)
        
        # Estrai i moduli dal formato Zanichelli
        if "syllabus_modules" in self.existing:
            self.existing_modules = self.existing["syllabus_modules"]
        elif "moduli" in self.existing:
            self.existing_modules = self.existing["moduli"]
        else:
            self.existing_modules = []
        
        # Estrai nome framework
        if "framework" in self.existing and "name" in self.existing["framework"]:
            self.existing_name = self.existing["framework"]["name"]
        else:
            self.existing_name = "Framework Esistente"
        
        print(f"Framework esistente caricato: {self.existing_name}")
        print(f"  Moduli trovati: {len(self.existing_modules)}")
    
    def _extract_concepts_from_existing(self, module: dict) -> set[str]:
        """Estrae concetti/keywords da un modulo del framework esistente."""
        concepts = set()
        
        # Nome del modulo
        if "name" in module:
            concepts.add(module["name"].lower())
        
        # Core contents
        if "core_contents" in module:
            for content in module["core_contents"]:
                # Aggiungi l'intero contenuto
                concepts.add(content.lower())
                # Estrai anche singole parole chiave
                words = content.lower().replace(",", " ").replace("/", " ").split()
                for word in words:
                    if len(word) > 3:
                        concepts.add(word)
        
        # Learning outcomes
        if "learning_outcomes" in module:
            for outcome in module["learning_outcomes"]:
                concepts.add(outcome.lower())
        
        # Argomenti (formato alternativo)
        if "argomenti" in module:
            for arg in module["argomenti"]:
                if isinstance(arg, str):
                    concepts.add(arg.lower())
                elif isinstance(arg, dict) and "nome" in arg:
                    concepts.add(arg["nome"].lower())
        
        # Keywords
        if "keywords" in module:
            for kw in module["keywords"]:
                concepts.add(kw.lower())
        
        return concepts
    
    def _extract_concepts_from_generated(self, module) -> set[str]:
        """Estrae concetti da un modulo generato."""
        concepts = set()
        
        # Nome modulo
        concepts.add(module.name.lower())
        
        # Concetti
        for c in module.concepts:
            concepts.add(c.canonical_name.lower())
            for v in c.variants:
                concepts.add(v.lower())
        
        return concepts
    
    def _calculate_similarity(self, set1: set[str], set2: set[str]) -> tuple[float, list[str], list[str], list[str]]:
        """Calcola similarità Jaccard e restituisce dettagli."""
        if not set1 or not set2:
            return 0.0, [], list(set1), list(set2)
        
        shared = set1 & set2
        only_1 = set1 - set2
        only_2 = set2 - set1
        
        # Jaccard
        union = set1 | set2
        similarity = len(shared) / len(union) if union else 0.0
        
        return similarity, list(shared), list(only_1), list(only_2)
    
    def _find_keyword_overlap(self, gen_concepts: set[str], ex_concepts: set[str]) -> float:
        """Calcola overlap basato su keyword matching parziale."""
        if not gen_concepts or not ex_concepts:
            return 0.0
        
        matches = 0
        total = len(gen_concepts)
        
        for gc in gen_concepts:
            gc_words = set(gc.split())
            for ec in ex_concepts:
                ec_words = set(ec.split())
                # Match se condividono parole significative
                common_words = gc_words & ec_words
                if common_words and any(len(w) > 3 for w in common_words):
                    matches += 1
                    break
                # Match parziale su contenimento
                if gc in ec or ec in gc:
                    matches += 0.5
                    break
        
        return matches / total if total > 0 else 0.0
    
    def compare(self, generated) -> FrameworkComparison:
        """Confronta framework generato con esistente."""
        if not self.existing:
            raise ValueError("Nessun framework esistente caricato")
        
        comp = FrameworkComparison(
            generated_name=generated.name,
            existing_name=self.existing_name,
            n_generated=len(generated.modules),
            n_existing=len(self.existing_modules)
        )
        
        # Track quali moduli esistenti sono stati matchati
        matched_existing_ids = set()
        
        # Per ogni modulo generato, trova il miglior match
        for gen_module in generated.modules:
            gen_concepts = self._extract_concepts_from_generated(gen_module)
            
            best_score = 0.0
            best_match = None
            best_shared = []
            best_only_gen = []
            best_only_ex = []
            
            for ex_module in self.existing_modules:
                ex_concepts = self._extract_concepts_from_existing(ex_module)
                
                # Calcola similarità Jaccard
                jaccard, shared, only_gen, only_ex = self._calculate_similarity(gen_concepts, ex_concepts)
                
                # Calcola anche overlap keyword (più flessibile)
                keyword_overlap = self._find_keyword_overlap(gen_concepts, ex_concepts)
                
                # Score combinato
                combined_score = (jaccard * 0.6) + (keyword_overlap * 0.4)
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_match = ex_module
                    best_shared = shared
                    best_only_gen = only_gen
                    best_only_ex = only_ex
            
            # Crea confronto modulo
            mc = ModuleComparison(
                generated_name=gen_module.name,
                generated_concepts=gen_module.n_concepts,
                similarity=best_score
            )
            
            if best_match and best_score > 0.05:  # Soglia minima 5%
                mc.matched_name = best_match.get("name", "")
                mc.matched_id = best_match.get("id")
                mc.shared_concepts = best_shared
                mc.only_in_generated = best_only_gen
                mc.only_in_existing = best_only_ex
                
                if best_score > 0.3:
                    mc.status = "matched"
                    comp.n_matched += 1
                    if mc.matched_id:
                        matched_existing_ids.add(mc.matched_id)
                else:
                    mc.status = "partial"
                    comp.n_partial += 1
            else:
                mc.status = "new"
                comp.n_new += 1
                mc.only_in_generated = list(gen_concepts)[:10]
            
            comp.module_comparisons.append(mc)
        
        # Trova moduli esistenti non coperti
        for ex_module in self.existing_modules:
            ex_id = ex_module.get("id")
            if ex_id not in matched_existing_ids:
                comp.existing_modules_not_found.append(
                    f"{ex_id}. {ex_module.get('name', 'Senza nome')}"
                )
        
        # Calcola similarità globale
        if comp.module_comparisons:
            comp.overall_similarity = sum(
                mc.similarity for mc in comp.module_comparisons
            ) / len(comp.module_comparisons)
        
        # Genera raccomandazioni
        comp.recommendations = self._generate_recommendations(comp)
        
        return comp
    
    def _generate_recommendations(self, comp: FrameworkComparison) -> list[str]:
        """Genera raccomandazioni basate sul confronto."""
        recs = []
        
        # Similarità globale
        sim_pct = comp.overall_similarity * 100
        
        if sim_pct < 20:
            recs.append(
                f"Similarità bassa ({sim_pct:.0f}%): Il framework empirico L-13 ha una struttura "
                "significativamente diversa dal framework multidisciplinare. Questo è normale "
                "perché il framework esistente include moduli (Polimeri, Organometallica) poco "
                "presenti nei corsi L-13 Biologia."
            )
        elif sim_pct < 50:
            recs.append(
                f"Similarità moderata ({sim_pct:.0f}%): Buona sovrapposizione sui moduli core, "
                "differenze sui moduli specialistici."
            )
        else:
            recs.append(
                f"Similarità alta ({sim_pct:.0f}%): Il framework empirico conferma la struttura esistente."
            )
        
        # Moduli non coperti
        if comp.existing_modules_not_found:
            not_covered = ", ".join(comp.existing_modules_not_found[:5])
            recs.append(
                f"Moduli del framework esistente poco presenti nei syllabus L-13: {not_covered}. "
                "Questi moduli potrebbero essere più rilevanti per altri indirizzi (Farmacia, CTF)."
            )
        
        # Moduli nuovi
        new_modules = [mc.generated_name for mc in comp.module_comparisons if mc.status == "new"]
        if new_modules:
            recs.append(
                f"Il framework empirico ha identificato {len(new_modules)} raggruppamenti "
                "non presenti nel framework esistente. Valuta se integrarli."
            )
        
        # Match buoni
        good_matches = [mc for mc in comp.module_comparisons if mc.status == "matched"]
        if good_matches:
            matched_names = ", ".join([mc.matched_name for mc in good_matches[:3]])
            recs.append(
                f"Buona corrispondenza per: {matched_names}. "
                "Questi moduli sono confermati dall'analisi empirica."
            )
        
        return recs
