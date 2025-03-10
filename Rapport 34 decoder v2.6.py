import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Configuration avancée de la page
st.set_page_config(page_title="Analyse AS-IS Télécom", layout="wide", initial_sidebar_state="expanded")

# Injecter du CSS personnalisé avancé
st.markdown("""
    <style>
        .main {background-color: #f4f6f8; font-family: 'Arial', sans-serif;}
        .stSidebar {background-color: #ffffff;}
        .stMetric {padding: 20px; border-radius: 10px; background-color: #ffffff; box-shadow: 0 6px 12px rgba(0,0,0,0.1);}
        .stExpander, .stTabs {background-color: #ffffff; border-radius: 10px; padding: 10px;}
        .css-1d391kg {padding-top: 20px;}
        h1, h2, h3 {color: #262730;}
    </style>
""", unsafe_allow_html=True)

# Chargement des données
@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    return df

uploaded_file = st.file_uploader("📁 Chargez votre fichier Excel ici", type=["xls", "xlsx"])

if uploaded_file:
    df = load_data(uploaded_file)

    # Traitement des données
    duplicates = df[df.duplicated(subset=['Subscriber Number'], keep=False)]

    df['Contract End Date'] = pd.to_datetime(df['Contract End Date'], errors='coerce', dayfirst=True)
    upcoming_contracts = df[(df['Contract End Date'] >= pd.Timestamp.today()) & 
                            (df['Contract End Date'] <= pd.Timestamp.today() + pd.DateOffset(months=3))]

    # Sidebar - Statistiques clés et filtres
    with st.sidebar:
        st.image("https://plus.unsplash.com/premium_photo-1661764570116-b1b0a2da783c?q=80&w=2670&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", use_container_width=True)
        st.subheader("📌 Statistiques clés")
        cols = st.columns(3)
        cols[0].metric("Total abonnés", df.shape[0])
        cols[1].metric("Produits dépendants", duplicates.shape[0])
        cols[2].metric("Contrats à renouveler", upcoming_contracts.shape[0])

        # Filtres interactifs
        st.subheader("🔍 Filtres")
        product_filter = st.multiselect("Produit", df['Product Description'].unique())
        address_filter = st.multiselect("Adresse", df['Installation Address'].unique())
        years = sorted(df['Contract End Date'].dt.year.dropna().astype(int).unique())
        year_filter = st.selectbox("Année fin contrat", ["Toutes"] + years)

    # Application des filtres
    def apply_filters(dataframe):
        df_filtered = dataframe.copy()
        if product_filter:
            df_filtered = df_filtered[df_filtered['Product Description'].isin(product_filter)]
        if address_filter:
            df_filtered = df_filtered[df_filtered['Installation Address'].isin(address_filter)]
        if year_filter != "Toutes":
            df_filtered = df_filtered[df_filtered['Contract End Date'].dt.year == int(year_filter)]
        return df_filtered

    df = apply_filters(df)
    duplicates = apply_filters(duplicates)

    # Onglets structurés avec contenu visuel amélioré
    tab1, tab2, tab3 = st.tabs(["📊 Données filtrées", "⚠️ Produits dépendants", "📅 Contrats à renouveler"])

    with tab1:
        st.subheader("📋 Données filtrées")
        df_display = df[['Subscriber Number', 'Installation Address', 'Product Description', 'Contract End Date']].copy()
        df_display['Contract End Date'] = df_display['Contract End Date'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_display, height=350)

        fig = px.bar(df['Product Description'].value_counts(), 
                     labels={'index':'Produit', 'value':'Nombre'},
                     title="Répartition des abonnements par produit",
                     color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("🚨 Produits dépendants")
        if not duplicates.empty:
            duplicates['Statut'] = duplicates.apply(lambda row: f"{row.get('Fiber Connection Status', 'No Fiber')} | {row.get('Copper Status', 'No Copper Phase Out')}", axis=1)
            duplicates['Vitesse (Mbit/s)'] = duplicates['Procodac DN Actual Speed Mbit/s'].fillna("N/A")
            st.dataframe(duplicates[['Subscriber Number', 'Installation Address', 'Product Description', 'Statut', 'Vitesse (Mbit/s)']], height=250)
        else:
            st.success("✅ Aucun produit dépendant détecté.")

    with tab3:
        st.subheader("⏳ Contrats expirant bientôt")
        if not upcoming_contracts.empty:
            upcoming_display = upcoming_contracts[['Subscriber Number', 'Installation Address', 'Product Description', 'Contract End Date']].copy()
            upcoming_display['Contract End Date'] = upcoming_display['Contract End Date'].dt.strftime('%d/%m/%Y')
            st.dataframe(upcoming_display, height=250)
        else:
            st.info("Aucun contrat ne nécessite de renouvellement imminent.")

    # Export des données filtrées
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Données Filtrées')
    buffer.seek(0)

    st.download_button(
        label="📥 Télécharger les données filtrées",
        data=buffer,
        file_name="donnees_filtrees.xlsx",
        mime="application/vnd.ms-excel"
    )
