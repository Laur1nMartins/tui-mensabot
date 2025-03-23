from telegram import Update, InputFile
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters
from datetime import datetime, timezone
import re
from cmd_base import CmdFactory
import uuid

date_format = "%Y-%m-%d %H:%M"
def parse_datetime(date_str):
    try:
        # Attempt to parse the string
        date_obj = datetime.strptime(date_str, date_format)
        return date_obj
    except ValueError:
        # Handle the error if parsing fails
        print(f"Error: '{date_str}' does not match the format '{date_format}'")
        return None

async def start_event(update: Update, context):
    context.user_data['step'] = 'name'
    await update.message.reply_text("Please provide the event name:")

async def handle_message(update: Update, context):
    step = context.user_data.get('step')
    if step == 'name':
        context.user_data['name'] = update.message.text
        context.user_data['step'] = 'location'
        await update.message.reply_text(f"Event: {context.user_data.get('name')}\nPlease provide the event location:")
    elif step == 'location':
        context.user_data['location'] = update.message.text
        context.user_data['step'] = 'start'
        await update.message.reply_text(f"Event: {context.user_data.get('name')} @ {context.user_data.get('location')}\nPlease provide the start time (YYYY-MM-DD HH:MM):")
    elif step == 'start':
        t_start = parse_datetime(update.message.text)
        if not t_start:
            return await update.message.reply_text(f"Failed to parse {update.message.text} as {date_format}. Try again")
        context.user_data['start'] = t_start
        context.user_data['step'] = 'end'
        await update.message.reply_text(f"Event: {context.user_data.get('name')} @ {context.user_data.get('location')} ({t_start} -> ?)\nPlease provide the end time (YYYY-MM-DD HH:MM):")
    elif step == 'end':
        t_end = parse_datetime(update.message.text)
        if not t_end:
            return await update.message.reply_text(f"Failed to parse {update.message.text} as {date_format}. Try again")
        context.user_data['end'] = t_end
        # Send confirmation
        await update.message.reply_text(f"Event: {context.user_data.get('name')} @ {context.user_data.get('location')} ({context.user_data['start']} -> {t_end})")
        # Send ics file
        await generate_ics(update, context)

async def generate_ics(update: Update, context):
    event_id = str(uuid.uuid4())
    name = context.user_data.get('name')
    location = context.user_data.get('location')
    start = context.user_data.get('start')
    end = context.user_data.get('end')
    
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MensaBot//EN
BEGIN:VEVENT
UID:{event_id}
DTSTAMP:{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}
DTSTART:{start.strftime("%Y%m%dT%H%M%SZ")}
DTEND:{end.strftime("%Y%m%dT%H%M%SZ")}
SUMMARY:{name}
LOCATION:{location}
END:VEVENT
END:VCALENDAR"""

    # Create and send the ics file
    file_path = "/tmp/event.ics"
    with open(file_path, "w") as file:
        file.write(ics_content)
    await update.message.reply_document(document=open(file_path, "rb"))

def RegisterCmds(bot):
    CmdFactory("ics", "Create an ICS file.", start_event)
    
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))