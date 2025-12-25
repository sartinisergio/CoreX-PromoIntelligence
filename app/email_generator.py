"""
CoreX - Email Generator
Generazione email commerciali personalizzate per Zanichelli
"""

from datetime import datetime


class EmailGenerator:
    """Genera email commerciali basate sull'analisi del programma"""
    
    def __init__(self):
        self.templates = self._carica_templates()
    
    def _carica_templates(self):
        """Template email per diverse situazioni"""
        return {
            'CONQUISTA': {
                'oggetto': "Proposta {manuale_zanichelli} per il corso di {corso}",
                'corpo': """Gentile Prof. {docente},

mi permetto di contattarLa in qualità di promotore editoriale Zanichelli per la Sua zona.

Ho avuto modo di consultare il programma del Suo corso di {corso} presso {universita} e ho notato che attualmente utilizza {concorrente} come testo di riferimento.

Desidero sottoporre alla Sua attenzione {manuale_zanichelli}, che ritengo possa rappresentare una valida alternativa per i Suoi studenti.

{punti_forza}

Sarei lieto di poterLe inviare una copia saggio del volume per una Sua valutazione diretta, senza alcun impegno.

Resto a disposizione per un eventuale incontro, anche in videoconferenza, per illustrarLe le caratteristiche del testo e i materiali di supporto alla didattica disponibili.

Cordiali saluti,

{firma}"""
            },
            
            'OPPORTUNITA_ALTA': {
                'oggetto': "Proposta adozione {manuale_zanichelli} - {corso}",
                'corpo': """Gentile Prof. {docente},

mi permetto di contattarLa in qualità di promotore editoriale Zanichelli per la Sua zona.

Consultando il programma del Suo corso di {corso} presso {universita}, ho notato che non è attualmente indicato un testo di riferimento specifico.

Mi fa piacere proporLe {manuale_zanichelli}, un volume che per completezza e rigore didattico potrebbe rappresentare un valido supporto per i Suoi studenti.

{punti_forza}

Sarei lieto di inviarLe una copia saggio per una Sua valutazione diretta.

Resto a disposizione per qualsiasi chiarimento o per un incontro di presentazione.

Cordiali saluti,

{firma}"""
            },
            
            'OPPORTUNITA_MEDIA': {
                'oggetto': "Proposta {manuale_zanichelli} per {corso}",
                'corpo': """Gentile Prof. {docente},

mi permetto di contattarLa in qualità di promotore editoriale Zanichelli.

Ho consultato con interesse il programma del Suo corso di {corso} presso {universita}.

Desidero sottoporre alla Sua attenzione {manuale_zanichelli}, che per struttura e contenuti potrebbe integrare efficacemente la bibliografia del Suo corso come testo principale di riferimento.

{punti_forza}

Sarò lieto di inviarLe una copia saggio e di illustrarLe personalmente i contenuti e i materiali digitali a corredo.

Cordiali saluti,

{firma}"""
            },
            
            'DIFESA': {
                'oggetto': "Aggiornamenti e novità per il Suo corso di {corso}",
                'corpo': """Gentile Prof. {docente},

La contatto in qualità di promotore editoriale Zanichelli per ringraziarLa della fiducia che accorda a {manuale_zanichelli} per il Suo corso di {corso}.

Desidero aggiornarLa sulle novità disponibili per il testo e sui materiali di supporto alla didattica:

{punti_forza}

Resto a Sua disposizione per qualsiasi esigenza e per programmare un incontro di aggiornamento.

Cordiali saluti,

{firma}"""
            },
            
            'FOLLOWUP': {
                'oggetto': "Seguito proposta {manuale_zanichelli}",
                'corpo': """Gentile Prof. {docente},

faccio seguito alla mia precedente comunicazione riguardante {manuale_zanichelli} per il Suo corso di {corso} presso {universita}.

Mi permetto di ricontattarLa per sapere se ha avuto modo di valutare la mia proposta e se posso esserLe utile con ulteriori informazioni o materiali.

{punti_forza}

Rimango a disposizione per un incontro, anche breve, per illustrarLe di persona le caratteristiche del volume.

Cordiali saluti,

{firma}"""
            }
        }
    
    def genera_email(self, analisi, tipo_email=None, firma=""):
        """
        Genera un'email commerciale basata sull'analisi
        
        Args:
            analisi: dict con risultati dell'analisi commerciale
            tipo_email: tipo di email (CONQUISTA, DIFESA, etc.) - se None usa la situazione
            firma: firma del promotore
        
        Returns:
            dict con oggetto e corpo dell'email
        """
        
        dati = analisi.get('dati_programma', {})
        manuale_z = analisi.get('manuale_zanichelli', {})
        concorrente = analisi.get('concorrente_principale', {})
        competitiva = analisi.get('analisi_competitiva', {})
        copertura = analisi.get('copertura_argomenti', {})
        raccomandazioni = analisi.get('raccomandazioni', {})
        
        # Nome completo manuale Zanichelli
        manuale_zanichelli_nome = f"{manuale_z.get('autore', '')}, {manuale_z.get('titolo', '')}"
        
        # Nome completo concorrente
        if concorrente:
            concorrente_nome = f"{concorrente.get('autore', '')}, {concorrente.get('titolo', '')} ({concorrente.get('editore', '')})"
        else:
            concorrente_nome = "altri testi"
        
        # Determina tipo email se non specificato
        if tipo_email is None:
            tipo_email = competitiva.get('situazione', 'OPPORTUNITA_MEDIA')
        
        # Seleziona template
        template = self.templates.get(tipo_email, self.templates['OPPORTUNITA_MEDIA'])
        
        # Genera punti di forza
        punti_forza = self._genera_punti_forza(analisi, manuale_zanichelli_nome)
        
        # Compila template
        oggetto = template['oggetto'].format(
            manuale_zanichelli=manuale_zanichelli_nome,
            corso=dati.get('corso', 'N/D'),
            docente=dati.get('docente', 'N/D')
        )
        
        corpo = template['corpo'].format(
            docente=dati.get('docente', 'N/D'),
            corso=dati.get('corso', 'N/D'),
            universita=dati.get('universita', 'N/D'),
            manuale_zanichelli=manuale_zanichelli_nome,
            concorrente=concorrente_nome,
            punti_forza=punti_forza,
            firma=firma if firma else "[Firma promotore]"
        )
        
        return {
            'oggetto': oggetto,
            'corpo': corpo,
            'tipo': tipo_email,
            'metadata': {
                'docente': dati.get('docente', ''),
                'universita': dati.get('universita', ''),
                'corso': dati.get('corso', ''),
                'manuale': manuale_zanichelli_nome,
                'generato_il': datetime.now().isoformat()
            }
        }
    def _genera_punti_forza(self, analisi, manuale_zanichelli_nome):
        """Genera i punti di forza personalizzati per l'email"""
        
        copertura = analisi.get('copertura_argomenti', {})
        competitiva = analisi.get('analisi_competitiva', {})
        situazione = competitiva.get('situazione', '')
        
        punti = []
        
        # Punto sulla copertura
        percentuale = copertura.get('percentuale', 0)
        if percentuale >= 80:
            punti.append(f"• {manuale_zanichelli_nome} copre in modo completo gli argomenti del Suo programma ({percentuale}% di corrispondenza)")
        elif percentuale >= 60:
            punti.append(f"• {manuale_zanichelli_nome} affronta la maggior parte degli argomenti previsti dal Suo corso")
        
        # Punti generici sul manuale
        if situazione != 'DIFESA':
            punti.append(f"• {manuale_zanichelli_nome} offre un approccio didattico moderno con numerosi esempi ed esercizi svolti")
            punti.append(f"• Sono disponibili materiali digitali integrativi per docenti e studenti")
            punti.append(f"• Il testo è corredato da risorse online costantemente aggiornate")
        else:
            punti.append(f"• Nuovi materiali digitali disponibili sulla piattaforma online")
            punti.append(f"• Slide aggiornate per le lezioni")
            punti.append(f"• Test bank ampliata per la verifica dell'apprendimento")
        
        return "\n".join(punti)
    
    def genera_tutte_varianti(self, analisi, firma=""):
        """Genera tutte le varianti di email disponibili"""
        
        varianti = {}
        for tipo in self.templates.keys():
            varianti[tipo] = self.genera_email(analisi, tipo_email=tipo, firma=firma)
        
        return varianti
    
    def get_tipi_disponibili(self):
        """Restituisce i tipi di email disponibili con descrizione"""
        return {
            'CONQUISTA': 'Email per proporre sostituzione del testo concorrente',
            'OPPORTUNITA_ALTA': 'Email per corsi senza testo di riferimento',
            'OPPORTUNITA_MEDIA': 'Email per corsi con solo testi di consultazione',
            'DIFESA': 'Email di fidelizzazione per corsi già Zanichelli',
            'FOLLOWUP': 'Email di follow-up dopo primo contatto'
        }
    
    def personalizza_email(self, email_base, personalizzazioni):
        """
        Permette di personalizzare ulteriormente un'email generata
        
        Args:
            email_base: dict con oggetto e corpo
            personalizzazioni: dict con campi da modificare
        
        Returns:
            dict con email personalizzata
        """
        
        email = email_base.copy()
        
        if 'oggetto' in personalizzazioni:
            email['oggetto'] = personalizzazioni['oggetto']
        
        if 'corpo' in personalizzazioni:
            email['corpo'] = personalizzazioni['corpo']
        
        if 'aggiungi_paragrafo' in personalizzazioni:
            # Aggiunge un paragrafo prima della firma
            corpo = email['corpo']
            parti = corpo.rsplit('\n\nCordiali saluti,', 1)
            if len(parti) == 2:
                email['corpo'] = parti[0] + '\n\n' + personalizzazioni['aggiungi_paragrafo'] + '\n\nCordiali saluti,' + parti[1]
        
        return email
    
    def esporta_email_html(self, email):
        """Esporta l'email in formato HTML per anteprima"""
        
        corpo_html = email['corpo'].replace('\n', '<br>')
        
        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>{email['oggetto']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 700px;
            margin: 50px auto;
            padding: 30px;
            background: #f5f5f5;
        }}
        .email-container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .oggetto {{
            background: #0066cc;
            color: white;
            padding: 15px 20px;
            border-radius: 8px 8px 0 0;
            margin: -30px -30px 20px -30px;
            font-weight: bold;
        }}
        .corpo {{
            line-height: 1.8;
            color: #333;
        }}
        .metadata {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 0.85em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="oggetto">📧 {email['oggetto']}</div>
        <div class="corpo">{corpo_html}</div>
        <div class="metadata">
            <strong>Tipo:</strong> {email.get('tipo', 'N/D')}<br>
            <strong>Generato:</strong> {email.get('metadata', {}).get('generato_il', 'N/D')}
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def copia_per_clipboard(self, email):
        """Restituisce il testo dell'email formattato per copia"""
        
        testo = f"""OGGETTO: {email['oggetto']}

---

{email['corpo']}"""
        
        return testo
