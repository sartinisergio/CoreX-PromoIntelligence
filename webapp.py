"""
CoreX - Core Extractor v1.7
Struttura semplificata - Una sola analisi attiva + Confronto Classi + Analisi Manuali
"""

import streamlit as st
import os
import json
import shutil
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="CoreX - Core Extractor",
    page_icon="🧪",
    layout="wide"
)

# === FUNZIONI UTILITÀ ===

def get_programmi_dir():
    prog_dir = Path("Programmi")
    prog_dir.mkdir(exist_ok=True)
    return prog_dir

def get_frameworks_dir():
    fw_dir = Path("frameworks")
    fw_dir.mkdir(exist_ok=True)
    return fw_dir

def get_data_dir():
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir

def get_analisi_dir():
    """Directory per l'analisi corrente"""
    analisi_dir = get_data_dir() / "analisi_corrente"
    analisi_dir.mkdir(exist_ok=True)
    return analisi_dir

def get_archivio_dir():
    """Directory per le analisi archiviate"""
    archivio_dir = Path("archivio")
    archivio_dir.mkdir(exist_ok=True)
    return archivio_dir

def get_confronti_dir():
    """Directory per i confronti tra classi"""
    confronti_dir = get_data_dir() / "confronti"
    confronti_dir.mkdir(exist_ok=True)
    return confronti_dir

def get_manuali_dir():
    """Directory per i manuali"""
    manuali_dir = get_data_dir() / "manuali"
    manuali_dir.mkdir(exist_ok=True)
    return manuali_dir

def get_materie():
    prog_dir = get_programmi_dir()
    materie = []
    for d in sorted(prog_dir.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            materie.append(d.name)
    return materie

def get_classi_laurea(materia: str):
    materia_dir = get_programmi_dir() / materia
    classi = []
    if materia_dir.exists():
        for d in sorted(materia_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                classi.append(d.name)
    return classi

def get_pdf_in_folder(materia: str, classe: str):
    folder = get_programmi_dir() / materia / classe
    if folder.exists():
        return sorted(folder.glob("*.pdf"))
    return []

def get_all_pdf_for_materia(materia: str):
    materia_dir = get_programmi_dir() / materia
    pdfs = {}
    if materia_dir.exists():
        for classe_dir in materia_dir.iterdir():
            if classe_dir.is_dir():
                classe_pdfs = list(classe_dir.glob("*.pdf"))
                if classe_pdfs:
                    pdfs[classe_dir.name] = classe_pdfs
    return pdfs

def create_materia(nome: str):
    safe_name = nome.replace(" ", "_")
    materia_dir = get_programmi_dir() / safe_name
    materia_dir.mkdir(exist_ok=True)
    return materia_dir

def create_classe(materia: str, classe: str):
    classe_dir = get_programmi_dir() / materia / classe
    classe_dir.mkdir(parents=True, exist_ok=True)
    return classe_dir

def load_settings():
    settings_file = get_data_dir() / ".settings.json"
    if settings_file.exists():
        with open(settings_file, "r") as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(get_data_dir() / ".settings.json", "w") as f:
        json.dump(settings, f)

def get_available_frameworks():
    fw_dir = get_frameworks_dir()
    frameworks = []
    for f in sorted(fw_dir.glob("*.json")):
        frameworks.append({
            "filename": f.name,
            "name": f.stem.replace("_", " ").title(),
            "path": f
        })
    return frameworks

def find_matching_framework(materia: str):
    from app.framework_adapter import FrameworkAdapter
    adapter = FrameworkAdapter()
    return adapter.find_framework(materia)

def get_current_analysis():
    """Carica i metadati dell'analisi corrente"""
    meta_file = get_analisi_dir() / "analisi.json"
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def archive_current_analysis():
    """Archivia l'analisi corrente"""
    analisi_dir = get_analisi_dir()
    meta = get_current_analysis()
    
    if meta:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome = meta.get("name", "analisi")
        archive_name = f"{nome}_{timestamp}"
        archive_path = get_archivio_dir() / archive_name
        
        shutil.copytree(analisi_dir, archive_path)
        
        for f in analisi_dir.iterdir():
            if f.is_file():
                f.unlink()
        
        return archive_path
    return None

def clear_current_analysis():
    """Elimina l'analisi corrente senza archiviare"""
    analisi_dir = get_analisi_dir()
    for f in analisi_dir.iterdir():
        if f.is_file():
            f.unlink()

def get_archived_analyses():
    """Lista delle analisi archiviate"""
    archivio = get_archivio_dir()
    analyses = []
    
    for d in sorted(archivio.iterdir(), reverse=True):
        if d.is_dir():
            meta_file = d / "analisi.json"
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        meta["path"] = d
                        meta["dir_name"] = d.name
                        analyses.append(meta)
                except:
                    pass
    
    return analyses

def delete_archived_analysis(path: Path):
    """Elimina un'analisi archiviata"""
    if path.exists():
        shutil.rmtree(path)
        return True
    return False

def get_saved_comparisons():
    """Lista dei confronti salvati"""
    confronti_dir = get_confronti_dir()
    comparisons = []
    
    for f in sorted(confronti_dir.glob("confronto_*.html"), reverse=True):
        timestamp = f.stem.replace("confronto_", "")
        json_file = confronti_dir / f"framework_unificato_{timestamp}.json"
        
        comparisons.append({
            "timestamp": timestamp,
            "html_path": f,
            "json_path": json_file if json_file.exists() else None,
            "date": f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[9:11]}:{timestamp[11:13]}"
        })
    
    return comparisons


# === SIDEBAR ===

st.sidebar.title("⚙️ Configurazione")

# API Key
st.sidebar.subheader("🔑 OpenAI API Key")
settings = load_settings()

try:
    saved_api_key = st.secrets.get("OPENAI_API_KEY", "") or settings.get("api_key", "")
except:
    saved_api_key = settings.get("api_key", "")

api_key = st.sidebar.text_input(
    "API Key",
    value=saved_api_key,
    type="password"
)

if api_key:
    os.environ["OPENAI_API_KEY"] = api_key
    if api_key != settings.get("api_key"):
        settings["api_key"] = api_key
        save_settings(settings)
    st.sidebar.success("✓ API Key configurata")

# Opzioni analisi
st.sidebar.subheader("🎛️ Opzioni")
use_llm = st.sidebar.checkbox("Usa LLM per labeling", value=bool(api_key))
n_clusters = st.sidebar.slider("Numero moduli (0=auto)", 0, 25, 0)
if n_clusters == 0:
    n_clusters = None

# Info framework
frameworks = get_available_frameworks()
st.sidebar.caption(f"📚 {len(frameworks)} framework disponibili")

# === MAIN ===

# Logo piccolo a sinistra + tagline centrato
col_logo, col_tagline = st.columns([1, 4])
with col_logo:
    st.image("logo.png", width=80)
with col_tagline:
    st.markdown(
        "<h1 style='margin-top: 10px;'>CoreX</h1>"
        "<p style='font-size: 1.2em; color: #6c757d; margin-top: -15px;'>"
        "Analizza. Confronta. Orienta.</p>",
        unsafe_allow_html=True
    )

st.markdown("---")

# === RIEPILOGO STATO ===
col1, col2, col3 = st.columns(3)

# Analisi corrente
current = get_current_analysis()
with col1:
    st.markdown("##### 📊 Analisi Corrente")
    if current:
        st.success(f"**{current.get('name', 'N/D')}**")
        st.caption(f"{current.get('n_syllabus', 0)} syllabus • {current.get('coverage', 0):.0f}% copertura")
    else:
        st.info("Nessuna analisi attiva")

# Archivio
archived = get_archived_analyses()
with col2:
    st.markdown("##### 📦 Archivio")
    if archived:
        st.write(f"**{len(archived)} analisi** archiviate")
        for a in archived[:3]:
            st.caption(f"• {a.get('name', 'N/D')} ({a.get('coverage', 0):.0f}%)")
        if len(archived) > 3:
            st.caption(f"... e altre {len(archived) - 3}")
    else:
        st.info("Archivio vuoto")

# Programmi disponibili
with col3:
    st.markdown("##### 📚 Programmi")
    materie = get_materie()
    total_pdfs = 0
    for m in materie:
        for c in get_classi_laurea(m):
            total_pdfs += len(get_pdf_in_folder(m, c))
    st.write(f"**{len(materie)} materie** • **{total_pdfs} PDF**")
    st.caption(f"{len(frameworks)} framework disponibili")

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📂 Programmi", 
    "🚀 Analisi", 
    "📊 Risultati", 
    "🔄 Confronta Classi",
    "⚙️ Gestione",
    "📖 Analisi Manuali",
    "🎓 Profilo Docente"
])

