import pymysql 
from pymongo import MongoClient
from datetime import datetime
import random


# Conexiones a las bases de datos MySQL y MongoDB

def conectar_mysql():
    print("Conectando a la base de datos MySQL...")
    return pymysql.connect(
        host='localhost',
        user='root',
        password='root',
        database='AquaLife',
        cursorclass=pymysql.cursors.DictCursor
    )


def conectar_mongo():
    print("Conectando a la base de datos MongoDB...")
    uri = "mongodb://admin:password@localhost:27017/"
    client = MongoClient(uri)
    return client


# Extraccion de datos de MySQL 

def obtener_especies_mysql(conn):
    print("Obteniendo todas las especies de MySQL...")
    with conn.cursor() as cursor:
        consulta = """SELECT e.IDProd, e.NombreComun, e.NombreCientifico, e.Categoria, 
                           e.TipoSustrato, e.HorasLuz, e.LitrosMinimosTanque, 
                           e.IDTA, e.IDT, e.IDCE,
                           p.Descripcion
                      FROM Especie e
                      JOIN Producto p ON e.IDProd = p.IDProd;"""
        
        cursor.execute(consulta)
        return cursor.fetchall()

# Generacion de documentos 

def generar_documentos_secundarios():
    # Creamos una lista con funciones que generan cada uno de los 5 tipos de documentos
    documentos = [
        # 1. Certificado Sanitario
        lambda: {
            "Tipo": "Certificado Sanitario",
            "Fecha": datetime(2024, random.randint(1, 12), random.randint(1, 28)).isoformat(),
            "EstadoSalud": random.choice(["Óptimo", "Bueno", "En observación"]),
            "LibreParasitos": random.choice([True, False]),
            "VeterinarioResponsable": "Dr. Aqua" 
        },
        # 2. Guía de Alimentación Estacional
        lambda: {
            "Tipo": "Guía de Alimentación Estacional",
            "Temporada": random.choice(["Primavera", "Verano", "Otoño", "Invierno"]),
            "DietaRecomendada": random.choice(["Escamas finas", "Micro-granulos", "Artemia", "Mysis"]),
            "FrecuenciaDiaria": random.choice(["1 vez al día", "2 veces al día", "3 veces al día"])
        },
        # 3. Manual de Tratamiento de Enfermedades
        lambda: {
            "Tipo": "Manual de Tratamiento",
            "EnfermedadComun": random.choice(["Punto blanco (Ich)", "Hongos", "Podredumbre de aleta"]),
            "Medicamento": random.choice(["Azul de metileno", "Sal marina", "Antibiótico específico"]),
            "DiasCuarentena": random.choice([7, 14, 21])
        },
        # 4. Historial de Crecimiento
        lambda: {
            "Tipo": "Historial de Crecimiento",
            "EtapaActual": random.choice(["Alevín", "Juvenil", "Adulto"]),
            "TallaActualCm": round(random.uniform(1.0, 15.0), 1),
            "EsperanzaVidaAnios": random.randint(2, 10)
        },
        # 5. Análisis de Agua
        lambda: {
            "Tipo": "Análisis de Agua",
            "FechaAnalisis": datetime(2024, random.randint(1, 12), random.randint(1, 28)).isoformat(),
            "Parametros": {
                "Ph": round(random.uniform(6.0, 8.5), 2),
                "DurezaGh": random.randint(2, 15),
                "TemperaturaC": random.randint(20, 28),
                "AmoniacoPpm": 0.0,
                "NitritosPpm": round(random.uniform(0.0, 0.5), 2),
                "NitratosPpm": random.randint(0, 40)
            }
        }
    ]
    
    # Seleccionamos aleatoriamente entre 3 y 5 tipos de documentos diferentes
    tipos_seleccionados = random.sample(documentos, random.randint(3, 5))
    
    # Ejecutamos las funciones seleccionadas para generar los subdocumentos
    documentos_generados = [generar() for generar in tipos_seleccionados]
    
    return documentos_generados


# Ejecucion principal e insercion

conn_mysql = conectar_mysql()
client_mongo = conectar_mongo()

db_mongo = client_mongo['AquaLifeDoc']
coleccion_mongo = db_mongo['fichas_especie']

# Limpiamos la coleccion 
coleccion_mongo.delete_many({})

especies = obtener_especies_mysql(conn_mysql)

documentos_a_insertar = []

for esp in especies:
    
    subdocs = generar_documentos_secundarios()
    
    doc_principal = {
        "IDProd": esp["IDProd"],
        "NombreComun": esp["NombreComun"],
        "NombreCientifico": esp["NombreCientifico"],
        "Categoria": esp["Categoria"],
        "TipoSustrato": esp["TipoSustrato"],
        "HorasLuz": esp["HorasLuz"],
        "LitrosMinimosTanque": esp["LitrosMinimosTanque"],
        "IDTA": esp["IDTA"],
        "IDT": esp["IDT"],
        "IDCE": esp["IDCE"],
        "Descripcion": esp["Descripcion"],
        "DocumentosSecundarios": subdocs 
    }
    
    documentos_a_insertar.append(doc_principal)
    
# Insertamos en MongoDB

resultado = coleccion_mongo.insert_many(documentos_a_insertar)
print(f"Se insertaron {len(resultado.inserted_ids)} fichas.\n")

conn_mysql.close()


# Consulta jerarquica

print("-" * 60)
id_buscado = documentos_a_insertar[0]["IDProd"]
print(f"Buscando la ficha completa de la especie con IDProd: {id_buscado}...\n")

ficha = coleccion_mongo.find_one({"IDProd": id_buscado})

from bson.json_util import dumps
print(dumps(ficha, indent=4, ensure_ascii=False))