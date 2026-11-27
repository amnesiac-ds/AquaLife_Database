#!/usr/bin/env python3
"""Generador aleatorio de init.sql para la base de datos AquaLife.

Uso:
    python3 generate_init_sql.py
    python3 generate_init_sql.py --seed 42 --output init.sql

Si no se especifican --seed ni --date, se usan DEFAULT_SEED y
DEFAULT_REFERENCE_DATE (definidos más abajo), de forma que ejecutar el
script sin argumentos produce siempre el mismo init.sql, sin importar el
día en que se ejecute.

Para variar el volumen de datos, edita las cantidades en el diccionario
CONFIG de más abajo y vuelve a ejecutar el script.
"""

import argparse
import random
import time
from datetime import date, timedelta

_INICIO = time.monotonic()


def log(mensaje):
    print(f"[{time.monotonic() - _INICIO:7.2f}s] {mensaje}", flush=True)


def log_progress(actual, total, cada=100000, prefijo=""):
    if total <= 0:
        return
    if actual % cada == 0 or actual == total:
        pct = actual * 100 // total
        log(f"  {prefijo}{actual:,}/{total:,} ({pct}%)")


# Semilla y fecha de referencia usadas cuando no se pasan --seed / --date,
# para que el resultado sea reproducible por defecto.
DEFAULT_SEED = 33
DEFAULT_REFERENCE_DATE = date(2026, 1, 1)

# ---------------------------------------------------------------------------
# CONFIG: cantidad de registros por tabla. Edita estos valores para variar
# el volumen de datos generado.
# ---------------------------------------------------------------------------
CONFIG = {
    "usuarios": 2000,
    "videos": 2000,
    "fotos": 2000,
    "especies": 4000,  # cantidad de especies (peces/invertebrados/plantas/corales)
    "productos_equipo": 2000,  # cantidad de productos que NO son especies (equipos, alimento, etc.)
    "tipos_agua": 10,  # <= tamaño del catálogo TIPOS_AGUA
    "cuidados_especificos": 30,  # <= tamaño del catálogo CUIDADOS_ESPECIFICOS
    "publicaciones": 2000,
    "comentarios": 1100000,
    "reacciones": 1100000,
    "gustar": 1100000,
    "compras": 1100000,
    "tener_foto": 1100000,
    "contribuciones": 1100000,
    "contribucion_foto": 1100000,
    "contribucion_video": 1100000,
}

REFERENCE_DATE = DEFAULT_REFERENCE_DATE

# ---------------------------------------------------------------------------
# Pools de datos aleatorios (vastos, para maximizar la variedad generada)
# ---------------------------------------------------------------------------

NOMBRES = [
    "Juan", "Luis", "Carlos", "Jorge", "Pedro", "Ana", "María", "Elena", "Laura", "Sonia",
    "Marta", "Julia", "Diego", "Miguel", "Rafael", "Gabriel", "Fernando", "Ricardo",
    "Andrés", "Alejandro", "Beatriz", "Camila", "Daniela", "Valentina", "Isabel",
    "Lucía", "Paula", "Patricia", "Claudia", "Rosa", "Teresa", "Victoria", "Adriana",
    "Cristina", "Mónica", "Sergio", "Roberto", "Alberto", "Eduardo", "Francisco",
    "Manuel", "Antonio", "Javier", "Raúl", "Óscar", "Ivonne", "Yolanda", "Susana",
    "Verónica", "Silvia",
]

APELLIDOS = [
    "Perez", "Gomez", "Sánchez", "López", "Rodríguez", "García", "Martínez", "Torres",
    "Ramírez", "Ruiz", "Fernández", "Álvarez", "Díaz", "Castro", "Morales", "Ortiz",
    "Vargas", "Reyes", "Jiménez", "Romero", "Herrera", "Medina", "Flores", "Suárez",
    "Guerrero", "Rojas", "Núñez", "Delgado", "Vega", "Molina",
]

CALLES = [
    "Ramírez", "Gomez", "Sánchez", "López", "Rodríguez", "García", "Martínez", "Torres",
    "Perez", "Ruiz", "Alameda", "Marina", "Coral", "Del Puerto", "Los Pinos", "Las Palmas",
]

DOMINIOS_EMAIL = ["email.com", "correo.com", "mailbox.com", "webmail.com"]

NOTIFICACIONES = ["activada", "desactivada"]
PRIVACIDAD = ["No compartir", "Compartir parcial", "Compartir totalmente"]

TIPOS_AGUA = [
    "Agua dulce tropical", "Agua dulce fría", "Agua marina / arrecife", "Agua salobre",
    "Agua dulce blackwater", "Agua dulce plantada (CO2)", "Agua marina fish-only",
    "Agua dulce rift lake (cíclidos africanos)", "Agua dulce de estanque exterior",
    "Agua marina de baja salinidad",
]

TEMPORADAS = ["Primavera", "Verano", "Otoño", "Invierno"]

TIPOS_SUSTRATO = [
    "Arena fina", "Grava fina", "Grava gruesa", "Sustrato fértil", "Roca volcánica",
    "Sustrato de coral triturado", "Sin sustrato (agua libre)", "Turba",
]

CUIDADOS_ESPECIFICOS = [
    "Cambios parciales de agua semanales del 20%.", "Control regular de parámetros de amoníaco y nitritos.",
    "Aclimatación lenta por goteo para nuevos ejemplares.", "Cuarentena de al menos dos semanas para peces nuevos.",
    "Uso de acondicionador de agua para eliminar cloro.", "Mantenimiento de temperatura estable con calentador termostático.",
    "Poda regular de plantas de crecimiento rápido.", "Suplementación de CO2 para plantas exigentes.",
    "Alimentación variada para evitar deficiencias nutricionales.", "Sifonado periódico del sustrato para eliminar detritos.",
    "Control de algas mediante caracoles y camarones limpiadores.", "Uso de skimmer de proteínas en acuarios marinos.",
    "Dosificación de calcio y alcalinidad en acuarios de arrecife.", "Iluminación LED programada según fotoperiodo natural.",
    "Cuidado especial durante la muda en crustáceos.", "Separación de ejemplares territoriales o agresivos.",
    "Filtración biológica robusta para cargas altas de bioload.", "Aireación adicional en épocas de calor.",
    "Revisión de la dureza del agua (GH/KH) según la especie.", "Uso de sustrato específico para plantas de raíz.",
    "Evitar sobrealimentación para prevenir picos de amoníaco.", "Aclimatación gradual a la salinidad para especies marinas.",
    "Cuidado de corales con corrientes adecuadas de bomba.", "Control de fósforo y nitratos en el agua.",
    "Revisión periódica del filtro y limpieza de medios filtrantes.", "Introducción escalonada de especies para evitar estrés.",
    "Uso de tapa en el acuario para evitar saltos de peces.", "Enriquecimiento del sustrato para plantas de fondo.",
    "Rotación de decoración para enriquecimiento ambiental.", "Monitoreo de la calidad del agua con kit de pruebas semanal.",
]

