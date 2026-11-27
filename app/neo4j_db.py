#!/bin/python3

from neo4j import GraphDatabase
import streamlit as st

from config import (
    NEO4J_URI, 
    NEO4J_USER, 
    NEO4J_PASSWORD
)


@st.cache_resource
def driver():
    drv = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    drv.verify_connectivity()
    with drv.session() as s:
        s.run("CREATE CONSTRAINT comentario_id IF NOT EXISTS FOR (c:Comentar) REQUIRE c.IDComentario IS UNIQUE")
        s.run("CREATE CONSTRAINT publicacion_id IF NOT EXISTS FOR (p:Publicacion) REQUIRE p.IDPub IS UNIQUE")
        s.run("CREATE CONSTRAINT usuario_id IF NOT EXISTS FOR (u:Usuario) REQUIRE u.IDU IS UNIQUE")
    return drv


def add_comment(
    user_id,
    user_name,
    post_id,
    text,
    comment_id,
    created_at,
    parent_comment_id=None,
):
    params = {
        "uid": user_id,
        "uname": user_name,
        "pid": post_id,
        "cid": comment_id,
        "text": text,
        "created": created_at.isoformat(),
    }

    with driver().session() as s:
        if parent_comment_id is None:
            query = (
                "MERGE (u:Usuario {IDU:$uid}) SET u.Nombre=$uname "
                "MERGE (p:Publicacion {IDPub:$pid}) "
                "MERGE (c:Comentar {IDComentario:$cid}) "
                "SET c.Comentario=$text, c.FechaCreacion=datetime($created) "
                "REMOVE c.IDPadre "
                "MERGE (u)-[:ESCRIBIO]->(c) "
                "MERGE (c)-[:EN_PUBLICACION]->(p)"
            )
        else:
            parent_exists = s.run(
                """
                MATCH (parent:Comentar {IDComentario: $parent})
                    -[:EN_PUBLICACION]->(p:Publicacion {IDPub: $pid})
                RETURN count(parent) AS count
                """,
                parent=parent_comment_id,
                pid=post_id,
            ).single()["count"]

            if not parent_exists:
                raise ValueError(
                    "El comentario padre no existe en esa publicación."
                )
            if not parent_exists:
                raise ValueError("El comentario padre no existe en Neo4j.")

            params["parent"] = parent_comment_id
            query = (
                "MATCH (parent:Comentar {IDComentario:$parent}) "
                "MERGE (u:Usuario {IDU:$uid}) SET u.Nombre=$uname "
                "MERGE (p:Publicacion {IDPub:$pid}) "
                "MERGE (c:Comentar {IDComentario:$cid}) "
                "SET c.Comentario=$text, c.FechaCreacion=datetime($created), "
                "c.IDPadre=$parent "
                "MERGE (u)-[:ESCRIBIO]->(c) "
                "MERGE (c)-[:EN_PUBLICACION]->(p) "
                "MERGE (c)-[:RESPONDE_A]->(parent)"
            )
        s.run(query, **params).consume()



def get_thread(post_id):
    # Se devuelve el hilo completo como una sola fila con una lista de mapas.
    # Asi el driver decodifica un registro en lugar de miles, que es el
    # cuello de botella al recuperar hilos grandes.
    with driver().session() as s:
        res = s.run(
            """
            MATCH (p:Publicacion {IDPub: $pid})
                <-[:EN_PUBLICACION]-(root:Comentar)
            WHERE NOT (root)-[:RESPONDE_A]->()

            MATCH path = (root)<-[:RESPONDE_A*0..]-(c:Comentar)
            OPTIONAL MATCH (c)<-[:ESCRIBIO]-(u:Usuario)

            WITH c, u, length(path) AS level
            ORDER BY c.IDComentario
            RETURN collect({
                id: c.IDComentario,
                parent_id: c.IDPadre,
                text: c.Comentario,
                author: u.Nombre,
                created: toString(c.FechaCreacion),
                level: level
            }) AS rows
            """,
            pid=post_id,
        )
        record = res.single()
        return record["rows"] if record else []
