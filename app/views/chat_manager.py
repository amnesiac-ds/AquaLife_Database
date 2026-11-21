#!/bin/python3

import pandas as pd
import streamlit as st
from db import connection
from neo4j_db import add_comment, get_thread


def render():
    st.title("Gestor de chats / hilos de comentarios (Neo4j)")
    st.caption("Comenta publicaciones y responde a comentarios creando hilos.")

    conn = connection()
    try:
        posts = pd.read_sql("SELECT IDPub, Texto, IDU FROM Publicacion ORDER BY IDPub DESC", conn)
    finally:
        conn.close()

    if posts.empty:
        st.info("No hay publicaciones.")
        return

    post_labels = posts.apply(lambda r: f"#{r['IDPub']} - {str(r['Texto'])[:60]}", axis=1).tolist()
    idx = st.selectbox("Publicación", range(len(post_labels)), format_func=lambda i: post_labels[i])
    post_id = int(posts.iloc[idx]["IDPub"])

    user_name = st.session_state.get("nombre_usuario", "").strip()
    if not user_name:
        st.warning("Introduce tu nombre en la barra lateral.")
        return

    user_id = user_name

    st.subheader("Nuevo comentario en la publicación")
    with st.form("new_post_comment"):
        txt = st.text_area("Comentario")
        if st.form_submit_button("Comentar post") and txt.strip():
            add_comment(user_id, user_name, post_id, txt.strip())
            st.success("Comentario agregado.")
            st.rerun()

    st.subheader("Hilo de comentarios")
    comments = get_thread(post_id)
    by_parent = {}
    author_by_id = {}
    for c in comments:
        by_parent.setdefault(c.get("parent_id"), []).append(c)
        author_by_id[c["id"]] = c.get("author", "?")

    def render_comment(c, level=0, parent_author=None):
        prefix = "↳ " if level else ""
        fecha = str(c.get("created", ""))[:16].replace("T", " ")
        st.markdown(f"{'&nbsp;&nbsp;&nbsp;&nbsp;' * level}{prefix}**{c.get('author','?')}** ({fecha}): {c['text']}", unsafe_allow_html=True)
        with st.expander(f"Responder a {c.get('author','?')}", expanded=False):
            with st.form(f"reply_{c['id']}"):
                rtxt = st.text_area("Respuesta", key=f"rtxt_{c['id']}")
                if st.form_submit_button("Responder") and rtxt.strip():
                    add_comment(user_id, user_name, post_id, rtxt.strip(), parent_comment_id=c["id"])
                    st.success("Respuesta agregada.")
                    st.rerun()
        for child in by_parent.get(c["id"], []):
            render_comment(child, level + 1, parent_author=c.get("author"))

    for c in by_parent.get(None, []):
        render_comment(c)


render()
