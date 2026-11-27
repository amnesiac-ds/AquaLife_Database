#!/bin/python3

import streamlit as st
from config import CATALOG
from db import execute_dql
from pathlib import Path

DDL_KEYWORDS = ('CREATE TRIGGER', 'CREATE PROCEDURE', 'CREATE FUNCTION', 'ALTER', 'DROP')

def is_ddl_file(query_file: str) -> bool:
	"""Detecta si el archivo SQL contiene DDL (trigger, procedure, etc.)."""
	sql_path = Path(__file__).resolve().parent.parent.parent / 'sql' / query_file
	if not sql_path.exists():
		return False
	text = sql_path.read_text(encoding='utf-8').upper()
	return any(kw in text for kw in DDL_KEYWORDS)

name = st.selectbox('Consulta', CATALOG.keys())
query_file = CATALOG[name]

with st.spinner('Ejecutando..'):
	if is_ddl_file(query_file):
		# Mostrar el SQL del objeto (trigger, procedure)
		sql_path = Path(__file__).resolve().parent.parent.parent / 'sql' / query_file
		if sql_path.exists():
			sql_text = sql_path.read_text(encoding='utf-8')
			st.code(sql_text, language='sql')
			st.info('Este es un objeto de base de datos (trigger/procedure). Se ejecuta automáticamente al cargar init.sql.')
		else:
			st.error(f'Archivo no encontrado: {sql_path}')
	else:
		df = execute_dql(query_file)
		if query_file == '3_i.sql':
			tablas = [
				(
					'1. Variación de precios',
					'1. Variación de precios (>30% en el mismo mes)',
				),
				(
					'2. Calificaciones polarizadas',
					'2. Calificaciones extremadamente polarizadas',
				),
				(
					'3. Baja actividad de compradores',
					'3. Compradores con poca actividad en la plataforma',
				),
				(
					'4. Patrón distinto al de otros vendedores',
					'4. Patrón distinto frente a otros vendedores del producto',
				),
			]
			for tipo, titulo in tablas:
				st.subheader(titulo)
				tabla = df.loc[df['tipo_analisis'] == tipo].drop(
					columns='tipo_analisis'
				)
				if tabla.empty:
					st.info('No se detectaron vendedores para este patrón.')
				else:
					st.dataframe(tabla, use_container_width=True, hide_index=True)
		else:
			st.dataframe(df, use_container_width=True)