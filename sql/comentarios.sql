USE AquaLife;

ALTER TABLE Usuario
    MODIFY COLUMN IDU INT(11) NOT NULL AUTO_INCREMENT,
    MODIFY COLUMN Nombre VARCHAR(50) NOT NULL,
    MODIFY COLUMN DireccionParticular VARCHAR(50) NULL,
    MODIFY COLUMN Email VARCHAR(50) NULL,
    MODIFY COLUMN FechaDeNacimiento DATE NULL,
    MODIFY COLUMN Notificaciones CHAR(17) NULL,
    MODIFY COLUMN ConfiguracionDePrivacidad CHAR(30) NULL;

DROP PROCEDURE IF EXISTS sp_obtener_hilo_comentarios;

DELIMITER $$

CREATE PROCEDURE sp_obtener_hilo_comentarios(IN p_IDPub INT)
BEGIN
    WITH RECURSIVE Hilo AS (
        SELECT
            c.IDComentario,
            c.IDU,
            c.IDPub,
            c.IDPadre,
            c.Comentario,
            c.FechaCreacion,
            0 AS Nivel
        FROM Comentar AS c
        WHERE c.IDPub = p_IDPub
          AND c.IDPadre IS NULL

        UNION ALL

        SELECT
            respuesta.IDComentario,
            respuesta.IDU,
            respuesta.IDPub,
            respuesta.IDPadre,
            respuesta.Comentario,
            respuesta.FechaCreacion,
            hilo.Nivel + 1
        FROM Comentar AS respuesta
        INNER JOIN Hilo AS hilo
            ON respuesta.IDPadre = hilo.IDComentario
           AND respuesta.IDPub = hilo.IDPub
    )
    SELECT
        hilo.IDComentario AS id,
        hilo.IDPadre AS parent_id,
        hilo.Comentario AS text,
        usuario.Nombre AS author,
        hilo.FechaCreacion AS created,
        hilo.Nivel AS level
    FROM Hilo AS hilo
    INNER JOIN Usuario AS usuario
        ON usuario.IDU = hilo.IDU
    ORDER BY hilo.IDComentario;
END$$

DELIMITER ;