"""
commercial_report_generator.py
CoreX - Zanichelli Promo Intelligence
Genera report HTML commerciali completi per promotori editoriali
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import html


class CommercialReportGenerator:
    """Generatore di report commerciali HTML per Zanichelli"""
    
    def __init__(self):
        self.today = datetime.now().strftime("%d/%m/%Y")
    
    def genera_report_html(self, analisi: Dict[str, Any]) -> str:
        """
        Genera il report HTML completo dall'oggetto analisi.
        
        Args:
            analisi: Dizionario contenente tutti i dati dell'analisi
            
        Returns:
            Stringa HTML del report completo
        """
        # Estrai dati con valori di default sicuri
        dati = self._estrai_dati_sicuri(analisi)
        
        # Costruisci il report HTML
        html_report = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analisi - {self._escape(dati['corso'])}</title>
    {self._get_styles()}
</head>
<body>
    {self._genera_header(dati)}
    {self._genera_manuale_box(dati)}
    {self._genera_postit(dati)}
    {self._genera_analisi_bibliografia(dati)}
    {self._genera_profilo_docente(dati)}
    {self._genera_analisi_copertura(dati)}
    {self._genera_gap_identificati(dati)}
    {self._genera_strategia(dati)}
    {self._genera_argomenti_vendita(dati)}
    {self._genera_email(dati)}
    {self._genera_footer(dati)}
</body>
</html>"""
        
        return html_report
    
    def _estrai_dati_sicuri(self, analisi: Dict[str, Any]) -> Dict[str, Any]:
        """Estrae i dati dall'analisi con valori di default sicuri"""
        
        # Dati programma
        dati_programma = analisi.get('dati_programma', {})
        
        # Manuale Zanichelli
        manuale_z = analisi.get('manuale_zanichelli', {})
        
        # Concorrente
        concorrente = analisi.get('concorrente_principale', {})
        
        # Analisi competitiva
        analisi_comp = analisi.get('analisi_competitiva', {})
        
        # Copertura
        copertura = analisi.get('copertura_argomenti', {})
        
        # Raccomandazioni
        raccomandazioni = analisi.get('raccomandazioni', {})
        
        # Profilo docente (può essere nested o flat)
        profilo = analisi.get('profilo_docente', {})
        
        # Gap analysis
        gap_analysis = analisi.get('gap_analysis', [])
        if not gap_analysis:
            gap_analysis = self._genera_gap_da_copertura(copertura)
        
        # Copertura dettagliata per moduli
        copertura_ideale = analisi.get('copertura_ideale', {})
        copertura_reale = analisi.get('copertura_reale', {})
        
        # Moduli copertura (se non presenti, genera da copertura_argomenti)
        moduli_ideale = copertura_ideale.get('moduli', [])
        moduli_reale = copertura_reale.get('moduli', [])
        
        if not moduli_ideale:
            moduli_ideale = self._genera_moduli_da_copertura(copertura, 'ideale')
        if not moduli_reale:
            moduli_reale = self._genera_moduli_da_copertura(copertura, 'reale')
        
        return {
            # Info base
            'corso': dati_programma.get('corso', 'Corso non specificato'),
            'docente': dati_programma.get('docente', 'Docente non specificato'),
            'universita': dati_programma.get('universita', 'Università non specificata'),
            'cfu': dati_programma.get('cfu', 'N/D'),
            'ore': dati_programma.get('ore', 'N/D'),
            'data': self.today,
            
            # Manuale Zanichelli
            'manuale_titolo': manuale_z.get('titolo', 'Titolo non disponibile'),
            'manuale_autore': manuale_z.get('autore', 'Autore non disponibile'),
            'match_score': manuale_z.get('match_score', 0),
            'capitoli_rilevanti': manuale_z.get('capitoli_rilevanti', []),
            
            # Concorrente
            'concorrente_titolo': concorrente.get('titolo', ''),
            'concorrente_autore': concorrente.get('autore', ''),
            'concorrente_editore': concorrente.get('editore', ''),
            
            # Analisi competitiva
            'situazione_zanichelli': analisi_comp.get('situazione', 'assente'),
            'descrizione_competitiva': analisi_comp.get('descrizione', ''),
            
            # Copertura
            'percentuale_copertura': copertura.get('percentuale', 0),
            'argomenti_coperti': copertura.get('argomenti_coperti', []),
            'argomenti_mancanti': copertura.get('argomenti_mancanti', []),
            
            # Copertura dettagliata
            'copertura_ideale_percentuale': copertura_ideale.get('percentuale', 54),
            'copertura_reale_percentuale': copertura_reale.get('percentuale', 77),
            'moduli_ideale': moduli_ideale,
            'moduli_reale': moduli_reale,
            'punti_forza_ideale': copertura_ideale.get('punti_forza', []),
            'aree_approfondire_ideale': copertura_ideale.get('aree_approfondire', []),
            'punti_forza_reale': copertura_reale.get('punti_forza', []),
            'aree_approfondire_reale': copertura_reale.get('aree_approfondire', []),
            
            # Raccomandazioni
            'priorita': raccomandazioni.get('priorita', 'media'),
            'lista_raccomandazioni': raccomandazioni.get('lista', []),
            'approccio': raccomandazioni.get('approccio', ''),
            
            # Punteggio
            'punteggio_opportunita': analisi.get('punteggio_opportunita', 50),
            
            # Profilo docente
            'approccio_didattico': profilo.get('approccio', 'Bilanciato'),
            'rigore': profilo.get('rigore', 'Alto'),
            'bilanciamento_teoria_pratica': profilo.get('bilanciamento', 80),
            'argomenti_chiave': profilo.get('argomenti_chiave', ''),
            'metodi_didattici': profilo.get('metodi_didattici', ['lezione frontale', 'esercitazioni']),
            'metodi_valutazione': profilo.get('metodi_valutazione', ['scritto', 'orale']),
            'ha_laboratorio': profilo.get('laboratorio', True),
            'ha_esercitazioni': profilo.get('esercitazioni', True),
            'insight_principale': profilo.get('insight', ''),
            'filosofia_didattica': profilo.get('filosofia', ''),
            
            # Gap
            'gap_analysis': gap_analysis,
            
            # Strategia
            'strategia': analisi.get('strategia', {}),
            'domande_discovery': analisi.get('domande_discovery', []),
            
            # Argomenti vendita
            'argomenti_vendita': analisi.get('argomenti_vendita', []),
            
            # Email
            'email': analisi.get('email', {}),
            
            # Post-it
            'postit': analisi.get('postit', {}),
            
            # Valutazione manuale attuale
            'valutazione_manuale_attuale': analisi.get('valutazione_manuale_attuale', ''),
        }
    
    def _escape(self, text: Any) -> str:
        """Escape HTML sicuro"""
        if text is None:
            return ''
        return html.escape(str(text))
    
    def _get_styles(self) -> str:
        """Ritorna gli stili CSS del report"""
        return """<style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 40px 20px; }
        h1 { color: #d97706; margin-bottom: 10px; font-size: 28px; }
        h2 { color: #d97706; margin: 30px 0 15px; padding-bottom: 8px; border-bottom: 2px solid #dbeafe; font-size: 20px; }
        h3 { color: #374151; margin: 20px 0 10px; font-size: 16px; }
        .header { margin-bottom: 30px; padding-bottom: 20px; border-bottom: 3px solid #d97706; }
        .meta { color: #6b7280; font-size: 14px; margin-top: 8px; }
        .meta span { margin-right: 20px; }
        .card { background: #f8fafc; border-radius: 8px; padding: 20px; margin: 15px 0; border-left: 4px solid #3b82f6; }
        .card.warning { border-left-color: #f59e0b; background: #fffbeb; }
        .card.success { border-left-color: #10b981; background: #ecfdf5; }
        .card.danger { border-left-color: #ef4444; background: #fef2f2; }
        .card.highlight { border-left-color: #8b5cf6; background: #f5f3ff; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-right: 8px; }
        .badge.alta { background: #fee2e2; color: #991b1b; }
        .badge.media { background: #fef3c7; color: #92400e; }
        .badge.bassa { background: #d1fae5; color: #065f46; }
        .badge.alto { background: #dbeafe; color: #1e40af; }
        .badge.medio { background: #fef3c7; color: #92400e; }
        .badge.basso { background: #fee2e2; color: #991b1b; }
        .badge.assente { background: #f3f4f6; color: #6b7280; }
        .postit { background: #fef9c3; padding: 25px; border-radius: 8px; font-size: 15px; line-height: 1.8; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); }
        .manual-box { background: linear-gradient(135deg, #d97706 0%, #3b82f6 100%); color: white; padding: 25px; border-radius: 12px; margin: 20px 0; }
        .manual-box h3 { color: white; margin: 0 0 5px; font-size: 22px; }
        .manual-box .author { opacity: 0.9; font-size: 16px; }
        .manual-box .score { font-size: 14px; margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.3); }
        ul { margin: 10px 0 10px 20px; }
        li { margin: 8px 0; }
        .gap-item { margin: 15px 0; padding: 15px; background: white; border-radius: 8px; border: 1px solid #e5e7eb; }
        .gap-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .strategy-phase { margin: 20px 0; padding: 20px; background: white; border-radius: 8px; border: 1px solid #e5e7eb; }
        .phase-number { display: inline-block; width: 30px; height: 30px; background: #d97706; color: white; border-radius: 50%; text-align: center; line-height: 30px; font-weight: bold; margin-right: 10px; }
        .email-box { background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 25px; white-space: pre-wrap; font-family: inherit; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 12px; text-align: center; }
        .meter { height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .meter-fill { height: 100%; border-radius: 10px; }
        .meter-label { display: flex; justify-content: space-between; font-size: 12px; color: #666; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
        .comparison-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        .comparison-table th, .comparison-table td { padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
        .comparison-table th { background: #f8fafc; font-weight: 600; }
        .comparison-table tr:hover { background: #f8fafc; }
        .coverage-bar { display: flex; align-items: center; gap: 10px; }
        .coverage-bar .bar { flex: 1; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; }
        .coverage-bar .fill { height: 100%; border-radius: 4px; }
        .coverage-bar .value { min-width: 45px; text-align: right; font-weight: 600; }
    </style>"""
    
    def _genera_header(self, dati: Dict[str, Any]) -> str:
        """Genera l'header del report"""
        return f"""
    <div class="header">
        <h1>{self._escape(dati['corso'])}</h1>
        <div class="meta">
            <span>📍 {self._escape(dati['universita'])}</span>
            <span>👤 {self._escape(dati['docente'])}</span>
            <span>📅 {self._escape(dati['data'])}</span>
        </div>
    </div>"""
    
    def _genera_manuale_box(self, dati: Dict[str, Any]) -> str:
        """Genera il box del manuale Zanichelli consigliato"""
        capitoli = dati.get('capitoli_rilevanti', [])
        capitoli_str = ', '.join(capitoli[:3]) if capitoli else 'Tutti i capitoli pertinenti'
        
        return f"""
    <div class="manual-box">
        <h3>📚 {self._escape(dati['manuale_titolo'])}</h3>
        <div class="author">{self._escape(dati['manuale_autore'])}</div>
        <div class="score">Match Score: <strong>{dati['match_score']}%</strong></div>
        <div style="margin-top: 10px; font-size: 13px; opacity: 0.9;">Capitoli chiave: {self._escape(capitoli_str)}</div>
    </div>"""
    
    def _genera_postit(self, dati: Dict[str, Any]) -> str:
        """Genera il post-it commerciale"""
        postit = dati.get('postit', {})
        
        if postit:
            docente_info = postit.get('docente', f"{dati['docente']}, approccio {dati.get('approccio_didattico', 'bilanciato').lower()}")
            usa_info = postit.get('usa', f"{dati['concorrente_titolo']} ({dati['concorrente_editore']})")
            obiettivo = postit.get('obiettivo', 'proporre il manuale Zanichelli')
            leva = postit.get('leva', dati.get('argomenti_mancanti', ['contenuti aggiuntivi'])[0] if dati.get('argomenti_mancanti') else 'contenuti completi')
            argomentazione = postit.get('argomentazione', 'Il nostro manuale offre una copertura più completa.')
        else:
            # Genera automaticamente
            docente_info = f"{dati['docente']}, approccio {dati.get('approccio_didattico', 'bilanciato').lower()}"
            usa_info = f"{dati['concorrente_titolo']} ({dati['concorrente_editore']})" if dati['concorrente_titolo'] else "Nessun manuale rilevato"
            obiettivo = "proporre il manuale Zanichelli"
            mancanti = dati.get('argomenti_mancanti', [])
            leva = mancanti[0] if mancanti else "completezza dei contenuti"
            argomentazione = f"Il nostro manuale offre una copertura approfondita di {leva}, fondamentale per il corso."
        
        return f"""
    <h2>📝 Post-it Commerciale</h2>
    
    <div class="postit">
        <strong>DOCENTE:</strong> {self._escape(docente_info)}. <strong>USA:</strong> {self._escape(usa_info)}. <strong>OBIETTIVO:</strong> {self._escape(obiettivo)}. <strong>LEVA:</strong> {self._escape(leva)}. <strong>ARGOMENTAZIONE:</strong> {self._escape(argomentazione)}
    </div>"""
    
    def _genera_analisi_bibliografia(self, dati: Dict[str, Any]) -> str:
        """Genera la sezione analisi bibliografia"""
        situazione = dati.get('situazione_zanichelli', 'assente')
        badge_situazione = self._get_badge_situazione(situazione)
        
        # Manuale principale competitor
        concorrente_html = ""
        if dati['concorrente_titolo']:
            concorrente_html = f"""
        <div style="background: #fff7ed; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 3px solid #f97316;">
            <h3 style="margin: 0 0 8px;">Manuale Principale <span class="badge alta">Competitor</span></h3>
            <p><strong>{self._escape(dati['concorrente_titolo'])}</strong></p>
            <p style="color: #6b7280;">{self._escape(dati['concorrente_autore'])} - {self._escape(dati['concorrente_editore'])}</p>
        </div>"""
        
        # Posizione Zanichelli
        posizione_html = ""
        if situazione == 'assente':
            posizione_html = """
        <div class="card danger" style="margin-top: 15px;">
            <p><strong>Posizione Zanichelli:</strong> ⚠️ Zanichelli non presente - Opportunità di introduzione</p>
        </div>"""
        elif situazione == 'presente':
            posizione_html = """
        <div class="card success" style="margin-top: 15px;">
            <p><strong>Posizione Zanichelli:</strong> ✅ Zanichelli già adottato - Opportunità di upselling</p>
        </div>"""
        elif situazione == 'consigliato':
            posizione_html = """
        <div class="card warning" style="margin-top: 15px;">
            <p><strong>Posizione Zanichelli:</strong> 📗 Zanichelli consigliato - Opportunità di adozione formale</p>
        </div>"""
        
        # Valutazione manuale attuale
        valutazione = dati.get('valutazione_manuale_attuale', '')
        if not valutazione and dati['concorrente_titolo']:
            valutazione = f"Il manuale {dati['concorrente_editore']} è ben strutturato, ma presenta lacune in aree chiave dove il nostro testo può offrire un valore aggiunto."
        
        valutazione_html = ""
        if valutazione:
            valutazione_html = f"""
        <div style="margin-top: 15px; padding: 15px; background: #f1f5f9; border-radius: 8px;">
            <h3 style="margin: 0 0 8px; font-size: 14px;">Valutazione Manuale Attuale</h3>
            <p>{self._escape(valutazione)}</p>
        </div>"""
        
        return f"""
    <h2>📖 Analisi Bibliografia Adottata</h2>
    <div class="card" style="border-left-color: #3b82f6;">
        <p style="margin-bottom: 15px;"><strong>Posizione Zanichelli:</strong> {badge_situazione}</p>
        {concorrente_html}
        {posizione_html}
        {valutazione_html}
    </div>"""
    
    def _get_badge_situazione(self, situazione: str) -> str:
        """Ritorna il badge HTML per la situazione"""
        situazioni = {
            'assente': '<span class="badge" style="background: #dbeafe; color: #1e40af;">assente</span>',
            'presente': '<span class="badge" style="background: #d1fae5; color: #065f46;">presente</span>',
            'consigliato': '<span class="badge" style="background: #fef3c7; color: #92400e;">consigliato</span>',
        }
        return situazioni.get(situazione.lower(), situazioni['assente'])
    
    def _genera_profilo_docente(self, dati: Dict[str, Any]) -> str:
        """Genera la sezione profilo pedagogico del docente"""
        # Insight principale
        insight = dati.get('insight_principale', '')
        if not insight:
            insight = f"C'è un'opportunità significativa per Zanichelli di colmare le lacune nel programma di {dati['corso']} del docente, migliorando l'esperienza didattica degli studenti."
        
        # Metodi didattici
        metodi_didattici = dati.get('metodi_didattici', ['lezione frontale', 'esercitazioni'])
        metodi_badges = ' '.join([f'<span class="badge" style="background: #e0e7ff; color: #3730a3;">{self._escape(m)}</span>' for m in metodi_didattici])
        
        # Metodi valutazione
        metodi_val = dati.get('metodi_valutazione', ['scritto', 'orale'])
        val_badges = ' '.join([f'<span class="badge" style="background: #fef3c7; color: #92400e;">{self._escape(m)}</span>' for m in metodi_val])
        
        # Argomenti chiave
        argomenti = dati.get('argomenti_chiave', '')
        argomenti_html = ""
        if argomenti:
            argomenti_html = f"""
        <div style="margin-top: 15px;">
            <p><strong>Argomenti Chiave:</strong></p>
            <p style="color: #6b7280;">{self._escape(argomenti)}</p>
        </div>"""
        
        # Features laboratorio/esercitazioni
        features = []
        if dati.get('ha_laboratorio', False):
            features.append("✓ Laboratorio")
        if dati.get('ha_esercitazioni', False):
            features.append("✓ Esercitazioni")
        features_html = "<br>".join(features) if features else ""
        
        bilanciamento = dati.get('bilanciamento_teoria_pratica', 50)
        
        return f"""
    <h2>🎓 Profilo Pedagogico del Docente</h2>
    
    <div class="card">
        <h3>💡 Insight Principale</h3>
        <p style="font-size: 1.1em;">{self._escape(insight)}</p>
    </div>
    
    <div class="card">
        <h3>📐 Filosofia Didattica</h3>
        <div class="grid">
            <div>
                <p><strong>Approccio:</strong> 🎯 {self._escape(dati.get('approccio_didattico', 'Bilanciato'))}</p>
                <p style="color: #6b7280; font-size: 14px;">Equilibrio teoria-pratica</p>
            </div>
            <div>
                <p><strong>Rigore:</strong> {self._escape(dati.get('rigore', 'Alto'))}</p>
                <p><strong>CFU:</strong> {dati['cfu']} | <strong>Ore:</strong> {dati['ore']}</p>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <p><strong>Bilanciamento Teoria/Pratica:</strong></p>
            <div class="meter-label"><span>Teoria</span><span>Pratica</span></div>
            <div class="meter">
                <div class="meter-fill" style="width: {bilanciamento}%; background: linear-gradient(90deg, #3b82f6, #22c55e);"></div>
            </div>
        </div>
        {argomenti_html}
    </div>
    
    <div class="card">
        <h3>🔬 Metodi</h3>
        <div class="grid">
            <div>
                <p><strong>Didattica:</strong></p>
                {metodi_badges}
            </div>
            <div>
                <p><strong>Valutazione:</strong></p>
                {val_badges}
            </div>
        </div>
        <div style="margin-top: 15px;">
            <p>
                {features_html}
            </p>
        </div>
    </div>"""
    
    def _genera_analisi_copertura(self, dati: Dict[str, Any]) -> str:
        """Genera la sezione analisi copertura"""
        return f"""
    <h2>📊 Analisi della Copertura</h2>
    
    {self._genera_copertura_ideale(dati)}
    {self._genera_copertura_reale(dati)}"""
    
    def _genera_copertura_ideale(self, dati: Dict[str, Any]) -> str:
        """Genera il blocco copertura vs framework ideale"""
        percentuale = dati.get('copertura_ideale_percentuale', dati.get('percentuale_copertura', 54))
        moduli = dati.get('moduli_ideale', [])
        
        # Determina colore e label
        if percentuale >= 75:
            colore = '#10b981'
            label = 'Copertura Buona'
        elif percentuale >= 50:
            colore = '#f59e0b'
            label = 'Copertura Parziale'
        else:
            colore = '#ef4444'
            label = 'Copertura Insufficiente'
        
        # Genera tabella moduli
        moduli_html = self._genera_tabella_moduli(moduli)
        
        # Punti di forza
        punti_forza = dati.get('punti_forza_ideale', [])
        if not punti_forza and moduli:
            punti_forza = [f"{m['nome']}: copertura eccellente ({m['copertura']}%)" 
                         for m in moduli if m.get('copertura', 0) >= 100][:3]
        
        punti_forza_html = ""
        if punti_forza:
            items = ''.join([f"<li>{self._escape(p)}</li>" for p in punti_forza])
            punti_forza_html = f"<div style='margin-top: 15px;'><strong>✅ Punti di forza:</strong><ul>{items}</ul></div>"
        
        # Aree da approfondire
        aree = dati.get('aree_approfondire_ideale', [])
        if not aree and dati.get('argomenti_mancanti'):
            aree = [f"{arg}" for arg in dati['argomenti_mancanti'][:3]]
        
        aree_html = ""
        if aree:
            items = ''.join([f"<li>{self._escape(a)}</li>" for a in aree])
            aree_html = f"<div style='margin-top: 15px;'><strong>⚠️ Aree da approfondire:</strong><ul>{items}</ul></div>"
        
        return f"""
    <div class="card">
        <h3>🎯 Confronto vs Framework Ideale</h3>
        <p style="color: #6b7280; margin-bottom: 15px;">Quanto il programma copre il catalogo Zanichelli</p>
        
        <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 20px;">
            <div style="text-align: center;">
                <div style="font-size: 36px; font-weight: bold; color: {colore};">{percentuale}%</div>
                <div style="color: #6b7280;">{label}</div>
            </div>
            <div style="flex: 1;">
                <div class="meter" style="height: 12px;">
                    <div class="meter-fill" style="width: {percentuale}%; background: {colore};"></div>
                </div>
            </div>
        </div>
        
        {moduli_html}
        {punti_forza_html}
        {aree_html}
    </div>"""
    
    def _genera_copertura_reale(self, dati: Dict[str, Any]) -> str:
        """Genera il blocco copertura vs framework reale"""
        percentuale = dati.get('copertura_reale_percentuale', 77)
        moduli = dati.get('moduli_reale', [])
        
        # Determina colore e label
        if percentuale >= 75:
            colore = '#10b981'
            label = 'Copertura Buona'
        elif percentuale >= 50:
            colore = '#f59e0b'
            label = 'Copertura Parziale'
        else:
            colore = '#ef4444'
            label = 'Copertura Insufficiente'
        
        # Genera tabella moduli
        moduli_html = self._genera_tabella_moduli(moduli)
        
        # Punti di forza
        punti_forza = dati.get('punti_forza_reale', [])
        punti_forza_html = ""
        if punti_forza:
            items = ''.join([f"<li>{self._escape(p)}</li>" for p in punti_forza])
            punti_forza_html = f"<div style='margin-top: 15px;'><strong>✅ Punti di forza:</strong><ul>{items}</ul></div>"
        
        # Aree da approfondire
        aree = dati.get('aree_approfondire_reale', [])
        aree_html = ""
        if aree:
            items = ''.join([f"<li>{self._escape(a)}</li>" for a in aree])
            aree_html = f"<div style='margin-top: 15px;'><strong>⚠️ Aree da approfondire:</strong><ul>{items}</ul></div>"
        
        return f"""
    <div class="card">
        <h3>📈 Confronto vs Framework Reale</h3>
        <p style="color: #6b7280; margin-bottom: 15px;">Quanto il programma è allineato a cosa si insegna effettivamente</p>
        
        <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 20px;">
            <div style="text-align: center;">
                <div style="font-size: 36px; font-weight: bold; color: {colore};">{percentuale}%</div>
                <div style="color: #6b7280;">{label}</div>
            </div>
            <div style="flex: 1;">
                <div class="meter" style="height: 12px;">
                    <div class="meter-fill" style="width: {percentuale}%; background: {colore};"></div>
                </div>
            </div>
        </div>
        
        {moduli_html}
        {punti_forza_html}
        {aree_html}
    </div>"""
    
    def _genera_tabella_moduli(self, moduli: List[Dict]) -> str:
        """Genera la tabella HTML dei moduli"""
        if not moduli:
            return ""
        
        rows = ""
        for m in moduli:
            nome = m.get('nome', 'Modulo')
            copertura = m.get('copertura', 0)
            rilevanza = m.get('rilevanza', 'medio')
            
            # Colore barra
            if copertura >= 75:
                colore = '#10b981'
            elif copertura >= 50:
                colore = '#f59e0b'
            else:
                colore = '#ef4444'
            
            # Badge rilevanza
            badge_class = rilevanza.lower() if rilevanza else 'medio'
            
            rows += f"""
            <tr>
                <td><strong>{self._escape(nome)}</strong></td>
                <td>
                    <div class="coverage-bar">
                        <div class="bar">
                            <div class="fill" style="width: {copertura}%; background: {colore};"></div>
                        </div>
                        <span class="value">{copertura}%</span>
                    </div>
                </td>
                <td><span class="badge {badge_class}">{self._escape(rilevanza)}</span></td>
            </tr>"""
        
        return f"""
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Modulo</th>
                    <th>Copertura</th>
                    <th>Rilevanza</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>"""
    
    def _genera_gap_identificati(self, dati: Dict[str, Any]) -> str:
        """Genera la sezione gap identificati"""
        gaps = dati.get('gap_analysis', [])
        
        if not gaps:
            # Genera gap dai dati di copertura
            gaps = self._genera_gap_da_copertura(dati)
        
        if not gaps:
            return """
    <h2>🔍 Gap Identificati</h2>
    <div class="card">
        <p>Nessun gap significativo identificato.</p>
    </div>"""
        
        gaps_html = ""
        for gap in gaps:
            tipo = gap.get('tipo', 'Contenuto Mancante')
            priorita = gap.get('priorita', 'media')
            titolo = gap.get('titolo', '')
            descrizione = gap.get('descrizione', '')
            fonte = gap.get('fonte', '')
            evidenza = gap.get('evidenza', '')
            impatto = gap.get('impatto_commerciale', '')
            
            badge_class = priorita.lower() if priorita else 'media'
            
            fonte_html = f"<em>Fonte: {self._escape(fonte)}</em>" if fonte else ""
            evidenza_html = f' | Evidenza: "{self._escape(evidenza)}"' if evidenza else ""
            impatto_html = f'<p style="font-size: 13px; color: #059669; margin-top: 8px;">💼 <strong>Impatto commerciale:</strong> {self._escape(impatto)}</p>' if impatto else ""
            
            gaps_html += f"""
        <div class="gap-item">
            <div class="gap-header">
                <strong>⚠️ {self._escape(tipo)}</strong>
                <span class="badge {badge_class}">{self._escape(priorita)}</span>
            </div>
            <p><strong>{self._escape(titolo)}</strong></p>
            <p>{self._escape(descrizione)}</p>
            <p style="font-size: 13px; color: #6b7280; margin-top: 8px;">
                {fonte_html}{evidenza_html}
            </p>
            {impatto_html}
        </div>"""
        
        return f"""
    <h2>🔍 Gap Identificati</h2>
    {gaps_html}"""
    
    def _genera_gap_da_copertura(self, dati_o_copertura: Dict) -> List[Dict]:
        """Genera automaticamente i gap dalla copertura argomenti"""
        gaps = []
        
        # Se è il dict completo dei dati
        if 'argomenti_mancanti' in dati_o_copertura:
            mancanti = dati_o_copertura.get('argomenti_mancanti', [])
        elif 'copertura_argomenti' in dati_o_copertura:
            mancanti = dati_o_copertura.get('copertura_argomenti', {}).get('argomenti_mancanti', [])
        else:
            mancanti = dati_o_copertura.get('argomenti_mancanti', [])
        
        for i, arg in enumerate(mancanti[:5]):  # Max 5 gap
            priorita = 'alta' if i == 0 else 'bassa'
            gaps.append({
                'tipo': 'Contenuto Mancante',
                'priorita': priorita,
                'titolo': arg,
                'descrizione': f"Modulo '{arg}' non sufficientemente coperto nel programma attuale",
                'fonte': 'ideale',
                'evidenza': f"Contenuti mancanti nel curriculum",
                'impatto_commerciale': f"Opportunità di proporre manuale Zanichelli con copertura completa di {arg}"
            })
        
        return gaps
    
    def _genera_moduli_da_copertura(self, copertura: Dict, tipo: str) -> List[Dict]:
        """Genera moduli fittizi dalla copertura argomenti"""
        coperti = copertura.get('argomenti_coperti', [])
        mancanti = copertura.get('argomenti_mancanti', [])
        
        moduli = []
        
        # Argomenti coperti = 75-100%
        for arg in coperti[:5]:
            moduli.append({
                'nome': arg,
                'copertura': 100 if tipo == 'reale' else 75,
                'rilevanza': 'alto'
            })
        
        # Argomenti mancanti = 0-25%
        for arg in mancanti[:5]:
            moduli.append({
                'nome': arg,
                'copertura': 25 if tipo == 'reale' else 0,
                'rilevanza': 'basso' if tipo == 'ideale' else 'medio'
            })
        
        return moduli
    
    def _genera_strategia(self, dati: Dict[str, Any]) -> str:
        """Genera la sezione strategia di approccio"""
        strategia = dati.get('strategia', {})
        domande = dati.get('domande_discovery', [])
        
        # Domande di default
        if not domande:
            domande = [
                f"Quali sono le sfide principali che affronta nel suo corso di {dati['corso']}?",
                "Come valuta l'importanza dei contenuti pratici e di laboratorio nel suo programma?"
            ]
        
        # Gap che risolve
        mancanti = dati.get('argomenti_mancanti', [])
        gap_risolve = ', '.join(mancanti[:3]) if mancanti else 'contenuti mancanti nel programma attuale'
        
        # Approccio
        approccio = dati.get('approccio', '')
        if not approccio:
            approccio = "Il promotore dovrebbe presentarsi come un partner accademico, pronto ad ascoltare le esigenze del docente e a proporre soluzioni personalizzate che possano integrare e migliorare il materiale didattico attuale."
        
        domande_html = ''.join([f"<li>{self._escape(d)}</li>" for d in domande])
        
        return f"""
    <h2>🎯 Strategia di Approccio</h2>
    
        <div class="strategy-phase">
            <h3><span class="phase-number">1</span>Apertura e Riconoscimento</h3>
            <p>Riconoscere il valore del programma del docente e il suo approccio didattico. Stabilire rapport.</p>
            <p><strong>Obiettivo:</strong> Creare fiducia e apertura al dialogo.</p>
        </div>
        
        <div class="strategy-phase">
            <h3><span class="phase-number">2</span>Discovery e Ascolto</h3>
            <p>Esplorare le esigenze e le criticità attuali.</p>
            <p><strong>Domande chiave:</strong></p>
            <ul>{domande_html}</ul>
        </div>
        
        <div class="strategy-phase">
            <h3><span class="phase-number">3</span>Proposta e Argomentazione</h3>
            
            <p><strong>Manuale da proporre:</strong> {self._escape(dati['manuale_titolo'])} di {self._escape(dati['manuale_autore'])}</p>
            <p><strong>Gap che risolve:</strong> {self._escape(gap_risolve)}</p>
            
            <p><strong>Approccio:</strong> {self._escape(approccio)}</p>
        </div>"""
    
    def _genera_argomenti_vendita(self, dati: Dict[str, Any]) -> str:
        """Genera la sezione argomenti di vendita"""
        argomenti = dati.get('argomenti_vendita', [])
        
        # Argomenti di default se non presenti
        if not argomenti:
            mancanti = dati.get('argomenti_mancanti', ['contenuti avanzati'])
            argomenti = [
                f"Copertura completa di {mancanti[0]}, essenziale per il corso." if mancanti else "Copertura completa dei contenuti fondamentali.",
                "Esercizi pratici e problemi che stimolano il problem solving e l'applicazione pratica.",
                "Materiali digitali e risorse online per supportare l'apprendimento degli studenti."
            ]
        
        argomenti_html = ""
        for arg in argomenti:
            argomenti_html += f"""
        <div class="card success">
            <p>✓ {self._escape(arg)}</p>
        </div>"""
        
        # Conta capitoli
        capitoli = dati.get('capitoli_rilevanti', [])
        num_capitoli = len(capitoli) if capitoli else 25
        
        return f"""
    <h2>💪 Argomenti di Vendita</h2>
    {argomenti_html}
    
        <div class="card highlight" style="margin-top: 20px;">
            <h3>📚 Manuale Zanichelli Consigliato</h3>
            <p style="font-size: 1.1em;"><strong>{self._escape(dati['manuale_titolo'])}</strong></p>
            <p style="color: #6b7280;">{self._escape(dati['manuale_autore'])}</p>
            <p style="margin-top: 10px;"><strong>Match Score:</strong> {dati['match_score']}%</p>
            <p style="margin-top: 10px; font-size: 14px;">📖 Testo completo ({num_capitoli} capitoli)<br>🔬 Supporto per attività di laboratorio</p>
        </div>"""
    
    def _genera_email(self, dati: Dict[str, Any]) -> str:
        """Genera la sezione email"""
        email_data = dati.get('email', {})
        
        oggetto = email_data.get('oggetto', f"Supporto didattico per il corso di {dati['corso']}")
        
        # Corpo email
        if email_data.get('corpo'):
            corpo = email_data['corpo']
        else:
            mancanti = dati.get('argomenti_mancanti', ['contenuti avanzati'])
            leva = mancanti[0] if mancanti else 'contenuti completi'
            gap_lista = ', '.join(mancanti[:2]) if mancanti else 'contenuti mancanti'
            
            argomenti = dati.get('argomenti_vendita', [
                "Copertura completa dei contenuti fondamentali del corso.",
                "Esercizi pratici e problemi che stimolano il problem solving.",
                "Materiali digitali per supportare l'apprendimento."
            ])
            argomenti_testo = '\n'.join([f"• {a}" for a in argomenti[:3]])
            
            corpo = f"""Gentile Prof. {dati['docente']},

Mi chiamo [Nome Promotore] e sono promotore editoriale per Zanichelli. Ho avuto modo di esaminare il programma del Suo corso di {dati['corso']} presso {dati['universita']}, apprezzando l'approccio didattico {dati.get('approccio_didattico', 'bilanciato').lower()} che caratterizza il Suo insegnamento.

Ho notato che il programma dedica particolare attenzione a {leva}, un'area in cui il manuale attualmente adottato potrebbe non offrire una copertura completa.

Per questo motivo, Le propongo di valutare "{dati['manuale_titolo']}" di {dati['manuale_autore']} (Zanichelli), che offre:
{argomenti_testo}

In particolare, questo testo risolve le criticità relative a: {gap_lista}.

Posso inviarLe una copia saggio per una valutazione senza impegno? Resto a disposizione per qualsiasi informazione o per fissare un breve incontro.

Cordiali saluti,
[Nome Promotore]
Promotore Editoriale - Zanichelli
[Telefono] | [Email]"""
        
        return f"""
    <h2>✉️ Email Generata</h2>
    <p><strong>Oggetto:</strong> {self._escape(oggetto)}</p>
    <div class="email-box">{self._escape(corpo)}</div>"""
    
    def _genera_footer(self, dati: Dict[str, Any]) -> str:
        """Genera il footer del report"""
        confidence = dati.get('punteggio_opportunita', 80)
        
        return f"""
    <div class="footer">
        <p>Analisi generata da CoreX - Zanichelli Promo Intelligence</p>
        <p>Confidence: {confidence}% | {dati['data']}</p>
    </div>"""


