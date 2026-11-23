#!/usr/bin/env python3
"""Migra datos de MySQL (Comentar, Publicacion, Usuario) a Neo4j.

Uso:
    python3 migrate_neo4j.py
    python3 migrate_neo4j.py --batch-size 5000 --dry-run

La migración es idempotente: se puede ejecutar múltiples veces sin duplicar datos.
Utiliza MERGE en Neo4j para nodos Usuario y Publicacion, y CREATE para Comentarios
(con IDComentario como clave única).

Estructura en Neo4j (nombres idénticos a tablas SQL):
  - Nodo :Usuario {IDU, Nombre, Email}
  - Nodo :Publicacion {IDPub, Texto, FechaCreacion}
  - Nodo :Comentar {IDComentario, Comentario, FechaCreacion, IDPadre}
  - Relación (:Usuario)-[:PUBLICO]->(:Publicacion)
  - Relación (:Usuario)-[:ESCRIBIO]->(:Comentar)
  - Relación (:Comentar)-[:EN_PUBLICACION]->(:Publicacion)
  - Relación (:Comentar)-[:RESPONDE_A]->(:Comentar)  [para respuestas con IDPadre]
"""

import argparse
import sys
import time
from datetime import datetime

import pymysql
from neo4j import GraphDatabase

_INICIO = time.monotonic()


def log(mensaje: str) -> None:
    """Imprime mensaje con timestamp transcurrido."""
    print(f"[{time.monotonic() - _INICIO:7.2f}s] {mensaje}", flush=True)


# ---------------------------------------------------------------------------
# Configuración por defecto (sobrescribible por argumentos)
# ---------------------------------------------------------------------------

DEFAULT_MYSQL_HOST = "localhost"
DEFAULT_MYSQL_PORT = 3306
DEFAULT_MYSQL_USER = "aqualife_user"
DEFAULT_MYSQL_PASSWORD = "aqualife_pass"
DEFAULT_MYSQL_DB = "AquaLife"

DEFAULT_NEO4J_URI = "bolt://localhost:7687"
DEFAULT_NEO4J_USER = "neo4j"
DEFAULT_NEO4J_PASSWORD = "password"

DEFAULT_BATCH_SIZE = 5000


# ---------------------------------------------------------------------------
# Conexiones
# ---------------------------------------------------------------------------

def conectar_mysql(host: str, port: int, user: str, password: str, database: str):
    """Abre conexión a MySQL."""
    log(f"Conectando a MySQL {host}:{port}/{database}...")
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.SSDictCursor,  # streaming para tablas grandes
        autocommit=True,
    )
    log("MySQL conectado.")
    return conn


