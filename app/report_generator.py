"""
CoreX - Report Generator v3.2
Report strutturato: Moduli IDEALI con copertura REALE
Copertura individuale per ogni syllabus
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class ReportGenerator:
    """Genera report HTML per analisi CoreX con mapping su framework ideale"""
    
    def __init__(self, reference_framework: Optional[Dict] = None):
        self.reference_framework = reference_framework
        self.analysis_data = None
    
    def set_analysis_data(self, data: Dict):
        """Imposta i dati dell'analisi"""
        self.analysis_data = data
    
    def _get_level_badge(self, level: int) -> str:
        """Genera badge HTML per il livello"""
        colors = {
            5: ("#2e7d32", "white"),
            4: ("#689f38", "white"),
            3: ("#fbc02d", "#333"),
            2: ("#f57c00", "white"),
            1: ("#d32f2f", "white"),
            0: ("#9e9e9e", "white")
        }
        bg, fg = colors.get(level, ("#9e9e9e", "white"))
        return f'<span class="level-badge" style="background:{bg};color:{fg};">{level}/5</span>'
    
    def _get_level_icon(self, level: int) -> str:
        """Emoji per il livello"""
        icons = {5: "🟢", 4: "🟢", 3: "🟡", 2: "🟠", 1: "🔴", 0: "⚪"}
        return icons.get(level, "⚪")
    
    def _format_concepts_list(self, concepts: List, max_show: int = 6) -> str:
        """Formatta lista concetti con frequenze"""
        if not concepts:
            return '<span class="no-data">Nessun concetto trovato</span>'
        
        html_parts = []
        for i, c in enumerate(concepts[:max_show]):
            if isinstance(c, dict):
                name = c.get("name", "?")
                freq = c.get("frequency", 0)
                freq_class = "freq-high" if freq >= 60 else "freq-medium" if freq >= 30 else "freq-low"
                html_parts.append(f'<span class="concept-tag {freq_class}">{name} ({freq:.0f}%)</span>')
            else:
                html_parts.append(f'<span class="concept-tag freq-low">{c}</span>')
        
        html = " ".join(html_parts)
        
        if len(concepts) > max_show:
            remaining = len(concepts) - max_show
            html += f' <span class="more-items">+{remaining} altri</span>'
        
        return html
    
    def _format_missing_contents(self, contents: List, max_show: int = 5) -> str:
        """Formatta lista contenuti mancanti"""
        if not contents:
            return '<span class="all-covered">✓ Tutti coperti</span>'
        
        html_parts = []
        for content in contents[:max_show]:
            html_parts.append(f'<span class="missing-item">{content}</span>')
        
        html = " ".join(html_parts)
        
        if len(contents) > max_show:
            remaining = len(contents) - max_show
            html += f' <span class="more-items">+{remaining} altri</span>'
        
        return html
    
    def _get_css_styles(self) -> str:
        """CSS completo per il report"""
        return """
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px 40px; 
                background: #f5f7fa; 
                color: #333;
                line-height: 1.6;
            }
            .container { 
                max-width: 1500px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px 40px; 
                border-radius: 12px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.07); 
            }
            h1 { 
                color: #1a237e; 
                border-bottom: 3px solid #3949ab; 
                padding-bottom: 15px; 
                margin-bottom: 10px;
                font-size: 1.8em;
            }
            h2 { 
                color: #283593; 
                margin-top: 35px; 
                margin-bottom: 15px;
                font-size: 1.3em;
                border-left: 4px solid #3949ab;
                padding-left: 15px;
            }
            h3 {
                color: #3949ab;
                margin-top: 25px;
                font-size: 1.1em;
            }
            .subtitle {
                color: #666;
                font-size: 1.05em;
                margin-bottom: 25px;
            }
            
            /* Summary Cards */
            .summary-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); 
                gap: 15px; 
                margin: 20px 0; 
            }
            .stat-card { 
                background: linear-gradient(135deg, #e8eaf6, #c5cae9); 
                padding: 18px; 
                border-radius: 10px; 
                text-align: center;
            }
            .stat-value { 
                font-size: 2em; 
                font-weight: bold; 
                color: #1a237e; 
            }
            .stat-label { 
                color: #5c6bc0; 
                margin-top: 5px; 
                font-size: 0.9em;
            }
            .stat-card.success { background: linear-gradient(135deg, #e8f5e9, #c8e6c9); }
            .stat-card.success .stat-value { color: #2e7d32; }
            .stat-card.warning { background: linear-gradient(135deg, #fff3e0, #ffe0b2); }
            .stat-card.warning .stat-value { color: #e65100; }
            .stat-card.info { background: linear-gradient(135deg, #e3f2fd, #bbdefb); }
            .stat-card.info .stat-value { color: #1565c0; }
            
            /* Level Badge */
            .level-badge {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-width: 50px;
                padding: 4px 12px;
                border-radius: 15px;
                font-weight: bold;
                font-size: 0.85em;
            }
            
            /* Table Styles */
            .data-table { 
                width: 100%; 
                border-collapse: collapse; 
                margin: 15px 0; 
                font-size: 0.92em;
            }
            .data-table th { 
                background: #3949ab; 
                color: white; 
                padding: 12px 10px; 
                text-align: left; 
                font-weight: 600;
            }
            .data-table th:first-child { border-radius: 8px 0 0 0; }
            .data-table th:last-child { border-radius: 0 8px 0 0; }
            .data-table td { 
                padding: 12px 10px; 
                border-bottom: 1px solid #e0e0e0; 
                vertical-align: top;
            }
            .data-table tr:hover { background: #f8f9ff; }
            .data-table tr.row-high { background: #f1f8e9; }
            .data-table tr.row-medium { background: #fffde7; }
            .data-table tr.row-low { background: #ffebee; }
            
            /* Concepts Styling */
            .concept-tag {
                display: inline-block;
                padding: 3px 10px;
                margin: 2px 3px 2px 0;
                border-radius: 12px;
                font-size: 0.85em;
            }
            .freq-high { background: #c8e6c9; color: #2e7d32; }
            .freq-medium { background: #fff3e0; color: #e65100; }
            .freq-low { background: #e3f2fd; color: #1565c0; }
            .no-data { color: #999; font-style: italic; }
            .more-items {
                color: #666;
                font-style: italic;
                font-size: 0.9em;
            }
            
            /* Missing Items */
            .missing-item {
                display: inline-block;
                padding: 3px 10px;
                margin: 2px 3px 2px 0;
                border-radius: 12px;
                font-size: 0.85em;
                background: #ffcdd2;
                color: #c62828;
            }
            .all-covered {
                color: #2e7d32;
                font-weight: 500;
            }
            
            /* Status Labels */
            .status-high { color: #2e7d32; font-weight: 600; }
            .status-medium { color: #f57c00; font-weight: 600; }
            .status-low { color: #d32f2f; font-weight: 600; }
            
            /* Assessment Box */
            .assessment-box {
                padding: 20px 25px;
                margin: 20px 0;
                border-radius: 10px;
                border-left: 5px solid;
            }
            .assessment-box.success { 
                background: linear-gradient(135deg, #e8f5e9, #fff);
                border-color: #4caf50;
            }
            .assessment-box.warning { 
                background: linear-gradient(135deg, #fff3e0, #fff);
                border-color: #ff9800;
            }
            .assessment-box.info { 
                background: linear-gradient(135deg, #e3f2fd, #fff);
                border-color: #2196f3;
            }
            .assessment-title { 
                font-size: 1.1em; 
                font-weight: bold; 
                margin-bottom: 10px;
            }
            .assessment-score {
                font-size: 2.8em;
                font-weight: bold;
                margin: 10px 0;
            }
            .score-high { color: #2e7d32; }
            .score-medium { color: #f57c00; }
            .score-low { color: #d32f2f; }
            
            /* Gap Section */
            .gap-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 20px 0;
            }
            .gap-box {
                padding: 20px;
                border-radius: 10px;
            }
            .gap-box.reality {
                background: #e8f5e9;
                border: 1px solid #a5d6a7;
            }
            .gap-box.ideal {
                background: #fff3e0;
                border: 1px solid #ffcc80;
            }
            .gap-title {
                font-weight: bold;
                font-size: 1.05em;
                margin-bottom: 10px;
            }
            .gap-item {
                display: inline-block;
                background: white;
                padding: 4px 12px;
                margin: 3px;
                border-radius: 15px;
                font-size: 0.9em;
            }
            
            /* Progress Bar */
            .progress-bar {
                width: 100%;
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
                overflow: hidden;
                margin-top: 5px;
            }
            .progress-fill {
                height: 100%;
                border-radius: 4px;
                transition: width 0.3s ease;
            }
            .progress-high { background: #4caf50; }
            .progress-medium { background: #ff9800; }
            .progress-low { background: #f44336; }
            
            /* Footer */
            .report-footer {
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                color: #888;
                font-size: 0.85em;
                text-align: center;
            }
            
            /* Syllabus Profile */
            .profile-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 15px;
                font-size: 0.85em;
                font-weight: 500;
            }
            .profile-completo { background: #c8e6c9; color: #2e7d32; }
            .profile-standard { background: #fff3e0; color: #e65100; }
            .profile-essenziale { background: #e3f2fd; color: #1565c0; }
            .profile-ridotto { background: #ffcdd2; color: #c62828; }
            
            /* Responsive */
            @media (max-width: 900px) {
                .gap-container { grid-template-columns: 1fr; }
                body { padding: 10px; }
                .container { padding: 15px; }
                .data-table { font-size: 0.85em; }
            }
        </style>
        """
    
    def generate_analysis_report(self, materia: str, classi: List[str]) -> str:
        """Genera il report HTML completo con mapping su framework ideale"""
        if not self.analysis_data:
            return "<html><body><h1>Errore: nessun dato di analisi</h1></body></html>"
        
        data = self.analysis_data
        
        # Estrai dati principali
        overall = data.get("overall_assessment", {})
        analysis_summary = data.get("analysis_summary", {})
        ideal_info = data.get("ideal_framework_info", {})
        modules_by_cov = data.get("modules_by_coverage", {})
        modules_analysis = data.get("modules_analysis", {})
        gaps = data.get("gaps_analysis", {})
        syllabus_details = data.get("syllabus_details", [])
        
        n_syllabus = analysis_summary.get("n_syllabus_analyzed", 0)
        n_concepts = analysis_summary.get("n_concepts_extracted", 0)
        n_mapped = analysis_summary.get("n_concepts_mapped", 0)
        
        coverage_pct = overall.get("coverage_percentage", 0)
        judgment = overall.get("judgment", "N/D")
        recommendation = overall.get("recommendation", "")
        
        # Determina classi di stile
        if coverage_pct >= 70:
            score_class = "score-high"
            box_class = "success"
        elif coverage_pct >= 40:
            score_class = "score-medium"
            box_class = "warning"
        else:
            score_class = "score-low"
            box_class = "info"
        
        # Inizia HTML
        html = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Report Analisi - {materia}</title>
    {self._get_css_styles()}
