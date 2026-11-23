# Base de Datos AquaLife - Docker Compose

Este proyecto contiene la configuración de Docker para levantar los servicios de base de datos usados en el proyecto AquaLife:

- **MySQL** (relacional) – datos principales
- **MongoDB** (documental) – fichas de especie jerárquicas
- **Neo4j** (grafos) – hilos de conversación

---

## Archivos

- `docker-compose.yml`: Orquesta los servicios MySQL, MongoDB y Neo4j.
- `Dockerfile`: Construye la imagen de MySQL con `init.sql` precargado (seed 33, fecha ref 2026-01-01).
- `generate_init_sql.py`: Genera `init.sql` reproducible (datos aleatorios, seed 33).
- `scripts/migrate_neo4j.py`: Migra `Usuario`, `Publicacion` y `Comentar` de MySQL a Neo4j.
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

## 2. Verificar que la base de datos MySQL se generó correctamente

La imagen incluye un `init.sql` reproducible. Comprueba su hash SHA-256:

```bash
docker run --rm --entrypoint sh aqualife-mysql:local -c \
  "sha256sum /docker-entrypoint-initdb.d/init.sql"
```

Resultado esperado (seed 33, fecha ref 2026-01-01):
```
d7a9c8df86a3ebf5cbaa20e76c23ed9d0f1b161c85684460424aeae13555c35d  /docker-entrypoint-initdb.d/init.sql
```

Si el hash no coincide, reconstruye desde un clon limpio del repositorio.

---

## 3. Verificar que los contenedores están corriendo

```bash
docker compose ps
```

Deberías ver `aqualife_mysql` (healthy), `aqualife_mongo` y `aqualife_neo4j` en estado **Up**.

---

## 4. Credenciales de las 3 BDs principales

| Servicio | Tipo | Host → Puerto | Usuario / Contraseña | Base de datos |
|----------|------|---------------|----------------------|---------------|
| `mysqllab` | SQL relacional (MySQL 8.0) | `localhost:3306` | `root/root` o `aqualife_user/aqualife_pass` | `AquaLife` |
| `mongo` | NoSQL documental (MongoDB 7) | `localhost:27017` | `admin/password` (authDB: `admin`) | — |
| `neo4j` | NoSQL grafos (Neo4j 5) | `localhost:7474` (HTTP) / `localhost:7687` (Bolt) | `neo4j/password` | — |

---

## 5. Migración MySQL → Neo4j (hilo de comentarios)

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

## 6. Verificar que todos los servicios funcionan

### MySQL
```bash
docker exec -it aqualife_mysql mysql -u aqualife_user -p
# Contraseña: aqualife_pass
```

### MongoDB
```bash
docker exec -it aqualife_mongo mongosh --username admin --password password --authenticationDatabase admin --eval "db.runCommand({ ping: 1 })"
# Respuesta: { ok: 1 }
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

## 7. Conectar desde Jupyter Notebook (MySQL)

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

## 8. Reiniciar la base de datos desde cero

```bash
# Detener y eliminar contenedores y volúmenes
docker compose down -v

# Volver a levantar (solo MySQL o las 3 principales)
docker compose up -d mysqllab
# o
docker compose up -d mysqllab mongo neo4j

# Volver a migrar a Neo4j
python3 scripts/migrate_neo4j.py
```