# (Categoria, NombreComun, NombreCientifico)
ESPECIES_POOL = [
    ("Pez", "Neón Tetra", "Paracheirodon innesi"), ("Pez", "Guppy", "Poecilia reticulata"),
    ("Pez", "Betta", "Betta splendens"), ("Pez", "Corydora Bronce", "Corydoras aeneus"),
    ("Pez", "Pez Ángel", "Pterophyllum scalare"), ("Pez", "Disco", "Symphysodon aequifasciatus"),
    ("Pez", "Oscar", "Astronotus ocellatus"), ("Pez", "Molly Negro", "Poecilia sphenops"),
    ("Pez", "Platy", "Xiphophorus maculatus"), ("Pez", "Espada", "Xiphophorus hellerii"),
    ("Pez", "Danio Cebra", "Danio rerio"), ("Pez", "Gourami Perla", "Trichopodus leerii"),
    ("Pez", "Barbo Tigre", "Puntigrus tetrazona"), ("Pez", "Rasbora Arlequín", "Trigonostigma heteromorpha"),
    ("Pez", "Pleco Común", "Hypostomus plecostomus"), ("Pez", "Killi Azul", "Nothobranchius rachovii"),
    ("Pez", "Tetra Cardenal", "Paracheirodon axelrodi"), ("Pez", "Loach Payaso", "Chromobotia macracanthus"),
    ("Pez", "Cíclido Ram", "Mikrogeophagus ramirezi"), ("Pez", "Arowana Plateado", "Osteoglossum bicirrhosum"),
    ("Pez", "Pez Dorado Común", "Carassius auratus"), ("Pez", "Carpa Koi", "Cyprinus rubrofuscus"),
    ("Pez", "Pez Dorado Oranda", "Carassius auratus var. oranda"), ("Pez", "Pez Payaso Ocelado", "Amphiprion ocellaris"),
    ("Pez", "Tang Azul", "Paracanthurus hepatus"), ("Pez", "Tang Amarillo", "Zebrasoma flavescens"),
    ("Pez", "Gobio Mandarín", "Synchiropus splendidus"), ("Pez", "Damisela Azul", "Chrysiptera cyanea"),
    ("Pez", "Pez Ángel Enano Naranja", "Centropyge loricula"), ("Pez", "Blenio Saltarín", "Salarias fasciatus"),
    ("Pez", "Pez Cirujano", "Acanthurus leucosternon"), ("Pez", "Caballito de Mar", "Hippocampus reidi"),
    ("Pez", "Pez León Enano", "Dendrochirus zebra"), ("Invertebrado", "Camarón Cereza", "Neocaridina davidi"),
    ("Invertebrado", "Camarón Amano", "Caridina multidentata"), ("Invertebrado", "Cangrejo Ermitaño", "Clibanarius sp."),
    ("Invertebrado", "Caracol Nerita", "Neritina natalensis"), ("Invertebrado", "Caracol Manzana", "Pomacea bridgesii"),
    ("Invertebrado", "Cangrejo Vampiro", "Geosesarma dennerle"), ("Invertebrado", "Estrella de Mar Azul", "Linckia laevigata"),
    ("Invertebrado", "Anémona Burbuja", "Entacmaea quadricolor"), ("Invertebrado", "Camarón Limpiador", "Lysmata amboinensis"),
    ("Invertebrado", "Erizo de Mar Lápiz", "Eucidaris tribuloides"), ("Planta Acuática", "Anubias", "Anubias barteri"),
    ("Planta Acuática", "Helecho de Java", "Microsorum pteropus"), ("Planta Acuática", "Musgo de Java", "Taxiphyllum barbieri"),
    ("Planta Acuática", "Espada Amazónica", "Echinodorus bleheri"), ("Planta Acuática", "Vallisneria", "Vallisneria spiralis"),
    ("Planta Acuática", "Cabomba", "Cabomba caroliniana"), ("Planta Acuática", "Rotala", "Rotala rotundifolia"),
    ("Planta Acuática", "Hierba de Estanque Enana", "Eleocharis parvula"), ("Planta Acuática", "Cryptocoryne", "Cryptocoryne wendtii"),
    ("Planta Acuática", "Elodea", "Egeria densa"), ("Planta Acuática", "Hornwort", "Ceratophyllum demersum"),
    ("Planta Acuática", "Wisteria de Agua", "Hygrophila difformis"), ("Planta Acuática", "Lechuga de Agua", "Pistia stratiotes"),
    ("Planta Acuática", "Helecho Flotante", "Salvinia natans"), ("Planta Acuática", "Lenteja de Agua", "Lemna minor"),
    ("Coral", "Coral Cuero", "Sarcophyton sp."), ("Coral", "Coral Cerebro", "Trachyphyllia geoffroyi"),
    ("Coral", "Coral Martillo", "Euphyllia ancora"), ("Coral", "Zoántidos", "Zoanthus sp."),
    ("Coral", "Coral Hongo", "Discosoma sp."), ("Coral", "Xenia Pulsante", "Xenia elongata"),
    ("Coral", "Coral Antorcha", "Euphyllia glabrescens"), ("Coral", "Coral Estrella", "Tubastraea sp."),
]

# (Nombre, Descripcion)
PRODUCTOS_EQUIPO_POOL = [
    ("Filtro de Cascada Compacto", "Filtracion mecanica y biologica eficiente para acuarios de hasta 100 litros."),
    ("Calentador Termostatico Sumergible", "Mantiene la temperatura del agua estable para especies tropicales."),
    ("Iluminacion LED Full Spectrum", "Espectro completo de luz para favorecer plantas y corales."),
    ("Skimmer de Proteinas Compacto", "Elimina compuestos organicos disueltos en acuarios marinos."),
    ("Bomba de Circulacion Ajustable", "Genera corriente controlada, ideal para acuarios de arrecife."),
    ("Kit de Pruebas de Agua Completo", "Mide pH, amoniaco, nitritos, nitratos, dureza y cloro."),
    ("Sustrato Fertil para Plantas", "Rico en nutrientes, favorece el enraizamiento de plantas acuaticas."),
    ("Grava Decorativa de Rio", "Sustrato inerte de grano fino, ideal para acuarios comunitarios."),
    ("Alimento en Escamas Premium", "Formula balanceada para peces tropicales de agua dulce."),
    ("Alimento Congelado para Corales", "Mezcla de zooplancton para corales y anemonas."),
    ("Acondicionador de Agua", "Neutraliza cloro y metales pesados, protege la mucosa de los peces."),
    ("Sal Marina Sintetica", "Mezcla de sales para preparar agua marina artificial."),
    ("Decoracion de Resina Tipo Roca", "Replica realista de roca volcanica, segura para acuarios."),
    ("Cueva Ceramica para Peces", "Refugio decorativo, ideal para especies territoriales."),
    ("Termometro Digital Sumergible", "Medicion precisa de temperatura con pantalla LCD."),
    ("Aireador de Doble Salida", "Bomba de aire silenciosa con dos salidas ajustables."),
    ("Fertilizante Liquido para Plantas", "Aporta micronutrientes esenciales para el crecimiento vegetal."),
    ("Difusor de CO2 Ceramico", "Disuelve CO2 en finas burbujas para plantas exigentes."),
    ("Alimentador Automatico Programable", "Dosifica raciones de alimento en horarios programados."),
    ("Bomba de Retorno Silenciosa", "Alta eficiencia energetica, bajo nivel de ruido."),
    ("Corales Artificiales Decorativos", "Replicas de silicona, seguras y de colores vivos."),
    ("Filtro de Mochila HOB", "Facil mantenimiento, filtracion mecanica y quimica."),
    ("Piedra Difusora de Aire", "Genera burbujas finas para mejorar la oxigenacion."),
    ("Medidor de Salinidad", "Refractometro de precision para agua marina."),
    ("Manta de Cultivo de Musgo", "Sustrato para fijar musgos y helechos acuaticos."),
]