# === TAB 1: SELEZIONE PROGRAMMI ===
with tab1:
    st.header("📂 Seleziona Programmi")
    
    # Upload rapido
    with st.expander("📤 Carica nuovi PDF", expanded=False):
        materie_disponibili = get_materie()
        
        if not materie_disponibili:
            st.warning("Crea prima una materia nella tab Gestione")
        else:
            col1, col2 = st.columns(2)
            with col1:
                upload_materia = st.selectbox("Materia", materie_disponibili, key="upload_mat")
            with col2:
                upload_classi = get_classi_laurea(upload_materia)
                if upload_classi:
                    upload_classe = st.selectbox("Classe", upload_classi, key="upload_cls")
                else:
                    st.warning("Crea prima una classe")
                    upload_classe = None
            
            if upload_classe:
                uploaded = st.file_uploader(
                    "Seleziona PDF",
                    type=["pdf"],
                    accept_multiple_files=True
                )
                
                if uploaded and st.button("💾 Salva PDF", type="primary"):
                    target = get_programmi_dir() / upload_materia / upload_classe
                    for f in uploaded:
                        with open(target / f.name, "wb") as out:
                            out.write(f.getbuffer())
                    st.success(f"✅ Salvati {len(uploaded)} PDF")
                    st.rerun()
    
    st.markdown("---")
    
    # Selezione materia/classe
    materie = get_materie()
    
    if not materie:
        st.warning("Nessuna materia. Vai alla tab Gestione per crearne una.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            selected_materia = st.selectbox("📚 Materia", materie)
        
        with col2:
            classi = get_classi_laurea(selected_materia) if selected_materia else []
            classe_options = ["Tutte le classi"] + classi
            selected_classe_idx = st.selectbox(
                "🎓 Classe di Laurea",
                range(len(classe_options)),
                format_func=lambda x: classe_options[x]
            )
        
        # Framework match
        if selected_materia:
            fw = find_matching_framework(selected_materia)
            if fw:
                st.success(f"✅ Framework: {fw.stem.replace('_', ' ').title()}")
            else:
                st.info("ℹ️ Nessun framework di riferimento")
        
        st.markdown("---")
        
        # Mostra PDF
        if selected_materia:
            if selected_classe_idx == 0:
                # Tutte le classi
                all_pdfs = get_all_pdf_for_materia(selected_materia)
                total = sum(len(p) for p in all_pdfs.values())
                
                st.subheader(f"📄 {total} PDF disponibili")
                
                if total == 0:
                    st.info("Nessun PDF. Usa 'Carica nuovi PDF' sopra.")
                else:
                    for classe, pdfs in all_pdfs.items():
                        with st.expander(f"**{classe}** ({len(pdfs)} PDF)"):
                            for pdf in pdfs:
                                st.write(f"📄 {pdf.name}")
                    
                    st.session_state.selected_materia = selected_materia
                    st.session_state.selected_classe = None
                    st.session_state.selected_pdfs = all_pdfs
                    
                    st.success(f"✅ {total} PDF selezionati → Vai alla tab **Analisi**")
            else:
                # Classe specifica
                selected_classe = classi[selected_classe_idx - 1]
                pdfs = get_pdf_in_folder(selected_materia, selected_classe)
                
                st.subheader(f"📄 {len(pdfs)} PDF in {selected_classe}")
                
                if not pdfs:
                    st.info("Nessun PDF. Usa 'Carica nuovi PDF' sopra.")
                else:
                    for pdf in pdfs:
                        st.write(f"📄 {pdf.name}")
                    
                    st.session_state.selected_materia = selected_materia
                    st.session_state.selected_classe = selected_classe
                    st.session_state.selected_pdfs = {selected_classe: pdfs}
                    
                    st.success(f"✅ {len(pdfs)} PDF selezionati → Vai alla tab **Analisi**")

# === TAB 2: ANALISI ===
with tab2:
    st.header("🚀 Avvia Analisi")
    
    if "selected_pdfs" not in st.session_state or not st.session_state.selected_pdfs:
        st.warning("⚠️ Seleziona prima i programmi nella tab 'Programmi'")
    else:
        materia = st.session_state.selected_materia
        classe = st.session_state.selected_classe
        pdfs = st.session_state.selected_pdfs
        total_pdfs = sum(len(p) for p in pdfs.values())
        classi_analizzate = list(pdfs.keys())
        
        # Riepilogo
        col1, col2, col3 = st.columns(3)
        col1.metric("Materia", materia.replace("_", " "))
        col2.metric("Classi", len(classi_analizzate))
        col3.metric("PDF", total_pdfs)
        
        # Nome analisi
        default_name = f"{materia}_{classi_analizzate[0]}" if len(classi_analizzate) == 1 else f"{materia}_Multiclasse"
        analysis_name = st.text_input("Nome analisi", value=default_name)
        
        # Verifica se c'è già un'analisi
        current = get_current_analysis()
        if current:
            st.warning(f"⚠️ Esiste già un'analisi: **{current.get('name', 'N/D')}**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📦 Archivia e procedi", type="primary", use_container_width=True):
                    archive_current_analysis()
                    st.success("✅ Archiviata")
                    st.rerun()
            with col2:
                if st.button("🔄 Sovrascrivi", use_container_width=True):
                    clear_current_analysis()
                    st.success("✅ Pronto per nuova analisi")
                    st.rerun()
            with col3:
                if st.button("❌ Annulla", use_container_width=True):
                    st.stop()
        
        st.markdown("---")
        
        # Avvia
        if st.button("🚀 Avvia Elaborazione", type="primary", use_container_width=True):
            
            # Pulisci directory
            clear_current_analysis()
            analisi_dir = get_analisi_dir()
            
            # Raccogli PDF
            all_pdf_paths = []
            for classe_name, pdf_list in pdfs.items():
                all_pdf_paths.extend(pdf_list)
            
            with st.spinner("Elaborazione in corso..."):
                try:
                    from app.main_pipeline import FrameworkGenerationPipeline
                    from app.report_generator import ReportGenerator
                    from app.framework_adapter import FrameworkAdapter
                    
                    pipeline = FrameworkGenerationPipeline()
                    progress = st.progress(0, text="Inizializzazione...")
                    
                    # Step 1: Estrazione
                    progress.progress(10, text="Estrazione testo dai PDF...")
                    syllabus_texts, syllabus_metadata = pipeline.extract_from_files(all_pdf_paths)
                    
                    if not syllabus_texts:
                        st.error("❌ Nessun testo estratto")
                        st.stop()
                    
                    # Step 2: Analisi
                    progress.progress(30, text="Analisi concetti...")
                    concept_collection, framework, coverages, coverage_matrix = pipeline.run_analysis(
                        syllabus_texts, syllabus_metadata, analysis_name, n_clusters, use_llm and bool(api_key)
                    )
                    
                    # Step 3: Output Zanichelli
                    progress.progress(50, text="Generazione output...")
                    zanichelli_output = pipeline.generate_zanichelli_output(
                        materia, concept_collection, coverages, syllabus_metadata, classi_analizzate
                    )
                    
                    # Step 4: Report
                    progress.progress(70, text="Generazione report...")
                    
                    adapter = FrameworkAdapter()
                    reference_fw = adapter.load_framework(materia)
                    
                    report_gen = ReportGenerator(reference_framework=reference_fw)
                    report_gen.set_analysis_data(zanichelli_output)
                    
                    report_html = report_gen.generate_analysis_report(materia, classi_analizzate)
                    changelog_html = report_gen.generate_changelog(materia, classi_analizzate)
                    updated_framework = report_gen.generate_updated_framework(materia, classi_analizzate)
                    
                    # Step 5: Salvataggio
                    progress.progress(90, text="Salvataggio...")
                    
                    # Salva i 3 file principali
                    with open(analisi_dir / "report_analisi.html", "w", encoding="utf-8") as f:
                        f.write(report_html)
                    
                    with open(analisi_dir / "changelog_framework.html", "w", encoding="utf-8") as f:
                        f.write(changelog_html)
                    
                    with open(analisi_dir / "framework_aggiornato.json", "w", encoding="utf-8") as f:
                        json.dump(updated_framework, f, indent=2, ensure_ascii=False)
                    
                    # Metadati
                    meta = {
                        "name": analysis_name,
                        "materia": materia,
                        "classi": classi_analizzate,
                        "created": datetime.now().isoformat(),
                        "n_syllabus": len(syllabus_texts),
                        "n_concepts": concept_collection.total_unique_concepts,
                        "n_modules": framework.n_modules,
                        "coverage": zanichelli_output.get("overall_assessment", {}).get("coverage_percentage", 0),
                        "judgment": zanichelli_output.get("overall_assessment", {}).get("judgment", "N/D")
                    }
                    with open(analisi_dir / "analisi.json", "w", encoding="utf-8") as f:
                        json.dump(meta, f, indent=2, ensure_ascii=False)
                    
                    progress.progress(100, text="✅ Completato!")
                    
                    st.success("✅ Analisi completata!")
                    st.info("👉 Vai alla tab **Risultati** per visualizzare i report")
                    
                except Exception as e:
                    st.error(f"❌ Errore: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

# === TAB 3: RISULTATI ===
with tab3:
    st.header("📊 Risultati")
    
    current = get_current_analysis()
    
    if not current:
        st.info("Nessuna analisi disponibile. Vai alla tab 'Analisi' per elaborare i programmi.")
    else:
        # Info analisi
        st.subheader(f"📋 {current.get('name', 'Analisi')}")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Materia", current.get("materia", "N/D").replace("_", " "))
        col2.metric("Syllabus", current.get("n_syllabus", 0))
        col3.metric("Concetti", current.get("n_concepts", 0))
        col4.metric("Copertura", f"{current.get('coverage', 0):.0f}%", current.get("judgment", ""))
        
        st.caption(f"Generata il {current.get('created', 'N/D')[:10]} | Classi: {', '.join(current.get('classi', []))}")
        
        st.markdown("---")
        
        # File
        analisi_dir = get_analisi_dir()
        report_file = analisi_dir / "report_analisi.html"
        changelog_file = analisi_dir / "changelog_framework.html"
        framework_file = analisi_dir / "framework_aggiornato.json"
        
        # Download buttons
        st.subheader("📥 Download")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if report_file.exists():
                with open(report_file, "r", encoding="utf-8") as f:
                    st.download_button(
                        "📄 Report Analisi",
                        f.read(),
                        f"report_{current.get('name', 'analisi')}.html",
                        "text/html",
                        use_container_width=True
                    )
        
        with col2:
            if changelog_file.exists():
                with open(changelog_file, "r", encoding="utf-8") as f:
                    st.download_button(
                        "🔄 Changelog",
                        f.read(),
                        f"changelog_{current.get('name', 'analisi')}.html",
                        "text/html",
                        use_container_width=True
                    )
        
        with col3:
            if framework_file.exists():
                with open(framework_file, "r", encoding="utf-8") as f:
                    st.download_button(
                        "📋 Framework JSON",
                        f.read(),
                        f"framework_{current.get('name', 'analisi')}.json",
                        "application/json",
                        use_container_width=True
                    )
        
        st.markdown("---")
        
        # Visualizzazione
        view_tab1, view_tab2, view_tab3 = st.tabs(["📄 Report", "🔄 Changelog", "📋 Framework"])
        
        with view_tab1:
            if report_file.exists():
                with open(report_file, "r", encoding="utf-8") as f:
                    st.components.v1.html(f.read(), height=700, scrolling=True)
            else:
                st.warning("File non trovato")
        
        with view_tab2:
            if changelog_file.exists():
                with open(changelog_file, "r", encoding="utf-8") as f:
                    st.components.v1.html(f.read(), height=700, scrolling=True)
            else:
                st.warning("File non trovato")
        
        with view_tab3:
            if framework_file.exists():
                with open(framework_file, "r", encoding="utf-8") as f:
                    fw = json.load(f)
                
                st.write(f"**{fw.get('framework', {}).get('name', 'N/D')}**")
                st.write(f"Classi: {', '.join(fw.get('framework', {}).get('classes_analyzed', []))}")
                
                st.markdown("---")
                
                for mod in fw.get("syllabus_modules", []):
                    class_data = mod.get("class_data", {})
                    if class_data:
                        first_class = list(class_data.keys())[0]
                        level = class_data[first_class].get("relevance_level", 0)
                        status = class_data[first_class].get("status", "").replace("_", " ")
                        
                        icons = {5: "🟢", 4: "🟢", 3: "🟡", 2: "🟠", 1: "🔴", 0: "⚪"}
                        icon = icons.get(level, "⚪")
                        
                        st.write(f"{icon} **{mod.get('name')}** — Livello {level}/5 ({status})")
            else:
                st.warning("File non trovato")

# === TAB 4: CONFRONTA CLASSI ===
with tab4:
    st.header("🔄 Confronto tra Classi di Laurea")
    st.markdown("Confronta framework generati da analisi di classi diverse per la stessa materia.")
    
    # Raccogli analisi disponibili
    archived = get_archived_analyses()
    current = get_current_analysis()
    
    available_analyses = []
    
    # Aggiungi analisi corrente
    if current:
        available_analyses.append({
            "id": "current",
            "label": f"🔵 [CORRENTE] {current.get('name', 'N/D')}",
            "path": get_analisi_dir(),
            "meta": current,
            "materia": current.get("materia", ""),
            "classi": current.get("classi", [])
        })
    
    # Aggiungi analisi archiviate
    for a in archived:
        available_analyses.append({
            "id": a["dir_name"],
            "label": f"📦 {a.get('name', 'N/D')} ({a.get('created', '')[:10]})",
            "path": a["path"],
            "meta": a,
            "materia": a.get("materia", ""),
            "classi": a.get("classi", [])
        })
    
    if len(available_analyses) < 2:
        st.warning("⚠️ Servono almeno 2 analisi per il confronto.")
        st.info("""
        **Come procedere:**
        1. Esegui un'analisi per una classe (es. L-27)
        2. Archiviala dalla tab Gestione
        3. Esegui un'analisi per un'altra classe (es. L-13)
        4. Torna qui per confrontare
        """)
    else:
        # Raggruppa per materia
        materie_disponibili = list(set(a["materia"] for a in available_analyses if a["materia"]))
        
        if materie_disponibili:
            selected_materia_confronto = st.selectbox(
                "Filtra per materia",
                ["Tutte"] + materie_disponibili,
                key="confronto_materia"
            )
            
            if selected_materia_confronto != "Tutte":
                available_analyses = [a for a in available_analyses if a["materia"] == selected_materia_confronto]
        
        st.markdown("---")
        
        # === NUOVO: Selezione tipo di confronto ===
        st.subheader("⚙️ Tipo di Confronto")
        
        comparison_type = st.radio(
            "Seleziona la modalità di confronto:",
            [
                "📊 Rispetto al Framework Ideale (quanto le classi coprono il catalogo Zanichelli)",
                "🔄 Confronto Diretto tra Classi (differenze reali di insegnamento)"
            ],
            key="comparison_type",
            help="""
            **Framework Ideale**: confronta quanto ogni classe copre il framework di riferimento Zanichelli.
            **Confronto Diretto**: analizza le differenze tra ciò che si insegna effettivamente nelle diverse classi.
            """
        )
        
        is_direct_comparison = "Diretto" in comparison_type
        
        if is_direct_comparison:
            st.info("💡 **Confronto Diretto**: analizzerà i concetti insegnati in ogni classe, evidenziando sovrapposizioni e differenze indipendentemente dal framework ideale.")
        else:
            st.info("💡 **Framework Ideale**: mostrerà quanto ogni classe è allineata al catalogo Zanichelli.")
        
        st.markdown("---")
        st.subheader("Seleziona analisi da confrontare")
        
        # Selezione con checkbox
        selected_for_comparison = []
        
        for item in available_analyses:
            classi_str = ", ".join(item["classi"]) if item["classi"] else "N/D"
            col1, col2, col3 = st.columns([0.5, 3, 2])
            
            with col1:
                is_selected = st.checkbox("", key=f"sel_{item['id']}")
            with col2:
                st.write(item["label"])
            with col3:
                st.caption(f"Classi: {classi_str}")
            
            if is_selected:
                selected_for_comparison.append(item)
        
        st.markdown("---")
        
        # Status selezione
        n_selected = len(selected_for_comparison)
        
        if n_selected == 0:
            st.info("Seleziona almeno 2 analisi per confrontarle")
        elif n_selected == 1:
            st.warning("Seleziona almeno un'altra analisi")
        else:
            st.success(f"✅ {n_selected} analisi selezionate")
            
            # Verifica stessa materia
            materie_sel = set(a["materia"] for a in selected_for_comparison)
            if len(materie_sel) > 1:
                st.warning(f"⚠️ Attenzione: stai confrontando materie diverse ({', '.join(materie_sel)})")
            
            # Nome confronto
            tipo_label = "Diretto" if is_direct_comparison else "vsIdeale"
            confronto_name = st.text_input(
                "Nome confronto (opzionale)",
                value=f"Confronto_{list(materie_sel)[0]}_{tipo_label}" if len(materie_sel) == 1 else f"Confronto_Multimateria_{tipo_label}"
            )
            
            if st.button("🔄 Genera Confronto", type="primary", use_container_width=True):
                
                with st.spinner("Elaborazione confronto in corso..."):
                    try:
                        from app.class_comparator import ClassComparator
                        
                        comparator = ClassComparator()
                        
                        # Carica analisi
                        analyses_loaded = []
                        for item in selected_for_comparison:
                            loaded = comparator.load_analysis(item["path"])
                            if loaded:
                                analyses_loaded.append(loaded)
                            else:
                                st.warning(f"⚠️ Impossibile caricare: {item['label']}")
                        
                        if len(analyses_loaded) < 2:
                            st.error("❌ Impossibile caricare abbastanza analisi")
                            st.stop()
                        
                        # Esegui confronto in base al tipo selezionato
                        if is_direct_comparison:
                            comparison_result = comparator.compare_analyses_direct(analyses_loaded)
                            report_html = comparator.generate_direct_comparison_report(comparison_result)
                        else:
                            comparison_result = comparator.compare_analyses(analyses_loaded)
                            report_html = comparator.generate_comparison_report(comparison_result)
                        
                        # Genera framework unificato
                        unified_framework = comparator.generate_unified_framework(comparison_result)
                        
                        # Salva
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        confronti_dir = get_confronti_dir()
                        
                        tipo_suffix = "_diretto" if is_direct_comparison else "_vs_ideale"
                        html_path = confronti_dir / f"confronto_{timestamp}{tipo_suffix}.html"
                        json_path = confronti_dir / f"framework_unificato_{timestamp}{tipo_suffix}.json"
                        
                        with open(html_path, "w", encoding="utf-8") as f:
                            f.write(report_html)
                        
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(unified_framework, f, indent=2, ensure_ascii=False)
                        
                        st.success("✅ Confronto completato!")
                        
                        # Mostra risultati
                        st.markdown("---")
                        st.subheader("📊 Risultati Confronto")
                        
                        # Statistiche
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Classi confrontate", len(comparison_result.classes_compared))
                        col2.metric("Moduli totali", len(comparison_result.modules))
                        col3.metric("Concetti totali", comparison_result.total_concepts)
                        col4.metric("Concetti core", comparison_result.core_concepts_count)
                        
                        # Info aggiuntive per confronto diretto
                        if is_direct_comparison and hasattr(comparison_result, 'class_specific_counts'):
                            st.markdown("---")
                            st.markdown("**📌 Concetti esclusivi per classe:**")
                            for classe, count in comparison_result.class_specific_counts.items():
                                st.write(f"  • **{classe}**: {count} concetti distintivi")
                        
                        # Download
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.download_button(
                                "📄 Scarica Report HTML",
                                report_html,
                                f"confronto_{confronto_name}_{timestamp}.html",
                                "text/html",
                                use_container_width=True
                            )
                        
                        with col2:
                            st.download_button(
                                "📋 Scarica Framework Unificato",
                                json.dumps(unified_framework, indent=2, ensure_ascii=False),
                                f"framework_unificato_{confronto_name}_{timestamp}.json",
                                "application/json",
                                use_container_width=True
                            )
                        
                        # Anteprima
                        st.markdown("---")
                        st.subheader("👁️ Anteprima Report")
                        st.components.v1.html(report_html, height=600, scrolling=True)
                        
                    except Exception as e:
                        st.error(f"❌ Errore durante il confronto: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
        
        # Sezione confronti salvati
        st.markdown("---")
        st.subheader("📁 Confronti Salvati")
        
        saved_comparisons = get_saved_comparisons()
        
        if not saved_comparisons:
            st.info("Nessun confronto salvato")
        else:
            for comp in saved_comparisons:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 0.5])
                
                with col1:
                    # Mostra tipo di confronto nel nome
                    tipo = "🔄 Diretto" if "_diretto" in comp["html_path"].name else "📊 vs Ideale"
                    st.write(f"{tipo} - {comp['date']}")
                
                with col2:
                    with open(comp["html_path"], "r", encoding="utf-8") as f:
                        st.download_button(
                            "HTML",
                            f.read(),
                            comp["html_path"].name,
                            "text/html",
                            key=f"dl_html_{comp['timestamp']}"
                        )
                
                with col3:
                    if comp["json_path"] and comp["json_path"].exists():
                        with open(comp["json_path"], "r", encoding="utf-8") as f:
                            st.download_button(
                                "JSON",
                                f.read(),
                                comp["json_path"].name,
                                "application/json",
                                key=f"dl_json_{comp['timestamp']}"
                            )
                
                with col4:
                    if st.button("🗑️", key=f"del_comp_{comp['timestamp']}", help="Elimina confronto"):
                        if comp["html_path"].exists():
                            comp["html_path"].unlink()
                        if comp["json_path"] and comp["json_path"].exists():
                            comp["json_path"].unlink()
                        st.rerun()
            
            st.markdown("---")
            if st.button("🗑️ Elimina tutti i confronti", type="secondary"):
                for comp in saved_comparisons:
                    if comp["html_path"].exists():
                        comp["html_path"].unlink()
                    if comp["json_path"] and comp["json_path"].exists():
                        comp["json_path"].unlink()
                st.success("✅ Tutti i confronti eliminati")
                st.rerun()

# === TAB 5: GESTIONE ===
with tab5:
    st.header("⚙️ Gestione")
    
    gest_tab1, gest_tab2, gest_tab3 = st.tabs(["📁 Cartelle", "📦 Archivio", "📚 Framework"])
    
    # Cartelle
    with gest_tab1:
        st.subheader("Gestione Cartelle Programmi")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Nuova Materia**")
            new_materia = st.text_input("Nome", placeholder="Es: Biochimica")
            if st.button("➕ Crea Materia") and new_materia:
                create_materia(new_materia)
                st.success("✅ Creata!")
                st.rerun()
        
        with col2:
            st.markdown("**Nuova Classe**")
            materie = get_materie()
            if materie:
                sel_mat = st.selectbox("Materia", materie, key="new_cls_mat")
                new_classe = st.text_input("Classe", placeholder="Es: L-27_Chimica")
                if st.button("➕ Crea Classe") and new_classe:
                    create_classe(sel_mat, new_classe)
                    st.success("✅ Creata!")
                    st.rerun()
        
        st.markdown("---")
        st.subheader("Struttura")
        
        for materia in get_materie():
            classi = get_classi_laurea(materia)
            n_pdfs = sum(len(get_pdf_in_folder(materia, c)) for c in classi)
            fw = find_matching_framework(materia)
            
            st.write(f"📚 **{materia}** — {len(classi)} classi, {n_pdfs} PDF {'✅' if fw else ''}")
    
    # Archivio
    with gest_tab2:
        st.subheader("📦 Analisi Archiviate")
        
        # Archivia analisi corrente
        current = get_current_analysis()
        if current:
            st.write(f"**Analisi corrente:** {current.get('name', 'N/D')}")
            if st.button("📦 Archivia analisi corrente"):
                path = archive_current_analysis()
                if path:
                    st.success(f"✅ Archiviata in: {path.name}")
                    st.rerun()
        
        st.markdown("---")
        
        # Lista archivio
        archived = get_archived_analyses()
        
        if not archived:
            st.info("Nessuna analisi in archivio")
        else:
            st.write(f"**{len(archived)} analisi archiviate:**")
            
            for a in archived:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{a.get('name', 'N/D')}**")
                    st.caption(f"{a.get('created', '')[:10]} — {a.get('n_syllabus', 0)} syllabus — Classi: {', '.join(a.get('classi', []))}")
                
                with col2:
                    st.write(f"{a.get('coverage', 0):.0f}%")
                
                with col3:
                    if st.button("🗑️", key=f"del_{a['dir_name']}"):
                        delete_archived_analysis(a["path"])
                        st.rerun()
            
            st.markdown("---")
            if st.button("🗑️ Elimina tutto l'archivio", type="secondary"):
                for a in archived:
                    delete_archived_analysis(a["path"])
                st.success("✅ Archivio svuotato")
                st.rerun()
    
    # Framework
    with gest_tab3:
        st.subheader("📚 Framework Zanichelli")
        st.caption(f"Percorso: `{get_frameworks_dir().absolute()}`")
        
        frameworks = get_available_frameworks()
        
        if frameworks:
            for fw in frameworks:
                st.write(f"• **{fw['name']}**")
        else:
            st.info("Nessun framework. Salva i JSON in `frameworks/`")


# === TAB 6: ANALISI MANUALI ===
with tab6:
    st.header("📖 Analisi Manuali")
    st.markdown("Confronta indici di manuali con framework IDEALE, REALE, o tra loro.")
    
    try:
        from app.manual_analyzer import ManualAnalyzer
        analyzer = ManualAnalyzer()
        
        # Sub-tabs per le diverse funzionalità
        man_tab1, man_tab2, man_tab3, man_tab4 = st.tabs([
            "📚 Manuali Disponibili",
            "🎯 Confronto vs Ideale",
            "📊 Confronto vs Reale", 
            "⚖️ Confronto tra Manuali"
        ])
        
        # === SUB-TAB 1: MANUALI DISPONIBILI ===
        with man_tab1:
            st.subheader("📚 Manuali Caricati")
            
            subjects = analyzer.get_available_subjects()
            
            if not subjects:
                st.warning("Nessun manuale trovato.")
                st.info(f"""
                **Per aggiungere manuali:**
                1. Crea la cartella `{get_manuali_dir() / '[Nome_Materia]' / 'indici'}`
                2. Aggiungi sottocartelle `manuali zanichelli/` e `manuali competitor/`
                3. Inserisci i file JSON degli indici
                """)
            else:
                for subject in subjects:
                    manuals = analyzer.get_manuals_for_subject(subject)
                    n_zan = len(manuals.get("zanichelli", []))
                    n_comp = len(manuals.get("competitor", []))
                    
                    with st.expander(f"📚 **{subject.replace('_', ' ')}** — {n_zan} Zanichelli, {n_comp} Competitor"):
                        
                        if n_zan > 0:
                            st.markdown("**🟦 Manuali Zanichelli:**")
                            for m in manuals["zanichelli"]:
                                st.write(f"  • **{m['title']}** — {m['author']} ({m['n_chapters']} cap.)")
                        
                        if n_comp > 0:
                            st.markdown("**🟧 Manuali Competitor:**")
                            for m in manuals["competitor"]:
                                st.write(f"  • **{m['title']}** — {m['author']}, {m['publisher']} ({m['n_chapters']} cap.)")
                
                st.markdown("---")
                st.caption(f"📁 Percorso manuali: `{get_manuali_dir().absolute()}`")
        
        # === SUB-TAB 2: CONFRONTO VS IDEALE ===
        with man_tab2:
            st.subheader("🎯 Confronto Manuale vs Framework Ideale")
            st.markdown("Analizza quanto un manuale copre il framework ideale Zanichelli.")
            
            subjects = analyzer.get_available_subjects()
            
            if not subjects:
                st.warning("Nessun manuale disponibile. Carica prima i JSON degli indici.")
            else:
                # Selezione materia
                selected_subject = st.selectbox(
                    "Seleziona Materia",
                    subjects,
                    key="ideal_subject"
                )
                
                if selected_subject:
                    # Verifica framework ideale
                    from app.framework_adapter import FrameworkAdapter
                    adapter = FrameworkAdapter()
                    ideal_fw = adapter.load_framework(selected_subject)
                    
                    if not ideal_fw:
                        st.error(f"❌ Nessun framework ideale trovato per {selected_subject}")
                        st.info("Verifica che esista un file JSON corrispondente in `frameworks/`")
                    else:
                        st.success(f"✅ Framework ideale: {ideal_fw.get('framework', {}).get('name', 'N/D')}")
                        
                        # Selezione manuale
                        manuals = analyzer.get_manuals_for_subject(selected_subject)
                        all_manuals = manuals.get("zanichelli", []) + manuals.get("competitor", [])
                        
                        if not all_manuals:
                            st.warning("Nessun manuale disponibile per questa materia.")
                        else:
                            # CORRETTO: mostra autore nel menu
                            manual_options = {
                                f"{m['title']} - {m['author']} ({m['publisher']})": m for m in all_manuals
                            }
                            
                            selected_manual_name = st.selectbox(
                                "Seleziona Manuale",
                                list(manual_options.keys()),
                                key="ideal_manual"
                            )
                            
                            if selected_manual_name and st.button("🔍 Analizza vs Ideale", type="primary"):
                                selected_manual_info = manual_options[selected_manual_name]
                                
                                with st.spinner("Analisi in corso..."):
                                    # Carica manuale
                                    manual = analyzer.load_manual(selected_manual_info["path"])
                                    
                                    if not manual:
                                        st.error("❌ Errore caricamento manuale")
                                    else:
                                        # Esegui analisi
                                        analysis = analyzer.analyze_manual_vs_ideal(manual, ideal_fw)
                                        
                                        # Mostra risultati
                                        st.markdown("---")
                                        st.subheader("📊 Risultati Analisi")
                                        
                                        # Metriche
                                        col1, col2, col3, col4 = st.columns(4)
                                        col1.metric("Copertura", f"{analysis['overall_coverage']:.1f}%")
                                        col2.metric("Giudizio", analysis['judgment'])
                                        col3.metric("Capitoli", analysis['manual_info']['n_chapters'])
                                        col4.metric("Sezioni", analysis['manual_info']['n_sections'])
                                        
                                        # Dettaglio per modulo
                                        st.markdown("---")
                                        st.markdown("**Copertura per Modulo:**")
                                        
                                        for mod in analysis['modules_analysis']:
                                            cov = mod['coverage_percentage']
                                            status_color = "🟢" if cov >= 70 else ("🟡" if cov >= 40 else "🔴")
                                            
                                            with st.expander(f"{status_color} {mod['module_name']} — {cov:.0f}%"):
                                                st.write(f"Contenuti coperti: {mod['contents_covered']}/{mod['contents_total']}")
                                                
                                                if mod['content_matches']:
                                                    st.markdown("**Trovati:**")
                                                    for cm in mod['content_matches']:
                                                        if cm['matched_by']:
                                                            st.write(f"  ✅ {cm['content']} → Cap. {cm.get('chapter', '?')}")
                                                        else:
                                                            st.write(f"  ❌ {cm['content']}")
                                        
                                        # Gap
                                        if analysis['gaps']['missing_in_manual']:
                                            st.markdown("---")
                                            st.markdown("**⚠️ Contenuti mancanti nel manuale:**")
                                            for gap in analysis['gaps']['missing_in_manual'][:10]:
                                                st.write(f"  • {gap['content']} (Modulo: {gap['module']})")
                                        
                                        # Download report
                                        st.markdown("---")
                                        report_html = analyzer.generate_single_analysis_report_html(analysis, "ideal")
                                        
                                        st.download_button(
                                            "📥 Scarica Report HTML",
                                            report_html,
                                            f"analisi_{manual['id']}_vs_ideale.html",
                                            "text/html",
                                            use_container_width=True
                                        )
        
        # === SUB-TAB 3: CONFRONTO VS REALE ===
        with man_tab3:
            st.subheader("📊 Confronto Manuale vs Framework Reale")
            st.markdown("Analizza quanto un manuale copre ciò che viene **effettivamente insegnato** nei corsi universitari.")
            
            subjects = analyzer.get_available_subjects()
            
            if not subjects:
                st.warning("Nessun manuale disponibile.")
            else:
                selected_subject = st.selectbox(
                    "Seleziona Materia",
                    subjects,
                    key="real_subject"
                )
                
                if selected_subject:
                    # Trova framework reali disponibili
                    real_frameworks = analyzer.get_available_real_frameworks(selected_subject)
                    
                    if not real_frameworks:
                        st.warning(f"Nessun framework reale disponibile per {selected_subject}.")
                        st.info("Esegui prima un'analisi dei programmi d'esame nella tab 'Analisi'.")
                    else:
                        # Selezione framework reale
                        fw_options = {
                            f"{fw['name']} ({fw['date']}) - {fw['n_syllabus']} programmi": fw 
                            for fw in real_frameworks
                        }
                        
                        selected_fw_name = st.selectbox(
                            "Seleziona Framework Reale",
                            list(fw_options.keys()),
                            key="real_fw"
                        )
                        
                        # Selezione manuale
                        manuals = analyzer.get_manuals_for_subject(selected_subject)
                        all_manuals = manuals.get("zanichelli", []) + manuals.get("competitor", [])
                        
                        if all_manuals:
                            # CORRETTO: mostra autore nel menu
                            manual_options = {
                                f"{m['title']} - {m['author']} ({m['publisher']})": m for m in all_manuals
                            }
                            
                            selected_manual_name = st.selectbox(
                                "Seleziona Manuale",
                                list(manual_options.keys()),
                                key="real_manual"
                            )
                            
                            if selected_manual_name and st.button("🔍 Analizza vs Reale", type="primary"):
                                selected_fw_info = fw_options[selected_fw_name]
                                selected_manual_info = manual_options[selected_manual_name]
                                
                                with st.spinner("Analisi in corso..."):
                                    # Carica
                                    manual = analyzer.load_manual(selected_manual_info["path"])
                                    real_fw = analyzer.load_real_framework(selected_fw_info["framework_path"])
                                    
                                    if not manual or not real_fw:
                                        st.error("❌ Errore caricamento dati")
                                    else:
                                        # Esegui analisi
                                        analysis = analyzer.analyze_manual_vs_real(manual, real_fw)
                                        
                                        # Mostra risultati
                                        st.markdown("---")
                                        st.subheader("📊 Risultati Analisi")
                                        
                                        col1, col2, col3 = st.columns(3)
                                        col1.metric("Copertura Base", f"{analysis['overall_coverage']:.1f}%")
                                        col2.metric("Copertura Pesata", f"{analysis['overall_weighted_coverage']:.1f}%")
                                        col3.metric("Giudizio", analysis['judgment'])
                                        
                                        st.info(f"💡 {analysis.get('recommendation', '')}")
                                        
                                        # Dettaglio moduli
                                        st.markdown("---")
                                        st.markdown("**Copertura per Modulo (pesata per frequenza nei programmi):**")
                                        
                                        for mod in analysis['modules_analysis']:
                                            cov = mod['weighted_coverage']
                                            real_cov = mod['real_coverage_in_programs']
                                            status = "🟢" if cov >= 70 else ("🟡" if cov >= 40 else "🔴")
                                            
                                            st.write(f"{status} **{mod['module_name']}** — Manuale: {cov:.0f}% | Nei programmi: {real_cov:.0f}%")
                                        
                                        # Download
                                        st.markdown("---")
                                        report_html = analyzer.generate_single_analysis_report_html(analysis, "real")
                                        
                                        st.download_button(
                                            "📥 Scarica Report HTML",
                                            report_html,
                                            f"analisi_{manual['id']}_vs_reale.html",
                                            "text/html",
                                            use_container_width=True
                                        )
        
        # === SUB-TAB 4: CONFRONTO TRA MANUALI ===
        with man_tab4:
            st.subheader("⚖️ Confronto tra Manuali")
            st.markdown("Confronta più manuali tra loro rispetto a un framework di riferimento.")
            
            subjects = analyzer.get_available_subjects()
            
            if not subjects:
                st.warning("Nessun manuale disponibile.")
            else:
                selected_subject = st.selectbox(
                    "Seleziona Materia",
                    subjects,
                    key="compare_subject"
                )
                
                if selected_subject:
                    manuals = analyzer.get_manuals_for_subject(selected_subject)
                    all_manuals = manuals.get("zanichelli", []) + manuals.get("competitor", [])
                    
                    if len(all_manuals) < 2:
                        st.warning("Servono almeno 2 manuali per il confronto.")
                    else:
                        st.markdown("**Seleziona manuali da confrontare:**")
                        
                        selected_manuals = []
                        for m in all_manuals:
                            col1, col2 = st.columns([0.5, 4])
                            with col1:
                                is_sel = st.checkbox("", key=f"cmp_{m['id']}")
                            with col2:
                                badge = "🟦" if m['publisher'].lower() == "zanichelli" else "🟧"
                                # CORRETTO: mostra autore nella lista
                                st.write(f"{badge} **{m['title']}** — {m['author']} ({m['publisher']})")
                            
                            if is_sel:
                                selected_manuals.append(m)
                        
                        st.markdown("---")
                        
                        # Selezione framework di riferimento
                        st.markdown("**Framework di riferimento:**")
                        
                        fw_type = st.radio(
                            "Tipo",
                            ["Ideale (Zanichelli)", "Reale (da analisi programmi)", "Nessuno (solo struttura)"],
                            key="compare_fw_type",
                            horizontal=True
                        )
                        
                        reference_framework = None
                        framework_type = "none"
                        
                        if "Ideale" in fw_type:
                            from app.framework_adapter import FrameworkAdapter
                            adapter = FrameworkAdapter()
                            reference_framework = adapter.load_framework(selected_subject)
                            framework_type = "ideal"
                            if reference_framework:
                                st.success(f"✅ Framework ideale caricato")
                            else:
                                st.warning("Framework ideale non trovato")
                        
                        elif "Reale" in fw_type:
                            real_fws = analyzer.get_available_real_frameworks(selected_subject)
                            if real_fws:
                                fw_options = {f"{fw['name']} ({fw['date']})": fw for fw in real_fws}
                                sel_fw = st.selectbox("Seleziona", list(fw_options.keys()), key="compare_real_fw")
                                if sel_fw:
                                    reference_framework = analyzer.load_real_framework(fw_options[sel_fw]["framework_path"])
                                    framework_type = "real"
                            else:
                                st.warning("Nessun framework reale disponibile")
                        
                        st.markdown("---")
                        
                        # Bottone confronto
                        n_selected = len(selected_manuals)
                        
                        if n_selected < 2:
                            st.info(f"Seleziona almeno 2 manuali ({n_selected} selezionati)")
                        else:
                            st.success(f"✅ {n_selected} manuali selezionati")
                            
                            if st.button("⚖️ Confronta Manuali", type="primary", use_container_width=True):
                                
                                with st.spinner("Confronto in corso..."):
                                    # Carica tutti i manuali
                                    loaded_manuals = []
                                    for m in selected_manuals:
                                        manual = analyzer.load_manual(m["path"])
                                        if manual:
                                            loaded_manuals.append(manual)
                                    
                                    if len(loaded_manuals) < 2:
                                        st.error("❌ Errore caricamento manuali")
                                    else:
                                        # Esegui confronto
                                        comparison = analyzer.compare_manuals(
                                            loaded_manuals, 
                                            reference_framework, 
                                            framework_type
                                        )
                                        
                                        # Mostra risultati
                                        st.markdown("---")
                                        st.subheader("🏆 Ranking Manuali")
                                        
                                        for i, m in enumerate(comparison['ranking']):
                                            rank = i + 1
                                            medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"{rank}."))
                                            cov = m.get('weighted_coverage', m.get('coverage', 0)) or 0
                                            
                                            col1, col2, col3, col4 = st.columns([0.5, 2.5, 1, 1])
                                            with col1:
                                                st.write(medal)
                                            with col2:
                                                st.write(f"**{m['manual_title']}**")
                                                st.caption(f"{m['author']} — {m['publisher']}")
                                            with col3:
                                                if cov > 0:
                                                    st.metric("Copertura", f"{cov:.0f}%")
                                            with col4:
                                                st.write(m.get('judgment', 'N/D'))
                                        
                                        # Confronto per modulo
                                        if comparison['modules_comparison']:
                                            st.markdown("---")
                                            st.subheader("📊 Confronto per Modulo")
                                            
                                            for mod in comparison['modules_comparison']:
                                                with st.expander(f"**{mod['module_name']}** — Media: {mod['avg_coverage']:.0f}%"):
                                                    for ms in mod['manual_scores']:
                                                        bar_pct = min(ms['coverage'], 100)
                                                        st.write(f"{ms['manual']}: **{ms['coverage']:.0f}%**")
                                                        st.progress(bar_pct / 100)
                                        
                                        # Download report
                                        st.markdown("---")
                                        report_html = analyzer.generate_comparison_report_html(comparison)
                                        
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.download_button(
                                                "📥 Scarica Report HTML",
                                                report_html,
                                                f"confronto_manuali_{selected_subject}_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                                                "text/html",
                                                use_container_width=True
                                            )
                                        with col2:
                                            st.download_button(
                                                "📥 Scarica JSON",
                                                json.dumps(comparison, indent=2, ensure_ascii=False, default=str),
                                                f"confronto_manuali_{selected_subject}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                                                "application/json",
                                                use_container_width=True
                                            )
    
    except ImportError as e:
        st.error(f"❌ Errore importazione ManualAnalyzer: {e}")
        st.info("Verifica che il file `app/manual_analyzer.py` sia presente.")
    except Exception as e:
        st.error(f"❌ Errore: {e}")
        import traceback
        st.code(traceback.format_exc())
        
