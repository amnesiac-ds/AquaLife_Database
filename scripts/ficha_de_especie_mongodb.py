import pymysql 
from pymongo import MongoClient
from datetime import datetime
import random


#Conexiones a las bases de datos MySQL y MongoDB

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
        consulta = """SELECT e.IDProd, e.NombreComun, e.NombreCientifico, e.Categoria, p.Descripcion
        FROM Especie e
        JOIN Producto p ON e.IDProd = p.IDProd;"""
        
        cursor.execute(consulta)
        return cursor.fetchall()

# Generacion de documentos 

def generar_documentos_secundarios():
    # Creamos una lista con funciones que generan cada uno de los 5 tipos dwe documentos para tener variedad de datos de cada documentos
    documetos = [
        # Certificado sanitario
        lambda: {
            "tipo" : "Certificado Sanitario",
            "fecha" : datetime(2024, random.randint(1, 12), random.randint(1, 28)).isoformat(),
            "estado_salud": random.choice(["Óptimo", "Bueno", "En observación"]),
            "libre_parasitos": random.choice([True, False]),
            "veterinario_responsable": "Dr. Aqua" 
        },
        # 2. Guía de Alimentación Estacional
        lambda: {
            "tipo": "Guía de Alimentación Estacional",
            "temporada": random.choice(["Primavera", "Verano", "Otoño", "Invierno"]),
            "dieta_recomendada": random.choice(["Escamas finas", "Micro-granulos", "Artemia", "Mysis"]),
            "frecuencia_diaria": random.choice(["1 vez al día", "2 veces al día", "3 veces al día"])
        },
        # 3. Manual de Tratamiento de Enfermedades
        lambda: {
            "tipo": "Manual de Tratamiento",
            "enfermedad_comun": random.choice(["Punto blanco (Ich)", "Hongos", "Podredumbre de aleta"]),
            "medicamento": random.choice(["Azul de metileno", "Sal marina", "Antibiótico específico"]),
            "dias_cuarentena": random.choice([7, 14, 21])
        },
        # 4. Historial de Crecimiento
        lambda: {
            "tipo": "Historial de Crecimiento",
            "etapa_actual": random.choice(["Alevín", "Juvenil", "Adulto"]),
            "talla_actual_cm": round(random.uniform(1.0, 15.0), 1),
            "esperanza_vida_anios": random.randint(2, 10)
        },
        # 5. Análisis de Agua
        lambda: {
            "tipo": "Análisis de Agua",
            "fecha_analisis": datetime(2024, random.randint(1, 12), random.randint(1, 28)).isoformat(),
            "parametros": {
                "ph": round(random.uniform(6.0, 8.5), 2),
                "dureza_gh": random.randint(2, 15),
                "temperatura_c": random.randint(20, 28),
                "amoníaco_ppm": 0.0,
                "nitritos_ppm": round(random.uniform(0.0, 0.5), 2),
                "nitratos_ppm": random.randint(0, 40)
            }
        }
    ]
    
    # seleccionamos aleatoriamente entre 3 y 5 tipos de documentos diferentes
    tipos_seleccionados = random.sample(documetos, random.randint(3,5))
    
    # ejecutamos las funciones seleccioandas para generar los subdocumentos
    
    documentos_generados = [generar() for generar in tipos_seleccionados]
    
    return documentos_generados



# Ejecucion principal e insercion

conn_mysql = conectar_mysql()
client_mongo = conectar_mongo()

db_mongo = client_mongo['AquaLifeDoc']
coleccion_mongo = db_mongo['fichas_especies']

# limpiamos la coleccion 
coleccion_mongo.delete_many({})

especies = obtener_especies_mysql(conn_mysql)

documentos_a_insertar = []


for esp in especies:
    
    subdocs = generar_documentos_secundarios()
    
    doc_principal = {
        "_id": esp["IDProd"],
        "nombre_comun": esp["NombreComun"],
        "nombre_cientifico": esp["NombreCientifico"],
                "categoria": esp["Categoria"],
                "descripcion": esp["Descripcion"],
                "documentos_secundarios": subdocs 
    }
    
    documentos_a_insertar.append(doc_principal)
    
# Insertamos en MongoDB

resultado = coleccion_mongo.insert_many(documentos_a_insertar)
print(f"Se insertaron {len(resultado.inserted_ids)} fichas.\n")

conn_mysql.close()


# Consulta jerarquica

print("-"*60)
id_buscado = documentos_a_insertar[0]["_id"]
print(f"Buscando la ficha completa de la especie con id: {id_buscado}...\n")

ficha = coleccion_mongo.find_one({"_id": id_buscado})

from bson.json_util import dumps
print(dumps(ficha, indent=4, ensure_ascii=False))

