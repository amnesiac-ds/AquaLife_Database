WITH variacion_mensual AS (
    SELECT
        IDUV,
        IDProd,
        YEAR(Fecha) AS anio,
        MONTH(Fecha) AS mes,
        MIN(Precio) AS precio_minimo,
        MAX(Precio) AS precio_maximo
    FROM Compra
    GROUP BY IDUV, IDProd, YEAR(Fecha), MONTH(Fecha)
    HAVING MIN(Precio) > 0
        AND (MAX(Precio) - MIN(Precio)) / MIN(Precio) > 0.30
),
evidencia_precios AS (
    SELECT
        ps.IDUV,
        GROUP_CONCAT(
            DISTINCT CONCAT(
                pr.Nombre, ' (', ps.anio, '-', LPAD(ps.mes, 2, '0'),
                ': ', ROUND(ps.precio_minimo, 2), ' a ',
                ROUND(ps.precio_maximo, 2), ', variación ',
                ROUND((ps.precio_maximo - ps.precio_minimo)
                    / ps.precio_minimo * 100, 1), '%)'
            )
            SEPARATOR '; '
        ) AS detalle
    FROM variacion_mensual AS ps
    JOIN Producto AS pr ON pr.IDProd = ps.IDProd
    GROUP BY ps.IDUV
),
resumen_calificaciones AS (
    SELECT
        IDUV,
        IDProd,
        COUNT(Puntuacion) AS calificaciones,
        SUM(CASE WHEN Puntuacion = 1 THEN 1 ELSE 0 END) AS puntuaciones_1,
        SUM(CASE WHEN Puntuacion = 5 THEN 1 ELSE 0 END) AS puntuaciones_5,
        SUM(CASE WHEN Puntuacion BETWEEN 2 AND 4 THEN 1 ELSE 0 END)
            AS puntuaciones_intermedias
    FROM Compra
    WHERE Puntuacion BETWEEN 1 AND 5
    GROUP BY IDUV, IDProd
    HAVING COUNT(Puntuacion) >= 5
        AND SUM(CASE WHEN Puntuacion = 1 THEN 1 ELSE 0 END)
            / COUNT(Puntuacion) >= 0.30
        AND SUM(CASE WHEN Puntuacion = 5 THEN 1 ELSE 0 END)
            / COUNT(Puntuacion) >= 0.30
        AND SUM(CASE WHEN Puntuacion BETWEEN 2 AND 4 THEN 1 ELSE 0 END)
            / COUNT(Puntuacion) <= 0.20
),
evidencia_calificaciones AS (
    SELECT
        rc.IDUV,
        GROUP_CONCAT(
            DISTINCT CONCAT(
                pr.Nombre, ' (', rc.calificaciones, ' calificaciones: ',
                rc.puntuaciones_1, ' de 1, ', rc.puntuaciones_5,
                ' de 5, ', rc.puntuaciones_intermedias, ' intermedias)'
            )
            SEPARATOR '; '
        ) AS detalle
    FROM resumen_calificaciones AS rc
    JOIN Producto AS pr ON pr.IDProd = rc.IDProd
    GROUP BY rc.IDUV
),
productos_por_comprador AS (
    SELECT IDUC, COUNT(DISTINCT IDProd) AS productos_distintos
    FROM Compra
    GROUP BY IDUC
),
compradores_vendedor AS (
    SELECT
        c.IDUV,
        COUNT(DISTINCT c.IDUC) AS compradores,
        COUNT(DISTINCT CASE
            WHEN pc.productos_distintos > 1 THEN c.IDUC
        END) AS compradores_con_otros_productos
    FROM Compra AS c
    JOIN productos_por_comprador AS pc ON pc.IDUC = c.IDUC
    GROUP BY c.IDUV
),
resumen_vendedor_producto AS (
    SELECT
        IDUV,
        IDProd,
        COUNT(*) AS compras,
        AVG(Precio) AS precio_promedio,
        SUM(Cantidad) AS unidades_vendidas,
        AVG(Puntuacion) AS puntuacion_promedio
    FROM Compra
    GROUP BY IDUV, IDProd
    HAVING COUNT(*) >= 3
),
resumen_producto AS (
    SELECT
        IDProd,
        COUNT(*) AS vendedores,
        SUM(precio_promedio) AS suma_precios,
        SUM(unidades_vendidas) AS suma_unidades,
        SUM(puntuacion_promedio) AS suma_calificaciones,
        COUNT(puntuacion_promedio) AS vendedores_calificados
    FROM resumen_vendedor_producto
    GROUP BY IDProd
    HAVING COUNT(*) >= 2
),
comparacion_vendedores AS (
    SELECT
        propio.IDUV,
        propio.IDProd,
        propio.precio_promedio,
        propio.unidades_vendidas,
        propio.puntuacion_promedio,
        rp.vendedores - 1 AS vendedores_comparables,
        (rp.suma_precios - propio.precio_promedio)
            / (rp.vendedores - 1) AS precio_promedio_otros_vendedores,
        (rp.suma_unidades - propio.unidades_vendidas)
            / (rp.vendedores - 1) AS unidades_promedio_otros_vendedores,
        CASE
            WHEN rp.vendedores_calificados
                - CASE WHEN propio.puntuacion_promedio IS NOT NULL
                    THEN 1 ELSE 0 END > 0
            THEN (rp.suma_calificaciones
                - COALESCE(propio.puntuacion_promedio, 0))
                / (rp.vendedores_calificados
                    - CASE WHEN propio.puntuacion_promedio IS NOT NULL
                        THEN 1 ELSE 0 END)
        END AS puntuacion_promedio_otros_vendedores
    FROM resumen_vendedor_producto AS propio
    JOIN resumen_producto AS rp ON rp.IDProd = propio.IDProd
),
patrones_distintos AS (
    SELECT
        cv.IDUV,
        cv.IDProd,
        CONCAT_WS(
            ', ',
            CASE
                WHEN cv.precio_promedio_otros_vendedores > 0
                    AND ABS(cv.precio_promedio
                        - cv.precio_promedio_otros_vendedores)
                        / cv.precio_promedio_otros_vendedores > 0.30
                THEN CONCAT(
                    'precio medio ', ROUND(cv.precio_promedio, 2),
                    ' vs otros vendedores ',
                    ROUND(cv.precio_promedio_otros_vendedores, 2),
                    ' (', ROUND((
                        cv.precio_promedio
                        - cv.precio_promedio_otros_vendedores
                    ) / cv.precio_promedio_otros_vendedores * 100, 1), '%)'
                )
            END,
            CASE
                WHEN cv.unidades_promedio_otros_vendedores > 0
                    AND (cv.unidades_vendidas
                            > 2 * cv.unidades_promedio_otros_vendedores
                        OR cv.unidades_vendidas
                            < 0.5 * cv.unidades_promedio_otros_vendedores)
                THEN CONCAT(
                    'unidades vendidas ', cv.unidades_vendidas,
                    ' vs promedio de otros vendedores ',
                    ROUND(cv.unidades_promedio_otros_vendedores, 1)
                )
            END,
            CASE
                WHEN cv.puntuacion_promedio IS NOT NULL
                    AND cv.puntuacion_promedio_otros_vendedores IS NOT NULL
                    AND ABS(cv.puntuacion_promedio
                        - cv.puntuacion_promedio_otros_vendedores) >= 1.5
                THEN CONCAT(
                    'calificación media ',
                    ROUND(cv.puntuacion_promedio, 2),
                    ' vs otros vendedores ',
                    ROUND(cv.puntuacion_promedio_otros_vendedores, 2)
                )
            END
        ) AS detalle
    FROM comparacion_vendedores AS cv
    WHERE (cv.precio_promedio_otros_vendedores > 0
            AND ABS(cv.precio_promedio
                - cv.precio_promedio_otros_vendedores)
                / cv.precio_promedio_otros_vendedores > 0.30)
        OR (cv.unidades_promedio_otros_vendedores > 0
            AND (cv.unidades_vendidas
                    > 2 * cv.unidades_promedio_otros_vendedores
                OR cv.unidades_vendidas
                    < 0.5 * cv.unidades_promedio_otros_vendedores))
        OR (cv.puntuacion_promedio IS NOT NULL
            AND cv.puntuacion_promedio_otros_vendedores IS NOT NULL
            AND ABS(cv.puntuacion_promedio
                - cv.puntuacion_promedio_otros_vendedores) >= 1.5)
),
evidencia_patrones AS (
    SELECT
        pd.IDUV,
        GROUP_CONCAT(
            DISTINCT CONCAT(pr.Nombre, ' (', pd.detalle, ')')
            SEPARATOR '; '
        ) AS detalle
    FROM patrones_distintos AS pd
    JOIN Producto AS pr ON pr.IDProd = pd.IDProd
    GROUP BY pd.IDUV
),
vendedores AS (
    SELECT
        u.IDU AS IDUV,
        u.Nombre,
        ep.detalle AS evidencia_precios,
        ec.detalle AS evidencia_calificaciones,
        CASE
            WHEN cv.compradores >= 5
                AND cv.compradores_con_otros_productos / cv.compradores <= 0.20
            THEN CONCAT(
                cv.compradores_con_otros_productos, ' de ', cv.compradores,
                ' compradores también compraron otro producto (',
                ROUND(cv.compradores_con_otros_productos
                    / cv.compradores * 100, 1), '%)'
            )
        END AS evidencia_compradores,
        epat.detalle AS evidencia_patrones
    FROM Usuario AS u
    LEFT JOIN evidencia_precios AS ep ON ep.IDUV = u.IDU
    LEFT JOIN evidencia_calificaciones AS ec ON ec.IDUV = u.IDU
    LEFT JOIN compradores_vendedor AS cv ON cv.IDUV = u.IDU
    LEFT JOIN evidencia_patrones AS epat ON epat.IDUV = u.IDU
),
sospecha AS (
    SELECT
        IDUV,
        Nombre,
        (
            CASE WHEN evidencia_precios IS NOT NULL THEN 30 ELSE 0 END
            + CASE WHEN evidencia_calificaciones IS NOT NULL THEN 25 ELSE 0 END
            + CASE WHEN evidencia_compradores IS NOT NULL THEN 20 ELSE 0 END
            + CASE WHEN evidencia_patrones IS NOT NULL THEN 25 ELSE 0 END
        ) AS indice_sospecha,
        evidencia_precios,
        evidencia_calificaciones,
        evidencia_compradores,
        evidencia_patrones
    FROM vendedores
    WHERE evidencia_precios IS NOT NULL
        OR evidencia_calificaciones IS NOT NULL
        OR evidencia_compradores IS NOT NULL
        OR evidencia_patrones IS NOT NULL
)
SELECT
    '1. Variación de precios' AS tipo_analisis,
    IDUV,
    Nombre AS vendedor,
    indice_sospecha,
    evidencia_precios AS evidencias
FROM sospecha
WHERE evidencia_precios IS NOT NULL
UNION ALL
SELECT
    '2. Calificaciones polarizadas',
    IDUV,
    Nombre,
    indice_sospecha,
    evidencia_calificaciones
FROM sospecha
WHERE evidencia_calificaciones IS NOT NULL
UNION ALL
SELECT
    '3. Baja actividad de compradores',
    IDUV,
    Nombre,
    indice_sospecha,
    evidencia_compradores
FROM sospecha
WHERE evidencia_compradores IS NOT NULL
UNION ALL
SELECT
    '4. Patrón distinto al de otros vendedores',
    IDUV,
    Nombre,
    indice_sospecha,
    evidencia_patrones
FROM sospecha
WHERE evidencia_patrones IS NOT NULL
ORDER BY tipo_analisis, indice_sospecha DESC, IDUV;
