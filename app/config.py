#!/bin/python3

from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
SQL_DIR = ROOT_DIR/'sql'

# ===================== Neo4j =====================
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"
# =================================================

CATALOG_NAMES = [
	'Termometro de la comunidad',
	'Publicaciones mejor recibidas por la comunidad',
	'Perfil demografico de la comunidad',
	'Tendencias de contribucion segun el tipo de agua',
	'Vendedores mejor calificados',
	'Análisis de influencers y su impacto en ventas',
	'Detección de patrones de comportamiento anómalo en vendedores',
]

CATALOG_QUERY = ['3_'+x+'.sql' for x in 'abcdehi']

CATALOG = defaultdict(str)

for i,j in zip(CATALOG_NAMES, CATALOG_QUERY):
	CATALOG[i] = j