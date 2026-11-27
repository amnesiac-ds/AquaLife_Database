#!/usr/bin/env python3
"""Inserta publicaciones de prueba con hilos profundos en MySQL y Neo4j.

Por defecto crea 50 publicaciones (IDPub 2001-2050), cada una con un hilo
de 6 niveles (nivel 0 a 5). Sirve para comparar el SP recursivo de MySQL
con el traversal de Neo4j en la pagina "Gestor de chats".

Uso:
    python3 scripts/seed_hilos_prueba.py
    python3 scripts/seed_hilos_prueba.py --count 50 --depth 5
    python3 scripts/seed_hilos_prueba.py --branching 3   # arbol, no cadena

El script es idempotente: borra y vuelve a crear solo las publicaciones
del rango indicado que tengan el marcador [PRUEBA-RECURSION].
"""

import argparse
import sys
import time
from datetime import datetime, timedelta

import pymysql
from neo4j import GraphDatabase

_INICIO = time.monotonic()
MARKER = "[PRUEBA-RECURSION]"

DEFAULT_MYSQL_HOST = "localhost"
DEFAULT_MYSQL_PORT = 3306
DEFAULT_MYSQL_USER = "aqualife_user"
DEFAULT_MYSQL_PASSWORD = "aqualife_pass"
DEFAULT_MYSQL_DB = "AquaLife"

DEFAULT_NEO4J_URI = "bolt://localhost:7687"
DEFAULT_NEO4J_USER = "neo4j"
DEFAULT_NEO4J_PASSWORD = "password"


def log(mensaje: str) -> None:
    """Imprime un mensaje con el tiempo transcurrido."""
    print(f"[{time.monotonic() - _INICIO:7.2f}s] {mensaje}", flush=True)


# ---------------------------------------------------------------------------
# Conexiones
# ---------------------------------------------------------------------------

def conectar_mysql(args):
    log(f"Conectando a MySQL {args.mysql_host}:{args.mysql_port}/{args.mysql_db}...")
    conn = pymysql.connect(
        host=args.mysql_host,
        port=args.mysql_port,
        user=args.mysql_user,
        password=args.mysql_password,
        database=args.mysql_db,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    log("MySQL conectado.")
    return conn


def conectar_neo4j(args):
    log(f"Conectando a Neo4j {args.neo4j_uri}...")
    driver = GraphDatabase.driver(
        args.neo4j_uri,
        auth=(args.neo4j_user, args.neo4j_password),
    )
    driver.verify_connectivity()
    log("Neo4j conectado.")
    return driver


# ---------------------------------------------------------------------------
# Datos de prueba
# ---------------------------------------------------------------------------

def cargar_usuarios(conn):
    """Devuelve los usuarios existentes para reutilizarlos en los hilos."""
    with conn.cursor() as cur:
        cur.execute("SELECT IDU, Nombre FROM Usuario ORDER BY IDU")
        usuarios = cur.fetchall()

    if not usuarios:
        raise SystemExit(
            "No hay usuarios en MySQL. Ejecuta primero el generador de la base de datos."
        )

    log(f"Usuarios disponibles: {len(usuarios):,}")
    return usuarios


def verificar_rango(conn, start_pub: int, end_pub: int) -> None:
    """Aborta si el rango contiene publicaciones que no son de prueba."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) AS n
            FROM Publicacion
            WHERE IDPub BETWEEN %s AND %s
              AND COALESCE(Texto, '') NOT LIKE %s
            """,
            (start_pub, end_pub, f"{MARKER}%"),
        )
        ajenas = cur.fetchone()["n"]

    if ajenas:
        raise SystemExit(
            f"Hay {ajenas} publicaciones no marcadas como prueba en el rango "
            f"{start_pub}-{end_pub}. Abortando para no borrar datos reales."
        )


def construir_publicaciones(args, usuarios, ahora):
    """Construye la lista de publicaciones que se van a insertar."""
    publicaciones = []
    for i in range(args.count):
        pub_id = args.start_pub + i
        pos = (pub_id * 3) % len(usuarios)
        autor = usuarios[pos]
        publicaciones.append(
            {
                "id": pub_id,
                "texto": (
                    f"{MARKER} Hilo profundo #{pub_id} para comparar SQL vs Neo4j"
                ),
                "uid": autor["IDU"],
                "autor": autor["Nombre"],
                "fecha": ahora - timedelta(days=args.count - i),
                "depth": args.depth,
                "branching": args.branching,
            }
        )
    return publicaciones


# ---------------------------------------------------------------------------
# MySQL
# ---------------------------------------------------------------------------

