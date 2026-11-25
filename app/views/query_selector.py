#!/bin/python3

import streamlit as st
from config import CATALOG
from db import execute_dql

name = st.selectbox('Consulta', CATALOG.keys())

with st.spinner('Ejecutando..'):
	df = execute_dql(CATALOG[name])
	if CATALOG[name] == '3_i.sql':
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

