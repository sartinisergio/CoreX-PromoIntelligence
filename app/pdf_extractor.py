"""
pdf_extractor.py
Estrazione testo da PDF
"""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass

try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


@dataclass
class ExtractedSyllabus:
    id: str
    filename: str
    university: str
    professor: str
    text: str
    n_pages: int
    extraction_method: str
    success: bool
    error: Optional[str] = None


class PDFExtractor:
    def __init__(self):
        if not HAS_PYMUPDF and not HAS_PDFPLUMBER:
            raise ImportError("Installa pymupdf o pdfplumber")
        self.preferred_method = "pymupdf" if HAS_PYMUPDF else "pdfplumber"
    
    def extract_text_pymupdf(self, pdf_path: Path) -> tuple[str, int]:
        doc = fitz.open(pdf_path)
        text_parts = [page.get_text() for page in doc]
        n_pages = len(doc)
        doc.close()
        return "\n".join(text_parts), n_pages
    
    def extract_text_pdfplumber(self, pdf_path: Path) -> tuple[str, int]:
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            n_pages = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return "\n".join(text_parts), n_pages
    
    def parse_filename(self, filename: str) -> tuple[str, str]:
        name = Path(filename).stem
        parts = name.split("_")
        if len(parts) >= 3:
            return parts[1].strip(), parts[2].strip()
        elif len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        return "Unknown", name
    
    def extract(self, pdf_path: Path | str) -> ExtractedSyllabus:
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            return ExtractedSyllabus(
                id=pdf_path.stem, filename=pdf_path.name,
                university="Unknown", professor="Unknown",
                text="", n_pages=0, extraction_method="none",
                success=False, error=f"File non trovato: {pdf_path}"
            )
        
        university, professor = self.parse_filename(pdf_path.name)
        
        try:
            if self.preferred_method == "pymupdf" and HAS_PYMUPDF:
                text, n_pages = self.extract_text_pymupdf(pdf_path)
                method = "pymupdf"
            else:
                text, n_pages = self.extract_text_pdfplumber(pdf_path)
                method = "pdfplumber"
            
            syllabus_id = f"{university.lower().replace(' ', '_')}_{professor.lower().split()[0] if professor else 'unknown'}"
            syllabus_id = "".join(c for c in syllabus_id if c.isalnum() or c == "_")
            
            return ExtractedSyllabus(
                id=syllabus_id, filename=pdf_path.name,
                university=university, professor=professor,
                text=text, n_pages=n_pages,
                extraction_method=method, success=True
            )
        except Exception as e:
            return ExtractedSyllabus(
                id=pdf_path.stem, filename=pdf_path.name,
                university=university, professor=professor,
                text="", n_pages=0, extraction_method=self.preferred_method,
                success=False, error=str(e)
            )
    
    def extract_batch(self, pdf_dir: Path | str, pattern: str = "*.pdf") -> list[ExtractedSyllabus]:
        pdf_dir = Path(pdf_dir)
        results = []
        pdf_files = sorted(pdf_dir.glob(pattern))
        print(f"Trovati {len(pdf_files)} file PDF")
        
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"  [{i}/{len(pdf_files)}] {pdf_path.name}...", end=" ")
            result = self.extract(pdf_path)
            print("✓" if result.success else f"✗ {result.error}")
            results.append(result)
        
        return results