PUBLICACION_TEXTOS = [
    "Mi primer acuario plantado, qué satisfacción verlo crecer.",
    "Consejos para el cambio de agua semanal.", "Mi betta macho por fin hizo su nido de burbujas.",
    "Increíble atardecer visto desde mi ventana.", "Rutinas de mantenimiento para principiantes en acuarismo.",
    "Mi arrecife después de seis meses de maduración.", "Los mejores camarones limpiadores para tu acuario.",
    "Cómo aclimaté mis nuevos peces sin estrés.", "Mi primera cría exitosa de guppys.",
    "Explorando nuevas especies para mi próximo acuario.", "Viajar y visitar acuarios públicos: mi experiencia.",
    "Técnicas de meditación para la ansiedad.", "Lectura recomendada de este mes sobre acuarismo.",
    "Mi opinión sobre el último equipo de filtración que probé.", "Hermoso día en el parque!",
    "Mi jardín de corales sigue creciendo.", "Cómo bajé el amoníaco de mi acuario en una semana.",
    "Recomendaciones de iluminación para plantas exigentes.", "Mi pecera comunitaria cumple un año.",
    "Consejos para elegir el sustrato correcto.",
]

COMENTARIOS_POOL = [
    "Me encantó esta publicación, ¡gracias por compartir!", "Totalmente de acuerdo contigo.",
    "No comparto la misma opinión, pero respeto tu punto de vista.", "Esto me recuerda a una experiencia que tuve.",
    "Este es el tipo de contenido por el que estoy aquí.", "No estaba al tanto de esto, interesante.",
    "¿Podrías profundizar más sobre este tema?", "¿Tienes más recomendaciones similares?",
    "Lamentablemente, mi experiencia fue diferente.", "Increíble, ¡quiero saber más!",
    "¿Qué parámetros de agua usas para eso?", "Yo tuve un problema similar con mi acuario.",
]

REACCION_TIPOS = [
    "Me gusta", "Me encanta", "Me asombra", "Me entristece", "Me enoja", "Me divierte",
]

OPINIONES_COMPRA = [
    "Excelente producto, muy recomendado.", "No era lo que esperaba.",
    "Cumple con las expectativas.", "Definitivamente compraría de nuevo.",
    "Buena calidad, pero el envío fue lento.",
]

NOTAS_CONTRIBUCION = [
    "Gran aporte a la comunidad de acuarismo.", "Necesita mejor cuidado.",
    "Donación de alevines.", "Voluntariado en mantenimiento de acuario comunitario.",
    "Excelente condición del ejemplar.", "Registro de crecimiento satisfactorio.",
]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def sql_str(value):
    if value is None:
        return "NULL"
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def sql_val(value):
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return sql_str(value)
    return str(value)


def random_date(days_back_min, days_back_max):
    days_back = random.randint(days_back_min, days_back_max)
    return REFERENCE_DATE - timedelta(days=days_back)


def maybe_none(value, prob_none):
    return None if random.random() < prob_none else value


def unique_pairs(n_a, n_b, count, one_indexed=True):
    """Genera hasta `count` pares (a, b) unicos, con a en [1..n_a], b en [1..n_b]."""
    max_possible = n_a * n_b
    count = min(count, max_possible)
    seen = set()
    result = []
    attempts = 0
    max_attempts = count * 20 + 1000
    while len(result) < count and attempts < max_attempts:
        attempts += 1
        a = random.randint(1, n_a)
        b = random.randint(1, n_b)
        if (a, b) not in seen:
            seen.add((a, b))
            result.append((a, b))
    return result


def validar_configuracion(config):
    """Valida las cantidades de CONFIG contra los topes reales: el tamano de
    los catalogos fijos (TIPOS_AGUA, CUIDADOS_ESPECIFICOS) y la cantidad de
    combinaciones unicas posibles en las tablas de clave compuesta. Si una
    cantidad solicitada excede su tope, se imprime una alerta y se ajusta
    al maximo posible (en vez de fallar en silencio durante la generacion).

    Devuelve una copia ajustada de `config`.
    """
    validado = dict(config)
    alertas = []

    def limitar(clave, maximo, motivo):
        solicitado = validado[clave]
        if solicitado > maximo:
            alertas.append(
                f"- '{clave}': se pidieron {solicitado}, pero el maximo posible es {maximo} "
                f"({motivo}). Se ajusta el valor a {maximo}."
            )
            validado[clave] = maximo

    limitar("tipos_agua", len(TIPOS_AGUA), f"TIPOS_AGUA solo tiene {len(TIPOS_AGUA)} opciones")
    limitar("cuidados_especificos", len(CUIDADOS_ESPECIFICOS), f"CUIDADOS_ESPECIFICOS solo tiene {len(CUIDADOS_ESPECIFICOS)} opciones")

    max_usuario_publicacion = validado["usuarios"] * validado["publicaciones"]
    limitar("reacciones", max_usuario_publicacion, "combinaciones unicas de (usuario, publicacion)")

    max_usuario_especie = validado["usuarios"] * validado["especies"]
    limitar("gustar", max_usuario_especie, "combinaciones unicas de (usuario, especie)")

    max_publicacion_foto = validado["publicaciones"] * validado["fotos"]
    limitar("tener_foto", max_publicacion_foto, "combinaciones unicas de (publicacion, foto)")

    ventana_dias = 2 * 365
    n_productos_totales = validado["especies"] + validado["productos_equipo"]
    max_compras = validado["usuarios"] * n_productos_totales * ventana_dias
    limitar("compras", max_compras, "combinaciones unicas de (comprador, producto, fecha) en una ventana de 2 anios")

    max_contribuciones = validado["especies"] * ventana_dias
    limitar("contribuciones", max_contribuciones, "combinaciones unicas de (especie, fecha) en una ventana de 2 anios")

    max_contribucion_foto = validado["contribuciones"] * validado["fotos"]
    limitar("contribucion_foto", max_contribucion_foto, "combinaciones unicas de (contribucion, foto)")

    max_contribucion_video = validado["contribuciones"] * validado["videos"]
    limitar("contribucion_video", max_contribucion_video, "combinaciones unicas de (contribucion, video)")

    if alertas:
        print("ALERTAS de configuracion (valores ajustados automaticamente):")
        for alerta in alertas:
            print(alerta)
        print()

    return validado


def sql_str(value):
    if value is None:
        return "NULL"
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def sql_val(value):
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return sql_str(value)
    return str(value)


def random_date(days_back_min, days_back_max):
    days_back = random.randint(days_back_min, days_back_max)
    return REFERENCE_DATE - timedelta(days=days_back)


def maybe_none(value, prob_none):
    return None if random.random() < prob_none else value


def unique_pairs(n_a, n_b, count, one_indexed=True):
    """Genera hasta `count` pares (a, b) unicos, con a en [1..n_a], b en [1..n_b]."""
    max_possible = n_a * n_b
    count = min(count, max_possible)
    seen = set()
    result = []
    attempts = 0
    max_attempts = count * 20 + 1000
    while len(result) < count and attempts < max_attempts:
        attempts += 1
        a = random.randint(1, n_a)
        b = random.randint(1, n_b)
        if (a, b) not in seen:
            seen.add((a, b))
            result.append((a, b))
    return result