def conectar_neo4j(uri: str, user: str, password: str):
    """Abre driver Neo4j y verifica conectividad."""
    log(f"Conectando a Neo4j {uri}...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    log("Neo4j conectado.")
    return driver


# ---------------------------------------------------------------------------
# Esquema Neo4j (constraints)
# ---------------------------------------------------------------------------

def crear_constraints(session) -> None:
    """Crea constraints de unicidad si no existen."""
    log("Creando constraints en Neo4j...")
    constraints = [
        "CREATE CONSTRAINT usuario_id IF NOT EXISTS FOR (u:Usuario) REQUIRE u.IDU IS UNIQUE",
        "CREATE CONSTRAINT publicacion_id IF NOT EXISTS FOR (p:Publicacion) REQUIRE p.IDPub IS UNIQUE",
        "CREATE CONSTRAINT comentario_id IF NOT EXISTS FOR (c:Comentar) REQUIRE c.IDComentario IS UNIQUE",
    ]
    for c in constraints:
        session.run(c)
    log("Constraints listos.")


# ---------------------------------------------------------------------------
# Migración de datos
# ---------------------------------------------------------------------------

def migrar_usuarios(mysql_conn, neo4j_session, batch_size: int, dry_run: bool) -> int:
    """Migra usuarios de MySQL a Neo4j."""
    log("Migrando usuarios...")
    cursor = mysql_conn.cursor()
    cursor.execute("""
        SELECT IDU, Nombre, Email
        FROM Usuario
    """)

    count = 0
    batch = []
    for row in cursor:
        batch.append({
            "IDU": row["IDU"],
            "Nombre": row["Nombre"],
            "Email": row["Email"],
        })
        if len(batch) >= batch_size:
            if not dry_run:
                _upsert_usuarios_batch(neo4j_session, batch)
            count += len(batch)
            log(f"  Usuarios: {count:,}")
            batch = []

    if batch:
        if not dry_run:
            _upsert_usuarios_batch(neo4j_session, batch)
        count += len(batch)

    log(f"Usuarios migrados: {count:,}")
    return count


def _upsert_usuarios_batch(session, batch: list) -> None:
    query = """
    UNWIND $batch AS row
    MERGE (u:Usuario {IDU: row.IDU})
    SET u.Nombre = row.Nombre,
        u.Email = row.Email
    """
    session.run(query, batch=batch)


def migrar_publicaciones(mysql_conn, neo4j_session, batch_size: int, dry_run: bool) -> int:
    """Migra publicaciones de MySQL a Neo4j."""
    log("Migrando publicaciones...")
    cursor = mysql_conn.cursor()
    cursor.execute("""
        SELECT IDPub, Texto, IDU, FechaCreacion
        FROM Publicacion
    """)

    count = 0
    batch = []
    for row in cursor:
        batch.append({
            "IDPub": row["IDPub"],
            "Texto": row["Texto"],
            "IDU": row["IDU"],
            "FechaCreacion": row["FechaCreacion"].isoformat() if isinstance(row["FechaCreacion"], datetime) else str(row["FechaCreacion"]),
        })
        if len(batch) >= batch_size:
            if not dry_run:
                _upsert_publicaciones_batch(neo4j_session, batch)
            count += len(batch)
            log(f"  Publicaciones: {count:,}")
            batch = []

    if batch:
        if not dry_run:
            _upsert_publicaciones_batch(neo4j_session, batch)
        count += len(batch)

    log(f"Publicaciones migradas: {count:,}")
    return count


def _upsert_publicaciones_batch(session, batch: list) -> None:
    query = """
    UNWIND $batch AS row
    MERGE (p:Publicacion {IDPub: row.IDPub})
    SET p.Texto = row.Texto,
        p.FechaCreacion = datetime(row.FechaCreacion)
    WITH p, row
    MATCH (u:Usuario {IDU: row.IDU})
    MERGE (u)-[:PUBLICO]->(p)
    """
    session.run(query, batch=batch)


def migrar_comentarios(mysql_conn, neo4j_session, batch_size: int, dry_run: bool) -> int:
    """Migra comentarios (raíces + respuestas) de MySQL a Neo4j."""
    log("Migrando comentarios...")
    cursor = mysql_conn.cursor()
    cursor.execute("""
        SELECT IDComentario, IDU, IDPub, IDPadre, Comentario, FechaCreacion
        FROM Comentar
        ORDER BY IDComentario
    """)

    count = 0
    batch = []
    for row in cursor:
        batch.append({
            "IDComentario": row["IDComentario"],
            "IDU": row["IDU"],
            "IDPub": row["IDPub"],
            "IDPadre": row["IDPadre"],
            "Comentario": row["Comentario"],
            "FechaCreacion": row["FechaCreacion"].isoformat() if isinstance(row["FechaCreacion"], datetime) else str(row["FechaCreacion"]),
        })
        if len(batch) >= batch_size:
            if not dry_run:
                _upsert_comentarios_batch(neo4j_session, batch)
            count += len(batch)
            log(f"  Comentarios: {count:,}")
            batch = []

    if batch:
        if not dry_run:
            _upsert_comentarios_batch(neo4j_session, batch)
        count += len(batch)

    log(f"Comentarios migrados: {count:,}")
    return count


def _upsert_comentarios_batch(session, batch: list) -> None:
    """Inserta/actualiza comentarios y sus relaciones (idempotente).
    Usa MERGE para todo: Usuario, Publicacion, Comentar.
    """
    query = """
    UNWIND $batch AS row
    // Asegurar que el usuario existe
    MERGE (u:Usuario {IDU: row.IDU})
    // Asegurar que la publicación existe
    MERGE (p:Publicacion {IDPub: row.IDPub})
    // Crear/actualizar el comentario (idempotente por IDComentario único)
    MERGE (c:Comentar {IDComentario: row.IDComentario})
    SET c.Comentario = row.Comentario,
        c.FechaCreacion = datetime(row.FechaCreacion),
        c.IDPadre = row.IDPadre
    // Relaciones
    MERGE (u)-[:ESCRIBIO]->(c)
    MERGE (c)-[:EN_PUBLICACION]->(p)
    // Si tiene padre, crear relación RESPONDE_A
    WITH c, row
    WHERE row.IDPadre IS NOT NULL
    MATCH (parent:Comentar {IDComentario: row.IDPadre})
    MERGE (c)-[:RESPONDE_A]->(parent)
    """
    session.run(query, batch=batch)


# ---------------------------------------------------------------------------
# Verificación post-migración
# ---------------------------------------------------------------------------

def verificar_migracion(neo4j_session) -> dict:
    """Ejecuta conteos de verificación en Neo4j."""
    log("Verificando migración...")
    queries = {
        "usuarios": "MATCH (u:Usuario) RETURN count(u) AS n",
        "publicaciones": "MATCH (p:Publicacion) RETURN count(p) AS n",
        "comentarios": "MATCH (c:Comentar) RETURN count(c) AS n",
        "rel_escrito": "MATCH ()-[:ESCRIBIO]->() RETURN count(*) AS n",
        "rel_en_publicacion": "MATCH ()-[:EN_PUBLICACION]->() RETURN count(*) AS n",
        "rel_responde_a": "MATCH ()-[:RESPONDE_A]->() RETURN count(*) AS n",
        "rel_publico": "MATCH ()-[:PUBLICO]->() RETURN count(*) AS n",
    }
    resultados = {}
    for nombre, query in queries.items():
        result = neo4j_session.run(query).single()
        resultados[nombre] = result["n"]
        log(f"  {nombre}: {resultados[nombre]:,}")
    return resultados


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Migra datos de MySQL (Comentar, Publicacion, Usuario) a Neo4j.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mysql-host", default=DEFAULT_MYSQL_HOST, help=f"Host MySQL (default: {DEFAULT_MYSQL_HOST})"
    )
    parser.add_argument(
        "--mysql-port", type=int, default=DEFAULT_MYSQL_PORT, help=f"Puerto MySQL (default: {DEFAULT_MYSQL_PORT})"
    )
    parser.add_argument(
        "--mysql-user", default=DEFAULT_MYSQL_USER, help=f"Usuario MySQL (default: {DEFAULT_MYSQL_USER})"
    )
    parser.add_argument(
        "--mysql-password", default=DEFAULT_MYSQL_PASSWORD, help=f"Password MySQL (default: {DEFAULT_MYSQL_PASSWORD})"
    )
    parser.add_argument(
        "--mysql-db", default=DEFAULT_MYSQL_DB, help=f"Base de datos MySQL (default: {DEFAULT_MYSQL_DB})"
    )
    parser.add_argument(
        "--neo4j-uri", default=DEFAULT_NEO4J_URI, help=f"URI Neo4j (default: {DEFAULT_NEO4J_URI})"
    )
    parser.add_argument(
        "--neo4j-user", default=DEFAULT_NEO4J_USER, help=f"Usuario Neo4j (default: {DEFAULT_NEO4J_USER})"
    )
    parser.add_argument(
        "--neo4j-password", default=DEFAULT_NEO4J_PASSWORD, help=f"Password Neo4j (default: {DEFAULT_NEO4J_PASSWORD})"
    )
    parser.add_argument(
        "--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help=f"Tamaño de lote (default: {DEFAULT_BATCH_SIZE})"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Solo simula, no escribe en Neo4j"
    )
    parser.add_argument(
        "--skip-users", action="store_true", help="Saltar migración de usuarios"
    )
    parser.add_argument(
        "--skip-posts", action="store_true", help="Saltar migración de publicaciones"
    )
    parser.add_argument(
        "--skip-comments", action="store_true", help="Saltar migración de comentarios"
    )
    parser.add_argument(
        "--verify-only", action="store_true", help="Solo verifica conteos en Neo4j"
    )

    args = parser.parse_args()

    if args.dry_run:
        log("=== MODO DRY-RUN: no se escribirá en Neo4j ===")

    mysql_conn = None
    neo4j_driver = None

    try:
        # Conexiones
        mysql_conn = conectar_mysql(
            args.mysql_host, args.mysql_port, args.mysql_user, args.mysql_password, args.mysql_db
        )
        neo4j_driver = conectar_neo4j(args.neo4j_uri, args.neo4j_user, args.neo4j_password)

        with neo4j_driver.session() as session:
            if args.verify_only:
                verificar_migracion(session)
                return

            # Constraints
            if not args.dry_run:
                crear_constraints(session)

            # Migración en orden: usuarios -> publicaciones -> comentarios
            if not args.skip_users:
                migrar_usuarios(mysql_conn, session, args.batch_size, args.dry_run)

            if not args.skip_posts:
                migrar_publicaciones(mysql_conn, session, args.batch_size, args.dry_run)

            if not args.skip_comments:
                migrar_comentarios(mysql_conn, session, args.batch_size, args.dry_run)

            # Verificación final
            if not args.dry_run:
                verificar_migracion(session)
            else:
                log("Dry-run completado. No se escribió nada en Neo4j.")

    except KeyboardInterrupt:
        log("Interrumpido por el usuario.")
        sys.exit(1)
    except Exception as e:
        log(f"ERROR: {e}")
        sys.exit(1)
    finally:
        if mysql_conn:
            mysql_conn.close()
            log("MySQL desconectado.")
        if neo4j_driver:
            neo4j_driver.close()
            log("Neo4j desconectado.")

    log("Migración finalizada.")


if __name__ == "__main__":
    main()