</head>
<body>
<div class="container">
    <h1>📊 Report Analisi: {materia.replace('_', ' ')}</h1>
    <p class="subtitle">
        <strong>Classi di laurea:</strong> {', '.join(classi)} | 
        <strong>Framework ideale:</strong> {ideal_info.get('name', 'N/D')} |
        <strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </p>
    
    <!-- Valutazione Complessiva -->
    <div class="assessment-box {box_class}">
        <div class="assessment-title">📐 Copertura Complessiva del Framework Ideale</div>
        <div class="assessment-score {score_class}">{coverage_pct:.0f}%</div>
        <div><strong>{judgment}</strong></div>
        <div style="margin-top: 8px; color: #666;">{recommendation}</div>
        <div class="progress-bar" style="margin-top: 15px;">
            <div class="progress-fill progress-{'high' if coverage_pct >= 70 else 'medium' if coverage_pct >= 40 else 'low'}" 
                 style="width: {min(coverage_pct, 100)}%;"></div>
        </div>
    </div>
    
    <!-- Statistiche Riassuntive -->
    <div class="summary-grid">
        <div class="stat-card">
            <div class="stat-value">{n_syllabus}</div>
            <div class="stat-label">Programmi analizzati</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{n_concepts}</div>
            <div class="stat-label">Concetti estratti</div>
        </div>
        <div class="stat-card info">
            <div class="stat-value">{n_mapped}</div>
            <div class="stat-label">Concetti mappati</div>
        </div>
        <div class="stat-card {'success' if coverage_pct >= 60 else 'warning'}">
            <div class="stat-value">{overall.get('contents_covered', 'N/D')}</div>
            <div class="stat-label">Contenuti coperti</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{ideal_info.get('n_modules', 0)}</div>
            <div class="stat-label">Moduli ideali</div>
        </div>
    </div>
    
    <!-- ============================================ -->
    <!-- TABELLA MODULI IDEALI CON COPERTURA REALE -->
    <!-- ============================================ -->
    
    <h2>📚 Analisi per Modulo del Framework Ideale</h2>
    <p>Ogni riga rappresenta un modulo del framework ideale. La copertura indica quanto di quel modulo 
    è effettivamente presente nei programmi universitari analizzati.</p>
    
    <table class="data-table">
        <thead>
            <tr>
                <th style="width: 18%;">Modulo</th>
                <th style="width: 10%;">Copertura</th>
                <th style="width: 8%;">Livello</th>
                <th style="width: 32%;">Concetti trovati</th>
                <th style="width: 32%;">Contenuti mancanti</th>
            </tr>
        </thead>
        <tbody>
