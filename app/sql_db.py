from datetime import datetime

import pymysql

from db import connection


def add_comment(
    user_name: str,
    post_id: int,
    text: str,
    parent_comment_id: int | None = None,
) -> tuple[int, int, datetime]:
    conn = connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(
                "SELECT IDU FROM Usuario WHERE Nombre = %s ORDER BY IDU LIMIT 1",
                (user_name,),
            )
            user = cur.fetchone()

            if user:
                user_id = user["IDU"]
            else:
                cur.execute(
                    "INSERT INTO Usuario (Nombre) VALUES (%s)",
                    (user_name,),
                )
                user_id = cur.lastrowid

            if parent_comment_id is not None:
                cur.execute(
                    """
                    SELECT IDComentario
                    FROM Comentar
                    WHERE IDComentario = %s AND IDPub = %s
                    """,
                    (parent_comment_id, post_id),
                )
                if cur.fetchone() is None:
                    raise ValueError(
                        "El comentario padre no existe en esta publicación."
                    )

            cur.execute(
                """
                INSERT INTO Comentar
                    (IDU, IDPub, IDPadre, Comentario)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, post_id, parent_comment_id, text),
            )
            comment_id = cur.lastrowid
            cur.execute(
                "SELECT FechaCreacion FROM Comentar WHERE IDComentario = %s",
                (comment_id,),
            )
            created_at = cur.fetchone()["FechaCreacion"]
        conn.commit()
        return user_id, comment_id, created_at
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_thread(post_id: int) -> list[dict]:
    conn = connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("CALL sp_obtener_hilo_comentarios(%s)", (post_id,))
            return cur.fetchall()
    finally:
        conn.close()