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
        s.run("CREATE CONSTRAINT comment_id IF NOT EXISTS FOR (c:Comment) REQUIRE c.id IS UNIQUE")
        s.run("CREATE CONSTRAINT post_id IF NOT EXISTS FOR (p:Post) REQUIRE p.id IS UNIQUE")
        s.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
    return drv


def add_comment(user_id, user_name, post_id, text, parent_comment_id=None):
    with driver().session() as s:
        if parent_comment_id is None:
            s.run(
                "MERGE (u:User {id:$uid}) SET u.name=$uname "
                "MERGE (p:Post {id:$pid}) "
                "CREATE (c:Comment {id:randomUUID(), text:$text, author:$uname, created:datetime()}) "
                "MERGE (u)-[:WROTE]->(c) "
                "MERGE (c)-[:ON]->(p)",
                uid=user_id, uname=user_name, pid=post_id, text=text,
            )
        else:
            s.run(
                "MERGE (u:User {id:$uid}) SET u.name=$uname "
                "MATCH (parent:Comment {id:$parent}) "
                "CREATE (c:Comment {id:randomUUID(), text:$text, author:$uname, created:datetime()}) "
                "MERGE (u)-[:WROTE]->(c) "
                "MERGE (c)-[:REPLIES_TO]->(parent)",
                uid=user_id, uname=user_name, parent=parent_comment_id, text=text,
            )


def get_thread(post_id):
    with driver().session() as s:
        res = s.run(
            "MATCH (p:Post {id:$pid})<-[:ON]-(root:Comment) "
            "MATCH (root)<-[:REPLIES_TO*0..]-(c:Comment) "
            "OPTIONAL MATCH (c)-[:REPLIES_TO]->(parent:Comment) "
            "RETURN DISTINCT c.id AS id, c.text AS text, c.author AS author, c.created AS created, "
            "parent.id AS parent_id",
            pid=post_id,
        )
        return [r.data() for r in res]