"""
        
        # Ordina moduli per ID
        sorted_modules = sorted(modules_analysis.values(), key=lambda x: x.get("module_id", 0))
        
        for mod in sorted_modules:
            mod_name = mod.get("module_name", "N/D")
            coverage = mod.get("coverage_percentage", 0)
            n_covered = mod.get("n_contents_covered", 0)
            n_total = mod.get("n_contents_total", 0)
            matched_concepts = mod.get("matched_concepts", [])
            missing = mod.get("missing_contents", [])
            
            level = 5 if coverage >= 80 else 4 if coverage >= 60 else 3 if coverage >= 40 else 2 if coverage >= 20 else 1
            row_class = "row-high" if coverage >= 70 else "row-medium" if coverage >= 40 else "row-low"
            status_class = "status-high" if coverage >= 70 else "status-medium" if coverage >= 40 else "status-low"
            
            html += f"""
            <tr class="{row_class}">
                <td>
                    <strong>{mod_name}</strong><br>
                    <small style="color:#666;">{n_covered}/{n_total} contenuti</small>
                </td>
                <td style="text-align: center;">
                    <span class="{status_class}" style="font-size: 1.2em;">{coverage:.0f}%</span>
                    <div class="progress-bar" style="margin-top: 5px;">
                        <div class="progress-fill progress-{'high' if coverage >= 70 else 'medium' if coverage >= 40 else 'low'}" 
                             style="width: {min(coverage, 100)}%;"></div>
                    </div>
                </td>
                <td style="text-align: center;">
                    {self._get_level_icon(level)} {self._get_level_badge(level)}
                </td>
                <td>{self._format_concepts_list(matched_concepts)}</td>
                <td>{self._format_missing_contents(missing)}</td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>
"""
        
        # Riepilogo moduli per copertura
        well_covered = modules_by_cov.get("well_covered", [])
        partially_covered = modules_by_cov.get("partially_covered", [])
        poorly_covered = modules_by_cov.get("poorly_covered", [])
        
        html += f"""
    <h2>📈 Riepilogo per Livello di Copertura</h2>
    <div class="summary-grid">
        <div class="stat-card success">
            <div class="stat-value">{len(well_covered)}</div>
            <div class="stat-label">Ben coperti (≥70%)</div>
        </div>
        <div class="stat-card warning">
            <div class="stat-value">{len(partially_covered)}</div>
            <div class="stat-label">Parzialmente (40-70%)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(poorly_covered)}</div>
            <div class="stat-label">Poco coperti (<40%)</div>
        </div>
    </div>
"""
        
        # Gap Analysis
        reality_gaps = gaps.get("reality_not_in_ideal", {})
        ideal_gaps = gaps.get("ideal_not_in_reality", {})
        reality_items = reality_gaps.get("items", [])
        ideal_items = ideal_gaps.get("items", [])
        
        if reality_items or ideal_items:
            html += """
    <h2>🔍 Analisi dei Gap</h2>
    <div class="gap-container">
"""
            
            if reality_items:
                html += f"""
        <div class="gap-box reality">
            <div class="gap-title">✅ Nella REALTÀ ma non nell'IDEALE</div>
            <p style="font-size: 0.9em; color: #666; margin-bottom: 10px;">
                {reality_gaps.get('description', 'Argomenti frequenti nei programmi ma non nel framework')}
            </p>
            <div>
"""
                for item in reality_items[:12]:
                    name = item.get("name", item) if isinstance(item, dict) else item
                    freq = item.get("frequency", "") if isinstance(item, dict) else ""
                    freq_str = f" ({freq:.0f}%)" if freq else ""
                    html += f'<span class="gap-item">{name}{freq_str}</span>\n'
                
                if len(reality_items) > 12:
                    html += f'<span class="gap-item" style="background:#c8e6c9;">+{len(reality_items)-12} altri</span>'
                
                html += """
            </div>
            <p style="font-size: 0.85em; color: #2e7d32; margin-top: 10px;">
                <strong>Azione:</strong> Valutare l'inserimento nel framework ideale
            </p>
        </div>
"""
            
            if ideal_items:
                html += f"""
        <div class="gap-box ideal">
            <div class="gap-title">⚠️ Nell'IDEALE ma non nella REALTÀ</div>
            <p style="font-size: 0.9em; color: #666; margin-bottom: 10px;">
                {ideal_gaps.get('description', 'Contenuti previsti ma raramente insegnati')}
            </p>
            <div>
"""
                for item in ideal_items[:12]:
                    content = item.get("content", item) if isinstance(item, dict) else item
                    html += f'<span class="gap-item">{content}</span>\n'
                
                if len(ideal_items) > 12:
                    html += f'<span class="gap-item" style="background:#ffe0b2;">+{len(ideal_items)-12} altri</span>'
                
                html += """
            </div>
            <p style="font-size: 0.85em; color: #e65100; margin-top: 10px;">
                <strong>Azione:</strong> Verificare se mantenere o aggiornare il framework
            </p>
        </div>
"""
            
            html += """
    </div>
"""
        
        # ============================================
        # DETTAGLIO PROGRAMMI ANALIZZATI
        # ============================================
        
        if syllabus_details:
            # Calcola medie per confronto
            avg_concepts = sum(s.get("n_concepts", 0) for s in syllabus_details) / len(syllabus_details) if syllabus_details else 0
            
            html += """
    <h2>📄 Dettaglio Programmi Analizzati</h2>
    <p>Per ogni programma vengono mostrate due metriche:</p>
    <ul style="margin: 10px 0 20px 20px; color: #666;">
        <li><strong>Ampiezza:</strong> Numero di concetti estratti da questo programma (rispetto alla media)</li>
        <li><strong>Copertura Framework Ideale:</strong> Percentuale di contenuti del framework ideale coperti da questo specifico programma</li>
    </ul>
    
    <table class="data-table">
        <thead>
            <tr>
                <th>Università</th>
                <th>Docente</th>
                <th>Classe</th>
                <th style="width: 12%;">Ampiezza</th>
                <th style="width: 18%;">Copertura Framework Ideale</th>
                <th style="width: 12%;">Profilo</th>
            </tr>
        </thead>
        <tbody>