# Funzione di utilità per uso diretto
def genera_report_html(analisi: Dict[str, Any]) -> str:
    """
    Funzione wrapper per generare il report HTML.
    
    Args:
        analisi: Dizionario con i dati dell'analisi
        
    Returns:
        Stringa HTML del report
    """
    generator = CommercialReportGenerator()
    return generator.genera_report_html(analisi)


# Test del modulo
if __name__ == "__main__":
    # Dati di test
    test_analisi = {
        'dati_programma': {
            'docente': 'Monica Scognamiglio',
            'corso': 'Chimica organica',
            'universita': 'Campania Vanvitelli',
            'cfu': 8,
            'ore': 80
        },
        'manuale_zanichelli': {
            'titolo': 'Chimica organica',
            'autore': 'Solomons',
            'match_score': 100,
            'capitoli_rilevanti': ['Cap. 5: Stereochimica', 'Cap. 19: Composti dicarbonilici', 'Cap. 9: NMR']
        },
        'concorrente_principale': {
            'titolo': 'Chimica organica',
            'autore': 'Bruice',
            'editore': 'EdiSES'
        },
        'analisi_competitiva': {
            'situazione': 'assente',
            'descrizione': 'Zanichelli non presente in bibliografia'
        },
        'copertura_argomenti': {
            'percentuale': 54,
            'argomenti_coperti': ['Stereochimica', 'Gruppi funzionali', 'Meccanismi di reazione'],
            'argomenti_mancanti': ['Chimica dei polimeri', 'Tecniche spettroscopiche', 'Sintesi avanzata']
        },
        'raccomandazioni': {
            'priorita': 'alta',
            'lista': ['Proporre copia saggio', 'Evidenziare gap polimeri'],
            'approccio': 'Consultivo'
        },
        'punteggio_opportunita': 80
    }
    
    report = genera_report_html(test_analisi)
    
    # Salva il report di test
    with open('test_report.html', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("Report di test generato: test_report.html")
