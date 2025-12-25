"""
CoreX - Commercial Analyzer
Analisi commerciale dei programmi d'esame per Zanichelli
"""

import json
import os
from datetime import datetime
from pathlib import Path

class CommercialAnalyzer:
    """Analizzatore commerciale per programmi d'esame universitari"""
    
    def __init__(self, config_path="config/frameworks"):
        self.config_path = Path(config_path)
        self.frameworks = {}
        self.analisi_dir = Path("data/analisi_commerciali")
        self.analisi_dir.mkdir(parents=True, exist_ok=True)
        self._load_frameworks()
    
    def _load_frameworks(self):
        """Carica i framework disciplinari dalla cartella config"""
        if self.config_path.exists():
            for file in self.config_path.glob("*.json"):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        framework = json.load(f)
                        nome = file.stem
                        self.frameworks[nome] = framework
                except Exception as e:
                    print(f"Errore caricamento framework {file}: {e}")
    
    def get_framework(self, materia):
        """Restituisce il framework per una materia specifica"""
        return self.frameworks.get(materia, {})
    
    def get_materie_disponibili(self):
        """Restituisce l'elenco delle materie con framework disponibile"""
        return list(self.frameworks.keys())
    
    def analizza_programma(self, dati_programma, contenuto_pdf, bibliografia, manuale_zanichelli):
        """
        Esegue l'analisi commerciale completa
        
        Args:
            dati_programma: dict con docente, corso, universita, cfu, materia
            contenuto_pdf: testo estratto dal PDF del programma
            bibliografia: lista di dict con titolo, autore, editore, ruolo
            manuale_zanichelli: dict con titolo, autore (il manuale Zanichelli da promuovere)
        
        Returns:
            dict con risultati dell'analisi
        """
        materia = dati_programma.get('materia', '')
        framework = self.get_framework(materia)
        
        # Identifica il manuale concorrente principale
        concorrente_principale = self._identifica_concorrente_principale(bibliografia)
        
        # Analisi copertura argomenti
        copertura = self._analizza_copertura(contenuto_pdf, framework)
        
        # Analisi competitiva
        analisi_competitiva = self._analizza_competizione(
            bibliografia, 
            manuale_zanichelli,
            framework
        )
        
        # Genera raccomandazioni
        raccomandazioni = self._genera_raccomandazioni(
            dati_programma,
            copertura,
            analisi_competitiva,
            manuale_zanichelli,
            concorrente_principale
        )
        
        # Calcola punteggio opportunità
        punteggio = self._calcola_punteggio_opportunita(
            copertura,
            analisi_competitiva,
            dati_programma
        )
        
        risultato = {
            'timestamp': datetime.now().isoformat(),
            'dati_programma': dati_programma,
            'manuale_zanichelli': manuale_zanichelli,
            'concorrente_principale': concorrente_principale,
            'bibliografia_completa': bibliografia,
            'copertura_argomenti': copertura,
            'analisi_competitiva': analisi_competitiva,
            'raccomandazioni': raccomandazioni,
            'punteggio_opportunita': punteggio,
            'contenuto_programma': contenuto_pdf[:2000]  # Primi 2000 caratteri per riferimento
        }
        
        # Salva automaticamente l'analisi
        self._salva_analisi(risultato)
        
        return risultato
    
    def _identifica_concorrente_principale(self, bibliografia):
        """Identifica il manuale concorrente principale dalla bibliografia"""
        for libro in bibliografia:
            if libro.get('ruolo') == 'principale':
                editore = libro.get('editore', '').upper()
                if editore != 'ZANICHELLI':
                    return {
                        'titolo': libro.get('titolo', ''),
                        'autore': libro.get('autore', ''),
                        'editore': libro.get('editore', '')
                    }
        
        # Se non trova un principale non-Zanichelli, prende il primo non-Zanichelli
        for libro in bibliografia:
            editore = libro.get('editore', '').upper()
            if editore != 'ZANICHELLI':
                return {
                    'titolo': libro.get('titolo', ''),
                    'autore': libro.get('autore', ''),
                    'editore': libro.get('editore', '')
                }
        
        return None
    
    def _analizza_copertura(self, contenuto_pdf, framework):
        """Analizza la copertura degli argomenti del framework nel programma"""
        if not framework:
            return {'percentuale': 0, 'argomenti_trovati': [], 'argomenti_mancanti': []}
        
        contenuto_lower = contenuto_pdf.lower()
        argomenti_core = framework.get('argomenti_core', [])
        
        trovati = []
        mancanti = []
        
        for argomento in argomenti_core:
            # Cerca l'argomento e le sue varianti
            keywords = [argomento.lower()]
            if 'varianti' in framework:
                keywords.extend([v.lower() for v in framework.get('varianti', {}).get(argomento, [])])
            
            found = any(kw in contenuto_lower for kw in keywords)
            if found:
                trovati.append(argomento)
            else:
                mancanti.append(argomento)
        
        percentuale = (len(trovati) / len(argomenti_core) * 100) if argomenti_core else 0
        
        return {
            'percentuale': round(percentuale, 1),
            'argomenti_trovati': trovati,
            'argomenti_mancanti': mancanti,
            'totale_argomenti': len(argomenti_core)
        }
    
    def _analizza_competizione(self, bibliografia, manuale_zanichelli, framework):
        """Analizza il posizionamento competitivo"""
        
        zanichelli_presente = False
        concorrenti = []
        
        for libro in bibliografia:
            editore = libro.get('editore', '').upper()
            if editore == 'ZANICHELLI':
                zanichelli_presente = True
            else:
                concorrenti.append({
                    'titolo': libro.get('titolo', ''),
                    'autore': libro.get('autore', ''),
                    'editore': libro.get('editore', ''),
                    'ruolo': libro.get('ruolo', 'consultazione')
                })
        
        # Valutazione situazione competitiva
        if zanichelli_presente:
            situazione = 'DIFESA'
            descrizione = f"{manuale_zanichelli['autore']}, {manuale_zanichelli['titolo']} è già in adozione"
        elif len(concorrenti) == 0:
            situazione = 'OPPORTUNITA_ALTA'
            descrizione = 'Nessun manuale specifico indicato - opportunità di prima adozione'
        else:
            concorrente_princ = next((c for c in concorrenti if c['ruolo'] == 'principale'), concorrenti[0] if concorrenti else None)
            if concorrente_princ:
                situazione = 'CONQUISTA'
                descrizione = f"USA: {concorrente_princ['autore']}, {concorrente_princ['titolo']} ({concorrente_princ['editore']})"
            else:
                situazione = 'OPPORTUNITA_MEDIA'
                descrizione = 'Solo testi di consultazione indicati'
        
        return {
            'zanichelli_presente': zanichelli_presente,
            'situazione': situazione,
            'descrizione': descrizione,
            'concorrenti': concorrenti,
            'numero_concorrenti': len(concorrenti)
        }
    def _genera_raccomandazioni(self, dati_programma, copertura, analisi_competitiva, manuale_zanichelli, concorrente_principale):
        """Genera raccomandazioni commerciali personalizzate"""
        
        raccomandazioni = []
        priorita = 'MEDIA'
        
        situazione = analisi_competitiva['situazione']
        manuale_nome_completo = f"{manuale_zanichelli['autore']}, {manuale_zanichelli['titolo']}"
        
        if situazione == 'DIFESA':
            priorita = 'BASSA'
            raccomandazioni.append({
                'tipo': 'MANTENIMENTO',
                'azione': f'Mantenere relazione con {dati_programma.get("docente", "il docente")}',
                'dettaglio': f'{manuale_nome_completo} è già adottato. Programmare visita di cortesia e aggiornamento su novità editoriali.'
            })
            raccomandazioni.append({
                'tipo': 'FIDELIZZAZIONE',
                'azione': 'Proporre materiali integrativi',
                'dettaglio': 'Verificare interesse per risorse digitali, slide docente, test bank.'
            })
            
        elif situazione == 'CONQUISTA':
            priorita = 'ALTA'
            conc_nome = f"{concorrente_principale['autore']}, {concorrente_principale['titolo']}" if concorrente_principale else "il manuale attuale"
            
            raccomandazioni.append({
                'tipo': 'SOSTITUZIONE',
                'azione': f'Proporre {manuale_nome_completo} in sostituzione di {conc_nome}',
                'dettaglio': f'Preparare confronto dettagliato tra {manuale_nome_completo} e {conc_nome}. Evidenziare punti di forza specifici per il programma.'
            })
            raccomandazioni.append({
                'tipo': 'COPIA_SAGGIO',
                'azione': 'Inviare copia saggio',
                'dettaglio': f'Inviare {manuale_nome_completo} con lettera di accompagnamento personalizzata.'
            })
            
            # Raccomandazioni basate sulla copertura
            if copertura['percentuale'] >= 80:
                raccomandazioni.append({
                    'tipo': 'ARGOMENTO_VENDITA',
                    'azione': 'Eccellente copertura del programma',
                    'dettaglio': f'{manuale_nome_completo} copre il {copertura["percentuale"]}% degli argomenti del corso. Usare come argomento principale.'
                })
                
        elif situazione == 'OPPORTUNITA_ALTA':
            priorita = 'ALTA'
            raccomandazioni.append({
                'tipo': 'PRIMA_ADOZIONE',
                'azione': f'Proporre {manuale_nome_completo} come testo di riferimento',
                'dettaglio': 'Nessun manuale attualmente indicato. Ottima opportunità per prima adozione.'
            })
            raccomandazioni.append({
                'tipo': 'COPIA_SAGGIO',
                'azione': 'Inviare copia saggio prioritaria',
                'dettaglio': f'Inviare {manuale_nome_completo} con proposta di adozione.'
            })
            
        else:  # OPPORTUNITA_MEDIA
            priorita = 'MEDIA'
            raccomandazioni.append({
                'tipo': 'PROPOSTA',
                'azione': f'Proporre {manuale_nome_completo} come testo principale',
                'dettaglio': 'Attualmente indicati solo testi di consultazione. Proporre adozione di un manuale strutturato.'
            })
        
        return {
            'priorita': priorita,
            'lista': raccomandazioni
        }
    
    def _calcola_punteggio_opportunita(self, copertura, analisi_competitiva, dati_programma):
        """Calcola un punteggio di opportunità commerciale da 0 a 100"""
        
        punteggio = 50  # Base
        
        # Fattore situazione competitiva
        situazione = analisi_competitiva['situazione']
        if situazione == 'OPPORTUNITA_ALTA':
            punteggio += 30
        elif situazione == 'CONQUISTA':
            punteggio += 15
        elif situazione == 'OPPORTUNITA_MEDIA':
            punteggio += 20
        elif situazione == 'DIFESA':
            punteggio -= 20
        
        # Fattore copertura
        copertura_pct = copertura.get('percentuale', 0)
        if copertura_pct >= 80:
            punteggio += 15
        elif copertura_pct >= 60:
            punteggio += 10
        elif copertura_pct >= 40:
            punteggio += 5
        
        # Fattore CFU (corsi più grandi = più studenti potenziali)
        cfu = dati_programma.get('cfu', 0)
        try:
            cfu = int(cfu)
            if cfu >= 12:
                punteggio += 10
            elif cfu >= 8:
                punteggio += 5
        except:
            pass
        
        # Limita tra 0 e 100
        return max(0, min(100, punteggio))
    
    def _salva_analisi(self, risultato):
        """Salva l'analisi in formato JSON"""
        
        # Crea nome file univoco
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        docente = risultato['dati_programma'].get('docente', 'unknown').replace(' ', '_')
        universita = risultato['dati_programma'].get('universita', 'unknown').replace(' ', '_')
        
        filename = f"analisi_{docente}_{universita}_{timestamp}.json"
        filepath = self.analisi_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(risultato, f, ensure_ascii=False, indent=2)
            risultato['file_salvato'] = str(filepath)
        except Exception as e:
            print(f"Errore salvataggio analisi: {e}")
            risultato['file_salvato'] = None
        
        return filepath
    
    def carica_analisi(self, filepath):
        """Carica un'analisi salvata"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore caricamento analisi: {e}")
            return None
    
    def lista_analisi_salvate(self):
        """Restituisce l'elenco delle analisi salvate"""
        analisi = []
        for file in self.analisi_dir.glob("analisi_*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    analisi.append({
                        'file': str(file),
                        'filename': file.name,
                        'timestamp': data.get('timestamp', ''),
                        'docente': data.get('dati_programma', {}).get('docente', ''),
                        'universita': data.get('dati_programma', {}).get('universita', ''),
                        'punteggio': data.get('punteggio_opportunita', 0)
                    })
            except:
                pass
        
        # Ordina per timestamp decrescente
        analisi.sort(key=lambda x: x['timestamp'], reverse=True)
        return analisi
    
    def esporta_analisi(self, risultato, formato='json'):
        """Esporta l'analisi nel formato richiesto"""
        
        if formato == 'json':
            return json.dumps(risultato, ensure_ascii=False, indent=2)
        
        elif formato == 'html':
            # Import del report generator per HTML
            from app.commercial_report_generator import CommercialReportGenerator
            generator = CommercialReportGenerator()
            return generator.genera_report_html(risultato)
        
        else:
            return json.dumps(risultato, ensure_ascii=False, indent=2)