"""
            
            for syl in syllabus_details:
                university = syl.get("university", "N/D")
                professor = syl.get("professor", "N/D")
                classe = syl.get("classe", "N/D")
                n_concepts = syl.get("n_concepts", 0)
                ideal_coverage = syl.get("ideal_coverage", 0)
                judgment = syl.get("judgment", "N/D")
                contents_covered = syl.get("contents_covered", 0)
                total_contents = syl.get("total_ideal_contents", 0)
                
                # Ampiezza rispetto alla media
                if avg_concepts > 0:
                    ampiezza_ratio = n_concepts / avg_concepts
                    if ampiezza_ratio >= 1.2:
                        ampiezza_desc = "Molto ampio"
                        ampiezza_class = "status-high"
                    elif ampiezza_ratio >= 0.8:
                        ampiezza_desc = "Nella media"
                        ampiezza_class = "status-medium"
                    else:
                        ampiezza_desc = "Ridotto"
                        ampiezza_class = "status-low"
                else:
                    ampiezza_desc = "N/D"
                    ampiezza_class = ""
                
                # Classe per copertura
                if ideal_coverage >= 55:
                    cov_class = "status-high"
                    profile_class = "profile-completo"
                elif ideal_coverage >= 40:
                    cov_class = "status-medium"
                    profile_class = "profile-standard"
                elif ideal_coverage >= 25:
                    cov_class = "status-medium"
                    profile_class = "profile-essenziale"
                else:
                    cov_class = "status-low"
                    profile_class = "profile-ridotto"
                
                html += f"""
            <tr>
                <td>{university}</td>
                <td>{professor}</td>
                <td>{classe}</td>
                <td style="text-align: center;">
                    <span class="{ampiezza_class}">{ampiezza_desc}</span><br>
                    <small style="color: #999;">{n_concepts} concetti</small>
                </td>
                <td style="text-align: center;">
                    <span class="{cov_class}" style="font-size: 1.1em;">{ideal_coverage:.0f}%</span>
                    <div class="progress-bar" style="margin-top: 5px;">
                        <div class="progress-fill progress-{'high' if ideal_coverage >= 55 else 'medium' if ideal_coverage >= 25 else 'low'}" 
                             style="width: {min(ideal_coverage, 100)}%;"></div>
                    </div>
                    <small style="color: #999;">{contents_covered}/{total_contents} contenuti</small>
                </td>
                <td style="text-align: center;">
                    <span class="profile-badge {profile_class}">{judgment.replace('Programma ', '')}</span>
                </td>
            </tr>
"""
            
            html += """
        </tbody>
    </table>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 15px;">
        <strong>Legenda Profili:</strong><br>
        <span class="profile-badge profile-completo" style="margin: 5px;">Completo</span> Copertura ≥55% del framework ideale<br>
        <span class="profile-badge profile-standard" style="margin: 5px;">Standard</span> Copertura 40-55%<br>
        <span class="profile-badge profile-essenziale" style="margin: 5px;">Essenziale</span> Copertura 25-40%<br>
        <span class="profile-badge profile-ridotto" style="margin: 5px;">Ridotto</span> Copertura <25%
    </div>