# === TAB 7: PROFILO DOCENTE (Report Commerciale) ===
# === TAB 7: PROFILO DOCENTE ===
with tab7:
    st.header("🎓 Profilo Docente - Report Commerciale")
    st.markdown("""
    Genera un report commerciale personalizzato per il promotore, analizzando:
    - Il programma del docente
    - I manuali attualmente adottati
    - Il miglior manuale Zanichelli da proporre
    """)
    
    # Verifica materie disponibili
    materie_doc = get_materie()
    
    if not materie_doc:
        st.warning("⚠️ Nessuna materia disponibile. Crea prima una materia nella tab Gestione.")
    else:
        # === SEZIONE 1: SELEZIONE PROGRAMMA ===
        st.subheader("📄 1. Seleziona il Programma")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_materia_doc = st.selectbox(
                "Materia",
                materie_doc,
                key="promo_materia"
            )
        
        with col2:
            classi_doc = get_classi_laurea(selected_materia_doc) if selected_materia_doc else []
            if classi_doc:
                selected_classe_doc = st.selectbox(
                    "Classe di Laurea",
                    classi_doc,
                    key="promo_classe"
                )
            else:
                st.warning("Nessuna classe disponibile")
                selected_classe_doc = None
        
        # Selezione PDF
        selected_pdf_doc = None
        if selected_materia_doc and selected_classe_doc:
            pdfs_disponibili = get_pdf_in_folder(selected_materia_doc, selected_classe_doc)
            if pdfs_disponibili:
                pdf_names = [p.name for p in pdfs_disponibili]
                selected_pdf_name = st.selectbox(
                    "Programma (PDF)",
                    pdf_names,
                    key="promo_pdf"
                )
                selected_pdf_doc = pdfs_disponibili[pdf_names.index(selected_pdf_name)]
            else:
                st.warning("Nessun PDF disponibile in questa cartella")
        
        st.markdown("---")
        
        # === SEZIONE 2: MANUALI ADOTTATI ===
        st.subheader("📚 2. Indica i Manuali Attualmente Adottati")
        st.caption("Seleziona i manuali che il docente usa attualmente (Zanichelli E/O Competitor)")
        
        # Carica manuali disponibili per la materia
        manuali_disponibili = []
        manuali_dir = get_manuali_dir() / selected_materia_doc / "indici"
        
        # Manuali Zanichelli
        zanichelli_dir = manuali_dir / "Manuali_Zanichelli"
        if zanichelli_dir.exists():
            for json_file in zanichelli_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8-sig') as f:
                        content = f.read()
                        if content.startswith('\ufeff'):
                            content = content[1:]
                        data = json.loads(content)
                        manuali_disponibili.append({
                            'titolo': data.get('title', json_file.stem),
                            'autore': data.get('author', 'N/D'),
                            'editore': 'Zanichelli',
                            'path': str(json_file),
                            'label': f"🟦 {data.get('title', json_file.stem)} - {data.get('author', 'N/D')} (Zanichelli)"
                        })
                except:
                    pass
        
        # Manuali Competitor
        competitor_dir = manuali_dir / "Manuali_Competitor"
        if competitor_dir.exists():
            for json_file in competitor_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8-sig') as f:
                        content = f.read()
                        if content.startswith('\ufeff'):
                            content = content[1:]
                        data = json.loads(content)
                        editore = data.get('publisher', 'Altro')
                        manuali_disponibili.append({
                            'titolo': data.get('title', json_file.stem),
                            'autore': data.get('author', 'N/D'),
                            'editore': editore,
                            'path': str(json_file),
                            'label': f"🟧 {data.get('title', json_file.stem)} - {data.get('author', 'N/D')} ({editore})"
                        })
                except:
                    pass
        
        # Selezione manuali
        manuali_selezionati = []
        
        if manuali_disponibili:
            labels = [m['label'] for m in manuali_disponibili]
            selected_labels = st.multiselect(
                "Seleziona i manuali adottati dal docente",
                labels,
                key="promo_manuali_adottati"
            )
            
            for label in selected_labels:
                for m in manuali_disponibili:
                    if m['label'] == label:
                        manuali_selezionati.append({
                            'titolo': m['titolo'],
                            'autore': m['autore'],
                            'editore': m['editore']
                        })
        else:
            st.info(f"Nessun manuale caricato per {selected_materia_doc}. Puoi inserirli manualmente.")
        
        # Inserimento manuale
        with st.expander("➕ Aggiungi manuale manualmente"):
            col1, col2, col3 = st.columns(3)
            with col1:
                man_titolo = st.text_input("Titolo", key="man_titolo")
            with col2:
                man_autore = st.text_input("Autore", key="man_autore")
            with col3:
                man_editore = st.text_input("Editore", key="man_editore")
            
            if st.button("➕ Aggiungi"):
                if man_titolo and man_editore:
                    manuali_selezionati.append({
                        'titolo': man_titolo,
                        'autore': man_autore or 'N/D',
                        'editore': man_editore
                    })
                    st.success(f"✅ Aggiunto: {man_titolo}")
        
        # Mostra manuali selezionati
        if manuali_selezionati:
            st.markdown("**Manuali selezionati:**")
            for m in manuali_selezionati:
                icon = "🟦" if "zanichelli" in m['editore'].lower() else "🟧"
                st.write(f"{icon} {m['titolo']} - {m['autore']} ({m['editore']})")
        
        st.markdown("---")
        
        # === SEZIONE 3: GENERA REPORT ===
        st.subheader("🚀 3. Genera Report Commerciale")
        
        # Verifica prerequisiti
        can_generate = selected_pdf_doc is not None and len(manuali_selezionati) > 0
        
        if not selected_pdf_doc:
            st.warning("⚠️ Seleziona un programma PDF")
        if not manuali_selezionati:
            st.warning("⚠️ Indica almeno un manuale adottato")
        
        if can_generate:
            st.success("✅ Pronto per generare il report")
            
            if st.button("🚀 GENERA REPORT COMMERCIALE", type="primary", use_container_width=True):
                
                with st.spinner("Analisi in corso..."):
                    try:
                        from app.promo_orchestrator import PromoOrchestrator
                        from app.commercial_report_generator import CommercialReportGenerator
                        
                        # Progress
                        progress = st.progress(0, text="Inizializzazione...")
                        
                        # Inizializza orchestrator
                        orchestrator = PromoOrchestrator()
                        progress.progress(20, text="[1/7] Estrazione testo...")
                        
                        # Esegui analisi con il NUOVO metodo
                        progress.progress(40, text="[2/7] Analisi in corso...")
                        
                        analisi = orchestrator.analizza_programma_docente_con_competitor(
                            pdf_path=selected_pdf_doc,
                            materia=selected_materia_doc,
                            classe_laurea=selected_classe_doc,
                            manuali_adottati=manuali_selezionati
                        )
                        
                        progress.progress(70, text="[6/7] Generazione report...")
                        
                        # Genera HTML
                        generator = CommercialReportGenerator()
                        html_report = generator.genera_report_html(analisi)
                        
                        progress.progress(90, text="Salvataggio...")
                        
                        # Salva report
                        output_dir = get_analisi_dir()
                        pdf_stem = selected_pdf_doc.stem
                        output_path = output_dir / f"report_{pdf_stem}.html"
                        json_path = output_dir / f"analisi_{pdf_stem}.json"
                        
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(html_report)
                        
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(analisi, f, indent=2, ensure_ascii=False, default=str)
                        
                        progress.progress(100, text="✅ Completato!")
                        
                        st.success("✅ Report generato con successo!")
                        
                        # Riepilogo
                        st.markdown("---")
                        st.subheader("📊 Riepilogo")
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Punteggio Opportunità", f"{analisi.get('punteggio_opportunita', 0)}/100")
                        col2.metric("Copertura Ideale", f"{analisi.get('copertura_ideale', {}).get('percentuale', 0)}%")
                        col3.metric("Gap Identificati", len(analisi.get('gap_analysis', [])))
                        
                        # Manuale consigliato
                        manuale = analisi.get('manuale_zanichelli', {})
                        st.info(f"📚 **Manuale Zanichelli consigliato:** {manuale.get('titolo', 'N/D')} di {manuale.get('autore', 'N/D')}")
                        
                        # Download
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.download_button(
                                "📥 Scarica Report HTML",
                                html_report,
                                f"report_{pdf_stem}.html",
                                "text/html",
                                use_container_width=True
                            )
                        
                        with col2:
                            st.download_button(
                                "📥 Scarica Dati JSON",
                                json.dumps(analisi, indent=2, ensure_ascii=False, default=str),
                                f"analisi_{pdf_stem}.json",
                                "application/json",
                                use_container_width=True
                            )
                        
                        # Anteprima
                        st.markdown("---")
                        st.subheader("👁️ Anteprima Report")
                        st.components.v1.html(html_report, height=700, scrolling=True)
                        
                    except Exception as e:
                        st.error(f"❌ Errore: {str(e)}")
                        import traceback
                        with st.expander("Dettagli errore"):
                            st.code(traceback.format_exc())

# Footer
st.markdown("---")
st.caption("CoreX v1.7 — Zanichelli")
