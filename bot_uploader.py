import os
import telebot
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from classifier import classify_activity, categories
from transcriber import transcribe_audio
from notion_send import enviar_a_notion


USUARIO_AUTORIZADO = int(os.getenv("USUARIO_AUTORIZADO")) if os.getenv("USUARIO_AUTORIZADO") else None
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))


def es_usuario_autorizado(message) -> bool:
    return str(message.from_user.id) == str(USUARIO_AUTORIZADO)


def acceso_restringido(func):
    def wrapper(message):
        if not es_usuario_autorizado(message):
            bot.reply_to(message, "⛔ No estás autorizado para usar este bot.")
            return
        return func(message)
    return wrapper


def _fecha_hoy() -> str:
    return datetime.now().strftime("%Y-%m-%d")


@bot.message_handler(commands=["start"])
@acceso_restringido
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 ¡Hola! Cuéntame qué actividades realizaste hoy"
    )


@bot.message_handler(content_types=["text"])
@acceso_restringido
def handle_text(message):
    texto = (message.text or "").strip()
    if not texto:
        bot.reply_to(message, "Envía una descripción de la actividad (texto).")
        return

    bot.send_message(message.chat.id, "📌 Registrando actividad...")

    try:
        activity = classify_activity(
            texto=texto,
            categories=categories,
            today=_fecha_hoy()
        )
        result = enviar_a_notion(activity)
        if result.get("ok"):
            bot.send_message(
                message.chat.id,
                "✅ Actividad registrada en Notion.\n"
                f"📌 Nombre: {activity.name}\n"
                f"📌 Categoría: {activity.category}\n"
            )
        else:
            bot.send_message(message.chat.id, f"⚠️ No se pudo registrar: {result.get('error', 'Error desconocido')}")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ocurrió un error: {str(e)}")


@bot.message_handler(content_types=["voice"])
@acceso_restringido
def handle_voice(message):
    bot.send_message(message.chat.id, "🎙️ Recibido. Transcribiendo y registrando...")

    file_info = bot.get_file(message.voice.file_id)
    downloaded = bot.download_file(file_info.file_path)

    os.makedirs("temp", exist_ok=True)
    ruta_audio = os.path.join("temp", f"voice_{message.message_id}.ogg")
    with open(ruta_audio, "wb") as f:
        f.write(downloaded)

    try:
        texto = transcribe_audio(
            audio_path=ruta_audio
        )
        activity = classify_activity(
            texto=texto,
            categories=categories,
            today=_fecha_hoy()
        )
        result = enviar_a_notion(activity)
        if result.get("ok"):
            bot.send_message(
                message.chat.id,
                "✅ Actividad registrada en Notion.\n"
                f"📌 Nombre: {activity.name}\n"
                f"📌 Categoría: {activity.category}\n"
            )
        else:
            bot.send_message(message.chat.id, f"⚠️ No se pudo registrar: {result.get('error', 'Error desconocido')}")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ocurrió un error: {str(e)}")
    finally:
        try:
            os.remove(ruta_audio)
        except OSError:
            pass


@bot.message_handler(func=lambda message: True)
def fallback(message):
    if not es_usuario_autorizado(message):
        return
    bot.reply_to(message, "Envía una actividad como texto o una nota de voz.")


# Iniciar el bot
if __name__ == "__main__":
    print("🤖 Bot en ejecución...")
    bot.polling()

