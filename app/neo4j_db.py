#!/bin/python3

from neo4j import GraphDatabase
import streamlit as st

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"


@st.cache_resource
def driver():
    drv = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    drv.verify_connectivity()
    with drv.session() as s:
        s.run("CREATE CONSTRAINT comment_id IF NOT EXISTS FOR (c:Comment) REQUIRE c.IDComentario IS UNIQUE")
        s.run("CREATE CONSTRAINT post_id IF NOT EXISTS FOR (p:Post) REQUIRE p.IDPub IS UNIQUE")
        s.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.IDU IS UNIQUE")
    return drv


def add_comment(user_id, user_name, post_id, text, parent_comment_id=None):
    with driver().session() as s:
        if parent_comment_id is None:
            s.run(
                "MERGE (u:User {IDU:$uid}) SET u.`Nombre`=$uname "
                "MERGE (p:Post {IDPub:$pid}) "
                "CREATE (c:Comment {IDComentario:randomUUID(), Comentario:$text, FechaCreacion:datetime()}) "
                "MERGE (u)-[:WROTE]->(c) "
                "MERGE (c)-[:ON]->(p)",
                uid=user_id, uname=user_name, pid=post_id, text=text,
            )
        else:
            s.run(
                "MERGE (u:User {IDU:$uid}) SET u.`Nombre`=$uname "
                "MATCH (parent:Comment {IDComentario:$parent}) "
                "CREATE (c:Comment {IDComentario:randomUUID(), Comentario:$text, FechaCreacion:datetime()}) "
                "MERGE (u)-[:WROTE]->(c) "
                "MERGE (c)-[:REPLIES_TO]->(parent)",
                uid=user_id, uname=user_name, parent=parent_comment_id, text=text,
            )


def get_thread(post_id):
    with driver().session() as s:
        res = s.run(
            "MATCH (p:Post {IDPub:$pid})<-[:ON]-(root:Comment) "
            "MATCH (root)<-[:REPLIES_TO*0..]-(c:Comment) "
            "OPTIONAL MATCH (c)-[:REPLIES_TO]->(parent:Comment) "
            "OPTIONAL MATCH (c)<-[:WROTE]-(u:User) "
            "RETURN DISTINCT c.IDComentario AS id, c.Comentario AS text, u.IDU AS author, c.FechaCreacion AS created, "
            "parent.IDComentario AS parent_id",
            pid=post_id,
        )
        return [r.data() for r in res]