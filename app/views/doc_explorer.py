#!/bin/python3

import streamlit as st
from pymongo import MongoClient

from config import MONGO_URI, MONGO_DB, MONGO_COLLECTION


@st.cache_resource
def get_mongo_client():
    """Cliente MongoDB con caché."""
    client = MongoClient(MONGO_URI)
    return client


def get_collection():
    """Obtiene la colección de fichas de especie."""
    client = get_mongo_client()
    db = client[MONGO_DB]
    return db[MONGO_COLLECTION]


def get_species_list():
    """Obtiene lista de especies con ID y nombre para el selector."""
    col = get_collection()
    pipeline = [
        {"$project": {"IDProd": 1, "NombreCientifico": 1, "NombreComun": 1}},
        {"$sort": {"NombreCientifico": 1}}
    ]
    return list(col.aggregate(pipeline))


def get_ficha(especie_id):
    """Obtiene la ficha completa de una especie por ID (numérico, IDProd de MySQL)."""
    col = get_collection()
    return col.find_one({"IDProd": int(especie_id)})


def render_document(doc, nivel=0, titulo=None):
    """Renderiza un documento de forma recursiva con indentación."""
    if doc is None:
        return
    
    if titulo:
        st.markdown(f"{'&nbsp;&nbsp;&nbsp;&nbsp;' * nivel}**{titulo}**")
    
    if isinstance(doc, dict):
        for key, value in doc.items():
            if key in ("_id", "IDProd"):
                continue
            if isinstance(value, (dict, list)):
                with st.expander(f"{'&nbsp;&nbsp;&nbsp;&nbsp;' * nivel}{key}", expanded=(nivel < 2)):
                    render_document(value, nivel + 1)
            else:
                st.markdown(f"{'&nbsp;&nbsp;&nbsp;&nbsp;' * nivel}`{key}`: {value}")
    elif isinstance(doc, list):
        for i, item in enumerate(doc):
            with st.expander(f"{'&nbsp;&nbsp;&nbsp;&nbsp;' * nivel}[{i}]", expanded=(nivel < 2)):
                render_document(item, nivel + 1)
    else:
        st.markdown(f"{'&nbsp;&nbsp;&nbsp;&nbsp;' * nivel}{doc}")


def render():
    st.title("Explorador de Documentos Jerárquicos de Especies")
    st.caption("MongoDB - Fichas de especie con documentos secundarios jerárquicos")

    # Conexión y selector
    try:
        collection = get_collection()
        species_list = get_species_list()
    except Exception as e:
        st.error(f"No se pudo conectar a MongoDB: {e}")
        st.info("Verifica que el contenedor `aqualife_mongo` esté corriendo.")
        return

    if not species_list:
        st.warning("No hay especies en la colección `fichas_especie`.")
        st.info("Ejecuta el script de carga de datos documentales si existe.")
        return

    # Selector de especie
    species_options = {f"{s.get('NombreComun', '')} ({s.get('NombreCientifico', '')})": str(s["IDProd"]) for s in species_list}
    selected_label = st.selectbox("Seleccionar especie", options=list(species_options.keys()))
    especie_id = species_options[selected_label]

    # Cargar y mostrar ficha
    ficha = get_ficha(especie_id)
    
    if not ficha:
        st.error("No se encontró la ficha para esta especie.")
        return

    # Información principal
    st.subheader("Ficha Principal")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Nombre científico:** {ficha.get('NombreCientifico', 'N/A')}")
        st.markdown(f"**Nombre común:** {ficha.get('NombreComun', 'N/A')}")
    with col2:
        st.markdown(f"**Categoría:** {ficha.get('Categoria', 'N/A')}")
        st.markdown(f"**IDProd:** `{ficha['IDProd']}`")

    # Documentos secundarios jerárquicos
    st.divider()
    st.subheader("Documentos Secundarios (Jerárquicos)")

    docs_secundarios = ficha.get("DocumentosSecundarios", [])
    
    if not docs_secundarios:
        st.info("Esta especie no tiene documentos secundarios registrados.")
    else:
        for i, subdoc in enumerate(docs_secundarios):
            with st.expander(f"📄 {subdoc.get('Tipo', f'Documento {i+1}')}", expanded=False):
                render_document(subdoc, 0)


if __name__ == "__main__":
    render()