def limpiar_mysql(conn, start_pub: int, end_pub: int) -> None:
    """Borra los datos de prueba anteriores. No hace commit."""
    log(f"Limpiando datos de prueba en MySQL ({start_pub}-{end_pub})...")
    with conn.cursor() as cur:
        try:
            cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            for tabla in ("Comentar", "Reaccionar", "Tener_Foto"):
                cur.execute(
                    f"DELETE FROM {tabla} WHERE IDPub BETWEEN %s AND %s",
                    (start_pub, end_pub),
                )
            cur.execute(
                "DELETE FROM Publicacion WHERE IDPub BETWEEN %s AND %s",
                (start_pub, end_pub),
            )
        finally:
            cur.execute("SET FOREIGN_KEY_CHECKS = 1")


def insertar_mysql(conn, publicaciones, usuarios):
    """Inserta publicaciones y comentarios. Devuelve la lista de comentarios."""
    log("Insertando publicaciones y comentarios en MySQL...")
    comentarios = []

    with conn.cursor() as cur:
        for pub in publicaciones:
            cur.execute(
                """
                INSERT INTO Publicacion (IDPub, Texto, IDU, IDV, FechaCreacion)
                VALUES (%s, %s, %s, NULL, %s)
                """,
                (pub["id"], pub["texto"], pub["uid"], pub["fecha"]),
            )

            # Nivel 0: comentario raiz.
            pos = (pub["id"] * 3) % len(usuarios)
            autor = usuarios[pos]
            fecha = pub["fecha"] + timedelta(minutes=1)
            texto = f"{MARKER} Nivel 0: comentario raiz del hilo #{pub['id']}"
            cur.execute(
                """
                INSERT INTO Comentar (IDU, IDPub, IDPadre, Comentario, FechaCreacion)
                VALUES (%s, %s, NULL, %s, %s)
                """,
                (autor["IDU"], pub["id"], texto, fecha),
            )
            root_id = cur.lastrowid
            comentarios.append(
                {
                    "id": root_id,
                    "pub_id": pub["id"],
                    "uid": autor["IDU"],
                    "autor": autor["Nombre"],
                    "parent_id": None,
                    "texto": texto,
                    "fecha": fecha,
                }
            )

            # Niveles 1..depth. Con branching=1 es una cadena; con 2+ es un arbol.
            padres = [root_id]
            for nivel in range(1, pub["depth"] + 1):
                siguientes_padres = []
                for rama, parent_id in enumerate(padres):
                    for b in range(pub["branching"]):
                        pos = (
                            pub["id"] * 7
                            + nivel * 11
                            + rama * 13
                            + b * 17
                        ) % len(usuarios)
                        autor = usuarios[pos]
                        fecha = pub["fecha"] + timedelta(
                            minutes=1 + nivel * 5 + b
                        )
                        texto = (
                            f"{MARKER} Nivel {nivel}: respuesta "
                            f"(rama {b + 1}) del hilo #{pub['id']}"
                        )
                        cur.execute(
                            """
                            INSERT INTO Comentar
                                (IDU, IDPub, IDPadre, Comentario, FechaCreacion)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (autor["IDU"], pub["id"], parent_id, texto, fecha),
                        )
                        comment_id = cur.lastrowid
                        comentarios.append(
                            {
                                "id": comment_id,
                                "pub_id": pub["id"],
                                "uid": autor["IDU"],
                                "autor": autor["Nombre"],
                                "parent_id": parent_id,
                                "texto": texto,
                                "fecha": fecha,
                            }
                        )
                        siguientes_padres.append(comment_id)
                padres = siguientes_padres

            total_hilo = 1 + sum(
                pub["branching"] ** n
                for n in range(1, pub["depth"] + 1)
            )
            log(f"  Publicacion #{pub['id']}: {total_hilo} comentarios")

    conn.commit()
    log(f"Comentarios insertados en MySQL: {len(comentarios):,}")
    return comentarios


# ---------------------------------------------------------------------------
# Neo4j
# ---------------------------------------------------------------------------

def limpiar_neo4j(tx, start_pub: int, end_pub: int) -> None:
    """Borra comentarios y publicaciones de prueba dentro de la transaccion."""
    log(f"Limpiando datos de prueba en Neo4j ({start_pub}-{end_pub})...")
    tx.run(
        """
        MATCH (p:Publicacion)
        WHERE p.IDPub >= $start AND p.IDPub <= $end
        MATCH (c:Comentar)-[:EN_PUBLICACION]->(p)
        DETACH DELETE c
        """,
        start=start_pub,
        end=end_pub,
    )
    tx.run(
        """
        MATCH (p:Publicacion)
        WHERE p.IDPub >= $start AND p.IDPub <= $end
        DETACH DELETE p
        """,
        start=start_pub,
        end=end_pub,
    )


def insertar_neo4j(tx, publicaciones, comentarios, batch_size=5000) -> None:
    """Inserta publicaciones, comentarios y relaciones en Neo4j."""
    log("Insertando publicaciones en Neo4j...")
    tx.run(
        """
        UNWIND $pubs AS row
        MERGE (p:Publicacion {IDPub: row.id})
        SET p.Texto = row.texto,
            p.FechaCreacion = datetime(row.fecha)
        WITH p, row
        MERGE (u:Usuario {IDU: row.uid})
        SET u.Nombre = row.autor
        MERGE (u)-[:PUBLICO]->(p)
        """,
        pubs=[
            {
                "id": pub["id"],
                "texto": pub["texto"],
                "uid": pub["uid"],
                "autor": pub["autor"],
                "fecha": pub["fecha"].isoformat(),
            }
            for pub in publicaciones
        ],
    )

    log("Insertando comentarios en Neo4j...")
    for inicio in range(0, len(comentarios), batch_size):
        lote = comentarios[inicio : inicio + batch_size]
        tx.run(
            """
            UNWIND $rows AS row
            MERGE (c:Comentar {IDComentario: row.id})
            SET c.Comentario = row.texto,
                c.FechaCreacion = datetime(row.fecha),
                c.IDPadre = row.parent_id
            WITH c, row
            MATCH (p:Publicacion {IDPub: row.pub_id})
            MERGE (c)-[:EN_PUBLICACION]->(p)
            MERGE (u:Usuario {IDU: row.uid})
            SET u.Nombre = row.autor
            MERGE (u)-[:ESCRIBIO]->(c)
            """,
            rows=[
                {
                    "id": c["id"],
                    "pub_id": c["pub_id"],
                    "uid": c["uid"],
                    "autor": c["autor"],
                    "parent_id": c["parent_id"],
                    "texto": c["texto"],
                    "fecha": c["fecha"].isoformat(),
                }
                for c in lote
            ],
        )

    log("Creando relaciones RESPONDE_A en Neo4j...")
    for inicio in range(0, len(comentarios), batch_size):
        lote = comentarios[inicio : inicio + batch_size]
        rows = [
            {"id": c["id"], "parent_id": c["parent_id"]}
            for c in lote
            if c["parent_id"] is not None
        ]
        if not rows:
            continue
        tx.run(
            """
            UNWIND $rows AS row
            MATCH (c:Comentar {IDComentario: row.id})
            MATCH (parent:Comentar {IDComentario: row.parent_id})
            MERGE (c)-[:RESPONDE_A]->(parent)
            """,
            rows=rows,
        )


# ---------------------------------------------------------------------------
# Verificacion
# ---------------------------------------------------------------------------

def verificar(args, mysql_conn, neo4j_driver) -> None:
    """Comprueba que ambos motores tienen el mismo hilo y que el SP funciona."""
    start_pub = args.start_pub
    end_pub = args.start_pub + args.count - 1
    total_esperado = 1 + sum(
        args.branching ** n for n in range(1, args.depth + 1)
    )

    with mysql_conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM Publicacion WHERE IDPub BETWEEN %s AND %s",
            (start_pub, end_pub),
        )
        pubs_mysql = cur.fetchone()["n"]

        cur.execute(
            "SELECT COUNT(*) AS n FROM Comentar WHERE IDPub BETWEEN %s AND %s",
            (start_pub, end_pub),
        )
        comentarios_mysql = cur.fetchone()["n"]

        cur.execute("CALL sp_obtener_hilo_comentarios(%s)", (start_pub,))
        hilo_sql = cur.fetchall()

    with neo4j_driver.session() as session:
        pubs_neo4j = session.run(
            """
            MATCH (p:Publicacion)
            WHERE p.IDPub >= $start AND p.IDPub <= $end
            RETURN count(p) AS n
            """,
            start=start_pub,
            end=end_pub,
        ).single()["n"]

        comentarios_neo4j = session.run(
            """
            MATCH (c:Comentar)-[:EN_PUBLICACION]->(p:Publicacion)
            WHERE p.IDPub >= $start AND p.IDPub <= $end
            RETURN count(c) AS n
            """,
            start=start_pub,
            end=end_pub,
        ).single()["n"]

        hilo_neo4j = session.run(
            """
            MATCH (p:Publicacion {IDPub: $pid})<-[:EN_PUBLICACION]-(root:Comentar)
            WHERE NOT (root)-[:RESPONDE_A]->()
            MATCH path = (c:Comentar)-[:RESPONDE_A*0..]->(root)
            MATCH (c)-[:EN_PUBLICACION]->(p)
            RETURN count(DISTINCT c) AS n
            """,
            pid=start_pub,
        ).single()["n"]

    log(f"MySQL: {pubs_mysql} publicaciones, {comentarios_mysql} comentarios")
    log(f"Neo4j: {pubs_neo4j} publicaciones, {comentarios_neo4j} comentarios")
    log(
        f"Hilo #{start_pub}: SQL={len(hilo_sql)} filas, "
        f"Neo4j={hilo_neo4j} filas (esperado={total_esperado})"
    )

    if len(hilo_sql) != total_esperado or hilo_neo4j != total_esperado:
        raise SystemExit(
            "La verificacion del hilo no coincide con lo esperado. "
            "Revisa los datos insertados."
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Inserta publicaciones de prueba con hilos profundos en MySQL y Neo4j."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--start-pub",
        type=int,
        default=2001,
        help="Primer IDPub a generar (default: 2001).",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Cantidad de publicaciones (default: 50).",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=5,
        help="Nivel maximo, base 0 (default: 5, o sea 6 niveles).",
    )
    parser.add_argument(
        "--branching",
        type=int,
        default=1,
        help="Respuestas por comentario: 1 = cadena, 2+ = arbol (default: 1).",
    )
    parser.add_argument(
        "--mysql-host", default=DEFAULT_MYSQL_HOST, help="Host MySQL."
    )
    parser.add_argument(
        "--mysql-port", type=int, default=DEFAULT_MYSQL_PORT, help="Puerto MySQL."
    )
    parser.add_argument(
        "--mysql-user", default=DEFAULT_MYSQL_USER, help="Usuario MySQL."
    )
    parser.add_argument(
        "--mysql-password", default=DEFAULT_MYSQL_PASSWORD, help="Password MySQL."
    )
    parser.add_argument(
        "--mysql-db", default=DEFAULT_MYSQL_DB, help="Base de datos MySQL."
    )
    parser.add_argument(
        "--neo4j-uri", default=DEFAULT_NEO4J_URI, help="URI Neo4j."
    )
    parser.add_argument(
        "--neo4j-user", default=DEFAULT_NEO4J_USER, help="Usuario Neo4j."
    )
    parser.add_argument(
        "--neo4j-password", default=DEFAULT_NEO4J_PASSWORD, help="Password Neo4j."
    )

    args = parser.parse_args()

    if args.count <= 0:
        raise SystemExit("--count debe ser mayor que 0.")
    if args.depth < 0:
        raise SystemExit("--depth debe ser mayor o igual que 0.")
    if args.branching < 1:
        raise SystemExit("--branching debe ser mayor o igual que 1.")

    end_pub = args.start_pub + args.count - 1
    ahora = datetime.now()

    mysql_conn = None
    neo4j_driver = None

    try:
        mysql_conn = conectar_mysql(args)
        usuarios = cargar_usuarios(mysql_conn)
        verificar_rango(mysql_conn, args.start_pub, end_pub)

        limpiar_mysql(mysql_conn, args.start_pub, end_pub)
        publicaciones = construir_publicaciones(args, usuarios, ahora)
        comentarios = insertar_mysql(mysql_conn, publicaciones, usuarios)

        neo4j_driver = conectar_neo4j(args)
        with neo4j_driver.session() as session:
            def _transaccion(tx):
                limpiar_neo4j(tx, args.start_pub, end_pub)
                insertar_neo4j(tx, publicaciones, comentarios)

            session.execute_write(_transaccion)

        verificar(args, mysql_conn, neo4j_driver)

        log(
            f"Listo. Publicaciones de prueba: {args.start_pub}-{end_pub}. "
            f"Abre 'Gestor de chats' y selecciona una de ellas."
        )

    except KeyboardInterrupt:
        log("Interrumpido por el usuario.")
        if mysql_conn:
            mysql_conn.rollback()
        sys.exit(1)
    except Exception as error:
        log(f"ERROR: {error}")
        if mysql_conn:
            mysql_conn.rollback()
        sys.exit(1)
    finally:
        if mysql_conn:
            mysql_conn.close()
            log("MySQL desconectado.")
        if neo4j_driver:
            neo4j_driver.close()
            log("Neo4j desconectado.")


if __name__ == "__main__":
    main()
