# Base de Datos AquaLife - Docker Compose

Este proyecto contiene la configuración de Docker para levantar los servicios de base de datos usados en el proyecto AquaLife:

- **MySQL** (relacional) – datos principales
- **MongoDB** (documental) – fichas de especie jerárquicas
- **Neo4j** (grafos) – hilos de conversación

---

## Archivos

- `docker-compose.yml`: Orquesta los servicios MySQL, MongoDB y Neo4j (versiones fijadas: `mongo:7`, `neo4j:5`).
- `Dockerfile`: Construye la imagen de MySQL con `init.sql` precargado (seed 33, fecha ref 2026-01-01).
- `generate_init_sql.py`: Genera `init.sql` reproducible (datos aleatorios, seed 33, ~7M filas, 1.1M comentarios).
- `scripts/migrate_neo4j.py`: Migra `Usuario`, `Publicacion` y `Comentar` de MySQL a Neo4j.
- `scripts/ficha_de_especie_mongodb.py`: Genera 4000 fichas de especie en MongoDB leyendo `Especie` + `Producto` de MySQL (mismos nombres de campo PascalCase).
- `scripts/seed_hilos_prueba.py`: Crea publicaciones de prueba con hilos profundos en MySQL y Neo4j para benchmarking.
- `000-hash-init.sh` / `zzz-cleanup.sh`: Verificación de hash y limpieza en el contenedor MySQL.
- `guidelines.tex`: Orientación del proyecto.

---

## Uso a través de Docker Compose

### 1. Solo MySQL (desarrollo de consultas SQL)
```bash
docker compose up -d mysqllab
```

### 2. Las 3 BDs principales (MySQL + MongoDB + Neo4j) — **recomendado para el proyecto completo**
```bash
docker compose up -d mysqllab mongo neo4j
```

> **Nota**: La primera vez tarda unos minutos en construir la imagen de MySQL y cargar los datos. Para ver el progreso:
> ```bash
> docker compose build --progress=plain
> docker compose up -d
> ```

---

## Verificar que la base de datos MySQL se generó correctamente

La imagen incluye un `init.sql` reproducible. Comprueba su hash SHA-256:

```bash
docker run --rm --entrypoint sh aqualife-mysql:local -c \
  "sha256sum /docker-entrypoint-initdb.d/init.sql"
```

Resultado esperado (seed 33, fecha ref 2026-01-01):
```
604efe050a6e6197c7dab8060f274792d92086ce21937acd810524e7577908e1  /docker-entrypoint-initdb.d/init.sql
```

Si el hash no coincide, reconstruye desde un clon limpio del repositorio.

---

## Índices adicionales creados

El script `generate_init_sql.py` crea 11 índices secundarios **tras la carga masiva** (no antes, para no penalizar la inserción de ~7M filas) para optimizar las consultas analíticas (3.a–3.i) y el SP `sp_analisis_usuario`.

| Índice | Consultas / SP beneficiados | Justificación |
|--------|----------------------------|---------------|
| `Comentar(IDPub, IDPadre)` | `sp_obtener_hilo_comentarios` (CTE recursivo) | Caso base `WHERE IDPub=? AND IDPadre IS NULL` + JOIN recursivo `ON respuesta.IDPadre = hilo.IDComentario AND respuesta.IDPub = hilo.IDPub`. Sin compuesto, MySQL escanea todo `IDPub`. |
| `Compra(IDUV, IDProd, Fecha)` | 3.e (top vendedores), 3.i (`variacion_mensual`, `resumen_calificaciones`) | Agrupación por vendedor + producto + fecha. |
| `Compra(IDUC, Fecha)` | SP `sp_analisis_usuario`: `total_compras`, `monto_gastado` | Filtro por comprador + rango de fechas. |
| `Publicacion(IDU, FechaCreacion)` | SP: `total_publicaciones` | Filtro por autor + rango de fechas. |
| `Reaccionar(IDU, Fecha)` | SP: `total_reacciones_dadas` | Filtro por usuario + rango de fechas. |
| `Comentar(IDU, FechaCreacion)` | SP: `total_comentarios` | Filtro por usuario + rango de fechas. |
| `Contribucion(IDU, Fecha)` | SP: `total_contribuciones` | Filtro por usuario + rango de fechas. |
| `Reaccionar(IDPub)` | 3.a, 3.b, 3.h: JOIN con `Publicacion` | FK no crea índice en tabla referenciada (MySQL 8). |
| `Contribucion(IDProd)` | 3.d, 3.h: JOIN con `Especie` | |
| `Especie(IDTA)` | 3.d: JOIN con `TipoAgua` | |
| `Compra(IDUV, Puntuacion)` | 3.i (`resumen_calificaciones`), 3.e | Agrupación y filtro por puntuaciones 1–5. |