# ---------------------------------------------------------------------------
# Utilidades de escritura en streaming (batches)
# ---------------------------------------------------------------------------

BATCH_SIZE = 50000  # filas por batch para tablas grandes


def write_batch(f, table, columns, rows):
    """Escribe un batch de filas como INSERT VALUES."""
    if not rows:
        return
    cols = ", ".join(columns)
    f.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n")
    formatted = []
    for row in rows:
        formatted.append("(" + ", ".join(sql_val(v) for v in row) + ")")
    f.write(",\n".join(formatted) + ";\n\n")


def log_progress(actual, total, cada=100000, prefijo=""):
    if total <= 0:
        return
    if actual % cada == 0 or actual == total:
        pct = actual * 100 // total
        log(f"  {prefijo}{actual:,}/{total:,} ({pct}%)")


# ---------------------------------------------------------------------------
# Generadores por tabla (streaming para tablas grandes)
# ---------------------------------------------------------------------------


def gen_usuarios(n, f):
    log("Generando Usuario...")
    used_emails = set()
    rows = []
    for i in range(n):
        nombre = random.choice(NOMBRES)
        apellido = random.choice(APELLIDOS)
        nombre_completo = f"{nombre} {apellido}"
        calle = random.choice(CALLES)
        numero = random.randint(1, 99)
        direccion = f"Calle {calle} {numero}, Ciudad"
        base_email = f"{nombre}.{apellido}".lower().replace(" ", "")
        email = f"{base_email}{i}@{random.choice(DOMINIOS_EMAIL)}"
        while email in used_emails:
            email = f"{base_email}{i}{random.randint(0,999)}@{random.choice(DOMINIOS_EMAIL)}"
        used_emails.add(email)
        fecha_nacimiento = date(random.randint(1955, 2007), random.randint(1, 12), random.randint(1, 28))
        notificaciones = random.choice(NOTIFICACIONES)
        privacidad = random.choice(PRIVACIDAD)
        rows.append((nombre_completo, direccion, email, fecha_nacimiento.isoformat(), notificaciones, privacidad))
        log_progress(i + 1, n, cada=500, prefijo="Usuario: ")
    return rows


def gen_videos(n, f):
    log("Generando Video...")
    rows = []
    for i in range(n):
        rows.append((f"https://www.youtube.com/{random.getrandbits(48):012x}",))
        log_progress(i + 1, n, cada=500, prefijo="Video: ")
    return rows


def gen_fotos(n, f):
    log("Generando Foto...")
    rows = []
    for i in range(n):
        rows.append((f"https://images.google.com/images/{random.getrandbits(40):010x}",))
        log_progress(i + 1, n, cada=500, prefijo="Foto: ")
    return rows


def gen_productos_equipo(n, f):
    log("Generando Producto (equipo)...")
    rows = []
    for i in range(n):
        nombre, descripcion = random.choice(PRODUCTOS_EQUIPO_POOL)
        precio = round(random.uniform(3.0, 250.0), 2)
        rows.append((nombre, descripcion, precio))
        log_progress(i + 1, n, cada=500, prefijo="Producto equipo: ")
    return rows


def gen_especies_productos(n, f):
    """Genera las filas de Producto correspondientes a especies (precio de venta)."""
    log("Generando Producto (especies)...")
    rows = []
    especies_info = []
    for i in range(n):
        categoria, nombre_comun, nombre_cientifico = random.choice(ESPECIES_POOL)
        precio = round(random.uniform(1.5, 900.0), 2)
        rows.append((nombre_comun, f"{categoria}: {nombre_comun} ({nombre_cientifico}).", precio))
        especies_info.append((categoria, nombre_comun, nombre_cientifico))
        log_progress(i + 1, n, cada=1000, prefijo="Producto especie: ")
    return rows, especies_info


def gen_tipos_agua(n, f):
    n = min(n, len(TIPOS_AGUA))
    rows = [(t,) for t in random.sample(TIPOS_AGUA, n)]
    log(f"Generando TipoAgua... -> {len(rows):,} filas")
    return rows


def gen_cuidados_especificos(n, f):
    n = min(n, len(CUIDADOS_ESPECIFICOS))
    rows = [(c,) for c in random.sample(CUIDADOS_ESPECIFICOS, n)]
    log(f"Generando Cuidados_Especificos... -> {len(rows):,} filas")
    return rows


def gen_especies(especies_info, n_tipos_agua, n_temporadas, n_cuidados, f):
    log("Generando Especie...")
    rows = []
    for i, (categoria, nombre_comun, nombre_cientifico) in enumerate(especies_info, start=1):
        tipo_sustrato = random.choice(TIPOS_SUSTRATO)
        horas_luz = random.randint(4, 14)
        litros_min = random.choice([10, 20, 40, 60, 100, 150, 200, 300, 500])
        id_ta = random.randint(1, n_tipos_agua)
        id_t = random.randint(1, n_temporadas)
        id_ce = random.randint(1, n_cuidados)
        rows.append((i, nombre_cientifico, nombre_comun, tipo_sustrato, categoria,
                     random.randint(4, 14), random.choice([10, 20, 40, 60, 100, 150, 200, 300, 500]),
                     random.randint(1, n_tipos_agua), random.randint(1, n_temporadas), random.randint(1, n_cuidados)))
        log_progress(i, len(especies_info), cada=1000, prefijo="Especie: ")
    return rows


def gen_publicaciones(n, n_usuarios, n_videos, f):
    log("Generando Publicacion...")
    rows = []
    for i in range(n):
        texto = random.choice(PUBLICACION_TEXTOS)
        id_u = random.randint(1, n_usuarios)
        id_v = random.randint(1, n_videos) if random.random() < 0.5 else None
        fecha = random_date(1, 2 * 365)
        fecha_str = fecha.isoformat() + " " + f"{random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
        rows.append((texto, id_u, id_v, fecha_str))
        log_progress(i + 1, n, cada=500, prefijo="Publicacion: ")
    return rows


