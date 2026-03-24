import os
import json
from openai import OpenAI
from pydantic import BaseModel, Field

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_categories(file_path: str = 'categories.json') -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        categories = json.load(file)
    return categories


categories = load_categories('categories.json')


class Activity(BaseModel):
    name: str
    description: str
    date: str = Field(description="Fecha en formato AAAA-MM-DD.")
    category: str


class ActivityBatch(BaseModel):
    activities: list[Activity] = Field(description="Lista de actividades detectadas. Puede contener una o más actividades.")


def classify_activities(texto: str, categories: dict, today: str) -> list[Activity]:
    allowed = list(categories.keys())

    category_block = "\n".join(
        [
            (
                f"- {key}:\n"
                f"  nombre: {value.get('nombre', '')}\n"
                f"  descripcion: {value.get('descripcion', '')}\n"
                f"  usar_cuando: {value.get('usar_cuando', '')}"
            )
            for key, value in categories.items()
        ]
    )
    system_prompt = (
        "Eres un asistente para registrar actividades de gestión académica de la USDIC en la FCENA (PUCE). "
        "Tu tarea es detectar actividades concretas dentro de un texto, separarlas si hay más de una, "
        "clasificarlas en exactamente una categoría permitida y devolver la salida ajustada al esquema indicado.\n\n"
        "Contexto institucional:\n"
        "- FCENA incluye las carreras de Biología, Microbiología, Química, Bioingeniería, Ciencias Biomédicas y Ciencia de Datos.\n"
        "- También incluye programas de posgrado como Maestría en Biología y Maestría en Ciencias Actuariales.\n"
        "- Rutas académicas: procesos para que un estudiante apruebe un resultado de aprendizaje (RdA) pendiente.\n"
        "- Banner: sistema de gestión académica utilizado para matrícula, registro de notas y programación académica.\n"
        "- EVA: Entorno Virtual de Aprendizaje (aulas virtuales).\n\n"
        "Reglas generales:\n"
        "- No inventes información.\n"
        "- Si algo no está explícito, mantén la redacción general.\n"
        "- Cada actividad debe representar una acción concreta y diferenciable.\n"
        "- Cada actividad debe tener exactamente una categoría.\n"
        "- Clasifica según el objetivo principal de la actividad, no por palabras aisladas.\n"
        "- Si el texto menciona reunión, apoyo, gestión, revisión o coordinación, clasifica por el propósito principal de esa acción.\n"
        "- Usa la categoría 'Otras' solo como último recurso.\n"
    )
    user_prompt = (
        "Analiza el texto y devuelve solo el objeto del esquema con 'activities' como lista. "
        "Si hay una sola actividad, igualmente devuélvela dentro de la lista.\n\n"
        "Instrucciones:\n"
        "1) Detecta si el texto contiene una o varias actividades.\n"
        "2) Separa actividades solo si describen acciones realmente distintas.\n"
        "3) Para cada actividad, elige EXACTAMENTE una categoría de la lista permitida.\n"
        "4) Para cada actividad, genera un nombre corto, simple y administrativo de 3 a 8 palabras.\n"
        "5) Para cada actividad, redacta una descripción breve de una sola frase.\n"
        f"6) Si no hay fecha explícita, usa la de hoy: {today} (formato AAAA-MM-DD).\n"
        "7) Si hay una fecha explícita en el texto, conviértela a formato AAAA-MM-DD.\n"
        "8) No inventes responsables, detalles ni fechas adicionales.\n"
        "9) Prioriza la mejor categoría posible antes de usar 'Otras'.\n\n"
        f"Categorías permitidas: {allowed}\n\n"
        "Definición operativa de categorías:\n"
        f"{category_block}\n\n"
        "Reglas de desambiguación:\n"
        "- Si trata sobre sílabos, carreras, programas, maestrías o contratación docente general, prioriza 'Carreras-Programas'.\n"
        "- Si trata sobre presupuesto, logística, traspaso de información, metodologías organizativas o espacios físicos, prioriza 'Recursos'.\n"
        "- Si trata sobre rutas académicas, calificaciones, notas, recuperación académica o aprobación de RdA, prioriza 'RdA'.\n"
        "- Si trata sobre coordinación de asignaturas, componentes prácticos o articulación entre docentes de una materia, prioriza 'Áreas'.\n"
        "- Si trata sobre talleres, charlas o actividades formativas para docentes, prioriza 'Capacitacion'.\n"
        "- Si trata sobre seminario de titulación, integración curricular o prácticas preprofesionales, prioriza 'Titulacion-Practicas'.\n"
        "- Si trata sobre horarios, asignación docente, distribución de estudiantes, matrícula, inscripción o ajustes de oferta académica, prioriza 'Programacion'.\n"
        "- Usa 'Internacionalizacion', 'Evaluacion docente', 'Calidad' y 'Aulas virtuales' solo cuando el texto lo indique de forma explícita.\n\n"
        f"Texto a analizar:\n{texto}"
    )
    response = client.responses.parse(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        text_format=ActivityBatch,
        temperature=0,
    )
    parsed = response.output_parsed
    if not parsed or not parsed.activities:
        raise ValueError("No se detectaron actividades válidas en la respuesta del modelo.")
    return parsed.activities
