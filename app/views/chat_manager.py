#!/bin/python3

from html import escape
from time import perf_counter

import pandas as pd
import pymysql
import streamlit as st
from neo4j.exceptions import DriverError, Neo4jError

from db import connection
from neo4j_db import add_comment as add_neo4j_comment
from neo4j_db import get_thread as get_neo4j_thread
from sql_db import add_comment as add_sql_comment
from sql_db import get_thread as get_sql_thread


def _add_comment_to_both(user_name, post_id, text, parent_comment_id=None):
    user_id, comment_id, created_at = add_sql_comment(
        user_name,
        post_id,
        text,
        parent_comment_id=parent_comment_id,
    )
    try:
        add_neo4j_comment(
            user_id,
            user_name,
            post_id,
            text,
            comment_id=comment_id,
            created_at=created_at,
            parent_comment_id=parent_comment_id,
        )
    except (DriverError, Neo4jError, ValueError) as error:
        st.error(f"Guardado en SQL, pero no se pudo sincronizar con Neo4j: {error}")
        return False
    return True


def render():
    st.title("Gestor de chats / hilos de comentarios")
    st.caption("Muestra el hilo y compara automáticamente los tiempos de Neo4j y SQL.")

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

    st.subheader("Nuevo comentario en la publicación")
    with st.form("new_post_comment"):
        txt = st.text_area("Comentario")
        if st.form_submit_button("Comentar post") and txt.strip():
            if _add_comment_to_both(user_name, post_id, txt.strip()):
                st.success("Comentario agregado y sincronizado.")
                st.rerun()

    st.subheader("Hilo de comentarios")
    thread_loaders = {
        "Neo4j": get_neo4j_thread,
        "SQL": get_sql_thread,
    }
    threads = {}
    durations = {}
    errors = {}
    for backend, load_thread in thread_loaders.items():
        started = perf_counter()
        try:
            threads[backend] = load_thread(post_id)
            durations[backend] = perf_counter() - started
        except (DriverError, Neo4jError, pymysql.MySQLError) as error:
            durations[backend] = perf_counter() - started
            errors[backend] = error

    metric_columns = st.columns(2)
    for column, backend in zip(metric_columns, thread_loaders):
        if backend in errors:
            column.metric(backend, "No disponible")
            st.error(f"No se pudo obtener el hilo desde {backend}: {errors[backend]}")
        else:
            column.metric(f"{backend} (segundos)", f"{durations[backend]:.6f}")

    if "SQL" in errors:
        return

    comments = threads["SQL"]
    by_parent = {}
    for c in comments:
        by_parent.setdefault(c.get("parent_id"), []).append(c)

    def render_comment(c, level=0):
        prefix = "↳ " if level else ""
        fecha = escape(str(c.get("created", ""))[:16].replace("T", " "))
        nombre_autor = str(c.get("author") or "?")
        autor = escape(nombre_autor)
        texto = escape(str(c["text"])).replace("\n", "<br>")
        st.markdown(
            f'<div style="margin-left: {level * 24}px;">'
            f'{prefix}<strong>{autor}</strong> ({fecha}): {texto}</div>',
            unsafe_allow_html=True,
        )
        with st.expander(f"Responder a {nombre_autor}", expanded=False):
            with st.form(f"reply_{c['id']}"):
                rtxt = st.text_area("Respuesta", key=f"rtxt_{c['id']}")
                if st.form_submit_button("Responder") and rtxt.strip():
                    try:
                        added = _add_comment_to_both(
                            user_name,
                            post_id,
                            rtxt.strip(),
                            parent_comment_id=c["id"],
                        )
                    except ValueError as error:
                        st.error(str(error))
                        return
                    if added:
                        st.success("Respuesta agregada y sincronizada.")
                        st.rerun()
        for child in by_parent.get(c["id"], []):
            render_comment(child, level + 1)

    for c in by_parent.get(None, []):
        render_comment(c)


render()