def gen_comentar(n, n_usuarios, n_publicaciones, f):
    """Genera comentarios jerárquicos nivel por nivel, liberando memoria de niveles previos."""
    log("Generando Comentar...")
    n_raiz = int(n * 0.6)
    n_respuestas = n - n_raiz
    
    next_cid = 1
    BATCH_SIZE = 50000
    
    # 1. RAÍCES (nivel 0) - 60%
    log("  Generando raíces (nivel 0)...")
    batch = []
    raices_por_pub = {pub: [] for pub in range(1, n_publicaciones + 1)}
    
    for i in range(n_raiz):
        id_u = random.randint(1, n_usuarios)
        id_pub = random.randint(1, n_publicaciones)
        cid = next_cid
        next_cid += 1
        
        fecha = random_date(1, 5 * 365)
        fecha_str = fecha.isoformat() + " " + f"{random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
        
        yield [(cid, id_u, id_pub, None, random.choice(COMENTARIOS_POOL), fecha_str)]
        raices_por_pub[id_pub].append(cid)
        
        log_progress(next_cid - 1, n_raiz, cada=100000, prefijo="Raíces: ")
    
    log(f"  Raíces completadas: {n_raiz:,}")
    
    # 2. RESPUESTAS NIVEL POR NIVEL - liberando memoria de niveles previos
    padres_nivel_actual = raices_por_pub
    nivel = 1
    total_escritos = n_raiz
    n_respuestas = n - n_raiz
    
    while total_escritos < n:
        log(f"  Generando nivel {nivel}...")
        hijos_por_pub = {pub: [] for pub in range(1, n_publicaciones + 1)}
        pendientes_nivel = min(n - total_escritos, n_raiz * (2 ** nivel) // 2)
        
        respuestas_por_pub = {}
        total_raices = sum(len(v) for v in padres_nivel_actual.values())
        if total_raices == 0:
            break
            
        for pub, padres in padres_nivel_actual.items():
            if not padres:
                continue
            propor = len(padres) / total_raices
            pend = int(pendientes_nivel * propor)
            if pend > 0:
                respuestas_por_pub[pub] = min(pend, len(padres) * 5)
        
        # Asegurar que se cubran todas las respuestas
        if sum(respuestas_por_pub.values()) < n - total_escritos:
            for pub in range(1, n_publicaciones + 1):
                if respuestas_por_pub.get(pub, 0) < 100 and padres_nivel_actual.get(pub):
                    respuestas_por_pub[pub] = respuestas_por_pub.get(pub, 0) + 10
        
        for pub, num_respuestas in respuestas_por_pub.items():
            padres = padres_nivel_actual[pub]
            if not padres:
                continue
            
            for _ in range(num_respuestas):
                if total_escritos >= n:
                    break
                
                id_padre = random.choice(padres)
                id_u = random.randint(1, n_usuarios)
                fecha = random_date(1, 5 * 365)
                fecha_str = fecha.isoformat() + " " + f"{random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
                cid = next_cid
                next_cid += 1
                total_escritos += 1
                
                yield [(cid, id_u, pub, id_padre, random.choice(COMENTARIOS_POOL),
                       fecha.isoformat() + " " + f"{random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}")]
                
                hijos_por_pub[pub].append(cid)
                
                log_progress(total_escritos, n, cada=100000, prefijo=f"Nivel {nivel}: ")
        
        # Liberar memoria del nivel anterior
        padres_nivel_actual = hijos_por_pub
        nivel += 1
        
        if not any(padres_nivel_actual.values()):
            break
    
    log(f"  Comentarios generados: {total_escritos:,} (profundidad máx: {nivel-1})")



def gen_reaccionar(n, n_usuarios, n_publicaciones, f):
    log("Generando Reaccionar...")
    pares = unique_pairs(n_usuarios, n_publicaciones, n)
    rows = []
    for i, (u, p) in enumerate(pares):
        tipo = random.choice(REACCION_TIPOS)
        fecha = random_date(1, 5 * 365)
        rows.append((u, p, tipo, fecha.isoformat()))
        log_progress(i + 1, len(pares), cada=100000, prefijo="Reaccion: ")
    return rows


def gen_gustar(n, n_usuarios, n_especies, f):
    log("Generando Gustar...")
    pares = unique_pairs(n_usuarios, n_especies, n)
    log(f"  -> {len(pares):,} filas")
    return pares


def gen_compras(n, n_usuarios, n_productos, productos_precio, f):
    log("Generando Compra...")
    rows = []
    seen = set()
    attempts = 0
    max_attempts = n * 20 + 1000
    while len(rows) < n and attempts < max_attempts:
        attempts += 1
        id_uc = random.randint(1, n_usuarios)
        id_uv = random.randint(1, n_usuarios)
        if id_uc == id_uv:
            continue
        id_prod = random.randint(1, n_productos)
        fecha = random_date(1, 2 * 365)
        key = (id_uc, id_prod, fecha.isoformat())
        if key in seen:
            continue
        seen.add(key)
        precio_base = productos_precio[id_prod - 1]
        precio = round(precio_base * random.uniform(0.85, 1.15), 2)
        opinion = maybe_none(random.choice(OPINIONES_COMPRA), 0.5)
        puntuacion = maybe_none(random.randint(1, 5), 0.3)
        cantidad = random.randint(1, 5)
        rows.append((id_uc, id_uv, id_prod, fecha.isoformat(), opinion, precio, puntuacion, cantidad))
        log_progress(len(rows), n, cada=100000, prefijo="Compra: ")
    return rows


def gen_tener_foto(n, n_publicaciones, n_fotos, f):
    log("Generando Tener_Foto...")
    pares = unique_pairs(n_publicaciones, n_fotos, n)
    log(f"  -> {len(pares):,} filas")
    return pares


def gen_contribuciones(n, n_especies, n_usuarios, f):
    log("Generando Contribucion...")
    rows = []
    keys_en_orden = []
    seen = set()
    attempts = 0
    max_attempts = n * 20 + 1000
    while len(rows) < n and attempts < max_attempts:
        attempts += 1
        id_prod = random.randint(1, n_especies)
        fecha = random_date(1, 2 * 365)
        key = (id_prod, fecha.isoformat())
        if key in seen:
            continue
        seen.add(key)
        keys_en_orden.append(key)
        id_u = random.randint(1, n_usuarios)
        nota = maybe_none(random.choice(NOTAS_CONTRIBUCION), 0.3)
        rows.append((id_prod, id_u, fecha.isoformat(), nota))
        log_progress(len(rows), n, cada=100000, prefijo="Contribucion: ")
    return rows, keys_en_orden


def gen_contribucion_media(n, contribucion_keys, n_media, f, table_name):
    log(f"Generando {table_name}...")
    rows = []
    seen = set()
    attempts = 0
    max_attempts = n * 20 + 1000
    while len(rows) < n and attempts < max_attempts and contribucion_keys:
        attempts += 1
        id_prod, fecha = random.choice(contribucion_keys)
        id_media = random.randint(1, n_media)
        key = (id_prod, fecha, id_media)
        if key in seen:
            continue
        seen.add(key)
        rows.append((id_prod, fecha, id_media))
        log_progress(len(rows), n, cada=100000, prefijo=f"{table_name}: ")
    return rows


# ---------------------------------------------------------------------------
# Definicion de tablas (DDL)
# ---------------------------------------------------------------------------

DDL = """
-- Configurar el charset
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Optimizaciones para la carga masiva inicial (solo afectan a esta sesion).
-- Se restauran al final del archivo, despues de insertar todos los datos.
SET sql_log_bin = 0;
SET unique_checks = 0;
SET foreign_key_checks = 0;

-- Crear y usar la base de datos AquaLife
CREATE DATABASE IF NOT EXISTS AquaLife CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE AquaLife;

-- Crear tabla Usuario
CREATE TABLE IF NOT EXISTS Usuario (
	IDU INT(11) NOT NULL AUTO_INCREMENT,
	Nombre VARCHAR(50) NOT NULL,
	DireccionParticular VARCHAR(50) NOT NULL,
	Email VARCHAR(50) NOT NULL,
	FechaDeNacimiento DATE NOT NULL,
	Notificaciones CHAR(17) NOT NULL,
	ConfiguracionDePrivacidad CHAR(30) NOT NULL,
	PRIMARY KEY (IDU),
	UNIQUE (Email),
	CHECK (Notificaciones IN ('activada', 'desactivada')),
	CHECK (ConfiguracionDePrivacidad IN ('No compartir', 'Compartir parcial', 'Compartir totalmente'))
);

-- Crear tabla Video
CREATE TABLE IF NOT EXISTS Video(
    IDV INT NOT NULL AUTO_INCREMENT,
    URL VARCHAR(150) NOT NULL,
    PRIMARY KEY(IDV)
);

-- Crear tabla Publicacion
CREATE TABLE IF NOT EXISTS Publicacion(
    IDPub INT(11) NOT NULL AUTO_INCREMENT,
    Texto VARCHAR(700),
    IDU INT NOT NULL,
    IDV INT,
    FechaCreacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY cal_usuario(IDU) REFERENCES Usuario(IDU) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY cal_video(IDV) REFERENCES Video(IDV) ON DELETE RESTRICT ON UPDATE CASCADE,
    PRIMARY KEY (IDPub)
);

-- Crear tabla Comentar
CREATE TABLE IF NOT EXISTS Comentar(
    IDComentario INT AUTO_INCREMENT PRIMARY KEY,
    IDU INT NOT NULL,
    IDPub INT NOT NULL,
    IDPadre INT NULL,
    Comentario VARCHAR(400) NOT NULL,
    FechaCreacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (IDU) REFERENCES Usuario(IDU) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (IDPub) REFERENCES Publicacion(IDPub) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (IDPadre) REFERENCES Comentar(IDComentario) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Crear tabla Reaccionar
CREATE TABLE IF NOT EXISTS Reaccionar(
    IDU INT NOT NULL,
    IDPub INT NOT NULL,
    Tipo CHAR(21) NOT NULL,
    Fecha DATE NOT NULL,
    PRIMARY KEY(IDU, IDPub),
    FOREIGN KEY cal_usuario(IDU) REFERENCES Usuario(IDU) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY cal_pub(IDPub) REFERENCES Publicacion(IDPub) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Crear tabla Producto
CREATE TABLE IF NOT EXISTS Producto(
    IDProd INT NOT NULL AUTO_INCREMENT,
    Nombre CHAR(40) NOT NULL,
    Descripcion CHAR(240) NOT NULL,
    Precio FLOAT NOT NULL,
    PRIMARY KEY(IDProd)
);

-- Crear tablas auxiliares
CREATE TABLE IF NOT EXISTS TipoAgua(
    IDTA INT NOT NULL AUTO_INCREMENT,
    Tipo CHAR(70) NOT NULL,
    PRIMARY KEY(IDTA)
);

CREATE TABLE IF NOT EXISTS Temporada(
    IDT INT NOT NULL AUTO_INCREMENT,
    Nombre CHAR(30) NOT NULL,
    PRIMARY KEY(IDT),
    CHECK (Nombre IN ('Verano', 'Primavera', 'Invierno', 'Otoño'))
);

CREATE TABLE IF NOT EXISTS Cuidados_Especificos(
    IDCE INT NOT NULL AUTO_INCREMENT,
    Descripcion VARCHAR(300) NOT NULL,
    PRIMARY KEY(IDCE)
);

-- Crear tabla Especie
CREATE TABLE IF NOT EXISTS Especie(
    IDProd INT NOT NULL,
    NombreCientifico CHAR(40) NOT NULL,
    NombreComun CHAR(40) NOT NULL,
    TipoSustrato CHAR(100) NOT NULL,
    Categoria CHAR(40) NOT NULL,
    HorasLuz INT,
    LitrosMinimosTanque INT,
    IDTA INT NOT NULL,
    IDT INT NOT NULL,
    IDCE INT NOT NULL,
    PRIMARY KEY(IDProd),
    FOREIGN KEY cal_prod(IDProd) REFERENCES Producto(IDProd) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY cal_agua(IDTA) REFERENCES TipoAgua(IDTA) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY cal_temp(IDT) REFERENCES Temporada(IDT) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY cal_cuid(IDCE) REFERENCES Cuidados_Especificos(IDCE) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Crear tabla Gustar
CREATE TABLE IF NOT EXISTS Gustar(
    IDU INT NOT NULL,
    IDProd INT NOT NULL,
    PRIMARY KEY(IDU, IDProd),
    FOREIGN KEY cal_especie(IDProd) REFERENCES Especie(IDProd) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY cal_usuario(IDU) REFERENCES Usuario(IDU) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Crear tabla Compra
CREATE TABLE IF NOT EXISTS Compra(
    IDUC INT NOT NULL,
    IDUV INT NOT NULL,
    IDProd INT NOT NULL,
    Fecha DATE NOT NULL,
    Opinion VARCHAR(400),
    Precio FLOAT NOT NULL,
    Puntuacion INT,
    Cantidad INT NOT NULL,
    PRIMARY KEY(IDUC, IDProd, Fecha),
    FOREIGN KEY cal_comprador(IDUC) REFERENCES Usuario(IDU) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY cal_vendedor(IDUV) REFERENCES Usuario(IDU) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY cal_prod(IDProd) REFERENCES Producto(IDProd) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Crear tabla Foto
CREATE TABLE IF NOT EXISTS Foto(
    IdF INT NOT NULL AUTO_INCREMENT,
    URL VARCHAR(150) NOT NULL,
    PRIMARY KEY(IdF)
);

-- Crear tabla Tener_Foto
CREATE TABLE IF NOT EXISTS Tener_Foto(
    IDPub INT NOT NULL,
    IDF INT NOT NULL,
    PRIMARY KEY(IDPub, IDF),
    FOREIGN KEY cal_pub(IDPub) REFERENCES Publicacion(IDPub) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY cal_foto(IDF) REFERENCES Foto(IdF) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Crear tabla Contribucion
CREATE TABLE IF NOT EXISTS Contribucion(
    IDProd INT NOT NULL,
    IDU INT NOT NULL,
    Fecha DATE NOT NULL,
    Nota VARCHAR(300),
    PRIMARY KEY(IDProd, Fecha),
    FOREIGN KEY cal_prod(IDProd) REFERENCES Especie(IDProd) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY cal_usuario(IDU) REFERENCES Usuario(IDU) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Crear tabla Contribucion_Foto
CREATE TABLE IF NOT EXISTS Contribucion_Foto(
    IDProd INT NOT NULL,
    Fecha DATE NOT NULL,
    IDF INT NOT NULL,
    PRIMARY KEY(IDProd, Fecha, IDF),
    FOREIGN KEY cal_contrib(IDProd, Fecha) REFERENCES Contribucion(IDProd, Fecha) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY cal_foto(IDF) REFERENCES Foto(IdF) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Crear tabla Contribucion_Video
CREATE TABLE IF NOT EXISTS Contribucion_Video(
    IDProd INT NOT NULL,
    Fecha DATE NOT NULL,
    IDV INT NOT NULL,
    PRIMARY KEY(IDProd, Fecha, IDV),
    FOREIGN KEY cal_contrib(IDProd, Fecha) REFERENCES Contribucion(IDProd, Fecha) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY cal_video(IDV) REFERENCES Video(IDV) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Ejercicio 3f
CREATE TABLE Historial_Precios(
    IDHistorial INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    IDProd INT NOT NULL,
    PrecioAnterior DECIMAL(10, 2) NOT NULL,
    PrecioNuevo DECIMAL(10, 2) NOT NULL,
    FechaHora DATETIME DEFAULT CURRENT_TIMESTAMP,
    NombreUsuario VARCHAR(20),
    PorcentajeCambio DECIMAL(10, 2) ,
    FOREIGN KEY (IDProd) REFERENCES Producto(IDProd)
);

DELIMITER //

CREATE TRIGGER tgr_auditar_precio AFTER UPDATE
    ON Producto
    FOR EACH ROW
BEGIN
    IF NEW.Precio <> OLD.Precio THEN
        INSERT INTO Historial_Precios(
            IDProd,
            PrecioAnterior,
            PrecioNuevo,
            PorcentajeCambio,
            NombreUsuario
        )
        VALUES (
            NEW.IDProd,
            OLD.Precio,
            NEW.Precio,
            ROUND((NEW.Precio - OLD.Precio) / OLD.Precio * 100, 2),
            @nombre_usuario
        );
    END IF;
END //

DELIMITER ;

-- Ejercicio 3g
DELIMITER //

CREATE PROCEDURE sp_analisis_usuario(
        IN id_usuario INT,
        IN fecha_inicio DATE,
        IN fecha_fin DATE
    )
    BEGIN 
        SELECT COUNT(*) as total_publicaciones
            FROM Publicacion as pub 
            WHERE pub.IDU = id_usuario;

        SELECT COUNT(r.IDPub) as total_reacciones_dadas
            FROM Reaccionar as r
            WHERE r.IDU = id_usuario 
                AND r.Fecha BETWEEN fecha_inicio AND fecha_fin;

        SELECT COUNT(*) as total_reacciones_recibidas
            FROM Publicacion as p
            JOIN Reaccionar as r
                ON r.IDPub = p.IDPub
            WHERE p.IDU = id_usuario;

        SELECT COUNT(*) as total_comentarios
            FROM Comentar as c
            WHERE c.IDU = id_usuario;

        SELECT COUNT(*) as total_compras,
            ROUND(SUM(Cantidad*Precio), 2) as monto_gastado
            FROM Compra as c
            WHERE IDUC = id_usuario
                AND c.Fecha BETWEEN fecha_inicio AND fecha_fin;

        SELECT COUNT(*) as total_contribuciones
            FROM Contribucion as c
            WHERE c.IDU = id_usuario
                AND c.Fecha BETWEEN fecha_inicio AND fecha_fin;

        SELECT 
            (SELECT e.NombreCientifico
                FROM Contribucion as contr
                JOIN Especie as e
                    ON e.IDProd = contr.IDProd
                WHERE contr.IDU = id_usuario
                    AND contr.Fecha BETWEEN fecha_inicio AND fecha_fin
                GROUP BY e.NombreCientifico
                ORDER BY COUNT(*) DESC
                LIMIT 1
            )  as especie_mas_contribuida,
            (SELECT e.NombreCientifico
                FROM Especie as e
                JOIN Compra as c
                    ON e.IDProd = c.IDProd
                WHERE c.IDUC = id_usuario
                    AND c.Fecha BETWEEN fecha_inicio AND fecha_fin
                GROUP BY e.NombreCientifico
                ORDER BY SUM(c.Cantidad) DESC
                LIMIT 1
            ) as especie_mas_vendida;
    END //

DELIMITER ;
-- Ejercicio 4 comentarios recursivos


ALTER TABLE Usuario
    MODIFY COLUMN IDU INT(11) NOT NULL AUTO_INCREMENT,
    MODIFY COLUMN Nombre VARCHAR(50) NOT NULL,
    MODIFY COLUMN DireccionParticular VARCHAR(50) NULL,
    MODIFY COLUMN Email VARCHAR(50) NULL,
    MODIFY COLUMN FechaDeNacimiento DATE NULL,
    MODIFY COLUMN Notificaciones CHAR(17) NULL,
    MODIFY COLUMN ConfiguracionDePrivacidad CHAR(30) NULL;

DROP PROCEDURE IF EXISTS sp_obtener_hilo_comentarios;

DELIMITER //

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
END //

DELIMITER ;

""".strip()


# ---------------------------------------------------------------------------
# Ensamblado final (streaming a archivo)
# ---------------------------------------------------------------------------


def build_sql_streaming(config, seed=None, output_path="init.sql"):
    if seed is not None:
        random.seed(seed)

    log("Iniciando generación de init.sql (streaming)...")
    
    with open(output_path, "w", encoding="utf-8") as f:
        # DDL
        f.write(DDL + "\n\n")
        
        # Índices adicionales (prioridad >= 8) para optimizar consultas analíticas y SP
        # Ver análisis en informe_aqualife.tex sección 3.5 y config_database/README.md
        indices_adicionales = """
-- ============================================================
-- ÍNDICES ADICIONALES (prioridad >= 8)
-- Creados tras la carga masiva para optimizar consultas y SP
-- ============================================================

-- 1. Comentar(IDPub, IDPadre) — Prioridad 10/10
-- Crítico para CTE recursivo sp_obtener_hilo_comentarios:
-- caso base WHERE IDPub = ? AND IDPadre IS NULL
-- JOIN recursivo ON respuesta.IDPadre = hilo.IDComentario AND respuesta.IDPub = hilo.IDPub
CREATE INDEX idx_comentar_pub_padre ON Comentar (IDPub, IDPadre);

-- 2. Compra(IDUV, IDProd, Fecha) — Prioridad 9/10
-- Consultas 3_e.sql (top vendedores), 3_i.sql (variación_mensual, resumen_calificaciones)
-- Agrupación por vendedor + producto + fecha
CREATE INDEX idx_compra_uv_prod_fecha ON Compra (IDUV, IDProd, Fecha);

-- 3. Compra(IDUC, Fecha) — Prioridad 9/10
-- SP sp_analisis_usuario: total_compras + monto_gastado por usuario en rango de fechas
CREATE INDEX idx_compra_uc_fecha ON Compra (IDUC, Fecha);

-- 4. Publicacion(IDU, FechaCreacion) — Prioridad 9/10
-- SP sp_analisis_usuario: total_publicaciones por usuario en rango de fechas
CREATE INDEX idx_publicacion_usuario_fecha ON Publicacion (IDU, FechaCreacion);

-- 5. Reaccionar(IDU, Fecha) — Prioridad 9/10
-- SP sp_analisis_usuario: total_reacciones_dadas por usuario en rango de fechas
CREATE INDEX idx_reaccionar_usuario_fecha ON Reaccionar (IDU, Fecha);

-- 6. Comentar(IDU, FechaCreacion) — Prioridad 9/10
-- SP sp_analisis_usuario: total_comentarios por usuario en rango de fechas
CREATE INDEX idx_comentar_usuario_fecha ON Comentar (IDU, FechaCreacion);

-- 7. Contribucion(IDU, Fecha) — Prioridad 9/10
-- SP sp_analisis_usuario: total_contribuciones por usuario en rango de fechas
CREATE INDEX idx_contribucion_usuario_fecha ON Contribucion (IDU, Fecha);

-- 8. Reaccionar(IDPub) — Prioridad 8/10
-- Consultas 3_a, 3_b, 3_h: JOIN Reaccionar.IDPub = Publicacion.IDPub
-- (FK no crea índice automáticamente en MySQL 8 para la tabla referenciada)
CREATE INDEX idx_reaccionar_publicacion ON Reaccionar (IDPub);

-- 9. Contribucion(IDProd) — Prioridad 8/10
-- Consultas 3_d, 3_h: JOIN Contribucion.IDProd = Especie.IDProd
CREATE INDEX idx_contribucion_especie ON Contribucion (IDProd);

-- 10. Especie(IDTA) — Prioridad 8/10
-- Consulta 3_d: JOIN Especie.IDTA = TipoAgua.IDTA
CREATE INDEX idx_especie_tipoagua ON Especie (IDTA);

-- 11. Compra(IDUV, Puntuacion) — Prioridad 8/10
-- Consultas 3_i (resumen_calificaciones), 3_e (top vendedores)
-- Agrupación y filtro por puntuaciones 1-5
CREATE INDEX idx_compra_vendedor_puntuacion ON Compra (IDUV, Puntuacion);

"""
        f.write(indices_adicionales)
        
        # Usuarios
        usuarios = gen_usuarios(config["usuarios"], None)
        f.write("-- Insertar datos en Usuario\n")
        write_batch(f, "Usuario", ["Nombre", "DireccionParticular", "Email", "FechaDeNacimiento", "Notificaciones", "ConfiguracionDePrivacidad"], usuarios)
        
        # Video
        videos = gen_videos(config["videos"], None)
        f.write("\n-- Insertar datos en Video\n")
        write_batch(f, "Video", ["URL"], videos)
        
        # Publicacion
        publicaciones = gen_publicaciones(config["publicaciones"], config["usuarios"], config["videos"], None)
        f.write("\n-- Insertar datos en Publicacion\n")
        write_batch(f, "Publicacion", ["Texto", "IDU", "IDV", "FechaCreacion"], publicaciones)
        
        # Comentar (streaming con batches)
        log("Generando Comentar...")
        f.write("\n-- Insertar datos en Comentar\n")
        for batch in gen_comentar(config["comentarios"], config["usuarios"], config["publicaciones"], None):
            write_batch(f, "Comentar", ["IDComentario", "IDU", "IDPub", "IDPadre", "Comentario", "FechaCreacion"], batch)
        
        # Reaccionar
        reacciones = gen_reaccionar(config["reacciones"], config["usuarios"], config["publicaciones"], None)
        f.write("\n-- Insertar datos en Reaccionar\n")
        write_batch(f, "Reaccionar", ["IDU", "IDPub", "Tipo", "Fecha"], reacciones)
        
        # Producto (especies + equipo)
        log("Generando Producto (especies + equipo)...")
        especies_productos, especies_info = gen_especies_productos(config["especies"], None)
        productos_equipo = gen_productos_equipo(config["productos_equipo"], None)
        todos_los_productos = especies_productos + productos_equipo
        f.write("\n-- Insertar datos en Producto (especies + equipo)\n")
        write_batch(f, "Producto", ["Nombre", "Descripcion", "Precio"], todos_los_productos)
        
        # TipoAgua
        tipos_agua = gen_tipos_agua(config["tipos_agua"], None)
        f.write("\n-- Insertar datos en TipoAgua\n")
        write_batch(f, "TipoAgua", ["Tipo"], tipos_agua)
        
        # Temporada
        f.write("\n-- Insertar datos en Temporada\n")
        write_batch(f, "Temporada", ["Nombre"], [(t,) for t in TEMPORADAS])
        log(f"  -> {len(TEMPORADAS):,} filas")
        
        # Cuidados_Especificos
        cuidados = gen_cuidados_especificos(config["cuidados_especificos"], None)
        f.write("\n-- Insertar datos en Cuidados_Especificos\n")
        write_batch(f, "Cuidados_Especificos", ["Descripcion"], cuidados)
        
        # Especie
        especies = gen_especies(especies_info, len(tipos_agua), len(TEMPORADAS), len(cuidados), None)
        f.write("\n-- Insertar datos en Especie\n")
        write_batch(f, "Especie", ["IDProd", "NombreCientifico", "NombreComun", "TipoSustrato", "Categoria", "HorasLuz", "LitrosMinimosTanque", "IDTA", "IDT", "IDCE"], especies)
        
        # Gustar
        gustar = gen_gustar(config["gustar"], config["usuarios"], config["especies"], None)
        f.write("\n-- Insertar datos en Gustar\n")
        write_batch(f, "Gustar", ["IDU", "IDProd"], gustar)
        
        # Compra
        productos_precio = [p[2] for p in todos_los_productos]
        compras = gen_compras(config["compras"], config["usuarios"], len(todos_los_productos), productos_precio, None)
        f.write("\n-- Insertar datos en Compra\n")
        write_batch(f, "Compra", ["IDUC", "IDUV", "IDProd", "Fecha", "Opinion", "Precio", "Puntuacion", "Cantidad"], compras)
        
        # Foto
        fotos = gen_fotos(config["fotos"], None)
        f.write("\n-- Insertar datos en Foto\n")
        write_batch(f, "Foto", ["URL"], fotos)
        
        # Tener_Foto
        tener_foto = gen_tener_foto(config["tener_foto"], config["publicaciones"], config["fotos"], None)
        f.write("\n-- Insertar datos en Tener_Foto\n")
        write_batch(f, "Tener_Foto", ["IDPub", "IDF"], tener_foto)
        
        # Contribucion
        contribuciones, contribucion_keys = gen_contribuciones(config["contribuciones"], config["especies"], config["usuarios"], None)
        f.write("\n-- Insertar datos en Contribucion\n")
        write_batch(f, "Contribucion", ["IDProd", "IDU", "Fecha", "Nota"], contribuciones)
        
        # Contribucion_Foto
        contribucion_foto = gen_contribucion_media(config["contribucion_foto"], contribucion_keys, config["fotos"], None, "Contribucion_Foto")
        f.write("\n-- Insertar datos en Contribucion_Foto\n")
        write_batch(f, "Contribucion_Foto", ["IDProd", "Fecha", "IDF"], contribucion_foto)
        
        # Contribucion_Video
        contribucion_video = gen_contribucion_media(config["contribucion_video"], contribucion_keys, config["videos"], None, "Contribucion_Video")
        f.write("\n-- Insertar datos en Contribucion_Video\n")
        write_batch(f, "Contribucion_Video", ["IDProd", "Fecha", "IDV"], contribucion_video)

        # Restaurar las comprobaciones al terminar la carga.
        f.write("\n-- Restaurar comprobaciones\n")
        f.write("SET unique_checks = 1;\n")
        f.write("SET foreign_key_checks = 1;\n")
        f.write("SET sql_log_bin = 1;\n")
        
        log(f"Listo. Archivo generado: {output_path}")


def config_resumen():
    lineas = [f"  {clave}: {valor:,}" for clave, valor in CONFIG.items()]
    return "Configuracion actual (CONFIG en el script, editable):\n" + "\n".join(lineas)


def main():
    parser = argparse.ArgumentParser(
        description="Genera init.sql para AquaLife con datos aleatorios.",
        epilog=config_resumen(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help=f"Semilla aleatoria para datos reproducibles (por defecto {DEFAULT_SEED})."
    )
    parser.add_argument(
        "--output", type=str, default="init.sql",
        help="Ruta del archivo de salida (por defecto init.sql)."
    )
    parser.add_argument(
        "--date", type=date.fromisoformat, default=DEFAULT_REFERENCE_DATE,
        help=f"Fecha de referencia (YYYY-MM-DD) para calcular las fechas relativas (por defecto {DEFAULT_REFERENCE_DATE.isoformat()})."
    )
    args = parser.parse_args()

    global REFERENCE_DATE
    REFERENCE_DATE = args.date

    config_validado = validar_configuracion(CONFIG)
    build_sql_streaming(config_validado, seed=args.seed, output_path=args.output)

    print(f"Generado {args.output} con datos aleatorios para AquaLife (seed={args.seed}, date={REFERENCE_DATE.isoformat()}).")


if __name__ == "__main__":
    main()