"""
        
        # Footer
        html += f"""
    <div class="report-footer">
        Report generato da <strong>CoreX v3.2</strong> — Zanichelli<br>
        Mapping su Framework Ideale: {ideal_info.get('name', 'N/D')}<br>
        {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
</div>
</body>
</html>
"""
        
        return html
    
    def generate_changelog(self, materia: str, classi: List[str]) -> str:
        """Genera changelog con dettaglio concetti per modulo"""
        if not self.analysis_data:
            return "<html><body><h1>Errore: nessun dato</h1></body></html>"
        
        data = self.analysis_data
        modules_analysis = data.get("modules_analysis", {})
        modules_by_cov = data.get("modules_by_coverage", {})
        gaps = data.get("gaps_analysis", {})
        ideal_info = data.get("ideal_framework_info", {})
        
        html = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Changelog - {materia}</title>
    {self._get_css_styles()}
    <style>
        .module-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 5px solid;
        }}
        .module-card.high {{ border-color: #4caf50; }}
        .module-card.medium {{ border-color: #ff9800; }}
        .module-card.low {{ border-color: #f44336; }}
        .module-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .module-title {{ font-size: 1.1em; font-weight: bold; }}
        .module-coverage {{ font-size: 1.3em; font-weight: bold; }}
        .concepts-section {{ margin-top: 15px; }}
        .action-box {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>🔄 Changelog: {materia.replace('_', ' ')}</h1>
    <p class="subtitle">
        Classi: {', '.join(classi)} | 
        Framework: {ideal_info.get('name', 'N/D')} |
        Generato: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </p>
    
    <div class="summary-grid">
        <div class="stat-card success">
            <div class="stat-value">{len(modules_by_cov.get('well_covered', []))}</div>
            <div class="stat-label">Moduli ben coperti</div>
        </div>
        <div class="stat-card warning">
            <div class="stat-value">{len(modules_by_cov.get('partially_covered', []))}</div>
            <div class="stat-label">Parzialmente coperti</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(modules_by_cov.get('poorly_covered', []))}</div>
            <div class="stat-label">Poco coperti</div>
        </div>
    </div>
"""
        
        # Moduli ben coperti
        well_covered = modules_by_cov.get("well_covered", [])
        if well_covered:
            html += """
    <h2>✅ Moduli BEN COPERTI (≥70%)</h2>
    <p>Questi moduli del framework ideale sono ben rappresentati nei programmi reali:</p>
"""
            for mod in well_covered:
                html += self._render_module_card(mod, "high")
        
        # Moduli parzialmente coperti
        partially = modules_by_cov.get("partially_covered", [])
        if partially:
            html += """
    <h2>🔶 Moduli PARZIALMENTE COPERTI (40-70%)</h2>
    <p>Questi moduli hanno copertura intermedia:</p>
"""
            for mod in partially:
                html += self._render_module_card(mod, "medium")
        
        # Moduli poco coperti
        poorly = modules_by_cov.get("poorly_covered", [])
        if poorly:
            html += """
    <h2>⚠️ Moduli POCO COPERTI (<40%)</h2>
    <p>Questi moduli del framework ideale sono poco rappresentati:</p>
"""
            for mod in poorly:
                html += self._render_module_card(mod, "low")
        
        # Azioni suggerite
        html += """
    <h2>📋 Azioni Suggerite</h2>
    <div class="action-box">
"""
        
        reality_gaps = gaps.get("reality_not_in_ideal", {}).get("items", [])
        ideal_gaps = gaps.get("ideal_not_in_reality", {}).get("items", [])
        
        if reality_gaps:
            html += f"""
        <div style="margin-bottom: 15px; padding: 15px; background: #e8f5e9; border-radius: 8px;">
            <strong style="color: #2e7d32;">➕ Da considerare per il framework ideale</strong><br>
            <span style="color: #666;">{len(reality_gaps)} argomenti frequenti nei programmi ma non nel framework</span>
        </div>
"""
        
        if ideal_gaps:
            html += f"""
        <div style="margin-bottom: 15px; padding: 15px; background: #fff3e0; border-radius: 8px;">
            <strong style="color: #e65100;">🔍 Da verificare nel framework ideale</strong><br>
            <span style="color: #666;">{len(ideal_gaps)} contenuti del framework sono raramente insegnati</span>
        </div>
"""
        
        if poorly:
            html += f"""
        <div style="padding: 15px; background: #ffebee; border-radius: 8px;">
            <strong style="color: #c62828;">⚡ Attenzione richiesta</strong><br>
            <span style="color: #666;">{len(poorly)} moduli hanno copertura inferiore al 40%</span>
        </div>
"""
        
        html += f"""
    </div>
    
    <div class="report-footer">
        Changelog generato da <strong>CoreX v3.2</strong> — Zanichelli<br>
        {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
</div>
</body>
</html>
"""
        
        return html
    
    def _render_module_card(self, mod: Dict, level: str) -> str:
        """Renderizza una card per un modulo"""
        name = mod.get("module_name", "N/D")
        coverage = mod.get("coverage_percentage", 0)
        concepts = mod.get("matched_concepts", [])
        missing = mod.get("missing_contents", [])
        
        cov_class = "status-high" if coverage >= 70 else "status-medium" if coverage >= 40 else "status-low"
        
        html = f"""
    <div class="module-card {level}">
        <div class="module-header">
            <div class="module-title">{name}</div>
            <div class="module-coverage {cov_class}">{coverage:.0f}%</div>
        </div>
"""
        
        if concepts:
            html += """
        <div class="concepts-section">
            <strong>Concetti trovati:</strong><br>
"""
            for c in concepts[:8]:
                name_c = c.get("name", "?")
                freq = c.get("frequency", 0)
                freq_class = "freq-high" if freq >= 60 else "freq-medium" if freq >= 30 else "freq-low"
                html += f'<span class="concept-tag {freq_class}">{name_c} ({freq:.0f}%)</span> '
            
            if len(concepts) > 8:
                html += f'<span class="more-items">+{len(concepts)-8} altri</span>'
            
            html += """
        </div>
"""
        
        if missing:
            html += """
        <div class="concepts-section" style="margin-top: 10px;">
            <strong style="color: #c62828;">Contenuti mancanti:</strong><br>
"""
            for content in missing[:5]:
                html += f'<span class="missing-item">{content}</span> '
            
            if len(missing) > 5:
                html += f'<span class="more-items">+{len(missing)-5} altri</span>'
            
            html += """
        </div>
"""
        
        html += """
    </div>
"""
        
        return html
    
    def generate_updated_framework(self, materia: str, classi: List[str]) -> Dict:
        """Genera il framework aggiornato in formato JSON"""
        if not self.analysis_data:
            return {}
        
        data = self.analysis_data
        modules_analysis = data.get("modules_analysis", {})
        overall = data.get("overall_assessment", {})
        ideal_info = data.get("ideal_framework_info", {})
        
        framework = {
            "framework": {
                "name": f"Framework REALE - {materia.replace('_', ' ')}",
                "type": "real_from_programs",
                "description": "Framework generato dalla mappatura dei programmi reali sul framework ideale",
                "materia": materia,
                "classes_analyzed": classi,
                "generation_date": datetime.now().isoformat(),
                "source": "CoreX v3.2",
                "ideal_framework_reference": ideal_info.get("name", "N/D")
            },
            "overall_statistics": {
                "coverage_percentage": overall.get("coverage_percentage", 0),
                "judgment": overall.get("judgment", "N/D"),
                "contents_covered": overall.get("contents_covered", "N/D"),
                "n_syllabus_analyzed": data.get("analysis_summary", {}).get("n_syllabus_analyzed", 0),
                "n_concepts_mapped": data.get("analysis_summary", {}).get("n_concepts_mapped", 0)
            },
            "syllabus_modules": []
        }
        
        sorted_modules = sorted(modules_analysis.values(), key=lambda x: x.get("module_id", 0))
        
        for mod in sorted_modules:
            module_entry = {
                "id": mod.get("module_id", 0),
                "name": mod.get("module_name", "N/D"),
                "coverage_percentage": mod.get("coverage_percentage", 0),
                "n_contents_covered": mod.get("n_contents_covered", 0),
                "n_contents_total": mod.get("n_contents_total", 0),
                "avg_frequency": mod.get("avg_frequency", 0),
                "status": self._coverage_to_status(mod.get("coverage_percentage", 0)),
                "matched_concepts": [
                    {"name": c.get("name", ""), "frequency": c.get("frequency", 0)}
                    for c in mod.get("matched_concepts", [])
                ],
                "missing_contents": mod.get("missing_contents", []),
                "class_data": {}
            }
            
            for classe in classi:
                module_entry["class_data"][classe] = {
                    "coverage": mod.get("coverage_percentage", 0),
                    "status": module_entry["status"]
                }
            
            framework["syllabus_modules"].append(module_entry)
        
        gaps = data.get("gaps_analysis", {})
        framework["gaps_analysis"] = {
            "reality_not_in_ideal": [
                {"name": item.get("name", ""), "frequency": item.get("frequency", 0)}
                for item in gaps.get("reality_not_in_ideal", {}).get("items", [])
            ],
            "ideal_not_in_reality": [
                {"content": item.get("content", ""), "module": item.get("module", "")}
                for item in gaps.get("ideal_not_in_reality", {}).get("items", [])
            ]
        }
        
        return framework
    
    def _coverage_to_status(self, coverage: float) -> str:
        """Converte copertura in status testuale"""
        if coverage >= 80:
            return "eccellente"
        elif coverage >= 60:
            return "buono"
        elif coverage >= 40:
            return "sufficiente"
        elif coverage >= 20:
            return "basso"
        else:
            return "minimo"


# =============================================================================
# MULTICLASS REPORT GENERATOR v2.0
# Report basato su Framework Ideale con analisi per modulo
# =============================================================================

class MulticlassReportGenerator:
    """Genera report HTML per analisi multiclasse su framework ideale"""
    
    def __init__(
        self, 
        reference_framework: Optional[Dict] = None,
        core_threshold: float = 60.0,
        gap_threshold: float = 40.0
    ):
        self.reference_framework = reference_framework
        self.core_threshold = core_threshold
        self.gap_threshold = gap_threshold
    
    def _get_css_styles(self) -> str:
        """CSS per report multiclasse"""
        return """
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px 40px; 
                background: #f5f7fa; 
                color: #333;
                line-height: 1.6;
            }
            .container { 
                max-width: 1400px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px 40px; 
                border-radius: 12px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.07); 
            }
            h1 { 
                color: #1a237e; 
                border-bottom: 3px solid #3949ab; 
                padding-bottom: 15px; 
                margin-bottom: 10px;
                font-size: 1.8em;
            }
            h2 { 
                color: #283593; 
                margin-top: 35px; 
                margin-bottom: 15px;
                font-size: 1.3em;
                border-left: 4px solid #3949ab;
                padding-left: 15px;
            }
            h3 {
                color: #3949ab;
                margin-top: 20px;
                font-size: 1.1em;
            }
            .subtitle {
                color: #666;
                font-size: 1.05em;
                margin-bottom: 25px;
            }
            
            /* Summary Cards */
            .summary-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); 
                gap: 15px; 
                margin: 20px 0; 
            }
            .stat-card { 
                background: linear-gradient(135deg, #e8eaf6, #c5cae9); 
                padding: 18px; 
                border-radius: 10px; 
                text-align: center;
            }
            .stat-value { 
                font-size: 2em; 
                font-weight: bold; 
                color: #1a237e; 
            }
            .stat-label { 
                color: #5c6bc0; 
                margin-top: 5px; 
                font-size: 0.85em;
            }
            .stat-card.success { background: linear-gradient(135deg, #e8f5e9, #c8e6c9); }
            .stat-card.success .stat-value { color: #2e7d32; }
            .stat-card.warning { background: linear-gradient(135deg, #fff3e0, #ffe0b2); }
            .stat-card.warning .stat-value { color: #e65100; }
            .stat-card.danger { background: linear-gradient(135deg, #ffebee, #ffcdd2); }
            .stat-card.danger .stat-value { color: #c62828; }
            .stat-card.info { background: linear-gradient(135deg, #e3f2fd, #bbdefb); }
            .stat-card.info .stat-value { color: #1565c0; }
            
            /* Module Table */
            .module-table { 
                width: 100%; 
                border-collapse: collapse; 
                margin: 20px 0; 
                font-size: 0.9em;
            }
            .module-table th { 
                background: #3949ab; 
                color: white; 
                padding: 12px 8px; 
                text-align: center;
                font-weight: 600;
                position: sticky;
                top: 0;
            }
            .module-table th:first-child {
                text-align: left;
                min-width: 200px;
            }
            .module-table td { 
                padding: 10px 8px; 
                border-bottom: 1px solid #e0e0e0;
                text-align: center;
            }
            .module-table td:first-child {
                text-align: left;
                font-weight: 500;
            }
            .module-table tr:hover { 
                background: #f5f5f5; 
            }
            .module-table tr.core-row {
                background: #e8f5e9;
            }
            .module-table tr.gap-row {
                background: #fff3e0;
            }
            
            /* Coverage cells */
            .cov-cell {
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 4px;
            }
            .cov-high { background: #c8e6c9; color: #2e7d32; }
            .cov-medium { background: #fff3e0; color: #e65100; }
            .cov-low { background: #ffcdd2; color: #c62828; }
            
            /* Tags */
            .tag {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 0.75em;
                font-weight: 600;
                margin: 2px;
            }
            .tag-core { background: #c8e6c9; color: #2e7d32; }
            .tag-distinctive { background: #fff3e0; color: #e65100; }
            .tag-gap { background: #ffcdd2; color: #c62828; }
            
            /* Section boxes */
            .section-box {
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }
            .section-core {
                background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
                border: 2px solid #4caf50;
            }
            .section-distinctive {
                background: linear-gradient(135deg, #fff3e0, #fff8e1);
                border: 2px solid #ff9800;
            }
            .section-gap {
                background: linear-gradient(135deg, #ffebee, #fce4ec);
                border: 2px solid #f44336;
            }
            
            /* Module cards */
            .module-card {
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .module-card h4 {
                margin: 0 0 10px 0;
                color: #1a237e;
            }
            .module-stats {
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
                margin: 10px 0;
            }
            .module-stat {
                background: #f5f5f5;
                padding: 5px 12px;
                border-radius: 15px;
                font-size: 0.85em;
            }
            
            /* Class coverage bar */
            .class-cov-row {
                display: flex;
                align-items: center;
                margin: 5px 0;
            }
            .class-name {
                width: 180px;
                font-size: 0.85em;
            }
            .cov-bar-container {
                flex: 1;
                height: 20px;
                background: #e0e0e0;
                border-radius: 10px;
                overflow: hidden;
                margin: 0 10px;
            }
            .cov-bar {
                height: 100%;
                border-radius: 10px;
                transition: width 0.3s;
            }
            .cov-bar.high { background: linear-gradient(90deg, #66bb6a, #43a047); }
            .cov-bar.medium { background: linear-gradient(90deg, #ffb74d, #ff9800); }
            .cov-bar.low { background: linear-gradient(90deg, #ef5350, #e53935); }
            .cov-value {
                width: 50px;
                text-align: right;
                font-weight: bold;
                font-size: 0.9em;
            }
            
            /* Concept list */
            .concept-list {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                margin-top: 10px;
            }
            .concept-tag {
                background: #e3f2fd;
                color: #1565c0;
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 0.8em;
            }
            
            /* Footer */
            .report-footer {
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                color: #888;
                font-size: 0.85em;
                text-align: center;
            }
            
            /* Responsive */
            @media (max-width: 1000px) {
                body { padding: 10px; }
                .container { padding: 15px; }
                .module-table { font-size: 0.8em; }
                .class-name { width: 120px; }
            }
        </style>
        """
    
    def _get_coverage_class(self, coverage: float) -> str:
        """Ritorna la classe CSS per un valore di copertura"""
        if coverage >= self.core_threshold:
            return "high"
        elif coverage >= self.gap_threshold:
            return "medium"
        else:
            return "low"
    
    def _get_coverage_cell(self, coverage: float) -> str:
        """Genera HTML per una cella di copertura"""
        css_class = self._get_coverage_class(coverage)
        return f'<span class="cov-cell cov-{css_class}">{coverage:.0f}%</span>'
    
    def generate_multiclass_report(
        self,
        result,  # MulticlassResult
        materia: str,
        classes: List[str]
    ) -> str:
        """Genera report HTML completo per analisi multiclasse su framework ideale"""
        
        # Statistiche generali
        n_classes = len(classes)
        n_modules = result.n_modules_total
        n_core = result.n_modules_core
        n_distinctive = result.n_modules_distinctive
        
        # Conta gap totali
        total_gaps = sum(len(gaps) for gaps in result.gap_modules.values())
        
        # Copertura media globale
        avg_coverage_global = sum(result.overall_coverage_by_class.values()) / n_classes if n_classes > 0 else 0
        
        html = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analisi Multiclasse - {materia}</title>
    {self._get_css_styles()}
</head>
<body>
<div class="container">
    <h1>🔬 Analisi Multiclasse: {materia.replace('_', ' ')}</h1>
    <p class="subtitle">
        <strong>Framework di riferimento:</strong> {result.framework_name}<br>
        <strong>Classi analizzate:</strong> {', '.join(classes)}<br>
        <strong>Soglie:</strong> Core ≥{self.core_threshold:.0f}% | Gap &lt;{self.gap_threshold:.0f}%<br>
        <strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </p>
    
    <!-- STATISTICHE GENERALI -->
    <div class="summary-grid">
        <div class="stat-card info">
            <div class="stat-value">{n_classes}</div>
            <div class="stat-label">Classi Analizzate</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{n_modules}</div>
            <div class="stat-label">Moduli Framework</div>
        </div>
        <div class="stat-card success">
            <div class="stat-value">{n_core}</div>
            <div class="stat-label">Moduli CORE</div>
        </div>
        <div class="stat-card warning">
            <div class="stat-value">{n_distinctive}</div>
            <div class="stat-label">Moduli Distintivi</div>
        </div>
        <div class="stat-card danger">
            <div class="stat-value">{total_gaps}</div>
            <div class="stat-label">Gap Totali</div>
        </div>
        <div class="stat-card {'success' if avg_coverage_global >= 60 else 'warning' if avg_coverage_global >= 40 else 'danger'}">
            <div class="stat-value">{avg_coverage_global:.0f}%</div>
            <div class="stat-label">Copertura Media</div>
        </div>
    </div>
    
    <!-- ================================================ -->
    <!-- TABELLA PRINCIPALE: MODULI x CLASSI -->
    <!-- ================================================ -->
    <h2>📊 Matrice Copertura: Moduli × Classi</h2>
    <p>Ogni cella mostra la copertura del modulo del framework ideale per quella classe di laurea.</p>
    
    <table class="module-table">
        <thead>
            <tr>
                <th>Modulo Framework Ideale</th>
"""
        
        # Header classi
        for classe in classes:
            # Abbrevia nome classe se troppo lungo
            short_name = classe.replace("_", " ")
            if len(short_name) > 15:
                short_name = short_name[:12] + "..."
            html += f'                <th title="{classe}">{short_name}</th>\n'
        
        html += """                <th>Media</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
"""
        
        # Righe moduli
        for mod_id in sorted(result.module_analyses.keys()):
            mod = result.module_analyses[mod_id]
            
            # Determina classe riga
            row_class = ""
            if mod.is_core:
                row_class = "core-row"
            elif len(mod.gap_for) > 0:
                row_class = "gap-row"
            
            html += f'            <tr class="{row_class}">\n'
            html += f'                <td><strong>{mod.module_id}.</strong> {mod.module_name}</td>\n'
            
            # Copertura per classe
            for classe in classes:
                cov = mod.coverage_by_class.get(classe, 0)
                html += f'                <td>{self._get_coverage_cell(cov)}</td>\n'
            
            # Media
            html += f'                <td><strong>{mod.avg_coverage:.0f}%</strong></td>\n'
            
            # Status tags
            html += '                <td>'
            if mod.is_core:
                html += '<span class="tag tag-core">CORE</span>'
            if mod.is_distinctive:
                html += '<span class="tag tag-distinctive">DISTINTIVO</span>'
            if mod.gap_for:
                html += f'<span class="tag tag-gap">GAP ({len(mod.gap_for)})</span>'
            html += '</td>\n'
            
            html += '            </tr>\n'
        
        html += """        </tbody>
    </table>
    
    <!-- ================================================ -->
    <!-- MODULI CORE -->
    <!-- ================================================ -->
    <div class="section-box section-core">
        <h2>✅ MODULI CORE ({n_core} moduli)</h2>
        <p>Moduli coperti bene (≥{threshold}%) in <strong>TUTTE</strong> le classi. 
        Questi rappresentano il nucleo comune imprescindibile per qualsiasi manuale di {materia_display}.</p>
""".format(
            n_core=n_core,
            threshold=int(self.core_threshold),
            materia_display=materia.replace('_', ' ')
        )
        
        if result.core_modules:
            for mod in sorted(result.core_modules, key=lambda x: x.avg_coverage, reverse=True):
                html += f"""
        <div class="module-card">
            <h4>📗 {mod.module_id}. {mod.module_name}</h4>
            <div class="module-stats">
                <span class="module-stat">Media: <strong>{mod.avg_coverage:.0f}%</strong></span>
                <span class="module-stat">Min: {mod.min_coverage:.0f}%</span>
                <span class="module-stat">Max: {mod.max_coverage:.0f}%</span>
            </div>
"""
                # Barre copertura per classe
                for classe in classes:
                    cov = mod.coverage_by_class.get(classe, 0)
                    bar_class = self._get_coverage_class(cov)
                    html += f"""
            <div class="class-cov-row">
                <span class="class-name">{classe.replace('_', ' ')[:25]}</span>
                <div class="cov-bar-container">
                    <div class="cov-bar {bar_class}" style="width: {min(cov, 100)}%;"></div>
                </div>
                <span class="cov-value">{cov:.0f}%</span>
            </div>
"""
                html += '        </div>\n'
        else:
            html += """
        <p><em>Nessun modulo raggiunge la soglia core in tutte le classi. 
        Considera di abbassare la soglia o analizzare classi più omogenee.</em></p>
"""
        
        html += """    </div>
    
    <!-- ================================================ -->
    <!-- MODULI DISTINTIVI -->
    <!-- ================================================ -->
    <div class="section-box section-distinctive">
        <h2>⭐ MODULI DISTINTIVI ({n_distinctive} moduli)</h2>
        <p>Moduli con copertura significativamente più alta in alcune classi rispetto ad altre. 
        Utili per personalizzare la promozione per classe specifica.</p>
""".format(n_distinctive=n_distinctive)
        
        if result.distinctive_modules:
            for mod in sorted(result.distinctive_modules, key=lambda x: x.coverage_variance, reverse=True):
                html += f"""
        <div class="module-card">
            <h4>📙 {mod.module_id}. {mod.module_name}</h4>
            <div class="module-stats">
                <span class="module-stat">Media: {mod.avg_coverage:.0f}%</span>
                <span class="module-stat">Range: {mod.min_coverage:.0f}% - {mod.max_coverage:.0f}%</span>
                <span class="module-stat">Distintivo per: <strong>{', '.join(mod.distinctive_for)}</strong></span>
            </div>
"""
                for classe in classes:
                    cov = mod.coverage_by_class.get(classe, 0)
                    bar_class = self._get_coverage_class(cov)
                    is_distinctive = classe in mod.distinctive_for
                    label = " ⭐" if is_distinctive else ""
                    html += f"""
            <div class="class-cov-row">
                <span class="class-name">{classe.replace('_', ' ')[:25]}{label}</span>
                <div class="cov-bar-container">
                    <div class="cov-bar {bar_class}" style="width: {min(cov, 100)}%;"></div>
                </div>
                <span class="cov-value">{cov:.0f}%</span>
            </div>
"""
                html += '        </div>\n'
        else:
            html += """
        <p><em>Nessun modulo mostra differenze significative tra classi.</em></p>
"""
        
        html += """    </div>
    
    <!-- ================================================ -->
    <!-- GAP PER CLASSE -->
    <!-- ================================================ -->
    <div class="section-box section-gap">
        <h2>⚠️ GAP PER CLASSE</h2>
        <p>Moduli con copertura insufficiente (&lt;{threshold}%) per ciascuna classe. 
        Questi rappresentano aree di miglioramento o differenziazione curriculare.</p>
""".format(threshold=int(self.gap_threshold))
        
        if result.gap_modules:
            for classe in classes:
                gaps = result.gap_modules.get(classe, [])
                if gaps:
                    html += f"""
        <div class="module-card">
            <h4>🎓 {classe.replace('_', ' ')} — {len(gaps)} gap</h4>
            <div class="concept-list">
"""
                    for mod in sorted(gaps, key=lambda x: x.coverage_by_class.get(classe, 0)):
                        cov = mod.coverage_by_class.get(classe, 0)
                        html += f'                <span class="concept-tag" style="background:#ffcdd2;color:#c62828;">{mod.module_name} ({cov:.0f}%)</span>\n'
                    
                    html += """            </div>
        </div>
"""
            
            # Classi senza gap
            classes_no_gap = [c for c in classes if c not in result.gap_modules or not result.gap_modules[c]]
            if classes_no_gap:
                html += f"""
        <p>✅ <strong>Classi senza gap significativi:</strong> {', '.join(classes_no_gap)}</p>
"""
        else:
            html += """
        <p>✅ <strong>Nessun gap significativo rilevato in nessuna classe!</strong></p>
"""
        
        html += """    </div>
    
    <!-- ================================================ -->
    <!-- COPERTURA COMPLESSIVA PER CLASSE -->
    <!-- ================================================ -->
    <h2>📈 Copertura Complessiva Framework per Classe</h2>
    <p>Quanto ogni classe copre complessivamente il framework ideale.</p>
    
    <div class="module-card">
"""
        
        # Ordina classi per copertura decrescente
        sorted_classes = sorted(classes, key=lambda c: result.overall_coverage_by_class.get(c, 0), reverse=True)
        
        for classe in sorted_classes:
            cov = result.overall_coverage_by_class.get(classe, 0)
            bar_class = self._get_coverage_class(cov)
            class_result = result.class_results.get(classe)
            n_syl = class_result.n_syllabus if class_result else 0
            n_concepts = class_result.total_concepts_extracted if class_result else 0
            
            html += f"""
        <div class="class-cov-row" style="margin: 12px 0;">
            <span class="class-name" style="width: 220px;">
                <strong>{classe.replace('_', ' ')}</strong><br>
                <small style="color: #666;">{n_syl} syllabus, {n_concepts} concetti</small>
            </span>
            <div class="cov-bar-container" style="height: 25px;">
                <div class="cov-bar {bar_class}" style="width: {min(cov, 100)}%;"></div>
            </div>
            <span class="cov-value" style="width: 60px; font-size: 1.1em;">{cov:.0f}%</span>
        </div>
"""
        
        html += """    </div>
    
    <!-- ================================================ -->
    <!-- IMPLICAZIONI STRATEGICHE -->
    <!-- ================================================ -->
    <h2>💡 Implicazioni Strategiche</h2>
    
    <div class="module-card">
        <h4>Per il Catalogo Zanichelli</h4>
        <ul>
"""
        
        if result.core_modules:
            core_names = [m.module_name for m in result.core_modules[:5]]
            html += f"""
            <li><strong>Moduli CORE ({n_core}):</strong> Questi argomenti sono trattati in tutte le classi e DEVONO essere eccellenti nel manuale: {', '.join(core_names)}{'...' if len(result.core_modules) > 5 else ''}</li>
"""
        
        if result.distinctive_modules:
            html += f"""
            <li><strong>Moduli DISTINTIVI ({n_distinctive}):</strong> Personalizza la promozione enfatizzando questi moduli per le classi specifiche dove sono più rilevanti.</li>
"""
        
        if total_gaps > 0:
            html += f"""
            <li><strong>GAP ({total_gaps} totali):</strong> Alcuni moduli sono poco coperti in certe classi. Valuta se il manuale può colmare questi gap o se sono differenze curriculari intenzionali.</li>
"""
        
        html += """
        </ul>
        
        <h4>Per la Promozione</h4>
        <ul>
"""
        
        # Suggerimenti per classe
        for classe in sorted_classes[:5]:  # Top 5 classi
            cov = result.overall_coverage_by_class.get(classe, 0)
            gaps = result.gap_modules.get(classe, [])
            distinctive_here = [m for m in result.distinctive_modules if classe in m.distinctive_for]
            
            html += f'            <li><strong>{classe}:</strong> '
            
            if cov >= 60:
                html += f'Buona copertura ({cov:.0f}%). '
            else:
                html += f'Copertura da migliorare ({cov:.0f}%). '
            
            if distinctive_here:
                html += f'Enfatizza: {", ".join([m.module_name for m in distinctive_here[:2]])}. '
            
            if gaps:
                html += f'Gap in: {", ".join([m.module_name for m in gaps[:2]])}.'
            
            html += '</li>\n'
        
        html += f"""
        </ul>
    </div>
    
    <div class="report-footer">
        Report generato da <strong>CoreX Multiclasse v2.0</strong> — Zanichelli<br>
        Framework di riferimento: {result.framework_name}<br>
        {n_classes} classi analizzate | {n_modules} moduli | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    </div>
</div>
</body>
</html>
"""
        
        return html
    
    def generate_unified_framework(self, result) -> Dict:
        """Genera framework JSON unificato multiclasse"""
        
        modules_data = []
        for mod_id in sorted(result.module_analyses.keys()):
            mod = result.module_analyses[mod_id]
            
            modules_data.append({
                "id": mod.module_id,
                "name": mod.module_name,
                "core_contents": mod.core_contents,
                "coverage_by_class": {k: round(v, 1) for k, v in mod.coverage_by_class.items()},
                "avg_coverage": round(mod.avg_coverage, 1),
                "min_coverage": round(mod.min_coverage, 1),
                "max_coverage": round(mod.max_coverage, 1),
                "is_core": mod.is_core,
                "is_distinctive": mod.is_distinctive,
                "distinctive_for": mod.distinctive_for,
                "gap_for": mod.gap_for,
                "concepts_by_class": {
                    classe: [c.get("name", c) if isinstance(c, dict) else c for c in concepts[:10]]
                    for classe, concepts in mod.concepts_by_class.items()
                }
            })
        
        return {
            "framework": {
                "name": f"{result.materia} - Analisi Multiclasse su Framework Ideale",
                "type": "multiclass_on_ideal_framework",
                "reference_framework": result.framework_name,
                "classes_analyzed": result.classes,
                "generation_date": datetime.now().isoformat(),
                "thresholds": {
                    "core": self.core_threshold,
                    "gap": self.gap_threshold
                }
            },
            "summary": {
                "n_classes": len(result.classes),
                "n_modules_total": result.n_modules_total,
                "n_modules_core": result.n_modules_core,
                "n_modules_distinctive": result.n_modules_distinctive,
                "overall_coverage_by_class": {k: round(v, 1) for k, v in result.overall_coverage_by_class.items()}
            },
            "core_modules": [
                {"id": m.module_id, "name": m.module_name, "avg_coverage": round(m.avg_coverage, 1)}
                for m in result.core_modules
            ],
            "distinctive_modules": [
                {
                    "id": m.module_id, 
                    "name": m.module_name, 
                    "distinctive_for": m.distinctive_for,
                    "coverage_range": f"{m.min_coverage:.0f}%-{m.max_coverage:.0f}%"
                }
                for m in result.distinctive_modules
            ],
            "gap_by_class": {
                classe: [{"id": m.module_id, "name": m.module_name, "coverage": round(m.coverage_by_class.get(classe, 0), 1)} for m in gaps]
                for classe, gaps in result.gap_modules.items()
            },
            "class_details": {
                classe: {
                    "n_syllabus": res.n_syllabus,
                    "n_concepts_extracted": res.total_concepts_extracted,
                    "overall_coverage": round(res.overall_coverage, 1)
                }
                for classe, res in result.class_results.items()
            },
            "modules": modules_data
        }
