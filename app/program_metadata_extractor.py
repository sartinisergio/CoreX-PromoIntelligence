"""
CoreX - Program Metadata Extractor
Estrae automaticamente metadati e bibliografia dal testo del programma d'esame
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Per estrazione testo da PDF
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False


@dataclass
class ExtractedMetadata:
    """Metadati estratti dal programma d'esame"""
    dati_programma: Dict = field(default_factory=dict)
    bibliografia: List[Dict] = field(default_factory=list)
    contenuto_raw: str = ""
    confidence: float = 0.0


class ProgramMetadataExtractor:
    """
    Estrae metadati e bibliografia dal PDF di un programma d'esame.
    """
    
    # Editori noti con normalizzazione
    KNOWN_PUBLISHERS = {
        "zanichelli": "Zanichelli",
        "pearson": "Pearson",
        "mcgraw": "McGraw-Hill",
        "mcgraw-hill": "McGraw-Hill",
        "edises": "EdiSES",
        "edi-ermes": "Edi-Ermes",
        "hoepli": "Hoepli",
        "springer": "Springer",
        "wiley": "Wiley",
        "elsevier": "Elsevier",
        "utet": "UTET",
        "piccin": "Piccin",
        "cea": "CEA",
        "edra": "Edra",
        "ambrosiana": "CEA Ambrosiana",
        "cortina": "Raffaello Cortina",
        "carocci": "Carocci",
        "il mulino": "Il Mulino",
        "mulino": "Il Mulino",
        "mondadori": "Mondadori",
        "laterza": "Laterza",
    }
    
    # Pattern università italiane
    UNIVERSITY_PATTERNS = [
        (r"vanvitelli", "Università Vanvitelli"),
        (r"federico\s*ii", "Università Federico II"),
        (r"sapienza", "Sapienza Roma"),
        (r"politecnico\s+(?:di\s+)?milano", "Politecnico di Milano"),
        (r"politecnico\s+(?:di\s+)?torino", "Politecnico di Torino"),
        (r"bicocca", "Milano-Bicocca"),
        (r"statale\s+(?:di\s+)?milano", "Università Statale di Milano"),
        (r"bocconi", "Università Bocconi"),
        (r"universit[aà]\s+(?:degli\s+studi\s+)?(?:di\s+)?([a-zA-Z\s]+)", None),
    ]
    
    def __init__(self):
        self.text = ""
    
    def estrai_da_pdf(self, pdf_path: str) -> Dict:
        """
        Estrae metadati e bibliografia da un file PDF.
        
        Args:
            pdf_path: Percorso al file PDF
            
        Returns:
            Dict con dati_programma, bibliografia, contenuto_raw
        """
        # Estrai testo dal PDF
        self.text = self._extract_text_from_pdf(pdf_path)
        
        if not self.text:
            return {
                'dati_programma': {},
                'bibliografia': [],
                'contenuto_raw': '',
                'errore': 'Impossibile estrarre testo dal PDF'
            }
        
        text_lower = self.text.lower()
        
        # Estrai metadati
        dati_programma = {
            'docente': self._extract_docente(),
            'corso': self._extract_corso(),
            'universita': self._extract_universita(),
            'cfu': self._extract_cfu(),
            'anno_accademico': self._extract_anno_accademico(),
            'materia': self._guess_materia(),
        }
        
        # Estrai bibliografia
        bibliografia = self._extract_bibliografia()
        
        return {
            'dati_programma': dati_programma,
            'bibliografia': bibliografia,
            'contenuto_raw': self.text
        }
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Estrae testo dal PDF usando pdfplumber o PyPDF2"""
        
        text = ""
        
        # Prova con pdfplumber (migliore qualità)
        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                if text.strip():
                    return text
            except Exception as e:
                print(f"Errore pdfplumber: {e}")
        
        # Fallback a PyPDF2
        if HAS_PYPDF2:
            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
            except Exception as e:
                print(f"Errore PyPDF2: {e}")
        
        return text
    
    def _extract_docente(self) -> str:
        """Estrae il nome del docente"""
        
        patterns = [
            r"docente[:\s]+(?:prof\.?(?:ssa)?\.?\s*)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            r"prof\.?\s*(?:ssa)?\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            r"titolare[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            r"docente\s+responsabile[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_corso(self) -> str:
        """Estrae il nome del corso"""
        
        patterns = [
            r"insegnamento[:\s]+([^\n]+)",
            r"corso\s+di[:\s]+([^\n]+)",
            r"denominazione[:\s]+([^\n]+)",
            r"nome\s+insegnamento[:\s]+([^\n]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                corso = match.group(1).strip()
                corso = corso.split('\n')[0][:100]
                return corso
        
        return ""
    
    def _extract_universita(self) -> str:
        """Estrae il nome dell'università"""
        
        text_lower = self.text.lower()
        
        for pattern, fixed_name in self.UNIVERSITY_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                if fixed_name:
                    return fixed_name
                else:
                    # Usa il gruppo catturato
                    if match.groups():
                        return f"Università di {match.group(1).strip().title()}"
        
        return ""
    
    def _extract_cfu(self) -> str:
        """Estrae i CFU"""
        
        patterns = [
            r"(\d+)\s*cfu",
            r"cfu[:\s]+(\d+)",
            r"crediti[:\s]+(\d+)",
            r"(\d+)\s*crediti",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text.lower())
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_anno_accademico(self) -> str:
        """Estrae l'anno accademico"""
        
        patterns = [
            r"a\.?\s*a\.?\s*(\d{4})[/-](\d{2,4})",
            r"anno\s+accademico\s+(\d{4})[/-](\d{2,4})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                y1 = match.group(1)
                y2 = match.group(2)
                if len(y2) == 2:
                    y2 = y1[:2] + y2
                return f"{y1}/{y2}"
        
        return ""
    
    def _guess_materia(self) -> str:
        """Cerca di indovinare la materia dal contenuto"""
        
        text_lower = self.text.lower()
        
        materie_keywords = {
            'Chimica_Organica': ['chimica organica', 'organic chemistry', 'reazioni organiche', 'gruppi funzionali'],
            'Chimica_Generale': ['chimica generale', 'stechiometria', 'tavola periodica'],
            'Biochimica': ['biochimica', 'metabolismo', 'enzimi', 'proteine'],
            'Fisica': ['fisica', 'meccanica', 'termodinamica', 'elettromagnetismo'],
            'Biologia': ['biologia', 'cellula', 'genetica', 'evoluzione'],
            'Anatomia': ['anatomia', 'corpo umano', 'organi', 'apparati'],
            'Fisiologia': ['fisiologia', 'funzioni vitali', 'omeostasi'],
        }
        
        for materia, keywords in materie_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    return materia
        
        return ""
    
    def _extract_bibliografia(self) -> List[Dict]:
        """Estrae la bibliografia dal testo"""
        
        bibliografia = []
        
        # Trova sezione bibliografia
        section = self._find_bibliography_section()
        
        if section:
            bibliografia = self._parse_books_from_section(section)
        
        # Se non trovata, cerca editori noti nel testo
        if not bibliografia:
            bibliografia = self._find_books_by_publisher()
        
        # Imposta il primo come principale
        if bibliografia and not any(b.get('ruolo') == 'principale' for b in bibliografia):
            bibliografia[0]['ruolo'] = 'principale'
        
        return bibliografia
    
    def _find_bibliography_section(self) -> str:
        """Trova la sezione bibliografia nel testo"""
        
        headers = [
            r"testi?\s+(?:di\s+riferimento|consigliati?|adottati?)",
            r"bibliografia",
            r"libri?\s+di\s+testo",
            r"materiale\s+didattico",
            r"manuali?\s+(?:consigliati?|adottati?)",
        ]
        
        text_lower = self.text.lower()
        
        for header in headers:
            match = re.search(header, text_lower)
            if match:
                start = match.start()
                # Prendi i prossimi 2000 caratteri
                return self.text[start:start+2000]
        
        return ""
    
    def _parse_books_from_section(self, section: str) -> List[Dict]:
        """Estrae libri da una sezione di testo"""
        
        books = []
        found = set()
        
        # Pattern semplificati e robusti
        patterns = [
            # Autore, Titolo, Editore
            r"([A-Z][a-z]+(?:\s+[A-Z]\.?\s*[A-Z]?[a-z]*)?)\s*,\s*([^,\n]+?)\s*,\s*([A-Za-z\-\s]+?)(?:\s*,\s*\d{4})?(?:\n|$)",
            # Autore - Titolo - Editore  
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[-:]\s*([^-\n]+?)\s*[-:]\s*([A-Za-z\-\s]+)",
        ]
        
        for pattern in patterns:
            try:
                for match in re.finditer(pattern, section):
                    author = match.group(1).strip() if match.group(1) else ""
                    title = match.group(2).strip() if match.group(2) else ""
                    publisher_raw = match.group(3).strip() if match.group(3) else ""
                    
                    # Salta se troppo corto
                    if len(title) < 5:
                        continue
                    
                    # Normalizza editore
                    publisher = self._normalize_publisher(publisher_raw)
                    
                    # Evita duplicati
                    key = f"{author.lower()}_{title.lower()[:20]}"
                    if key in found:
                        continue
                    found.add(key)
                    
                    books.append({
                        'autore': author,
                        'titolo': title[:100],
                        'editore': publisher,
                        'ruolo': 'consultazione'
                    })
            except Exception:
                continue
        
        return books
    
    def _find_books_by_publisher(self) -> List[Dict]:
        """Trova libri cercando editori noti nel testo"""
        
        books = []
        
        for pub_key, pub_name in self.KNOWN_PUBLISHERS.items():
            if pub_key in self.text.lower():
                # Cerca contesto intorno all'editore
                pattern = rf"([A-Z][a-z]+(?:\s+[A-Z]?[a-z]*)?)\s*,?\s*([^,\n]{{10,80}}?)\s*,?\s*{pub_key}"
                
                for match in re.finditer(pattern, self.text, re.IGNORECASE):
                    author = match.group(1).strip()
                    title = match.group(2).strip()
                    
                    if len(title) > 5:
                        books.append({
                            'autore': author,
                            'titolo': title,
                            'editore': pub_name,
                            'ruolo': 'consultazione'
                        })
        
        return books
    
    def _normalize_publisher(self, raw: str) -> str:
        """Normalizza il nome dell'editore"""
        
        raw_lower = raw.lower().strip()
        
        for key, name in self.KNOWN_PUBLISHERS.items():
            if key in raw_lower:
                return name
        
        # Se non riconosciuto, restituisci pulito
        return raw.strip().title() if raw else "Altro"
