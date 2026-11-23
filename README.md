# AquaLife Database - Proyecto Final Bases de Datos

[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.0-008CC1?logo=neo4j&logoColor=white)](https://neo4j.com/)
[![Docker](https://img.shields.io/badge/Docker-24.0-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.65-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📑 Índice

- [Descripción del proyecto](#-descripción-del-proyecto)
- [Instalación y ejecución](#-instalación-y-ejecución)
- [Consultas SQL disponibles](#-consultas-sql-disponibles)
- [Estructura del repositorio](#-estructura-del-repositorio)
- [Autores](#-autores)
- [Licencia](#-licencia)

---

## 📖 Descripción del proyecto

**AquaLife** es el proyecto final de la asignatura de Bases de Datos. Implementa un sistema de información para una comunidad acuática que combina múltiples paradigmas de bases de datos:

- **Relacional (MySQL)**: Modelo principal con usuarios, publicaciones, reacciones, compras, contribuciones, especies y productos.
- **Documental (MongoDB)**: Almacenamiento jerárquico de fichas de especie con documentos secundarios variables.
- **Grafos (Neo4j)**: Modelo de conversaciones en hilos (comentarios y respuestas anidadas).

La aplicación **Streamlit** (`app/`) proporciona un dashboard interactivo para ejecutar consultas, analizar usuarios, gestionar hilos de comentarios, explorar documentos y auditar precios.

> **Nota**: Los detalles técnicos, comparativas entre SGBD y justificaciones de diseño se encuentran en el **Informe Técnico** (entregable separado).

---

## 🚀 Instalación y ejecución

### 1. Configuración de las bases de datos

Toda la configuración detallada de los servicios (MySQL, MongoDB, Neo4j), credenciales, comandos de verificación y reinicio se encuentra en el README de la base de datos:

👉 **[config_database/README.md](config_database/README.md)**

Allí encontrarás:

- Cómo construir e iniciar los contenedores con Docker Compose
- Credenciales y puertos de cada servicio
- Comandos para verificar que todos responden correctamente
- Cómo reiniciar la base de datos desde cero

### 2. Aplicación Streamlit

```bash
# Instalar dependencias Python (recomendado: entorno virtual)
pip install -r requirements.txt

# Lanzar la app
streamlit run app/main.py
```

> **Importante**: En la barra lateral de la app introduce tu nombre de usuario para que funcionen los módulos de chat (Neo4j) y auditoría de precios.

---

## 🗃️ Consultas SQL disponibles

| Archivo     | Tarea | Descripción                                                                |
| ----------- | ----- | --------------------------------------------------------------------------- |
| `3_a.sql` | 3.a   | Termómetro: reacciones totales por publicación con datos del post y autor |
| `3_b.sql` | 3.b   | Publicaciones mejor recibidas: reacciones positivas vs negativas            |
| `3_c.sql` | 3.c   | Perfil demográfico: distribución de edades en rangos de 10 años          |
| `3_d.sql` | 3.d   | Tendencias por tipo de agua: bitácoras de mantenimiento                    |
| `3_e.sql` | 3.e   | Top 5 vendedores mejor calificados                                          |
| `3_f.sql` | 3.f   | Trigger `tgr_auditar_precio` + tabla `Historial_Precios`                |
| `3_g.sql` | 3.g   | SP `sp_analisis_usuario(id_usuario, fecha_inicio, fecha_fin)`             |
| `3_h.sql` | 3.h   | Top 5 influencers, especies top, lift de ventas, tasa conversión           |
| `3_i.sql` | 3.i   | Detección de patrones anómalos en vendedores (Índice de Sospecha)        |

Todas las consultas usan **SQL nativo** (sin ORM) y son reproducibles con la seed **33** / fecha referencia **2026-01-01**.

---

## 📁 Estructura del repositorio

```text
AquaLife_Database/
├── app/                          # Aplicación Streamlit
│   ├── main.py                   # Punto de entrada y navegación
│   ├── config.py                 # Catálogo de consultas y rutas
│   ├── db.py                     # Conexión a MySQL (pymysql)
│   ├── neo4j_db.py               # Conexión y operaciones Neo4j
│   └── views/                    # Módulos de la UI
│       ├── home.py               # Página de bienvenida
│       ├── query_selector.py     # Selector y ejecución de consultas SQL
│       ├── user_analysis.py      # Análisis de usuario (sp_analisis_usuario)
│       ├── chat_manager.py       # Gestor de hilos de comentarios (Neo4j)
│       ├── doc_explorer.py       # Explorador de documentos jerárquicos (MongoDB)
│       └── product_price_manager.py # Gestor de precios y auditoría
├── config_database/              # Generación y carga de MySQL
│   ├── generate_init_sql.py      # Script Python que genera init.sql (seed 33)
│   ├── Dockerfile                # Imagen MySQL con init.sql precargado
│   ├── 000-hash-init.sh          # Verifica hash SHA-256 de init.sql
│   ├── zzz-cleanup.sh            # Limpia init.sql tras la carga
│   └── README.md                 # Configuración detallada de BDs
├── sql/                          # Consultas y objetos de BD
│   ├── 3_a.sql – 3_e.sql         # Consultas básicas/intermedias
│   ├── 3_f.sql                   # Trigger auditoría de precios
│   ├── 3_g.sql                   # SP sp_analisis_usuario
│   ├── 3_h.sql                   # Análisis influencers y ventas
│   ├── 3_i.sql                   # Detección patrones anómalos vendedores
│   └── Historial_Precios.sql     # Tabla de auditoría
├── scripts/                      # Scripts auxiliares (ej. migración Neo4j)
├── DOCS/                         # Documentación del proyecto
│   ├── 260915 Orientación Proy Final.pdf
│   └── (MERX, Informe Técnico, etc.)
├── docker-compose.yml            # Orquestación de todos los servicios
├── requirements.txt              # Dependencias Python
├── todo's.md                     # Lista de tareas del proyecto
└── README.md                     # Este archivo
```

---

## 👥 Autores

| Nombre (GitHub)                                        | Rol                                                                                                                                                        |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [**amnesiac-ds**](https://github.com/amnesiac-ds) | **SQL completo (Ejercicio 3)**: consultas 3_a–3_i, triggers, stored procedures, fixes esquema BD, migraciones.                                      |
| [**fcd06**](https://github.com/fcd06)             | **Neo4j completo (Ejercicio 4)**: modelo grafos, consultas Cypher, hilos de conversación, módulo Streamlit `chat_manager.py.`                    |
| [**darioqr**](https://github.com/darioqr)         | **MongoDB completo (Ejercicio 5)**: modelo documental, fichas de especie, documentos jerárquicos, consultas, módulo Streamlit `doc_explorer.py`. |

---

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

Proyecto académico para la asignatura **Bases de Datos** — Curso 2026.
