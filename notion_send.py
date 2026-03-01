import os
from classifier import Activity
from notion_client import Client as NotionClient

NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
notion = NotionClient(auth=os.getenv("NOTION_TOKEN"))

def enviar_a_notion(actividad: Activity):
    propiedades = {
        "Actividad": {"title": [{"text": {"content": actividad.name}}]},
        "Categoría": {"select": {"name": actividad.category}},
        "Fecha": {"date": {"start": actividad.date}},
        "Descripción": {"rich_text": [{"text": {"content": actividad.description}}]}
    }
    try:
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=propiedades
        )
    except Exception as e:
        print(f"Error al enviar a Notion: {e}")
        return {"ok": False, "error": str(e)}

    return {"ok": True}


def enviar_varias_a_notion(actividades: list[Activity]):
    resultados = []
    errores = []

    for actividad in actividades:
        resultado = enviar_a_notion(actividad)
        resultados.append(resultado)
        if not resultado.get("ok"):
            errores.append({"activity": actividad.name, "error": resultado.get("error", "Error desconocido")})

    return {
        "ok": len(errores) == 0,
        "total": len(actividades),
        "guardadas": len(actividades) - len(errores),
        "errores": errores,
    }
