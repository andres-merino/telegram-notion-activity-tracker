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

    system_prompt = (
        "Eres un asistente para registrar actividades de gestión académica de la USDIC en la FCENA (PUCE). "
        "Contexto institucional: FCENA incluye las carreras de Biología, Microbiología, Química, Bioingeniería, "
        "Ciencias Biomédicas y Ciencia de Datos; y programas de posgrado de Maestría en Biología y "
        "Maestría en Ciencias Actuariales. "
        "Conceptos clave:\n"
        "- Rutas académicas: procesos para que un estudiante apruebe un resultados de aprendizaje (RdA) pendiente.\n"
        "- Banner: sistema de gestión académica utilizado para matrícula, registro de notas, programación académica.\n"
        "- EVA: Entorno Virtual de Aprendizaje (aulas virtuales).\n"
        "Tu tarea es estructurar y clasificar actividades relacionadas con estos ámbitos. "
        "No inventes información; si algo no está explícito, manténlo general."
    )
    user_prompt = (
        "1) Detecta si el texto contiene una o varias actividades.\n"
        "2) Para cada actividad, elige EXACTAMENTE una categoría de la lista permitida.\n"
        "3) Para cada actividad, genera un nombre corto y simple pero que capture lo que se hace (3–8 palabras).\n"
        "4) Para cada actividad, redacta una descripción breve (1 frases).\n"
        f"5) Si no hay fecha explícita, usa la de hoy que es {today} (formato AAAA-MM-DD).\n"
        "6) Devuelve solo el objeto del esquema con 'activities' como lista. Si hay una sola actividad, igual devuélvela en la lista.\n\n"
        f"Categorías permitidas: {allowed}\n\n"
        f"Descripción de las categorías:\n" + "\n".join([f"- {key}: {value['descripcion']}" for key, value in categories.items()]) + "\n"
        "No inventes categorías. Si ninguna aplica, elige la más cercana evita lo máximo en usar la categoría Otras.\n\n"
        f"Actividad: {texto}"
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