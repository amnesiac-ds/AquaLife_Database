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


def add_comment(user_id, user_name, post_id, text, parent_comment_id=None):
    with driver().session() as s:
        if parent_comment_id is None:
            s.run(
                "MERGE (u:Usuario {IDU:$uid}) SET u.Nombre=$uname "
                "MERGE (p:Publicacion {IDPub:$pid}) "
                "CREATE (c:Comentar {IDComentario:randomUUID(), Comentario:$text, FechaCreacion:datetime()}) "
                "MERGE (u)-[:ESCRIBIO]->(c) "
                "MERGE (c)-[:EN_PUBLICACION]->(p)",
                uid=user_id, uname=user_name, pid=post_id, text=text,
            )
        else:
            s.run(
                "MERGE (u:Usuario {IDU:$uid}) SET u.Nombre=$uname "
                "MERGE (p:Publicacion {IDPub:$pid}) "
                "MATCH (parent:Comentar {IDComentario:$parent}) "
                "CREATE (c:Comentar {IDComentario:randomUUID(), Comentario:$text, FechaCreacion:datetime(), IDPadre:$parent}) "
                "MERGE (u)-[:ESCRIBIO]->(c) "
                "MERGE (c)-[:EN_PUBLICACION]->(p) "
                "MERGE (c)-[:RESPONDE_A]->(parent)",
                uid=user_id, uname=user_name, pid=post_id, parent=parent_comment_id, text=text,
            )


def get_thread(post_id):
    with driver().session() as s:
        res = s.run(
            "MATCH (p:Publicacion {IDPub:$pid})<-[:EN_PUBLICACION]-(root:Comentar) "
            "MATCH (root)<-[:RESPONDE_A*0..]-(c:Comentar) "
            "OPTIONAL MATCH (c)-[:RESPONDE_A]->(parent:Comentar) "
            "OPTIONAL MATCH (c)<-[:ESCRIBIO]-(u:Usuario) "
            "RETURN DISTINCT c.IDComentario AS id, c.Comentario AS text, u.IDU AS author, c.FechaCreacion AS created, "
            "parent.IDComentario AS parent_id",
            pid=post_id,
        )
        return [r.data() for r in res]