from pathlib import Path
import hashlib
import streamlit as st
import pandas as pd
from gaia_model import GaiaDNAPlatform, BASE_FEATURES
from analysis_core import export_csv

ROOT = Path(__file__).resolve().parent
# Set page configuration
st.set_page_config(
    page_title="GaiaDNA - Biodiversity Explorer",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #228B22;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f8f0;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2E8B57;
        margin: 0.5rem 0;
    }
    .dashboard-btn {
        background-color: #2E8B57;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin: 5px;
        cursor: pointer;
        border: none;
        font-size: 16px;
        font-weight: bold;
    }
    .dashboard-btn:hover {
        background-color: #228B22;
    }
    .prediction-high {
        background: linear-gradient(45deg, #FF6B6B, #FF8E53);
        color: white;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
    }
    .prediction-medium {
        background: linear-gradient(45deg, #4ECDC4, #44A08D);
        color: white;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
    }
    .prediction-low {
        background: linear-gradient(45deg, #556270, #4ECDC4);
        color: white;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def create_dashboard():
    """Create the main dashboard navigation"""
    st.markdown('<h1 class="main-header">🌿 GaiaDNA Platform</h1>', unsafe_allow_html=True)
    st.markdown("### Biodiversity Record Review & Experimental AI")

    # Dashboard buttons
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("📊 Data Overview", use_container_width=True):
            st.session_state.current_page = "data_overview"

    with col2:
        if st.button("🔍 Identification Gaps", use_container_width=True):
            st.session_state.current_page = "ghost_species"

    with col3:
        if st.button("🗺️ Record Map", use_container_width=True):
            st.session_state.current_page = "conservation_map"

    with col4:
        if st.button("🌱 Environment", use_container_width=True):
            st.session_state.current_page = "ai_analysis"

    with col5:
        if st.button("🤖 Experimental AI", use_container_width=True):
            st.session_state.current_page = "ai_prediction"

    return st.session_state.get('current_page', 'data_overview')

def show_data_overview(gaia):
    st.subheader('Dataset overview')
    columns = st.columns(4)
    for column, label, value in zip(columns, ['Occurrence records', 'Needs species identification', 'Species named', 'Missing genus and species'], [len(gaia.df), gaia.ghost_count, gaia.identified_count, gaia.unclassified_count]):
        column.metric(label, f'{value:,}')
    st.dataframe(gaia.df.head(100), hide_index=True)
    st.caption('Counts refer to occurrence records, not unique species. Preview shows the first 100 records.')


def show_ghost_species(gaia):
    st.subheader('Identification gaps')
    status = st.multiselect('Review status', sorted(gaia.df.review_status.unique()), default=['Needs species identification'] if gaia.ghost_count else [])
    genus = st.text_input('Genus contains')
    selected = gaia.df[gaia.df.review_status.isin(status)]
    if genus:
        selected = selected[selected.genus.str.contains(genus, case=False, regex=False)]
    st.write(f'{len(selected):,} matching records')
    counts = selected.loc[selected.genus.ne(''), 'genus'].value_counts().head(10)
    if not counts.empty:
        st.bar_chart(counts, horizontal=True)
    st.dataframe(selected.head(1000), hide_index=True)
    st.download_button('Export review queue', export_csv(selected.to_dict('records')), 'gaiadna-review.csv', 'text/csv', disabled=selected.empty)
    st.caption('Preview: up to 1,000 rows. Export: all matching records, including original attribution fields.')


def show_conservation_map(gaia):
    st.subheader('Occurrence record map')
    map_view = gaia.create_conservation_map(heatmap=True)
    st.caption(f'{int(gaia.df.valid_coordinates.sum()):,} valid locations. Up to 1,000 sampled markers; heatmap includes all unresolved records with valid locations.')
    if map_view is None:
        st.info('No valid coordinates are available.')
    else:
        st.components.v1.html(map_view.get_root().render(), height=550)
    st.caption('Red: needs species identification. Blue: species named. Gray: neither field populated. Density reflects recorded observations and sampling effort, not verified discovery or conservation priority.')


def show_ai_analysis(gaia):
    st.subheader('Environmental profiles')
    available = [c for c in BASE_FEATURES if c in gaia.df and gaia.df[c].notna().any()]
    if not available:
        st.info('No numeric environmental measurements were supplied. You can optionally enable simulation in the sidebar.')
        return
    st.dataframe(gaia.df[available].describe())
    feature = st.selectbox('Environmental feature', available)
    st.bar_chart(gaia.df[feature].value_counts(bins=20).sort_index().rename_axis('Range').rename('Records').pipe(lambda x: x.set_axis(x.index.astype(str))))
    st.caption('Supplied values are retained. Their measurement provenance must be verified separately.')


def show_ai_prediction(gaia):
    st.subheader('Experimental identification-gap classifier')
    st.warning('This experiment predicts whether records lack a species label. It does not estimate the probability of discovering a new species. Random record splits do not validate geographic generalization.')
    if gaia.model_results is None:
        if not st.button('Train experimental model'):
            st.info('Train once for this dataset; moving sliders will reuse the model.')
            return
        try:
            with st.spinner('Training and evaluating the model…'):
                gaia.train_prediction_model()
        except ValueError as exc:
            st.warning(str(exc))
            return
    results = gaia.model_results
    columns = st.columns(3)
    for col, label, key in zip(columns, ['Holdout accuracy', 'Holdout balanced accuracy', 'Cross-validation balanced accuracy'], ['test_accuracy', 'balanced_accuracy', 'cv_mean_accuracy']):
        col.metric(label, f'{results[key]:.1%}')
    st.caption(f"{results['n_samples']:,} eligible records. Missing-both records are excluded. Reported scores are measured, with no minimum display floor.")
    st.bar_chart(results['feature_importance'].set_index('feature'))
    values = [st.slider('Temperature (°C)', -10., 40., 15.), st.slider('Precipitation (mm)', 0., 3000., 800.), st.slider('Elevation (m)', 0., 5000., 500.), st.slider('Soil pH', 0., 14., 6.5), st.slider('Humidity (%)', 0., 100., 75.), st.slider('Vegetation index', 0., 1., .7), st.slider('Seasonality', 0., 10., 2.5)]
    prediction = gaia.predict_discovery_potential(values)
    st.metric('Experimental incomplete-identification score', f"{prediction['high_potential']:.1%}")
    st.caption('This is a model class probability, not a calibrated scientific discovery probability. Inputs outside the training distribution may be unreliable.')


def main():
    with st.sidebar:
        st.title('Data management')
        source = st.radio('Dataset', ['Fungi sample', 'Insects example', 'Upload CSV / TSV / Excel'])
        upload = st.file_uploader('Upload biodiversity data', type=['csv', 'tsv', 'xlsx']) if source.startswith('Upload') else None
        simulation = st.checkbox('Enable synthetic environment demo', value=False)
        st.caption('Simulation fills absent environmental columns only. Supplied columns are never overwritten.')
        st.caption('Upload limit: 20 MB / 100,000 records. Avoid confidential or sensitive-location data. Files are processed in server memory, not intentionally saved.')
    page = create_dashboard()
    st.info('Hackathon research prototype. Missing species names indicate records for review, not confirmed undiscovered species.')
    if source.startswith('Upload') and upload is None:
        st.info('Upload a dataset, or select a sample to begin.')
        return
    try:
        if upload is not None:
            raw, name = upload.getvalue(), upload.name
        else:
            name = 'Fungi_dataset.csv' if source == 'Fungi sample' else 'Insects_dataset.csv'
            raw = (ROOT / name).read_bytes()
        fingerprint = hashlib.sha256(raw + name.encode() + str(simulation).encode()).hexdigest()
        if st.session_state.get('dataset_fingerprint') != fingerprint:
            gaia = GaiaDNAPlatform()
            gaia.load_data(raw, name)
            if simulation:
                gaia.generate_environmental_data()
            st.session_state.platform = gaia
            st.session_state.dataset_fingerprint = fingerprint
        gaia = st.session_state.platform
    except (ValueError, UnicodeError, OSError) as exc:
        st.error(f'Could not load data: {exc}')
        return
    if gaia.synthetic_features:
        st.warning('SYNTHETIC DEMO DATA: ' + ', '.join(gaia.synthetic_features) + '. Model scores involving these inputs are illustrative only.')
    if source == 'Insects example':
        st.caption('Insect example provenance and environmental measurement sources are unverified.')
    else:
        st.caption('Bundled fungi records retain GBIF-style identifiers and CC_BY_NC_4_0 attribution fields. Original download DOI was not supplied.')
    {'data_overview': show_data_overview, 'ghost_species': show_ghost_species, 'conservation_map': show_conservation_map, 'ai_analysis': show_ai_analysis, 'ai_prediction': show_ai_prediction}[page](gaia)
    with st.expander('PM case study: from hackathon to a testable product'):
        case = ROOT / 'docs' / 'PM_CASE_STUDY.md'
        if not case.exists():
            case = ROOT / 'PM_CASE_STUDY.md'
        if case.exists():
            st.markdown(case.read_text())
        else:
            st.write('GaiaDNA explores whether transparent record triage can help researchers prepare useful expert-review queues. User validation is the next milestone; no field discoveries are claimed.')

if __name__ == '__main__':
    main()
