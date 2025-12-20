"""
concept_extractor.py
Estrazione concetti da testi syllabus (versione senza spaCy)
"""

import re
import hashlib
from collections import defaultdict
from typing import Optional

from .config import MIN_CONCEPT_LENGTH, THRESHOLD_CORE, THRESHOLD_COMUNE
from .chemistry_vocab import ChemistryVocabulary
from .models.concept import RawConcept, Concept, ConceptCollection, EntityType


class ConceptExtractor:
    """Estrattore di concetti basato su pattern matching."""
    
    def __init__(self, vocabulary: Optional[ChemistryVocabulary] = None):
        self.vocab = vocabulary or ChemistryVocabulary()
        self._id_counter = 0
        print("Usando estrazione basata su pattern matching")
    
    def _generate_id(self, text: str) -> str:
        self._id_counter += 1
        hash_part = hashlib.md5(text.encode()).hexdigest()[:8]
        return f"concept_{self._id_counter:05d}_{hash_part}"
    
    def preprocess_text(self, text: str) -> str:
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    
    def extract_program_section(self, text: str) -> str:
        patterns = [
            r"(?:PROGRAMMA|CONTENUTI|SYLLABUS)[:\s]*\n",
            r"(?:Contenuti|Programma)[:\s]*\n",
        ]
        end_patterns = [
            r"\n(?:MATERIALE|TESTI|BIBLIOGRAFIA)",
            r"\n(?:MODALITÀ|METODI)",
            r"\n(?:RISULTATI\s+DI\s+APPRENDIMENTO)",
        ]
        
        start_pos = 0
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                start_pos = match.end()
                break
        
        end_pos = len(text)
        remaining = text[start_pos:]
        for p in end_patterns:
            match = re.search(p, remaining, re.IGNORECASE)
            if match:
                end_pos = start_pos + match.start()
                break
        
        return text[start_pos:end_pos].strip()
    
    def extract_raw_concepts(self, text: str, syllabus_id: str) -> list[RawConcept]:
        raw_concepts = []
        
        # 1. Pattern matching per entità chimiche note
        entities = self.vocab.extract_entities(text)
        for match_text, entity_type, start, end in entities:
            ctx_start = max(0, text.rfind(".", 0, start) + 1)
            ctx_end = text.find(".", end)
            if ctx_end == -1:
                ctx_end = min(len(text), end + 100)
            
            etype = EntityType.GENERIC
            if entity_type in [e.value for e in EntityType]:
                etype = EntityType(entity_type)
            
            raw_concepts.append(RawConcept(
                text=match_text,
                source_syllabus_id=syllabus_id,
                position_in_text=start,
                context=text[ctx_start:ctx_end].strip(),
                entity_type=etype,
                confidence=0.9
            ))
        
        # 2. Estrazione basata su keywords chimiche
        chemistry_keywords = [
            r'\b(alcani|alcheni|alchini|cicloalcani|aromatici|benzene)\b',
            r'\b(alcoli|fenoli|eteri|epossidi|tioli|solfuri)\b',
            r'\b(aldeidi|chetoni|acidi\s+carbossilici)\b',
            r'\b(esteri|ammidi|anidridi|alogenuri\s+acilici)\b',
            r'\b(ammine|nitrili)\b',
            r'\b(stereochimica|chiralit[aà]|enantiomeri|diastereoisomeri)\b',
            r'\b(configurazione|proiezioni?\s+di\s+Fischer)\b',
            r'\b(isomeria|stereoisomeri|racemo|racemizzazione)\b',
            r'\b(SN1|SN2|E1|E2|SEAr)\b',
            r'\b(sostituzione\s+nucleofila|eliminazione)\b',
            r'\b(addizione\s+elettrofila|addizione\s+nucleofila)\b',
            r'\b(ossidazione|riduzione|idrogenazione)\b',
            r'\b(esterificazione|saponificazione|idrolisi)\b',
            r'\b(carboidrati|monosaccaridi|disaccaridi|polisaccaridi)\b',
            r'\b(amminoacidi|proteine|peptidi|legame\s+peptidico)\b',
            r'\b(lipidi|trigliceridi|fosfolipidi|steroidi)\b',
            r'\b(nucleotidi|nucleosidi|acidi\s+nucleici|DNA|RNA)\b',
            r'\b(glucosio|fruttosio|saccarosio|maltosio|lattosio)\b',
            r'\b(gruppo\s+funzionale|gruppo\s+carbonilico|gruppo\s+carbossilico)\b',
            r'\b(legame\s+\w+|ibridazione|risonanza|aromaticit[aà])\b',
            r'\b(acidit[aà]|basicit[aà]|pKa|pH|punto\s+isoelettrico)\b',
            r'\b(nucleofilo|elettrofilo|carbocatione|carbanione)\b',
            r'\b(tautomeria|equilibrio\s+cheto-enolico)\b',
            r'\b(Markovnikov|Zaitsev|Fischer|Friedel|Crafts|Grignard)\b',
            r'\b(condensazione\s+aldolica|condensazione\s+di\s+Claisen)\b',
            r'\b(mutarotazione|anomeri|legame\s+glicosidico)\b',
        ]
        
        for pattern in chemistry_keywords:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                match_text = match.group()
                start = match.start()
                
                already_found = any(
                    abs(rc.position_in_text - start) < 5 
                    for rc in raw_concepts
                )
                if already_found:
                    continue
                
                ctx_start = max(0, text.rfind(".", 0, start) + 1)
                ctx_end = text.find(".", start + len(match_text))
                if ctx_end == -1:
                    ctx_end = min(len(text), start + 150)
                
                raw_concepts.append(RawConcept(
                    text=match_text,
                    source_syllabus_id=syllabus_id,
                    position_in_text=start,
                    context=text[ctx_start:ctx_end].strip(),
                    entity_type=EntityType.GENERIC,
                    confidence=0.8
                ))
        
        return raw_concepts
    
    def normalize_concepts(self, raw_concepts: list[RawConcept]) -> dict[str, list[RawConcept]]:
        grouped = defaultdict(list)
        
        for raw in raw_concepts:
            canonical = self.vocab.normalize(raw.text)
            if len(canonical) < MIN_CONCEPT_LENGTH:
                continue
            if self.vocab.is_stopword(canonical):
                continue
            grouped[canonical].append(raw)
        
        return dict(grouped)
    
    def build_concept_collection(
        self, grouped: dict[str, list[RawConcept]], 
        total_syllabus: int,
        name: str = "Chimica Organica L-13"
    ) -> ConceptCollection:
        collection = ConceptCollection(
            id=self._generate_id(name),
            name=name,
            total_syllabus_analyzed=total_syllabus
        )
        
        for canonical_name, raw_list in grouped.items():
            entity_types = [r.entity_type for r in raw_list]
            most_common = max(set(entity_types), key=entity_types.count)
            
            variants = list(set(r.text for r in raw_list if r.text.lower() != canonical_name.lower()))
            source_ids = list(set(r.source_syllabus_id for r in raw_list))
            
            concept = Concept(
                id=self._generate_id(canonical_name),
                canonical_name=canonical_name,
                variants=variants,
                source_syllabus_ids=source_ids,
                frequency_absolute=len(source_ids),
                entity_type=most_common
            )
            concept.compute_classification(total_syllabus, THRESHOLD_CORE, THRESHOLD_COMUNE)
            collection.add_concept(concept)
        
        collection.compute_statistics()
        collection.total_raw_concepts_extracted = sum(len(v) for v in grouped.values())
        
        return collection
    
    def extract_from_syllabus(self, text: str, syllabus_id: str, extract_program_only: bool = True) -> list[RawConcept]:
        cleaned = self.preprocess_text(text)
        
        if extract_program_only:
            program = self.extract_program_section(cleaned)
            if len(program) < 100:
                program = cleaned
        else:
            program = cleaned
        
        return self.extract_raw_concepts(program, syllabus_id)
    
    def process_multiple_syllabus(self, syllabus_texts: dict[str, str], name: str = "Chimica Organica L-13") -> ConceptCollection:
        all_raw = []
        
        print(f"Elaborazione {len(syllabus_texts)} syllabus...")
        for i, (sid, text) in enumerate(syllabus_texts.items(), 1):
            raw = self.extract_from_syllabus(text, sid)
            all_raw.extend(raw)
            if i % 10 == 0:
                print(f"  Elaborati {i}/{len(syllabus_texts)} syllabus...")
        
        print(f"Concetti grezzi estratti: {len(all_raw)}")
        grouped = self.normalize_concepts(all_raw)
        print(f"Concetti unici: {len(grouped)}")
        
        return self.build_concept_collection(grouped, len(syllabus_texts), name)


def extract_concepts_from_texts(texts: dict[str, str], name: str = "Chimica Organica L-13") -> ConceptCollection:
    extractor = ConceptExtractor()
    return extractor.process_multiple_syllabus(texts, name)
