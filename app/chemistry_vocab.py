"""
chemistry_vocab.py
Vocabolario specializzato per chimica organica.
"""

from typing import Final
import re

# Mappatura sinonimi -> termine canonico
SYNONYM_MAP: Final[dict[str, str]] = {
    # Stereochimica
    "isomeria ottica": "chiralità",
    "enantiomeria": "enantiomeri",
    "centri chirali": "stereocentri",
    "centri stereogenici": "stereocentri",
    "carbonio asimmetrico": "stereocentri",
    "carbonio chirale": "stereocentri",
    "configurazione assoluta": "configurazione R/S",
    "convenzione r/s": "configurazione R/S",
    "proiezione di newman": "proiezioni di Newman",
    "proiezione di fischer": "proiezioni di Fischer",
    "miscela racemica": "miscele racemiche",
    
    # Meccanismi
    "sostituzione nucleofila bimolecolare": "SN2",
    "sostituzione nucleofila monomolecolare": "SN1",
    "sn 2": "SN2",
    "sn 1": "SN1",
    "eliminazione bimolecolare": "E2",
    "eliminazione monomolecolare": "E1",
    "sostituzione elettrofila aromatica": "SEAr",
    
    # Reazioni
    "regola di markovnikov": "regola di Markovnikov",
    "markovnikoff": "regola di Markovnikov",
    "esterificazione di fischer": "esterificazione di Fischer",
    "condensazione aldolica": "condensazione aldolica",
    "reazione aldolica": "condensazione aldolica",
    "condensazione di claisen": "condensazione di Claisen",
    "friedel-crafts": "reazioni di Friedel-Crafts",
    
    # Composti
    "composti carbonilici": "gruppo carbonilico",
    "gruppo carbonile": "gruppo carbonilico",
    "acidi carbossilici": "acidi carbossilici",
    "derivati degli acidi": "derivati acidi carbossilici",
    "alogenuri acilici": "alogenuri acilici",
    "cloruri acilici": "alogenuri acilici",
    
    # Tautomeria
    "tautomeria cheto-enolica": "tautomeria cheto-enolica",
    "equilibrio cheto-enolico": "tautomeria cheto-enolica",
    
    # Aromatici
    "regola di hückel": "regola di Hückel",
    "regola di huckel": "regola di Hückel",
    "regola 4n+2": "regola di Hückel",
    
    # Biomolecole
    "monosaccaridi": "monosaccaridi",
    "zuccheri semplici": "monosaccaridi",
    "amminoacidi": "amminoacidi",
    "aminoacidi": "amminoacidi",
    "punto isoelettrico": "punto isoelettrico",
    "legame peptidico": "legame peptidico",
    "trigliceridi": "trigliceridi",
    "triacilgliceroli": "trigliceridi",
    
    # Laboratorio
    "cromatografia su strato sottile": "TLC",
    "tlc": "TLC",
}

# Abbreviazioni
ABBREVIATIONS: Final[dict[str, str]] = {
    "SN1": "sostituzione nucleofila monomolecolare",
    "SN2": "sostituzione nucleofila bimolecolare",
    "E1": "eliminazione monomolecolare",
    "E2": "eliminazione bimolecolare",
    "SEAr": "sostituzione elettrofila aromatica",
    "TLC": "cromatografia su strato sottile",
    "IR": "spettroscopia infrarossa",
    "NMR": "risonanza magnetica nucleare",
    "pI": "punto isoelettrico",
    "pKa": "costante di dissociazione acida",
}

# Pattern regex per entità chimiche
CHEMISTRY_PATTERNS: Final[list[tuple[str, str]]] = [
    (r"reazion[ei]\s+di\s+[A-Z][a-z]+(?:\s*-\s*[A-Z][a-z]+)*", "REACTION"),
    (r"condensazion[ei]\s+(?:di\s+)?[A-Z][a-z]+", "REACTION"),
    (r"SN[12]", "MECHANISM"),
    (r"E[12]", "MECHANISM"),
    (r"SEAr", "MECHANISM"),
    (r"grupp[oi]\s+\w+", "FUNCTIONAL_GROUP"),
    (r"alcan[oi]", "COMPOUND_CLASS"),
    (r"alchen[oi]", "COMPOUND_CLASS"),
    (r"alchin[oi]", "COMPOUND_CLASS"),
    (r"alcol[oi]?", "COMPOUND_CLASS"),
    (r"aldeid[ei]", "COMPOUND_CLASS"),
    (r"cheton[oi]", "COMPOUND_CLASS"),
    (r"ammin[ae]", "COMPOUND_CLASS"),
    (r"carboidrat[oi]", "BIOMOLECULE"),
    (r"protein[ae]", "BIOMOLECULE"),
    (r"lipid[oi]", "BIOMOLECULE"),
    (r"enantiomer[oi]", "STEREOCHEMISTRY"),
    (r"diastereoisomer[oi]", "STEREOCHEMISTRY"),
    (r"chiralit[àa]", "STEREOCHEMISTRY"),
]

# Stopwords accademiche
ACADEMIC_STOPWORDS: Final[set[str]] = {
    "corso", "insegnamento", "esame", "prova", "orale", "scritto",
    "studente", "docente", "professore", "lezione", "ore", "cfu",
    "obiettivo", "obiettivi", "formativi", "apprendimento",
    "prerequisiti", "propedeutico", "testo", "testi", "bibliografia",
    "valutazione", "verifica", "modalità", "semestre", "anno",
    "dipartimento", "università", "programma", "syllabus",
}


class ChemistryVocabulary:
    """Gestisce il vocabolario chimico per normalizzazione."""
    
    def __init__(self):
        self.synonyms = SYNONYM_MAP
        self.abbreviations = ABBREVIATIONS
        self.stopwords = ACADEMIC_STOPWORDS
        self._compile_patterns()
    
    def _compile_patterns(self):
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), label)
            for pattern, label in CHEMISTRY_PATTERNS
        ]
    
    def normalize(self, term: str) -> str:
        normalized = term.lower().strip()
        normalized = re.sub(r"\s+", " ", normalized)
        
        if normalized in self.synonyms:
            return self.synonyms[normalized]
        
        term_upper = term.upper().strip()
        if term_upper in self.abbreviations:
            return term_upper
        
        return normalized
    
    def is_stopword(self, term: str) -> bool:
        return term.lower().strip() in self.stopwords
    
    def extract_entities(self, text: str) -> list[tuple[str, str, int, int]]:
        entities = []
        for pattern, label in self.compiled_patterns:
            for match in pattern.finditer(text):
                entities.append((match.group(), label, match.start(), match.end()))
        return entities
    
    def get_canonical_form(self, term: str) -> tuple[str, bool]:
        normalized = self.normalize(term)
        is_known = normalized != term.lower().strip()
        return normalized, is_known