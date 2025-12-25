"""
CoreX - Promo Orchestrator v1.0
Orchestra l'analisi completa per il report commerciale del promotore
Collega: PDF → Profilo Docente → Framework → Manuali → Report
"""

import json
import os
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
        except Exception as e:
            print(f"[WARN] PedagogicalAnalyzer non disponibile: {e}")
            self.pedagogical_analyzer = None
        
        try:
            from app.manual_analyzer import ManualAnalyzer
            self.manual_analyzer = ManualAnalyzer(
                manuali_dir=self.manuali_dir,
                frameworks_dir=self.frameworks_dir
            )
        except Exception as e:
            print(f"[WARN] ManualAnalyzer non disponibile: {e}")
            self.manual_analyzer = None
        
        try:
            from app.pdf_extractor import PDFExtractor
            self.pdf_extractor = PDFExtractor()
        except Exception as e:
            print(f"[WARN] PDFExtractor non disponibile: {e}")
            self.pdf_extractor = None
        
        try:
            from app.program_metadata_extractor import ProgramMetadataExtractor
            self.metadata_extractor = ProgramMetadataExtractor()
        except Exception as e:
            print(f"[WARN] MetadataExtractor non disponibile: {e}")
            self.metadata_extractor = None
    
    def analizza_programma_docente(
        self,
        pdf_path: Path,
        materia: str,
        classe_laurea: str = None,
        use_framework_reale: bool = True
    ) -> Dict:
        """
        Esegue l'analisi completa di un programma d'esame.
        
        Args:
            pdf_path: Path al PDF del programma
            materia: Nome della materia (es. "Chimica_Organica")
            classe_laurea: Classe di laurea opzionale (es. "L-13")
            use_framework_reale: Se True, usa anche il framework reale dall'archivio
            
        Returns:
            Dizionario completo pronto per il report generator
        """
        risultato = {
            'timestamp': datetime.now().isoformat(),
            'pdf_analizzato': str(pdf_path),
            'materia': materia,
            'classe_laurea': classe_laurea
        }
        
        # === STEP 1: Estrazione testo dal PDF ===
        print("[1/7] Estrazione testo dal PDF...")
        testo_programma = self._estrai_testo_pdf(pdf_path)
        if not testo_programma:
            risultato['errore'] = "Impossibile estrarre testo dal PDF"
            return risultato
        
        # === STEP 2: Estrazione metadati (docente, corso, università, CFU) ===
        print("[2/7] Estrazione metadati programma...")
        metadati = self._estrai_metadati(testo_programma, pdf_path)
        risultato['dati_programma'] = metadati
        
        # === STEP 3: Analisi profilo pedagogico docente ===
        print("[3/7] Analisi profilo pedagogico...")
        profilo_docente = self._analizza_profilo_docente(testo_programma, metadati)
        risultato['profilo_docente'] = profilo_docente
        
        # === STEP 4: Caricamento framework (ideale + reale) ===
        print("[4/7] Caricamento framework disciplinari...")
        framework_ideale = self._carica_framework_ideale(materia)
        framework_reale = self._carica_framework_reale(materia) if use_framework_reale else None
        
        # === STEP 5: Estrazione bibliografia e identificazione competitor ===
        print("[5/7] Analisi bibliografia...")
        bibliografia = self._estrai_bibliografia(testo_programma)
        concorrente = self._identifica_concorrente(bibliografia)
        risultato['concorrente_principale'] = concorrente
        risultato['bibliografia_completa'] = bibliografia
        risultato['analisi_competitiva'] = self._analizza_situazione_competitiva(bibliografia)
        
        # === STEP 6: Matching manuale Zanichelli migliore ===
        print("[6/7] Ricerca manuale Zanichelli ottimale...")
        manuale_match = self._trova_manuale_zanichelli_migliore(
            materia, testo_programma, framework_ideale, framework_reale
        )
        risultato['manuale_zanichelli'] = manuale_match['manuale']
        risultato['match_details'] = manuale_match['details']
        
        # === STEP 7: Analisi copertura e gap ===
        print("[7/7] Calcolo copertura e gap...")
        copertura = self._calcola_copertura_completa(
            testo_programma, framework_ideale, framework_reale, manuale_match
        )
        risultato['copertura_ideale'] = copertura['ideale']
        risultato['copertura_reale'] = copertura['reale']
        risultato['copertura_argomenti'] = copertura['sintesi']
        risultato['gap_analysis'] = copertura['gaps']
        
        # === Genera contenuti commerciali ===
        risultato['postit'] = self._genera_postit(risultato)
        risultato['argomenti_vendita'] = self._genera_argomenti_vendita(risultato)
        risultato['domande_discovery'] = self._genera_domande_discovery(risultato)
        risultato['email'] = self._genera_email(risultato)
        risultato['strategia'] = self._genera_strategia(risultato)
        risultato['punteggio_opportunita'] = self._calcola_punteggio(risultato)
        
        print("[OK] Analisi completata!")
        return risultato
    
    # =========================================================
    # STEP 1: Estrazione PDF
    # =========================================================
    
    def _estrai_testo_pdf(self, pdf_path: Path) -> Optional[str]:
        """Estrae il testo dal PDF"""
        if self.pdf_extractor:
            try:
                return self.pdf_extractor.extract_text(pdf_path)
            except:
                pass
        
        # Fallback con PyMuPDF
        try:
            import fitz
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"[ERR] Estrazione PDF fallita: {e}")
            return None
    
    # =========================================================
    # STEP 2: Estrazione Metadati
    # =========================================================
    
    def _estrai_metadati(self, testo: str, pdf_path: Path) -> Dict:
        """Estrae metadati dal programma"""
        metadati = {
            'docente': 'Docente non specificato',
            'corso': 'Corso non specificato',
            'universita': 'Università non specificata',
            'cfu': 'N/D',
            'ore': 'N/D',
            'anno_accademico': 'N/D'
        }
        
        # Prova con MetadataExtractor
        if self.metadata_extractor:
            try:
                extracted = self.metadata_extractor.extract(testo)
                metadati.update({k: v for k, v in extracted.items() if v})
            except:
                pass
        
        # Fallback: estrai dal nome file
        filename = pdf_path.stem
        parts = filename.split('_')
        
        if len(parts) >= 2:
            # Formato atteso: Materia_Università_Docente.pdf
            if len(parts) >= 3:
                metadati['universita'] = parts[1].replace('_', ' ')
                metadati['docente'] = parts[-1].replace('_', ' ')
            metadati['corso'] = parts[0].replace('_', ' ')
        
        # Estrazione pattern dal testo
        import re
        
        # Docente
        docente_patterns = [
            r'(?:docente|prof\.?|professore)[:\s]+([A-Z][a-zàèéìòù]+\s+[A-Z][a-zàèéìòù]+)',
            r'([A-Z][a-zàèéìòù]+\s+[A-Z][a-zàèéìòù]+)\s*[-–]\s*(?:docente|titolare)',
        ]
        for pattern in docente_patterns:
            match = re.search(pattern, testo, re.IGNORECASE)
            if match:
                metadati['docente'] = match.group(1).strip()
                break
        
        # CFU
        cfu_match = re.search(r'(\d+)\s*(?:CFU|crediti)', testo, re.IGNORECASE)
        if cfu_match:
            metadati['cfu'] = int(cfu_match.group(1))
        
        # Ore
        ore_match = re.search(r'(\d+)\s*(?:ore|h)', testo, re.IGNORECASE)
        if ore_match:
            metadati['ore'] = int(ore_match.group(1))
        
        # Corso
        corso_patterns = [
            r'(?:insegnamento|corso)[:\s]+([^\n]+)',
            r'(?:denominazione)[:\s]+([^\n]+)',
        ]
        for pattern in corso_patterns:
            match = re.search(pattern, testo, re.IGNORECASE)
            if match:
                corso = match.group(1).strip()
                if len(corso) > 5 and len(corso) < 100:
                    metadati['corso'] = corso
                    break
        
        return metadati
    
    # =========================================================
    # STEP 3: Profilo Pedagogico
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
        
        if self.pedagogical_analyzer:
            try:
                result = self.pedagogical_analyzer.analyze_program(testo, metadati)
                
                # Mappa i risultati
                approach_map = {
                    'teorico': 'Teorico',
                    'pratico': 'Pratico', 
                    'bilanciato': 'Bilanciato'
                }
                profilo['approccio'] = approach_map.get(
                    result.philosophy.approach.value, 'Bilanciato'
                )
                
                rigor_map = {
                    'alto_formale': 'Alto',
                    'accessibile': 'Accessibile',
                    'misto': 'Medio'
                }
                profilo['rigore'] = rigor_map.get(
                    result.philosophy.rigor_level.value, 'Alto'
                )
                
                profilo['bilanciamento'] = result.philosophy.application_emphasis
                profilo['metodi_didattici'] = result.priorities.teaching_methods or profilo['metodi_didattici']
                profilo['metodi_valutazione'] = result.priorities.assessment_methods or profilo['metodi_valutazione']
                profilo['laboratorio'] = 'laboratorio' in ' '.join(profilo['metodi_didattici']).lower()
                profilo['esercitazioni'] = 'esercitazioni' in ' '.join(profilo['metodi_didattici']).lower()
                profilo['insight'] = result.profile_summary or ''
                profilo['filosofia'] = result.suggested_approach or ''
                
                if result.key_insights:
                    profilo['argomenti_chiave'] = ', '.join(result.key_insights[:3])
                
            except Exception as e:
                print(f"[WARN] Analisi pedagogica fallback: {e}")
                profilo = self._analisi_pedagogica_euristica(testo, profilo)
        else:
            profilo = self._analisi_pedagogica_euristica(testo, profilo)
        
        return profilo
    
    def _analisi_pedagogica_euristica(self, testo: str, profilo: Dict) -> Dict:
        """Analisi pedagogica basata su euristiche"""
        testo_lower = testo.lower()
        
        # Teoria vs Pratica
        teoria_kw = ['teoria', 'teorico', 'teorema', 'dimostrazione', 'fondamenti']
        pratica_kw = ['laboratorio', 'esercitazione', 'pratico', 'applicazione', 'esperimento']
        
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
        
        # Metodi
        if 'laboratorio' in testo_lower:
            profilo['laboratorio'] = True
            if 'laboratorio' not in profilo['metodi_didattici']:
                profilo['metodi_didattici'].append('laboratorio')
        
        if 'progetto' in testo_lower or 'tesina' in testo_lower:
            if 'progetto' not in profilo['metodi_valutazione']:
                profilo['metodi_valutazione'].append('progetto')
        
        return profilo
    
    # =========================================================
    # STEP 4: Caricamento Framework
    # =========================================================
    
    def _carica_framework_ideale(self, materia: str) -> Optional[Dict]:
        """Carica il framework ideale per la materia"""
        # Cerca corrispondenza esatta o parziale
        materia_normalized = materia.replace(' ', '_').replace('-', '_')
        
        for fw_file in self.frameworks_dir.glob("*.json"):
            if materia_normalized.lower() in fw_file.stem.lower():
                try:
                    with open(fw_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
        
        # Prova match più ampio
        for fw_file in self.frameworks_dir.glob("*.json"):
            fw_name = fw_file.stem.lower().replace('_', ' ')
            if any(word in fw_name for word in materia.lower().split('_')):
                try:
                    with open(fw_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
        
        return None
    
    def _carica_framework_reale(self, materia: str) -> Optional[Dict]:
        """Carica il framework reale più recente dall'archivio"""
        if not self.archivio_dir.exists():
            return None
        
        materia_normalized = materia.replace(' ', '_').lower()
        
        # Cerca nell'archivio, ordinato per data (più recente prima)
        archivi = sorted(self.archivio_dir.iterdir(), reverse=True)
        
        for archivio in archivi:
            if archivio.is_dir() and materia_normalized in archivio.name.lower():
                fw_file = archivio / "framework_aggiornato.json"
                if fw_file.exists():
                    try:
                        with open(fw_file, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except:
                        pass
        
        return None
    
    # =========================================================
    # STEP 5: Bibliografia e Competitor
    # =========================================================
    
    def _estrai_bibliografia(self, testo: str) -> List[Dict]:
        """Estrae la bibliografia dal programma"""
        import re
        
        bibliografia = []
        
        # Pattern per identificare libri
        # Formato tipico: Autore, "Titolo", Editore, Anno
        patterns = [
            r'([A-Z][a-zàèéìòù]+(?:\s+[A-Z][a-zàèéìòù]+)?)\s*[,\-–]\s*["\"]?([^"\"]+)["\"]?\s*[,\-–]\s*([\w\s]+?)(?:\s*,\s*(\d{4}))?',
            r'([A-Z][a-zàèéìòù]+)\s+(?:et\s+al\.?)?\s*["\"]([^"\"]+)["\"]',
        ]
        
        # Cerca sezione bibliografia
        biblio_section = ""
        markers = ['bibliografia', 'testi consigliati', 'testi di riferimento', 'libri di testo', 'materiale didattico']
        
        testo_lower = testo.lower()
        for marker in markers:
            idx = testo_lower.find(marker)
            if idx != -1:
                biblio_section = testo[idx:idx+2000]
                break
        
        if not biblio_section:
            biblio_section = testo
        
        # Cerca editori noti
        editori_noti = {
            'zanichelli': 'Zanichelli',
            'edises': 'EdiSES',
            'piccin': 'Piccin',
            'mcgraw': 'McGraw-Hill',
            'pearson': 'Pearson',
            'edi-ermes': 'Edi-Ermes',
            'edi ermes': 'Edi-Ermes',
            'ambrosiana': 'Ambrosiana',
            'elsevier': 'Elsevier',
            'springer': 'Springer',
            'wiley': 'Wiley',
            'utet': 'UTET',
            'cea': 'CEA'
        }
        
        # Cerca menzioni di editori
        for editore_key, editore_nome in editori_noti.items():
            if editore_key in biblio_section.lower():
                # Cerca il contesto intorno all'editore
                idx = biblio_section.lower().find(editore_key)
                context = biblio_section[max(0, idx-150):idx+50]
                
                # Estrai autore e titolo dal contesto
                entry = {
                    'titolo': '',
                    'autore': '',
                    'editore': editore_nome,
                    'ruolo': 'consultazione'
                }
                
                # Pattern per autore
                autore_match = re.search(r'([A-Z][a-zàèéìòù]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-zàèéìòù]+)?)', context)
                if autore_match:
                    entry['autore'] = autore_match.group(1).strip()
                
                # Pattern per titolo
                titolo_match = re.search(r'["\"]([^"\"]+)["\"]', context)
                if titolo_match:
                    entry['titolo'] = titolo_match.group(1).strip()
                elif entry['autore']:
                    # Prova a prendere testo dopo l'autore
                    after_author = context[context.find(entry['autore'])+len(entry['autore']):]
                    titolo_match = re.search(r'[,\-–:]\s*([^,\-–\n]{10,60})', after_author)
                    if titolo_match:
                        entry['titolo'] = titolo_match.group(1).strip()
                
                # Determina se è principale
                if any(kw in context.lower() for kw in ['testo adottato', 'libro di testo', 'testo principale', 'obbligatorio']):
                    entry['ruolo'] = 'principale'
                
                if entry['titolo'] or entry['autore']:
                    # Evita duplicati
                    if not any(b['editore'] == entry['editore'] and b['autore'] == entry['autore'] for b in bibliografia):
                        bibliografia.append(entry)
        
        return bibliografia
    
    def _identifica_concorrente(self, bibliografia: List[Dict]) -> Optional[Dict]:
        """Identifica il principale manuale concorrente"""
        # Prima cerca il principale non-Zanichelli
        for libro in bibliografia:
            if libro.get('ruolo') == 'principale' and libro.get('editore', '').upper() != 'ZANICHELLI':
                return {
                    'titolo': libro.get('titolo', 'Titolo non specificato'),
                    'autore': libro.get('autore', 'Autore non specificato'),
                    'editore': libro.get('editore', 'Editore non specificato')
                }
        
        # Altrimenti prendi il primo non-Zanichelli
        for libro in bibliografia:
            if libro.get('editore', '').upper() != 'ZANICHELLI':
                return {
                    'titolo': libro.get('titolo', 'Titolo non specificato'),
                    'autore': libro.get('autore', 'Autore non specificato'),
                    'editore': libro.get('editore', 'Editore non specificato')
                }
        
        return None
    
    def _analizza_situazione_competitiva(self, bibliografia: List[Dict]) -> Dict:
        """Analizza la situazione competitiva"""
        zanichelli_presente = any(
            b.get('editore', '').upper() == 'ZANICHELLI' for b in bibliografia
        )
        
        if zanichelli_presente:
            return {
                'situazione': 'presente',
                'descrizione': 'Zanichelli già in bibliografia - opportunità di consolidamento'
            }
        elif not bibliografia:
            return {
                'situazione': 'assente',
                'descrizione': 'Nessuna bibliografia rilevata - opportunità di prima adozione'
            }
        else:
            return {
                'situazione': 'assente',
                'descrizione': 'Zanichelli non presente - opportunità di conquista'
            }
    
    # =========================================================
    # STEP 6: Matching Manuale Zanichelli
    # =========================================================
    
    def _trova_manuale_zanichelli_migliore(
        self,
        materia: str,
        testo_programma: str,
        framework_ideale: Dict,
        framework_reale: Dict
    ) -> Dict:
        """Trova il manuale Zanichelli più adatto"""
        
        risultato = {
            'manuale': {
                'titolo': 'Manuale non trovato',
                'autore': 'N/D',
                'match_score': 0,
                'capitoli_rilevanti': []
            },
            'details': {}
        }
        
        if not self.manual_analyzer:
            return risultato
        
        # Cerca manuali Zanichelli per la materia
        materia_normalized = materia.replace(' ', '_')
        manuali = self.manual_analyzer.get_manuals_for_subject(materia_normalized)
        
        if not manuali.get('zanichelli'):
            # Prova con varianti del nome
            for subject in self.manual_analyzer.get_available_subjects():
                if materia.lower().replace('_', ' ') in subject.lower().replace('_', ' '):
                    manuali = self.manual_analyzer.get_manuals_for_subject(subject)
                    break
        
        if not manuali.get('zanichelli'):
            return risultato
        
        # Analizza ogni manuale vs framework
        best_score = 0
        best_manual = None
        best_analysis = None
        
        for manual_info in manuali['zanichelli']:
            manual = self.manual_analyzer.load_manual(manual_info['path'])
            if not manual:
                continue
            
            # Analizza vs framework ideale
            if framework_ideale:
                analysis = self.manual_analyzer.analyze_manual_vs_ideal(manual, framework_ideale)
                score = analysis.get('overall_coverage', 0)
                
                # Bonus se copre anche framework reale
                if framework_reale:
                    real_analysis = self.manual_analyzer.analyze_manual_vs_real(manual, framework_reale)
                    real_score = real_analysis.get('overall_weighted_coverage', 0)
                    score = (score * 0.4) + (real_score * 0.6)  # Peso maggiore al reale
                
                if score > best_score:
                    best_score = score
                    best_manual = manual
                    best_analysis = analysis
        
        if best_manual:
            # Trova capitoli più rilevanti
            capitoli_rilevanti = []
            if best_analysis:
                for mod in best_analysis.get('modules_analysis', [])[:5]:
                    if mod.get('coverage_percentage', 0) >= 75:
                        for match in mod.get('content_matches', []):
                            if match.get('matched_by') and match.get('type') == 'chapter':
                                cap = f"Cap. {match.get('chapter', '')}: {match.get('matched_by', '')}"
                                if cap not in capitoli_rilevanti:
                                    capitoli_rilevanti.append(cap)
            
            risultato['manuale'] = {
                'titolo': best_manual.get('title', 'N/D'),
                'autore': best_manual.get('author', 'N/D'),
                'match_score': round(best_score, 0),
                'capitoli_rilevanti': capitoli_rilevanti[:5]
            }
            risultato['details'] = best_analysis or {}
        
        return risultato
    
    # =========================================================
    # STEP 7: Copertura e Gap
    # =========================================================
    
    def _calcola_copertura_completa(
        self,
        testo_programma: str,
        framework_ideale: Dict,
        framework_reale: Dict,
        manuale_match: Dict
    ) -> Dict:
        """Calcola la copertura del programma rispetto ai framework"""
        
        risultato = {
            'ideale': {'percentuale': 54, 'moduli': [], 'punti_forza': [], 'aree_approfondire': []},
            'reale': {'percentuale': 77, 'moduli': [], 'punti_forza': [], 'aree_approfondire': []},
            'sintesi': {'percentuale': 0, 'argomenti_coperti': [], 'argomenti_mancanti': []},
            'gaps': []
        }
        
        testo_lower = testo_programma.lower()
        
        # Analisi vs Framework Ideale
        if framework_ideale:
            moduli_ideale = framework_ideale.get('syllabus_modules', [])
            coperti = []
            mancanti = []
            moduli_analisi = []
            
            for modulo in moduli_ideale:
                nome = modulo.get('name', '')
                contenuti = modulo.get('core_contents', [])
                
                # Conta quanti contenuti sono menzionati nel programma
                trovati = 0
                for contenuto in contenuti:
                    contenuto_lower = contenuto.lower()
                    # Cerca il contenuto o parole chiave
                    keywords = contenuto_lower.split()[:3]  # Prime 3 parole
                    if any(kw in testo_lower for kw in keywords if len(kw) > 3):
                        trovati += 1
                
                copertura_modulo = (trovati / len(contenuti) * 100) if contenuti else 0
                
                # Determina rilevanza
                if copertura_modulo >= 75:
                    rilevanza = 'alto'
                    coperti.append(nome)
                elif copertura_modulo >= 50:
                    rilevanza = 'medio'
                elif copertura_modulo >= 25:
                    rilevanza = 'basso'
                    mancanti.append(nome)
                else:
                    rilevanza = 'assente'
                    mancanti.append(nome)
                    
                    # Aggiungi ai gap
                    risultato['gaps'].append({
                        'tipo': 'Contenuto Mancante',
                        'priorita': 'alta' if modulo.get('id', 0) <= 6 else 'bassa',
                        'titolo': nome,
                        'descrizione': f"Modulo '{nome}' coperto solo al {copertura_modulo:.0f}%",
                        'fonte': 'ideale',
                        'evidenza': f"Contenuti mancanti: {', '.join(contenuti[:3])}",
                        'impatto_commerciale': f"Opportunità di proporre manuale Zanichelli con copertura completa di {nome}"
                    })
                
                moduli_analisi.append({
                    'nome': nome,
                    'copertura': round(copertura_modulo),
                    'rilevanza': rilevanza
                })
            
            # Calcola percentuale totale
            percentuale_ideale = sum(m['copertura'] for m in moduli_analisi) / len(moduli_analisi) if moduli_analisi else 0
            
            risultato['ideale'] = {
                'percentuale': round(percentuale_ideale),
                'moduli': moduli_analisi,
                'punti_forza': [f"{m['nome']}: copertura eccellente ({m['copertura']}%)" for m in moduli_analisi if m['copertura'] >= 100][:3],
                'aree_approfondire': [f"{nome}: {', '.join(framework_ideale['syllabus_modules'][i].get('core_contents', [])[:3])}" 
                                     for i, nome in enumerate(mancanti[:3])]
            }
            
            risultato['sintesi']['argomenti_coperti'] = coperti
            risultato['sintesi']['argomenti_mancanti'] = mancanti
        
        # Analisi vs Framework Reale
        if framework_reale:
            moduli_reale = framework_reale.get('syllabus_modules', [])
            moduli_analisi_reale = []
            
            for modulo in moduli_reale:
                nome = modulo.get('name', '')
                # Usa coverage dal framework reale
                copertura_modulo = modulo.get('coverage_percentage', 50)
                status = modulo.get('status', 'unknown')
                
                if copertura_modulo >= 75:
                    rilevanza = 'alto'
                elif copertura_modulo >= 50:
                    rilevanza = 'medio'
                else:
                    rilevanza = 'basso'
                
                moduli_analisi_reale.append({
                    'nome': nome,
                    'copertura': round(copertura_modulo),
                    'rilevanza': rilevanza
                })
            
            percentuale_reale = sum(m['copertura'] for m in moduli_analisi_reale) / len(moduli_analisi_reale) if moduli_analisi_reale else 0
            
            risultato['reale'] = {
                'percentuale': round(percentuale_reale),
                'moduli': moduli_analisi_reale,
                'punti_forza': [f"{m['nome']}: copertura eccellente ({m['copertura']}%)" for m in moduli_analisi_reale if m['copertura'] >= 100][:3],
                'aree_approfondire': [f"{m['nome']}" for m in moduli_analisi_reale if m['copertura'] < 50][:3]
            }
        
        # Percentuale sintesi (media pesata)
        perc_ideale = risultato['ideale']['percentuale']
        perc_reale = risultato['reale']['percentuale']
        risultato['sintesi']['percentuale'] = round((perc_ideale * 0.3 + perc_reale * 0.7))
        
        return risultato
    
    # =========================================================
    # Generazione Contenuti Commerciali
    # =========================================================
    
    def _genera_postit(self, dati: Dict) -> Dict:
        """Genera il post-it commerciale"""
        docente = dati.get('dati_programma', {}).get('docente', 'Docente')
        approccio = dati.get('profilo_docente', {}).get('approccio', 'bilanciato').lower()
        
        concorrente = dati.get('concorrente_principale', {})
        usa = f"{concorrente.get('titolo', 'N/D')} ({concorrente.get('editore', 'N/D')})" if concorrente else "Nessun manuale rilevato"
        
        gaps = dati.get('gap_analysis', [])
        leva = gaps[0].get('titolo', 'contenuti completi') if gaps else 'completezza dei contenuti'
        
        manuale = dati.get('manuale_zanichelli', {})
        
        return {
            'docente': f"{docente}, approccio {approccio}",
            'usa': usa,
            'obiettivo': 'proporre il manuale Zanichelli',
            'leva': leva,
            'argomentazione': f"Il nostro manuale offre una copertura approfondita di {leva}, fondamentale per il corso."
        }
    
    def _genera_argomenti_vendita(self, dati: Dict) -> List[str]:
        """Genera gli argomenti di vendita"""
        argomenti = []
        
        gaps = dati.get('gap_analysis', [])
        if gaps:
            argomenti.append(f"Copertura completa di {gaps[0].get('titolo', 'argomenti chiave')}, essenziale per il corso.")
        
        profilo = dati.get('profilo_docente', {})
        if profilo.get('laboratorio'):
            argomenti.append("Esercizi pratici e problemi di laboratorio che stimolano il problem solving e l'applicazione pratica.")
        else:
            argomenti.append("Esercizi pratici e problemi che stimolano il problem solving e l'applicazione pratica.")
        
        argomenti.append("Materiali digitali e risorse online per supportare l'apprendimento degli studenti.")
        
        return argomenti
    
    def _genera_domande_discovery(self, dati: Dict) -> List[str]:
        """Genera domande per la fase di discovery"""
        corso = dati.get('dati_programma', {}).get('corso', 'questo corso')
        
        domande = [
            f"Quali sono le sfide principali che affronta nel suo corso di {corso}?",
            "Come valuta l'importanza dei contenuti pratici e di laboratorio nel suo programma?"
        ]
        
        gaps = dati.get('gap_analysis', [])
        if gaps:
            domande.append(f"Quanto ritiene importante la copertura di {gaps[0].get('titolo', 'argomenti avanzati')} per i suoi studenti?")
        
        return domande
    
    def _genera_email(self, dati: Dict) -> Dict:
        """Genera l'email commerciale"""
        dp = dati.get('dati_programma', {})
        manuale = dati.get('manuale_zanichelli', {})
        gaps = dati.get('gap_analysis', [])
        argomenti = dati.get('argomenti_vendita', [])
        
        gap_lista = ', '.join([g.get('titolo', '') for g in gaps[:2]]) if gaps else 'contenuti chiave'
        leva = gaps[0].get('titolo', 'contenuti completi') if gaps else 'contenuti completi'
        
        argomenti_testo = '\n'.join([f"• {a}" for a in argomenti[:3]])
        
        corpo = f"""Gentile Prof. {dp.get('docente', '[Nome]')},

Mi chiamo [Nome Promotore] e sono promotore editoriale per Zanichelli. Ho avuto modo di esaminare il programma del Suo corso di {dp.get('corso', '[Corso]')} presso {dp.get('universita', '[Università]')}, apprezzando l'approccio didattico che caratterizza il Suo insegnamento.

Ho notato che il programma dedica particolare attenzione a {leva}, un'area in cui il manuale attualmente adottato potrebbe non offrire una copertura completa.

Per questo motivo, Le propongo di valutare "{manuale.get('titolo', '[Titolo]')}" di {manuale.get('autore', '[Autore]')} (Zanichelli), che offre:
{argomenti_testo}

In particolare, questo testo risolve le criticità relative a: {gap_lista}.

Posso inviarLe una copia saggio per una valutazione senza impegno? Resto a disposizione per qualsiasi informazione o per fissare un breve incontro.

Cordiali saluti,
[Nome Promotore]
Promotore Editoriale - Zanichelli
[Telefono] | [Email]"""
        
        return {
            'oggetto': f"Supporto didattico per il corso di {dp.get('corso', '[Corso]')}",
            'corpo': corpo
        }
    
    def _genera_strategia(self, dati: Dict) -> Dict:
        """Genera la strategia di approccio"""
        return {
            'fase1': {
                'nome': 'Apertura e Riconoscimento',
                'descrizione': 'Riconoscere il valore del programma del docente e il suo approccio didattico. Stabilire rapport.',
                'obiettivo': 'Creare fiducia e apertura al dialogo.'
            },
            'fase2': {
                'nome': 'Discovery e Ascolto',
                'descrizione': 'Esplorare le esigenze e le criticità attuali.',
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
        
        # Situazione competitiva
        situazione = dati.get('analisi_competitiva', {}).get('situazione', 'assente')
        if situazione == 'assente':
            punteggio += 20
        elif situazione == 'presente':
            punteggio -= 10
        
        # Copertura
        copertura = dati.get('copertura_argomenti', {}).get('percentuale', 50)
        if copertura >= 70:
            punteggio += 15
        elif copertura >= 50:
            punteggio += 10
        
        # Match score manuale
        match_score = dati.get('manuale_zanichelli', {}).get('match_score', 0)
        if match_score >= 80:
            punteggio += 15
        elif match_score >= 60:
            punteggio += 10
        
        # Gap identificati (più gap = più opportunità)
        n_gaps = len(dati.get('gap_analysis', []))
        if n_gaps >= 3:
            punteggio += 10
        elif n_gaps >= 1:
            punteggio += 5
        
        return max(0, min(100, punteggio))


# =========================================================
# Funzione di utilità per uso diretto
# =========================================================

def genera_report_commerciale(
    pdf_path: str,
    materia: str,
    classe_laurea: str = None,
    output_path: str = None
) -> str:
    """
    Funzione wrapper per generare il report commerciale completo.
    
    Args:
        pdf_path: Path al PDF del programma
        materia: Nome della materia
        classe_laurea: Classe di laurea opzionale
        output_path: Path dove salvare l'HTML (opzionale)
        
    Returns:
        HTML del report
    """
    from app.commercial_report_generator import CommercialReportGenerator
    
    # Esegui analisi
    orchestrator = PromoOrchestrator()
    analisi = orchestrator.analizza_programma_docente(
        Path(pdf_path),
        materia,
        classe_laurea
    )
    
    # Genera report HTML
    generator = CommercialReportGenerator()
    html = generator.genera_report_html(analisi)
    
    # Salva se richiesto
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    return html