> **Nota**: Los índices se crean **después de la inserción de datos** (sección `ÍNDICES ADICIONALES` en `generate_init_sql.py`). El `docker-compose.yml` usa configuración duradera (`innodb_flush_log_at_trx_commit=1`, `sync_binlog=1`) para que la creación sea segura.

### Verificar índices creados
```bash
docker exec aqualife_mysql mysql -uaqualife_user -paqualife_pass -D AquaLife -e "SHOW INDEX FROM Comentar; SHOW INDEX FROM Compra; SHOW INDEX FROM Publicacion; SHOW INDEX FROM Reaccionar; SHOW INDEX FROM Contribucion; SHOW INDEX FROM Especie;"
```

---

## Verificar que los contenedores están corriendo

```bash
docker compose ps
```

Deberías ver `aqualife_mysql` (healthy), `aqualife_mongo` y `aqualife_neo4j` en estado **Up**.

### Ver logs de los servicios
```bash
# Ver logs de MySQL (carga inicial, healthcheck)
docker compose logs -f mysqllab

# Ver logs de MongoDB
docker compose logs -f mongo

# Ver logs de Neo4j
docker compose logs -f neo4j

# Ver todos los logs
docker compose logs -f
```

### Ver uso de recursos
```bash
docker stats --no-stream aqualife_mysql aqualife_mongo aqualife_neo4j
```

---

## Credenciales de las 3 BDs principales

| Servicio | Tipo | Host → Puerto | Usuario / Contraseña | Base de datos |
|----------|------|---------------|----------------------|---------------|
| `mysqllab` | SQL relacional (MySQL 8.0) | `localhost:3306` | `root/root` o `aqualife_user/aqualife_pass` | `AquaLife` |
| `mongo` | NoSQL documental (MongoDB 7) | `localhost:27017` | `admin/password` (authDB: `admin`) | `AquaLifeDoc` |
| `neo4j` | NoSQL grafos (Neo4j 5) | `localhost:7474` (HTTP) / `localhost:7687` (Bolt) | `neo4j/password` | `neo4j` |

---

## Migración MySQL → Neo4j (hilos de comentarios)

Una vez que los tres contenedores estén arriba, migra los datos de `Comentar`, `Publicacion` y `Usuario` de MySQL a Neo4j:

```bash
# Migración completa (usuarios, publicaciones, 1.1M comentarios ~6 min)
python3 scripts/migrate_neo4j.py

# Solo usuarios y publicaciones (rápido, para pruebas)
python3 scripts/migrate_neo4j.py --skip-comments

# Solo verificar conteos en Neo4j
python3 scripts/migrate_neo4j.py --verify-only

# Probar sin escribir (dry-run)
python3 scripts/migrate_neo4j.py --dry-run
```

La migración es **idempotente**: se puede ejecutar múltiples veces sin duplicar datos.

---

## Carga de fichas de especie en MongoDB

Genera los 4000 documentos en la colección `fichas_especie` de la base de datos `AquaLifeDoc`. Los campos usan **PascalCase** para coincidir exactamente con los nombres de columna en SQL (`IDProd`, `NombreComun`, `NombreCientifico`, `Categoria`, `TipoSustrato`, `HorasLuz`, `LitrosMinimosTanque`, `IDTA`, `IDT`, `IDCE`, `Descripcion`, `DocumentosSecundarios`).

```bash
python3 scripts/ficha_de_especie_mongodb.py
```

Verificación rápida:
```bash
docker exec -it aqualife_mongo mongosh --username admin --password password --authenticationDatabase admin \
  --eval "db.getSiblingDB('AquaLifeDoc').fichas_especie.countDocuments({})"
# Debe devolver 4000
```

---

## Hilos de prueba para benchmarking SQL vs Neo4j

