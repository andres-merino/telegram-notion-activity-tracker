from pydantic import BaseModel, Field
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
