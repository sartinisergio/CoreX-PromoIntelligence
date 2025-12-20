"""
webapp.py
Interfaccia web per CoreX con Streamlit
Con memorizzazione API Key e salvataggio file
"""

import streamlit as st
import os
import shutil
from pathlib import Path
from datetime import datetime
import json

# Directory base
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
SYLLABUS_DIR = DATA_DIR / "syllabus"
FRAMEWORKS_DIR = DATA_DIR / "frameworks"
OUTPUTS_DIR = DATA_DIR / "outputs"
SETTINGS_FILE = DATA_DIR / ".settings.json"

# Crea directory se non esistono
for d in [SYLLABUS_DIR, FRAMEWORKS_DIR, OUTPUTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def load_settings():
    """Carica impostazioni salvate."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_settings(settings):
    """Salva impostazioni."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)

def get_saved_projects():
    """Restituisce lista di progetti (cartelle) salvati."""
    projects = []
    if SYLLABUS_DIR.exists():
        for p in SYLLABUS_DIR.iterdir():
            if p.is_dir():
                pdf_count = len(list(p.glob("*.pdf")))
                if pdf_count > 0:
                    projects.append({
                        "name": p.name,
                        "path": p,
                        "pdf_count": pdf_count,
                        "created": datetime.fromtimestamp(p.stat().st_mtime)
                    })
    return sorted(projects, key=lambda x: x["created"], reverse=True)

# Carica impostazioni
settings = load_settings()

# Configura la pagina
st.set_page_config(
    page_title="CoreX - Core Extractor",
    page_icon="🧪",
    layout="wide"
)

# ============================================================
# SIDEBAR - Configurazione
# ============================================================

st.sidebar.title("⚙️ Configurazione")

# Input API Key con valore salvato
st.sidebar.subheader("🔑 OpenAI API Key")

saved_api_key = settings.get("api_key", "")

api_key = st.sidebar.text_input(
    "Inserisci la tua API Key",
    value=saved_api_key,
    type="password",
    help="La chiave viene salvata localmente per le sessioni future"
)

# Checkbox per salvare la chiave
save_key = st.sidebar.checkbox(
    "Ricorda API Key",
    value=bool(saved_api_key),
    help="Salva la chiave per non reinserirla ogni volta"
)

# Salva o rimuovi la chiave
if save_key and api_key:
    if api_key != saved_api_key:
        settings["api_key"] = api_key
        save_settings(settings)
        st.sidebar.success("✓ API Key salvata")
    else:
        st.sidebar.success("✓ API Key configurata")
elif not save_key and saved_api_key:
    settings["api_key"] = ""
    save_settings(settings)
    st.sidebar.info("API Key rimossa dalla memoria")

if api_key:
    os.environ["OPENAI_API_KEY"] = api_key
else:
    st.sidebar.warning("⚠️ Senza API Key il labeling sarà meno accurato")

# Opzioni
st.sidebar.subheader("🎛️ Opzioni")
use_llm = st.sidebar.checkbox("Usa LLM per labeling", value=bool(api_key))
n_clusters = st.sidebar.slider("Numero moduli (0 = auto)", 0, 25, 0)
if n_clusters == 0:
    n_clusters = None

# Progetti salvati
st.sidebar.divider()
st.sidebar.subheader("📁 Progetti Salvati")
saved_projects = get_saved_projects()

if saved_projects:
    for proj in saved_projects[:5]:
        st.sidebar.caption(f"• {proj['name']} ({proj['pdf_count']} PDF)")
else:
    st.sidebar.caption("Nessun progetto salvato")

# Info versione
st.sidebar.divider()
st.sidebar.caption("CoreX v1.1")
st.sidebar.caption("Generatore Framework Disciplinari")

# ============================================================
# MAIN PAGE
# ============================================================

st.title("🧪 CoreX - Core Extractor")
st.markdown("""
**Estrazione automatica di framework disciplinari da programmi d'esame universitari**

Carica i PDF dei syllabus e ottieni:
- 📊 Framework strutturato con moduli e concetti
- 📈 Matrice di copertura per ogni syllabus
- 🔄 Confronto con framework esistente
""")

st.divider()

# ============================================================
# SELEZIONE SORGENTE DATI
# ============================================================

st.subheader("📂 Sorgente Dati")

source_option = st.radio(
    "Scegli la sorgente dei syllabus:",
    ["📤 Carica nuovi file", "📁 Usa progetto salvato"],
    horizontal=True
)

uploaded_pdfs = []
project_name = ""
pdf_dir = None

if source_option == "📤 Carica nuovi file":
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_pdfs = st.file_uploader(
            "Seleziona i file PDF dei programmi d'esame",
            type=["pdf"],
            accept_multiple_files=True,
            help="Puoi caricare più file contemporaneamente"
        )
    
    with col2:
        project_name = st.text_input(
            "Nome progetto (per salvare i file)",
            value=f"Progetto_{datetime.now().strftime('%Y%m%d')}",
            help="I file verranno salvati in questa cartella"
        )
        
        # Pulisci nome progetto
        project_name = "".join(c for c in project_name if c.isalnum() or c in "_ -").strip()
    
    if uploaded_pdfs:
        st.success(f"✓ {len(uploaded_pdfs)} file pronti per l'elaborazione")

else:  # Usa progetto salvato
    if saved_projects:
        project_options = {f"{p['name']} ({p['pdf_count']} PDF)": p for p in saved_projects}
        selected = st.selectbox("Seleziona un progetto:", list(project_options.keys()))
        
        if selected:
            selected_project = project_options[selected]
            pdf_dir = selected_project["path"]
            project_name = selected_project["name"]
            st.success(f"✓ Progetto '{project_name}' selezionato con {selected_project['pdf_count']} PDF")
    else:
        st.warning("Nessun progetto salvato. Carica prima dei file.")

st.divider()

# ============================================================
# FRAMEWORK ESISTENTE
# ============================================================

col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Framework Esistente (opzionale)")
    
    # Opzione: carica nuovo o usa salvato
    fw_source = st.radio(
        "Sorgente framework:",
        ["📤 Carica file", "📁 Usa salvato"],
        horizontal=True,
        key="fw_source"
    )
    
    uploaded_framework = None
    existing_fw_path = None
    
    if fw_source == "📤 Carica file":
        uploaded_framework = st.file_uploader(
            "Carica il tuo framework JSON",
            type=["json"],
            help="Il framework verrà confrontato con quello generato"
        )
        if uploaded_framework:
            st.success(f"✓ {uploaded_framework.name}")
    else:
        saved_frameworks = list(FRAMEWORKS_DIR.glob("*.json"))
        if saved_frameworks:
            fw_options = {f.name: f for f in saved_frameworks}
            selected_fw = st.selectbox("Seleziona framework:", list(fw_options.keys()))
            if selected_fw:
                existing_fw_path = fw_options[selected_fw]
                st.success(f"✓ {selected_fw}")
        else:
            st.info("Nessun framework salvato in data/frameworks/")

with col2:
    st.subheader("⚙️ Configurazione Analisi")
    
    framework_name = st.text_input(
        "Nome del Framework da generare",
        value=settings.get("last_framework_name", "Framework Empirico Chimica Organica L-13")
    )
    
    # Salva ultimo nome usato
    if framework_name != settings.get("last_framework_name", ""):
        settings["last_framework_name"] = framework_name
        save_settings(settings)

st.divider()

# ============================================================
# ELABORAZIONE
# ============================================================

can_process = bool(uploaded_pdfs) or (pdf_dir and pdf_dir.exists())

if st.button("🚀 Avvia Elaborazione", type="primary", disabled=not can_process):
    
    # Determina la directory dei PDF
    if uploaded_pdfs:
        # Salva i nuovi file
        pdf_dir = SYLLABUS_DIR / project_name
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        with st.spinner(f"Salvataggio {len(uploaded_pdfs)} file in '{project_name}'..."):
            for pdf_file in uploaded_pdfs:
                pdf_path = pdf_dir / pdf_file.name
                with open(pdf_path, "wb") as f:
                    f.write(pdf_file.read())
        
        st.success(f"✓ File salvati in: data/syllabus/{project_name}/")
    
    # Salva framework esistente se caricato
    if uploaded_framework:
        fw_save_path = FRAMEWORKS_DIR / uploaded_framework.name
        with open(fw_save_path, "wb") as f:
            f.write(uploaded_framework.read())
        existing_fw_path = fw_save_path
        st.success(f"✓ Framework salvato in: data/frameworks/{uploaded_framework.name}")
    
    # Esegui pipeline
    with st.spinner("Elaborazione in corso..."):
        try:
            from app.main_pipeline import FrameworkGenerationPipeline
            from app.coverage_analyzer import CoverageAnalyzer
            
            # Directory output per questo progetto
            output_dir = OUTPUTS_DIR / project_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            pipeline = FrameworkGenerationPipeline(
                pdf_dir=pdf_dir,
                existing_framework_path=existing_fw_path,
                output_dir=output_dir,
                use_llm=use_llm and bool(api_key)
            )
            
            # Progress bar
            progress = st.progress(0, text="Inizializzazione...")
            
            # Estrazione PDF
            progress.progress(10, text="[1/5] Estrazione testo da PDF...")
            extracted = pipeline.pdf_extractor.extract_batch(pdf_dir)
            for es in extracted:
                if es.success:
                    pipeline.syllabus_texts[es.id] = es.text
                    pipeline.syllabus_metadata[es.id] = {
                        "university": es.university,
                        "professor": es.professor
                    }
            
            # Estrazione concetti
            progress.progress(30, text="[2/5] Estrazione concetti...")
            pipeline.concept_collection = pipeline.concept_extractor.process_multiple_syllabus(
                pipeline.syllabus_texts, framework_name
            )
            
            # Clustering
            progress.progress(50, text="[3/5] Clustering e generazione framework...")
            pipeline.framework = pipeline.clusterer.generate_framework(
                pipeline.concept_collection, 
                framework_name, 
                n_clusters, 
                use_llm and bool(api_key)
            )
            
            # Copertura
            progress.progress(70, text="[4/5] Analisi copertura...")
            analyzer = CoverageAnalyzer(pipeline.framework)
            pipeline.coverages, pipeline.coverage_matrix = analyzer.analyze_collection(
                pipeline.concept_collection, pipeline.syllabus_metadata
            )
            
            # Confronto
            progress.progress(85, text="[5/5] Confronto framework...")
            if pipeline.comparator:
                pipeline.comparison = pipeline.comparator.compare(pipeline.framework)
            
            progress.progress(100, text="Completato!")
            
            # Salva risultati automaticamente
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Framework JSON
            fw_json = {
                "metadata": {
                    "name": pipeline.framework.name,
                    "project": project_name,
                    "n_syllabus": pipeline.framework.n_syllabus_analyzed,
                    "generation_date": datetime.now().isoformat()
                },
                "statistics": {
                    "total_concepts": pipeline.framework.total_concepts,
                    "n_modules": pipeline.framework.n_modules,
                    "n_core": pipeline.concept_collection.n_core,
                    "n_comune": pipeline.concept_collection.n_comune,
                    "n_specifico": pipeline.concept_collection.n_specifico
                },
                "modules": [
                    {
                        "order": m.order,
                        "name": m.name,
                        "n_concepts": m.n_concepts,
                        "weight": round(m.suggested_weight, 4),
                        "classification": m.classification.value,
                        "avg_frequency": round(m.avg_frequency, 1),
                        "concepts": [
                            {
                                "name": c.canonical_name, 
                                "frequency": round(c.frequency_percentage, 1),
                                "classification": c.classification.value,
                                "variants": c.variants[:5]
                            }
                            for c in sorted(m.concepts, key=lambda x: -x.frequency_percentage)
                        ]
                    }
                    for m in sorted(pipeline.framework.modules, key=lambda x: x.order)
                ]
            }
            
            fw_file = output_dir / f"framework_{timestamp}.json"
            with open(fw_file, "w", encoding="utf-8") as f:
                json.dump(fw_json, f, ensure_ascii=False, indent=2)
            
            # Copertura JSON
            cov_json = {
                "metadata": {
                    "project": project_name,
                    "framework": framework_name,
                    "generation_date": datetime.now().isoformat()
                },
                "matrix": pipeline.coverage_matrix.to_dict(),
                "syllabus": [
                    {
                        "id": c.syllabus_id, 
                        "university": c.university,
                        "professor": c.professor,
                        "coverage": c.overall_coverage,
                        "concepts_found": c.n_concepts_found,
                        "core_found": c.n_core_found,
                        "core_missing": c.n_core_missing
                    }
                    for c in sorted(pipeline.coverages, key=lambda x: -x.overall_coverage)
                ]
            }
            
            cov_file = output_dir / f"coverage_{timestamp}.json"
            with open(cov_file, "w", encoding="utf-8") as f:
                json.dump(cov_json, f, ensure_ascii=False, indent=2)
            
            # Confronto JSON (se disponibile)
            comp_file = None
            if pipeline.comparison:
                comp_file = output_dir / f"comparison_{timestamp}.json"
                with open(comp_file, "w", encoding="utf-8") as f:
                    json.dump(pipeline.comparison.to_dict(), f, ensure_ascii=False, indent=2)
            
            # ============================================================
            # RISULTATI
            # ============================================================
            
            st.success("✅ Elaborazione completata!")
            st.info(f"📁 Risultati salvati in: data/outputs/{project_name}/")
            
            st.divider()
            st.header("📊 Risultati")
            
            # Statistiche generali
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Syllabus Analizzati", len(pipeline.syllabus_texts))
            col2.metric("Concetti Estratti", pipeline.concept_collection.total_unique_concepts)
            col3.metric("Moduli Generati", pipeline.framework.n_modules)
            col4.metric("Concetti CORE", pipeline.concept_collection.n_core)
            
            # Tabs per i diversi output
            tab1, tab2, tab3, tab4 = st.tabs(["🏗️ Framework", "📈 Copertura", "🔄 Confronto", "📥 Download"])
            
            with tab1:
                st.subheader("Framework Generato")
                for m in sorted(pipeline.framework.modules, key=lambda x: x.order):
                    with st.expander(f"**{m.order}. {m.name}** ({m.n_concepts} concetti, peso: {m.suggested_weight:.1%})"):
                        st.write(f"**Classificazione:** {m.classification.value}")
                        st.write(f"**Frequenza media:** {m.avg_frequency:.1f}%")
                        st.write("**Top concetti:**")
                        for c in sorted(m.concepts, key=lambda x: -x.frequency_percentage)[:10]:
                            class_badge = "🔴" if c.classification.value == "CORE" else "🟡" if c.classification.value == "COMUNE" else "⚪"
                            st.write(f"{class_badge} {c.canonical_name} ({c.frequency_percentage:.0f}%)")
            
            with tab2:
                st.subheader("Copertura per Syllabus")
                import pandas as pd
                
                cov_data = []
                for cov in sorted(pipeline.coverages, key=lambda x: -x.overall_coverage):
                    cov_data.append({
                        "Università": cov.university,
                        "Docente": cov.professor,
                        "Copertura": f"{cov.overall_coverage:.1f}%",
                        "Concetti trovati": cov.n_concepts_found,
                        "CORE trovati": cov.n_core_found,
                        "CORE mancanti": cov.n_core_missing
                    })
                
                df = pd.DataFrame(cov_data)
                st.dataframe(df, use_container_width=True)
            
            with tab3:
                if pipeline.comparison:
                    st.subheader("Confronto con Framework Esistente")
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Similarità Globale", f"{pipeline.comparison.overall_similarity:.1%}")
                    col2.metric("Moduli Matchati", pipeline.comparison.n_matched)
                    
                    st.write("**Raccomandazioni:**")
                    for rec in pipeline.comparison.recommendations:
                        st.info(rec)
                    
                    st.write("**Dettaglio Match:**")
                    for mc in pipeline.comparison.module_comparisons:
                        status_icon = "✅" if mc.status == "matched" else "🟡" if mc.status == "partial" else "🆕"
                        matched_name = mc.matched_name if mc.matched_name else "Nuovo"
                        st.write(f"{status_icon} **{mc.generated_name}** → {matched_name} ({mc.similarity:.0%})")
                else:
                    st.info("Nessun framework esistente caricato per il confronto")
            
            with tab4:
                st.subheader("Scarica Risultati")
                st.write(f"📁 I file sono già salvati in: `data/outputs/{project_name}/`")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button(
                        "📥 Framework (JSON)",
                        data=json.dumps(fw_json, ensure_ascii=False, indent=2),
                        file_name=f"framework_{project_name}_{timestamp}.json",
                        mime="application/json"
                    )
                
                with col2:
                    st.download_button(
                        "📥 Copertura (JSON)",
                        data=json.dumps(cov_json, ensure_ascii=False, indent=2),
                        file_name=f"coverage_{project_name}_{timestamp}.json",
                        mime="application/json"
                    )
                
                with col3:
                    if pipeline.comparison:
                        st.download_button(
                            "📥 Confronto (JSON)",
                            data=json.dumps(pipeline.comparison.to_dict(), ensure_ascii=False, indent=2),
                            file_name=f"comparison_{project_name}_{timestamp}.json",
                            mime="application/json"
                        )
        
        except Exception as e:
            st.error(f"Errore durante l'elaborazione: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# ============================================================
# FOOTER
# ============================================================

st.divider()
st.markdown("""
<div style="text-align: center; color: gray; font-size: 0.8em;">
    CoreX v1.1 - Generatore Framework Disciplinari<br>
    Sviluppato per Zanichelli
</div>
""", unsafe_allow_html=True)
