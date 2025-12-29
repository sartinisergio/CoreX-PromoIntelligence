"""
concept_extractor.py
Estrazione concetti da testi syllabus con LLM (versione universale multi-materia)
"""

import re
import json
import hashlib
import os
from collections import defaultdict
from typing import Optional, List, Dict, Tuple
import openai

from .config import MIN_CONCEPT_LENGTH, THRESHOLD_CORE, THRESHOLD_COMUNE
from .models.concept import RawConcept, Concept, ConceptCollection, EntityType


class ConceptExtractor:
    """Estrattore di concetti universale basato su LLM."""
    
    def __init__(self, use_llm: bool = True, materia: str = ""):
        self._id_counter = 0
        self.use_llm = use_llm
        self.materia = materia
        self.client = None
        
        # Inizializza client OpenAI se richiesto
        if use_llm:
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
                print(f"[OK] ConceptExtractor con LLM inizializzato per: {materia or 'materia generica'}")
            else:
                print("[WARN] API Key OpenAI non trovata - uso fallback pattern matching")
                self.use_llm = False
        
        if not self.use_llm:
            print("[INFO] Usando estrazione basata su pattern matching (modalità fallback)")
    
    def _generate_id(self, text: str) -> str:
        self._id_counter += 1
        hash_part = hashlib.md5(text.encode()).hexdigest()[:8]
        return f"concept_{self._id_counter:05d}_{hash_part}"
    
    def preprocess_text(self, text: str) -> str:
        """Pulisce il testo"""
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    
    def extract_program_section(self, text: str) -> str:
        """Estrae la sezione programma/contenuti dal testo"""
        patterns = [
            r"(?:PROGRAMMA|CONTENUTI|SYLLABUS|CONTENUTI\s+SPECIFICI)[:\s]*\n",
            r"(?:Contenuti|Programma|Argomenti)[:\s]*\n",
        ]
        end_patterns = [
            r"\n(?:MATERIALE|TESTI|BIBLIOGRAFIA|TEXTBOOK)",
            r"\n(?:MODALITÀ|METODI|METHODS)",
            r"\n(?:RISULTATI\s+DI\s+APPRENDIMENTO)",
            r"\n(?:PREREQUISITI|PREREQUISITES)",
            r"\n(?:English)\s*\n",  # Inizio sezione inglese
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
        
        section = text[start_pos:end_pos].strip()
        
        # Se la sezione è troppo corta, usa tutto il testo
        if len(section) < 200:
            return text[:5000]  # Limita a 5000 caratteri
        
        return section[:5000]  # Limita a 5000 caratteri per l'LLM
    
    # =========================================================
    # ESTRAZIONE CON LLM - CUORE DEL SISTEMA
    # =========================================================
    
    def extract_concepts_with_llm(self, text: str, syllabus_id: str) -> List[RawConcept]:
        """Estrae concetti usando LLM - funziona per qualsiasi materia"""
        
        if not self.client:
            return self._extract_concepts_fallback(text, syllabus_id)
        
        # Determina la materia dal contesto se non specificata
        materia_context = self.materia if self.materia else "questa disciplina accademica"
        
        prompt = f"""Analizza questo programma universitario di {materia_context} ed estrai TUTTI i concetti chiave, gli argomenti e i temi trattati.

TESTO DEL PROGRAMMA:
{text}

ISTRUZIONI:
1. Estrai ogni concetto, argomento o tema specifico menzionato
2. Includi sia concetti generali che specifici
3. Normalizza i nomi (es. "tessuto epiteliale" non "tessuti epiteliali")
4. Escludi parole generiche come "introduzione", "cenni", "approfondimenti"
5. Ogni concetto deve essere una stringa di 2-5 parole massimo

Rispondi SOLO con un array JSON di stringhe, esempio:
["concetto 1", "concetto 2", "concetto 3"]

CONCETTI ESTRATTI:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Sei un esperto accademico. Estrai concetti chiave da programmi universitari. Rispondi SOLO con JSON valido."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Pulisci la risposta
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            concepts_list = json.loads(response_text)
            
            if not isinstance(concepts_list, list):
                print(f"[WARN] Risposta LLM non è una lista per {syllabus_id}")
                return self._extract_concepts_fallback(text, syllabus_id)
            
            # Converti in RawConcept
            raw_concepts = []
            for i, concept_text in enumerate(concepts_list):
                if not isinstance(concept_text, str):
                    continue
                concept_text = concept_text.strip()
                if len(concept_text) < 3:
                    continue
                
                raw_concepts.append(RawConcept(
                    text=concept_text,
                    source_syllabus_id=syllabus_id,
                    position_in_text=i,
                    context="",
                    entity_type=EntityType.GENERIC,
                    confidence=0.9
                ))
            
            return raw_concepts
            
        except json.JSONDecodeError as e:
            print(f"[WARN] JSON non valido per {syllabus_id}: {e}")
            return self._extract_concepts_fallback(text, syllabus_id)
        except Exception as e:
            print(f"[ERR] Errore LLM per {syllabus_id}: {e}")
            return self._extract_concepts_fallback(text, syllabus_id)
    
    # =========================================================
    # FALLBACK - Pattern Matching Generico
    # =========================================================
    
    def _extract_concepts_fallback(self, text: str, syllabus_id: str) -> List[RawConcept]:
        """Fallback: estrazione basata su pattern matching generico"""
        raw_concepts = []
        
        # Pattern generici per qualsiasi materia accademica
        # Cerca frasi dopo ":", dopo elenchi puntati, titoli in maiuscolo, ecc.
        
        patterns = [
            # Elementi dopo due punti o punto e virgola
            r'[:\-]\s*([A-Z][a-zàèéìòù]+(?:\s+[a-zàèéìòù]+){0,4})',
            # Elementi in elenchi (dopo trattino o pallino)
            r'(?:^|\n)\s*[\-•]\s*([A-Z][a-zàèéìòù]+(?:\s+[a-zàèéìòù]+){0,4})',
            # Frasi che iniziano con maiuscola dopo punto
            r'\.\s+([A-Z][a-zàèéìòù]+(?:\s+[a-zàèéìòù]+){1,4})',
            # Titoli in MAIUSCOLO
            r'\n([A-Z]{2,}(?:\s+[A-Z]{2,}){0,3})\s*\n',
            # Pattern "Il/La/I/Le/Gli + sostantivo"
            r'\b((?:Il|La|I|Le|Gli|Lo)\s+[a-zàèéìòù]+(?:\s+[a-zàèéìòù]+){0,3})\b',
        ]
        
        seen = set()
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                concept_text = match.group(1).strip()
                
                # Normalizza
                concept_text = re.sub(r'\s+', ' ', concept_text)
                concept_lower = concept_text.lower()
                
                # Filtri
                if len(concept_text) < 4:
                    continue
                if len(concept_text) > 60:
                    continue
                if concept_lower in seen:
                    continue
                
                # Escludi parole troppo generiche
                stopwords = {
                    'introduzione', 'cenni', 'approfondimenti', 'elementi', 'aspetti',
                    'concetti', 'nozioni', 'fondamenti', 'principi', 'basi',
                    'corso', 'esame', 'lezione', 'studio', 'analisi', 'metodi',
                    'obiettivi', 'prerequisiti', 'bibliografia', 'testi', 'materiale'
                }
                if concept_lower in stopwords:
                    continue
                
                seen.add(concept_lower)
                
                raw_concepts.append(RawConcept(
                    text=concept_text,
                    source_syllabus_id=syllabus_id,
                    position_in_text=match.start(),
                    context="",
                    entity_type=EntityType.GENERIC,
                    confidence=0.6
                ))
        
        return raw_concepts
    
    # =========================================================
    # NORMALIZZAZIONE E AGGREGAZIONE
    # =========================================================
    
    def normalize_concept(self, text: str) -> str:
        """Normalizza un concetto"""
        # Lowercase
        text = text.lower().strip()
        # Rimuovi articoli iniziali
        text = re.sub(r'^(il|lo|la|i|gli|le|un|uno|una)\s+', '', text)
        # Rimuovi punteggiatura finale
        text = re.sub(r'[.,;:!?]+$', '', text)
        # Normalizza spazi
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def normalize_concepts(self, raw_concepts: List[RawConcept]) -> Dict[str, List[RawConcept]]:
        """Raggruppa concetti simili"""
        grouped = defaultdict(list)
        
        for raw in raw_concepts:
            canonical = self.normalize_concept(raw.text)
            if len(canonical) < MIN_CONCEPT_LENGTH:
                continue
            grouped[canonical].append(raw)
        
        return dict(grouped)
    
    def build_concept_collection(
        self, 
        grouped: Dict[str, List[RawConcept]], 
        total_syllabus: int,
        name: str = "Analisi"
    ) -> ConceptCollection:
        """Costruisce la collection di concetti"""
        collection = ConceptCollection(
            id=self._generate_id(name),
            name=name,
            total_syllabus_analyzed=total_syllabus
        )
        
        for canonical_name, raw_list in grouped.items():
            entity_types = [r.entity_type for r in raw_list]
            most_common = max(set(entity_types), key=entity_types.count)
            
            variants = list(set(
                r.text for r in raw_list 
                if r.text.lower() != canonical_name.lower()
            ))
            source_ids = list(set(r.source_syllabus_id for r in raw_list))
            
            concept = Concept(
                id=self._generate_id(canonical_name),
                canonical_name=canonical_name,
                variants=variants[:5],  # Limita varianti
                source_syllabus_ids=source_ids,
                frequency_absolute=len(source_ids),
                entity_type=most_common
            )
            concept.compute_classification(total_syllabus, THRESHOLD_CORE, THRESHOLD_COMUNE)
            collection.add_concept(concept)
        
        collection.compute_statistics()
        collection.total_raw_concepts_extracted = sum(len(v) for v in grouped.values())
        
        return collection
    
    # =========================================================
    # METODI PUBBLICI PRINCIPALI
    # =========================================================
    
    def extract_from_syllabus(
        self, 
        text: str, 
        syllabus_id: str, 
        extract_program_only: bool = True
    ) -> List[RawConcept]:
        """Estrae concetti da un singolo syllabus"""
        cleaned = self.preprocess_text(text)
        
        if extract_program_only:
            program = self.extract_program_section(cleaned)
        else:
            program = cleaned[:5000]  # Limita per LLM
        
        if self.use_llm and self.client:
            return self.extract_concepts_with_llm(program, syllabus_id)
        else:
            return self._extract_concepts_fallback(program, syllabus_id)
    
    def process_multiple_syllabus(
        self, 
        syllabus_texts: Dict[str, str], 
        name: str = "Analisi"
    ) -> ConceptCollection:
        """Processa multipli syllabus e genera collection"""
        all_raw = []
        total = len(syllabus_texts)
        
        print(f"Elaborazione {total} syllabus...")
        if self.use_llm and self.client:
            print(f"[LLM] Estrazione concetti per: {self.materia or name}")
        
        for i, (sid, text) in enumerate(syllabus_texts.items(), 1):
            raw = self.extract_from_syllabus(text, sid)
            all_raw.extend(raw)
            
            if i % 5 == 0 or i == total:
                print(f"  Elaborati {i}/{total} syllabus... ({len(all_raw)} concetti grezzi)")
        
        print(f"Concetti grezzi totali estratti: {len(all_raw)}")
        grouped = self.normalize_concepts(all_raw)
        print(f"Concetti unici dopo normalizzazione: {len(grouped)}")
        
        return self.build_concept_collection(grouped, total, name)


# =========================================================
# FUNZIONE DI UTILITÀ
# =========================================================

def extract_concepts_from_texts(
    texts: Dict[str, str], 
    name: str = "Analisi",
    materia: str = "",
    use_llm: bool = True
) -> ConceptCollection:
    """Funzione wrapper per estrazione concetti"""
    extractor = ConceptExtractor(use_llm=use_llm, materia=materia)
    return extractor.process_multiple_syllabus(texts, name)