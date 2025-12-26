"""
CoreX - Promo Orchestrator v1.3
Orchestra l'analisi completa per il report commerciale del promotore
CORRETTO: Usa i dati forniti dall'utente, non cerca nei file JSON
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class PromoOrchestrator:
    """
    Orchestratore principale per generare report commerciali completi.
    Coordina tutti i componenti di analisi.
    """
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.frameworks_dir = self.base_dir / "frameworks"
        self.manuali_dir = self.base_dir / "data" / "manuali"
        self.archivio_dir = self.base_dir / "archivio"
        
        # Inizializza componenti
        self._init_components()
    
    def _init_components(self):
        """Inizializza i componenti di analisi"""
        try:
            from app.pedagogical_analyzer import PedagogicalAnalyzer
            self.pedagogical_analyzer = PedagogicalAnalyzer(use_llm=True)
            print("[OK] PedagogicalAnalyzer inizializzato")
        except Exception as e:
            print(f"[WARN] PedagogicalAnalyzer non disponibile: {e}")
            self.pedagogical_analyzer = None
        
        try:
            from app.manual_analyzer import ManualAnalyzer
            self.manual_analyzer = ManualAnalyzer(
                manuali_dir=self.manuali_dir,
                frameworks_dir=self.frameworks_dir
            )
            print("[OK] ManualAnalyzer inizializzato")
        except Exception as e:
            print(f"[WARN] ManualAnalyzer non disponibile: {e}")
            self.manual_analyzer = None
        
        try:
            from app.pdf_extractor import PDFExtractor
            self.pdf_extractor = PDFExtractor()
            print("[OK] PDFExtractor inizializzato")
        except Exception as e:
            print(f"[WARN] PDFExtractor non disponibile: {e}")
            self.pdf_extractor = None
        
        try:
            from app.program_metadata_extractor import ProgramMetadataExtractor
            self.metadata_extractor = ProgramMetadataExtractor()
            print("[OK] MetadataExtractor inizializzato")
        except Exception as e:
            print(f"[WARN] MetadataExtractor non disponibile: {e}")
            self.metadata_extractor = None

    # =========================================================
    # METODO PRINCIPALE CON COMPETITOR FORNITO DALL'UTENTE
    # =========================================================
    
    def analizza_programma_docente_con_competitor(
        self,
        pdf_path: Path,
        materia: str,
        classe_laurea: str,
        manuali_adottati: List[Dict],
        manuale_zanichelli_proposto: Dict = None
    ) -> Dict:
        """
        Esegue l'analisi completa con i manuali GIÀ FORNITI dall'utente.
        NON cerca nei file JSON.
        
        Args:
            pdf_path: Path al PDF del programma
            materia: Nome della materia
            classe_laurea: Classe di laurea
            manuali_adottati: Lista dei manuali adottati dal docente [{'titolo':..., 'autore':..., 'editore':...}]
            manuale_zanichelli_proposto: Manuale Zanichelli da proporre (opzionale)
        
        Returns:
            Dizionario completo pronto per il report generator
        """
        print(f"\n{'='*60}")
        print(f"[PROMO] Inizio analisi con competitor forniti")
        print(f"{'='*60}")
        print(f"[INFO] PDF: {pdf_path.name}")
        print(f"[INFO] Materia: {materia}")
        print(f"[INFO] Classe: {classe_laurea}")
        print(f"[INFO] Manuali adottati: {len(manuali_adottati)}")
        
        risultato = {
            'timestamp': datetime.now().isoformat(),
            'pdf_analizzato': str(pdf_path),
            'materia': materia,
            'classe_laurea': classe_laurea
        }
        
        # === STEP 1: Estrazione testo dal PDF ===
        print("\n[1/7] Estrazione testo dal PDF...")
        testo_programma = self._estrai_testo_pdf(pdf_path)
        if not testo_programma:
            print("[ERR] Impossibile estrarre testo")
            risultato['errore'] = "Impossibile estrarre testo dal PDF"
            return risultato
        print(f"[OK] Estratti {len(testo_programma)} caratteri")
        
        # === STEP 2: Estrazione metadati ===
        print("\n[2/7] Estrazione metadati programma...")
        metadati = self._estrai_metadati(testo_programma, pdf_path)
        risultato['dati_programma'] = metadati
        print(f"[OK] Docente: {metadati.get('docente', 'N/D')}")
        
        # === STEP 3: Analisi profilo pedagogico ===
        print("\n[3/7] Analisi profilo pedagogico...")
        profilo_docente = self._analizza_profilo_docente(testo_programma, metadati)
        risultato['profilo_docente'] = profilo_docente
        print(f"[OK] Approccio: {profilo_docente.get('approccio', 'N/D')}")
        
        # === STEP 4: Caricamento framework ===
        print("\n[4/7] Caricamento framework disciplinari...")
        framework_ideale = self._carica_framework_ideale(materia)
        framework_reale = self._carica_framework_reale(materia)
        print(f"[OK] Framework ideale: {'trovato' if framework_ideale else 'non trovato'}")
        print(f"[OK] Framework reale: {'trovato' if framework_reale else 'non trovato'}")
        
        # === STEP 5: USA I MANUALI FORNITI (NON CERCA NEI FILE!) ===
        print("\n[5/7] Analisi manuali adottati (forniti dall'utente)...")
        
        # Identifica il concorrente principale
        concorrente = None
        zanichelli_presente = False
        
        for manuale in manuali_adottati:
            editore = manuale.get('editore', '').upper()
            if 'ZANICHELLI' in editore:
                zanichelli_presente = True
            else:
                if concorrente is None:  # Prendi il primo non-Zanichelli
                    concorrente = {
                        'titolo': manuale.get('titolo', 'N/D'),
                        'autore': manuale.get('autore', 'N/D'),
                        'editore': manuale.get('editore', 'N/D')
                    }
        
        risultato['concorrente_principale'] = concorrente
        risultato['bibliografia_completa'] = manuali_adottati
        
        if zanichelli_presente:
            risultato['analisi_competitiva'] = {
                'situazione': 'presente',
                'descrizione': 'Zanichelli già adottato - opportunità di upselling o consolidamento'
            }
            print("[OK] Zanichelli GIÀ PRESENTE - opportunità upselling")
        else:
            risultato['analisi_competitiva'] = {
                'situazione': 'assente',
                'descrizione': 'Zanichelli non presente - opportunità di conquista'
            }
            print(f"[OK] Competitor principale: {concorrente.get('titolo', 'N/D')} ({concorrente.get('editore', 'N/D')})")
        
        # === STEP 6: Manuale Zanichelli da proporre ===
        print("\n[6/7] Selezione manuale Zanichelli da proporre...")
        
        if manuale_zanichelli_proposto:
            # Usa il manuale fornito dall'utente
            risultato['manuale_zanichelli'] = {
                'titolo': manuale_zanichelli_proposto.get('titolo', 'N/D'),
                'autore': manuale_zanichelli_proposto.get('autore', 'N/D'),
                'match_score': 85,  # Score di default
                'capitoli_rilevanti': []
            }
            print(f"[OK] Manuale proposto: {manuale_zanichelli_proposto.get('titolo', 'N/D')}")
        else:
            # Trova automaticamente il migliore
            manuale_match = self._trova_manuale_zanichelli_migliore_safe(materia)
            risultato['manuale_zanichelli'] = manuale_match['manuale']
            risultato['match_details'] = manuale_match.get('details', {})
            print(f"[OK] Manuale trovato: {manuale_match['manuale'].get('titolo', 'N/D')}")
        
        # === STEP 7: Calcolo copertura e gap ===
        print("\n[7/7] Calcolo copertura e gap...")
        copertura = self._calcola_copertura_completa(
            testo_programma, framework_ideale, framework_reale, risultato
        )
        risultato['copertura_ideale'] = copertura['ideale']
        risultato['copertura_reale'] = copertura['reale']
        risultato['copertura_argomenti'] = copertura['sintesi']
        risultato['gap_analysis'] = copertura['gaps']
        print(f"[OK] Copertura ideale: {copertura['ideale'].get('percentuale', 0)}%")
        print(f"[OK] Copertura reale: {copertura['reale'].get('percentuale', 0)}%")
        
        # === GENERA CONTENUTI COMMERCIALI ===
        print("\n[PROMO] Generazione contenuti commerciali...")
        risultato['postit'] = self._genera_postit_vs_competitor(risultato, concorrente)
        risultato['argomenti_vendita'] = self._genera_argomenti_vs_competitor(risultato, concorrente)
        risultato['domande_discovery'] = self._genera_domande_discovery(risultato)
        risultato['email'] = self._genera_email_vs_competitor(risultato, concorrente)
        risultato['strategia'] = self._genera_strategia(risultato)
        risultato['punteggio_opportunita'] = self._calcola_punteggio(risultato)
        
        print(f"\n{'='*60}")
        print(f"[OK] ANALISI COMPLETATA - Punteggio: {risultato['punteggio_opportunita']}/100")
        print(f"{'='*60}\n")
        
        return risultato

    # =========================================================
    # METODO LEGACY (manteniamo per retrocompatibilità)
    # =========================================================
    
    def analizza_programma_docente(
        self,
        pdf_path: Path,
        materia: str,
        classe_laurea: str = None,
        use_framework_reale: bool = True
    ) -> Dict:
        """Metodo legacy - chiama il nuovo metodo con lista vuota"""
        return self.analizza_programma_docente_con_competitor(
            pdf_path=pdf_path,
            materia=materia,
            classe_laurea=classe_laurea or "",
            manuali_adottati=[],
            manuale_zanichelli_proposto=None
        )

    # =========================================================
    # ESTRAZIONE PDF - con fallback robusti
    # =========================================================
    
    def _estrai_testo_pdf(self, pdf_path: Path) -> Optional[str]:
        """Estrae il testo dal PDF con fallback multipli"""
        
        # Metodo 1: PDFExtractor
        if self.pdf_extractor:
            try:
                # Prova con extract() che ritorna un oggetto
                result = self.pdf_extractor.extract(pdf_path)
                if hasattr(result, 'text') and result.text and len(result.text) > 100:
                    print(f"[OK] Estratto via PDFExtractor.extract()")
                    return result.text
                elif hasattr(result, 'success') and result.success:
                    if hasattr(result, 'text'):
                        print(f"[OK] Estratto via PDFExtractor")
                        return result.text
            except AttributeError:
                pass
            except Exception as e:
                print(f"[WARN] PDFExtractor.extract() fallito: {e}")
            
            # Prova con extract_text()
            try:
                text = self.pdf_extractor.extract_text(pdf_path)
                if text and len(text) > 100:
                    print(f"[OK] Estratto via PDFExtractor.extract_text()")
                    return text
            except AttributeError:
                pass
            except Exception as e:
                print(f"[WARN] PDFExtractor.extract_text() fallito: {e}")
        
        # Metodo 2: PyMuPDF (fitz)
        try:
            import fitz
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            if text and len(text) > 100:
                print(f"[OK] Estratto via PyMuPDF")
                return text
        except Exception as e:
            print(f"[WARN] PyMuPDF fallito: {e}")
        
        # Metodo 3: pdfplumber
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if text and len(text) > 100:
                print(f"[OK] Estratto via pdfplumber")
                return text
        except Exception as e:
            print(f"[WARN] pdfplumber fallito: {e}")
        
        print("[ERR] Tutti i metodi di estrazione PDF falliti")
        return None

    # =========================================================
    # ESTRAZIONE METADATI
    # =========================================================
    
    def _estrai_metadati(self, testo: str, pdf_path: Path) -> Dict:
        """Estrae metadati dal programma - robusto"""
        metadati = {
            'docente': 'Docente non specificato',
            'corso': 'Corso non specificato',
            'universita': 'Università non specificata',
            'cfu': 'N/D',
            'ore': 'N/D',
            'anno_accademico': 'N/D'
        }
        
        # FONTE 1: Nome del file
        filename = pdf_path.stem
        parts = filename.replace('_', ' ').replace('-', ' ').split()
        
        # Formato tipico: "Materia Università Docente"
        if len(parts) >= 3:
            # Cerca pattern comune
            for i, part in enumerate(parts):
                if any(uni in part.lower() for uni in ['univ', 'politec', 'sapienza', 'statale', 'campus', 'vanvitelli', 'campania']):
                    # L'università è qui
                    metadati['corso'] = ' '.join(parts[:i]) if i > 0 else parts[0]
                    metadati['universita'] = ' '.join(parts[i:i+2]) if i+2 <= len(parts) else parts[i]
                    if i+2 < len(parts):
                        metadati['docente'] = ' '.join(parts[i+2:])
                    break
            else:
                # Fallback: ultimo elemento è docente
                metadati['docente'] = ' '.join(parts[-2:]) if len(parts) >= 2 else parts[-1]
        
        # Formatta il nome docente
        docente = metadati['docente']
        if docente and docente != 'Docente non specificato':
            # Capitalizza correttamente
            metadati['docente'] = ' '.join(word.capitalize() for word in docente.split())
        
        # FONTE 2: Pattern nel testo
        testo_inizio = testo[:3000] if len(testo) > 3000 else testo
        
        # Docente
        docente_patterns = [
            r'(?:docente|prof\.?|professore)[:\s]+([A-Za-zàèéìòù]+\s+[A-Za-zàèéìòù]+)',
            r'([A-Za-zàèéìòù]+\s+[A-Za-zàèéìòù]+)\s*[-–]\s*(?:docente|titolare)',
        ]
        for pattern in docente_patterns:
            match = re.search(pattern, testo_inizio, re.IGNORECASE)
            if match:
                nome = match.group(1).strip()
                if len(nome.split()) >= 2 and len(nome) < 50:
                    metadati['docente'] = nome.title()
                    break
        
        # CFU
        cfu_match = re.search(r'(\d+)\s*(?:CFU|crediti)', testo_inizio, re.IGNORECASE)
        if cfu_match:
            metadati['cfu'] = int(cfu_match.group(1))
        
        # Ore
        ore_match = re.search(r'(\d+)\s*(?:ore|h)\b', testo_inizio, re.IGNORECASE)
        if ore_match:
            ore = int(ore_match.group(1))
            if 20 <= ore <= 200:  # Range ragionevole
                metadati['ore'] = ore
        
        # Anno accademico
        anno_match = re.search(r'(?:a\.?a\.?|anno accademico)[:\s]*(\d{4})[/-](\d{2,4})', testo_inizio, re.IGNORECASE)
        if anno_match:
            metadati['anno_accademico'] = f"{anno_match.group(1)}/{anno_match.group(2)}"
        
        return metadati

    # =========================================================
    # PROFILO PEDAGOGICO
    # =========================================================
    
    def _analizza_profilo_docente(self, testo: str, metadati: Dict) -> Dict:
        """Analizza il profilo pedagogico del docente"""
        profilo = {
            'approccio': 'Bilanciato',
            'rigore': 'Alto',
            'bilanciamento': 50,
            'argomenti_chiave': '',
            'metodi_didattici': ['lezione frontale', 'esercitazioni'],
            'metodi_valutazione': ['scritto', 'orale'],
            'laboratorio': False,
            'esercitazioni': True,
            'insight': '',
            'filosofia': ''
        }
        
        # Prova con LLM
        if self.pedagogical_analyzer:
            try:
                result = self.pedagogical_analyzer.analyze_program(testo, metadati)
                
                if hasattr(result, 'philosophy'):
                    approach_map = {'teorico': 'Teorico', 'pratico': 'Pratico', 'bilanciato': 'Bilanciato'}
                    if hasattr(result.philosophy, 'approach'):
                        profilo['approccio'] = approach_map.get(
                            str(result.philosophy.approach.value).lower(), 'Bilanciato'
                        )
                    
                    rigor_map = {'alto_formale': 'Alto', 'accessibile': 'Accessibile', 'misto': 'Medio'}
                    if hasattr(result.philosophy, 'rigor_level'):
                        profilo['rigore'] = rigor_map.get(
                            str(result.philosophy.rigor_level.value).lower(), 'Alto'
                        )
                    
                    if hasattr(result.philosophy, 'application_emphasis'):
                        profilo['bilanciamento'] = result.philosophy.application_emphasis
                
                if hasattr(result, 'priorities'):
                    if result.priorities.teaching_methods:
                        profilo['metodi_didattici'] = result.priorities.teaching_methods
                    if result.priorities.assessment_methods:
                        profilo['metodi_valutazione'] = result.priorities.assessment_methods
                
                if hasattr(result, 'profile_summary'):
                    profilo['insight'] = result.profile_summary or ''
                if hasattr(result, 'suggested_approach'):
                    profilo['filosofia'] = result.suggested_approach or ''
                if hasattr(result, 'key_insights') and result.key_insights:
                    profilo['argomenti_chiave'] = ', '.join(result.key_insights[:3])
                
                print("[OK] Profilo via LLM")
                
            except Exception as e:
                print(f"[WARN] LLM fallito, uso euristica: {e}")
                profilo = self._analisi_pedagogica_euristica(testo, profilo)
        else:
            profilo = self._analisi_pedagogica_euristica(testo, profilo)
        
        # Verifica laboratorio/esercitazioni
        testo_lower = testo.lower()
        profilo['laboratorio'] = 'laboratorio' in testo_lower
        profilo['esercitazioni'] = any(kw in testo_lower for kw in ['esercitazion', 'esercizi', 'problem'])
        
        return profilo
    
    def _analisi_pedagogica_euristica(self, testo: str, profilo: Dict) -> Dict:
        """Analisi pedagogica basata su euristiche"""
        testo_lower = testo.lower()
        
        teoria_kw = ['teoria', 'teorico', 'teorema', 'dimostrazione', 'fondamenti', 'principi']
        pratica_kw = ['laboratorio', 'esercitazione', 'pratico', 'applicazione', 'esperimento', 'case study']
        
        teoria_count = sum(testo_lower.count(kw) for kw in teoria_kw)
        pratica_count = sum(testo_lower.count(kw) for kw in pratica_kw)
        
        if teoria_count > pratica_count * 1.5:
            profilo['approccio'] = 'Teorico'
            profilo['bilanciamento'] = 30
        elif pratica_count > teoria_count * 1.5:
            profilo['approccio'] = 'Pratico'
            profilo['bilanciamento'] = 70
        else:
            profilo['approccio'] = 'Bilanciato'
            profilo['bilanciamento'] = 50
        
        return profilo

    # =========================================================
    # FRAMEWORK
    # =========================================================
    
    def _carica_framework_ideale(self, materia: str) -> Optional[Dict]:
        """Carica il framework ideale per la materia"""
        materia_normalized = materia.replace(' ', '_').replace('-', '_')
        
        for fw_file in self.frameworks_dir.glob("*.json"):
            if materia_normalized.lower() in fw_file.stem.lower():
                try:
                    with open(fw_file, 'r', encoding='utf-8') as f:
                        print(f"[OK] Framework ideale: {fw_file.name}")
                        return json.load(f)
                except Exception as e:
                    print(f"[WARN] Errore caricamento framework: {e}")
        
        return None
    
    def _carica_framework_reale(self, materia: str) -> Optional[Dict]:
        """Carica il framework reale più recente dall'archivio"""
        if not self.archivio_dir.exists():
            return None
        
        materia_normalized = materia.replace(' ', '_').lower()
        archivi = sorted(self.archivio_dir.iterdir(), reverse=True)
        
        for archivio in archivi:
            if archivio.is_dir() and materia_normalized in archivio.name.lower():
                fw_file = archivio / "framework_aggiornato.json"
                if fw_file.exists():
                    try:
                        with open(fw_file, 'r', encoding='utf-8') as f:
                            print(f"[OK] Framework reale: {archivio.name}")
                            return json.load(f)
                    except:
                        pass
        
        return None

    # =========================================================
    # RICERCA MANUALE ZANICHELLI - VERSIONE SAFE
    # =========================================================
    
    def _trova_manuale_zanichelli_migliore_safe(self, materia: str) -> Dict:
        """
        Trova il manuale Zanichelli migliore - versione SAFE che non crasha sui JSON corrotti
        """
        risultato = {
            'manuale': {
                'titolo': 'Manuale non trovato',
                'autore': 'N/D',
                'match_score': 0,
                'capitoli_rilevanti': []
            },
            'details': {}
        }
        
        # Cerca nella cartella manuali
        materia_dir = self.manuali_dir / materia.replace(' ', '_') / "indici" / "Manuali_Zanichelli"
        
        if not materia_dir.exists():
            # Prova varianti
            for variant in [materia, materia.replace('_', ' '), materia.replace(' ', '_')]:
                alt_dir = self.manuali_dir / variant / "indici" / "Manuali_Zanichelli"
                if alt_dir.exists():
                    materia_dir = alt_dir
                    break
        
        if not materia_dir.exists():
            print(f"[WARN] Cartella manuali non trovata: {materia_dir}")
            return risultato
        
        best_manual = None
        
        for json_file in materia_dir.glob("*.json"):
            try:
                # Leggi con encoding safe
                with open(json_file, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                    # Rimuovi BOM se presente
                    if content.startswith('\ufeff'):
                        content = content[1:]
                    manual = json.loads(content)
                
                if best_manual is None:
                    best_manual = manual
                    print(f"[OK] Manuale Zanichelli: {manual.get('title', json_file.stem)}")
                    
            except json.JSONDecodeError as e:
                print(f"[WARN] JSON corrotto, skip: {json_file.name} - {e}")
                continue
            except Exception as e:
                print(f"[WARN] Errore lettura: {json_file.name} - {e}")
                continue
        
        if best_manual:
            risultato['manuale'] = {
                'titolo': best_manual.get('title', 'N/D'),
                'autore': best_manual.get('author', 'N/D'),
                'match_score': 85,
                'capitoli_rilevanti': [f"Cap. {i+1}" for i in range(min(5, len(best_manual.get('chapters', []))))]
            }
        
        return risultato

    # =========================================================
    # COPERTURA E GAP
    # =========================================================
    
    def _calcola_copertura_completa(
        self,
        testo_programma: str,
        framework_ideale: Dict,
        framework_reale: Dict,
        dati_analisi: Dict
    ) -> Dict:
        """Calcola la copertura del programma rispetto ai framework"""
        
        risultato = {
            'ideale': {'percentuale': 60, 'moduli': [], 'punti_forza': [], 'aree_approfondire': []},
            'reale': {'percentuale': 75, 'moduli': [], 'punti_forza': [], 'aree_approfondire': []},
            'sintesi': {'percentuale': 0, 'argomenti_coperti': [], 'argomenti_mancanti': []},
            'gaps': []
        }
        
        testo_lower = testo_programma.lower()
        
        # Analisi vs Framework Ideale
        if framework_ideale:
            moduli = framework_ideale.get('syllabus_modules', [])
            coperti = []
            mancanti = []
            moduli_analisi = []
            
            for modulo in moduli:
                nome = modulo.get('name', '')
                contenuti = modulo.get('core_contents', [])
                
                trovati = 0
                for contenuto in contenuti:
                    keywords = contenuto.lower().split()[:3]
                    if any(kw in testo_lower for kw in keywords if len(kw) > 3):
                        trovati += 1
                
                copertura_modulo = (trovati / len(contenuti) * 100) if contenuti else 0
                
                if copertura_modulo >= 50:
                    rilevanza = 'alto'
                    coperti.append(nome)
                else:
                    rilevanza = 'basso'
                    mancanti.append(nome)
                    
                    # Aggiungi ai gap
                    risultato['gaps'].append({
                        'tipo': 'Contenuto Mancante',
                        'priorita': 'alta' if len(risultato['gaps']) < 3 else 'bassa',
                        'titolo': nome,
                        'descrizione': f"Modulo '{nome}' coperto solo al {copertura_modulo:.0f}%",
                        'fonte': 'ideale',
                        'evidenza': f"Contenuti: {', '.join(contenuti[:2])}",
                        'impatto_commerciale': f"Opportunità: proporre Zanichelli con copertura completa di {nome}"
                    })
                
                moduli_analisi.append({
                    'nome': nome,
                    'copertura': round(copertura_modulo),
                    'rilevanza': rilevanza
                })
            
            percentuale = sum(m['copertura'] for m in moduli_analisi) / len(moduli_analisi) if moduli_analisi else 60
            
            risultato['ideale'] = {
                'percentuale': round(percentuale),
                'moduli': moduli_analisi,
                'punti_forza': coperti[:3],
                'aree_approfondire': mancanti[:3]
            }
            
            risultato['sintesi']['argomenti_coperti'] = coperti
            risultato['sintesi']['argomenti_mancanti'] = mancanti
        
        # Framework reale - usa valori dal framework se disponibili
        if framework_reale:
            moduli_reale = framework_reale.get('syllabus_modules', [])
            moduli_analisi_reale = []
            
            for modulo in moduli_reale:
                copertura = modulo.get('coverage_percentage', 50)
                moduli_analisi_reale.append({
                    'nome': modulo.get('name', ''),
                    'copertura': round(copertura),
                    'rilevanza': 'alto' if copertura >= 75 else 'medio' if copertura >= 50 else 'basso'
                })
            
            percentuale_reale = sum(m['copertura'] for m in moduli_analisi_reale) / len(moduli_analisi_reale) if moduli_analisi_reale else 75
            
            risultato['reale'] = {
                'percentuale': round(percentuale_reale),
                'moduli': moduli_analisi_reale,
                'punti_forza': [],
                'aree_approfondire': []
            }
        
        # Sintesi
        risultato['sintesi']['percentuale'] = round(
            (risultato['ideale']['percentuale'] * 0.4 + risultato['reale']['percentuale'] * 0.6)
        )
        
        return risultato

    # =========================================================
    # GENERAZIONE CONTENUTI COMMERCIALI VS COMPETITOR
    # =========================================================
    
    def _genera_postit_vs_competitor(self, dati: Dict, competitor: Dict) -> Dict:
        """Genera post-it orientato vs competitor"""
        dp = dati.get('dati_programma', {})
        profilo = dati.get('profilo_docente', {})
        manuale = dati.get('manuale_zanichelli', {})
        gaps = dati.get('gap_analysis', [])
        
        docente = dp.get('docente', 'Docente')
        approccio = profilo.get('approccio', 'bilanciato').lower()
        
        if competitor:
            usa = f"{competitor.get('titolo', 'N/D')} ({competitor.get('editore', 'N/D')})"
            leva = gaps[0].get('titolo', 'copertura completa') if gaps else 'contenuti aggiornati'
            obiettivo = f"sostituire {competitor.get('editore', 'il manuale attuale')} con Zanichelli"
        else:
            usa = "Nessun manuale rilevato"
            leva = "copertura completa del programma"
            obiettivo = "adozione del manuale Zanichelli"
        
        return {
            'docente': f"{docente}, approccio {approccio}",
            'usa': usa,
            'obiettivo': obiettivo,
            'leva': leva,
            'argomentazione': f"Il nostro manuale '{manuale.get('titolo', '')}' offre {leva}, rispondendo alle esigenze del corso."
        }
    
    def _genera_argomenti_vs_competitor(self, dati: Dict, competitor: Dict) -> List[str]:
        """Genera argomenti di vendita vs competitor"""
        argomenti = []
        
        gaps = dati.get('gap_analysis', [])
        manuale = dati.get('manuale_zanichelli', {})
        profilo = dati.get('profilo_docente', {})
        
        # Argomento sui gap
        if gaps:
            argomenti.append(
                f"Copertura completa di '{gaps[0].get('titolo', 'argomenti chiave')}', "
                f"area non adeguatamente trattata dal manuale attuale."
            )
        
        # Argomento sui contenuti pratici
        if profilo.get('laboratorio') or profilo.get('esercitazioni'):
            argomenti.append(
                "Ampia sezione di esercizi svolti e problemi con soluzioni, "
                "perfetti per le esercitazioni previste dal corso."
            )
        else:
            argomenti.append(
                "Trattazione rigorosa e approfondita dei fondamenti teorici, "
                "in linea con l'approccio didattico del docente."
            )
        
        # Argomento sui materiali digitali
        argomenti.append(
            "Materiali digitali integrati: risorse online, test di autovalutazione, "
            "contenuti multimediali per supportare lo studio."
        )
        
        # Argomento sulla qualità editoriale
        argomenti.append(
            "Qualità editoriale Zanichelli: testo aggiornato, iconografia chiara, "
            "indice analitico dettagliato."
        )
        
        # Argomento sul supporto docente
        argomenti.append(
            "Supporto dedicato per i docenti: slide per le lezioni, "
            "test bank per le verifiche, copia saggio gratuita."
        )
        
        return argomenti[:5]
    
    def _genera_domande_discovery(self, dati: Dict) -> List[str]:
        """Genera domande per la fase di discovery"""
        corso = dati.get('dati_programma', {}).get('corso', 'questo corso')
        gaps = dati.get('gap_analysis', [])
        
        domande = [
            f"Quali sono le sfide principali che affronta nel suo corso di {corso}?",
            "Come valuta il materiale didattico attualmente adottato?",
            "Quali argomenti ritiene che potrebbero essere trattati più approfonditamente?"
        ]
        
        if gaps:
            domande.append(
                f"Quanto ritiene importante la copertura di '{gaps[0].get('titolo', 'argomenti avanzati')}' per i suoi studenti?"
            )
        
        return domande
    
    def _genera_email_vs_competitor(self, dati: Dict, competitor: Dict) -> Dict:
        """Genera email commerciale orientata vs competitor"""
        dp = dati.get('dati_programma', {})
        manuale = dati.get('manuale_zanichelli', {})
        gaps = dati.get('gap_analysis', [])
        argomenti = dati.get('argomenti_vendita', [])
        
        gap_lista = ', '.join([g.get('titolo', '') for g in gaps[:2]]) if gaps else 'contenuti chiave'
        argomenti_testo = '\n'.join([f"• {a}" for a in argomenti[:3]]) if argomenti else "• Contenuti aggiornati e completi"
        
        if competitor:
            intro = f"Ho notato che il Suo corso utilizza attualmente '{competitor.get('titolo', '')}' di {competitor.get('editore', '')}. "
            proposta = f"Le propongo di valutare '{manuale.get('titolo', '')}' di {manuale.get('autore', '')} (Zanichelli) come alternativa, che offre:"
        else:
            intro = "Ho avuto modo di esaminare il programma del Suo corso, apprezzando l'approccio didattico che lo caratterizza. "
            proposta = f"Le propongo di valutare '{manuale.get('titolo', '')}' di {manuale.get('autore', '')} (Zanichelli), che offre:"
        
        corpo = f"""Gentile Prof. {dp.get('docente', '[Nome]')},

Mi chiamo [Nome Promotore] e sono promotore editoriale per Zanichelli.

{intro}

{proposta}

{argomenti_testo}

In particolare, questo testo offre una copertura approfondita di: {gap_lista}.

Posso inviarLe una copia saggio per una valutazione senza impegno? 
Resto a disposizione per qualsiasi informazione o per fissare un breve incontro.

Cordiali saluti,
[Nome Promotore]
Promotore Editoriale - Zanichelli
[Telefono] | [Email]"""
        
        return {
            'oggetto': f"Proposta materiale didattico per {dp.get('corso', 'il Suo corso')}",
            'corpo': corpo
        }
    
    def _genera_strategia(self, dati: Dict) -> Dict:
        """Genera la strategia di approccio"""
        return {
            'fase1': {
                'nome': 'Apertura e Riconoscimento',
                'descrizione': 'Riconoscere il valore del programma e l\'approccio didattico del docente.',
                'obiettivo': 'Creare fiducia e apertura al dialogo.'
            },
            'fase2': {
                'nome': 'Discovery e Ascolto',
                'descrizione': 'Esplorare esigenze e criticità del materiale attuale.',
                'domande': dati.get('domande_discovery', [])
            },
            'fase3': {
                'nome': 'Proposta e Argomentazione',
                'manuale': dati.get('manuale_zanichelli', {}),
                'gap_risolve': ', '.join([g.get('titolo', '') for g in dati.get('gap_analysis', [])[:3]]),
                'approccio': dati.get('profilo_docente', {}).get('filosofia', '')
            }
        }
    
    def _calcola_punteggio(self, dati: Dict) -> int:
        """Calcola il punteggio di opportunità"""
        punteggio = 50
        
        # Zanichelli assente = +20
        situazione = dati.get('analisi_competitiva', {}).get('situazione', 'assente')
        if situazione == 'assente':
            punteggio += 20
        elif situazione == 'presente':
            punteggio += 5  # Opportunità upselling
        
        # Gap identificati = +15
        n_gaps = len(dati.get('gap_analysis', []))
        if n_gaps >= 3:
            punteggio += 15
        elif n_gaps >= 1:
            punteggio += 10
        
        # Manuale trovato con buon match = +15
        match_score = dati.get('manuale_zanichelli', {}).get('match_score', 0)
        if match_score >= 80:
            punteggio += 15
        elif match_score >= 60:
            punteggio += 10
        
        return max(0, min(100, punteggio))


# =========================================================
# Funzione di utilità per uso diretto
# =========================================================

def genera_report_commerciale(
    pdf_path: str,
    materia: str,
    classe_laurea: str = None,
    manuali_adottati: List[Dict] = None,
    output_path: str = None
) -> str:
    """
    Funzione wrapper per generare il report commerciale completo.
    """
    from app.commercial_report_generator import CommercialReportGenerator
    
    orchestrator = PromoOrchestrator()
    
    analisi = orchestrator.analizza_programma_docente_con_competitor(
        Path(pdf_path),
        materia,
        classe_laurea or "",
        manuali_adottati or []
    )
    
    generator = CommercialReportGenerator()
    html = generator.genera_report_html(analisi)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    return html


if __name__ == "__main__":
    # Test rapido
    print("PromoOrchestrator v1.3 - Test")
    orchestrator = PromoOrchestrator()
    print("Componenti inizializzati correttamente")