Crea publicaciones de prueba con hilos profundos/ramificados en **ambos** motores simultáneamente. El script es idempotente (borra y recrea solo el rango indicado).

```bash
# 50 publicaciones, 6 niveles (cadena), IDs 2001–2050 → 300 comentarios totales
python3 scripts/seed_hilos_prueba.py

# 1 publicación, árbol 4 respuestas × 7 niveles → 21,845 comentarios
python3 scripts/seed_hilos_prueba.py --start-pub 6001 --count 1 --branching 4 --depth 7

# 5 publicaciones, árbol ancho
python3 scripts/seed_hilos_prueba.py --start-pub 6001 --count 5 --branching 4 --depth 7
```

Luego abre la app Streamlit → **Gestor de chats** → selecciona una publicación (ej. 2001, 3001, 6001) para comparar tiempos `SQL (segundos)` vs `Neo4j (segundos)`.

---

## Verificar que todos los servicios funcionan

### MySQL
```bash
docker exec -it aqualife_mysql mysql -u aqualife_user -p
# Contraseña: aqualife_pass

# O consulta directa
docker exec aqualife_mysql mysql -uaqualife_user -paqualife_pass -D AquaLife -e "SELECT COUNT(*) FROM Comentar;"
```

### MongoDB
```bash
docker exec -it aqualife_mongo mongosh --username admin --password password --authenticationDatabase admin --eval "db.runCommand({ ping: 1 })"
# Respuesta: { ok: 1 }

# Verificar colección fichas_especie
docker exec -it aqualife_mongo mongosh --username admin --password password --authenticationDatabase admin \
  --eval "db.getSiblingDB('AquaLifeDoc').fichas_especie.findOne()"
```

### Neo4j
```bash
docker exec -it aqualife_neo4j cypher-shell -u neo4j -p password "RETURN 1 AS ok;"
# Respuesta: una fila con ok = 1
```

### Verificar migración Neo4j
```bash
docker exec -it aqualife_neo4j cypher-shell -u neo4j -p password "
MATCH (u:Usuario) RETURN count(u) AS usuarios;
MATCH (p:Publicacion) RETURN count(p) AS publicaciones;
MATCH (c:Comentar) RETURN count(c) AS comentarios;
"
```

---

## Conectar desde Jupyter Notebook (MySQL)

```python
%load_ext sql
%sql mysql://root:root@localhost:3306/AquaLife
```

O si el notebook corre en el mismo docker-compose:
```python
%load_ext sql
%sql mysql://root:root@mysqllab:3306/AquaLife
```

---

## Reiniciar la base de datos desde cero

```bash
# Detener y eliminar contenedores y volúmenes
docker compose down -v

# Volver a levantar (solo MySQL o las 3 principales)
docker compose up -d mysqllab
# o
docker compose up -d mysqllab mongo neo4j

# Volver a migrar a Neo4j
python3 scripts/migrate_neo4j.py

# Volver a cargar fichas MongoDB
python3 scripts/ficha_de_especie_mongodb.py

# Volver a crear hilos de prueba
python3 scripts/seed_hilos_prueba.py
```

---

## Comandos útiles de diagnóstico

```bash
# Ver estado de salud de MySQL
docker inspect aqualife_mysql | grep -A 5 Health

# Ver puertos expuestos
docker port aqualife_mysql
docker port aqualife_mongo
docker port aqualife_neo4j

# Entrar al contenedor MySQL
docker exec -it aqualife_mysql bash

# Ver variables de MySQL relevantes
docker exec aqualife_mysql mysql -uroot -proot -e "SHOW VARIABLES LIKE 'innodb_flush_log_at_trx_commit'; SHOW VARIABLES LIKE 'sync_binlog';"

# Ver índices de Comentar
docker exec aqualife_mysql mysql -uaqualife_user -paqualife_pass -D AquaLife -e "SHOW INDEX FROM Comentar;"

# Ver constraints en Neo4j
docker exec -it aqualife_neo4j cypher-shell -u neo4j -p password "SHOW CONSTRAINTS;"

# Verificar IDs de MongoDB coinciden con MySQL
docker exec -it aqualife_mongo mongosh --username admin --password password --authenticationDatabase admin \
  --eval "db.getSiblingDB('AquaLifeDoc').fichas_especie.findOne({}, {IDProd:1, NombreComun:1})"
```