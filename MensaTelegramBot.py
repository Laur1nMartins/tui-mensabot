from cmd_base import GetCmds
from telegram import Update 
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import os, sys, logging
import mensa
import polls
import ics

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

API_KEY = os.environ['TELEGRAM_API_KEY']

def validateParameter():
    if API_KEY == "":
        sys.exit("missing api key")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    send = "Commands: \n"
    print(GetCmds())
    for cmd in GetCmds():
        send += f"-  /{cmd.getName()}: {cmd.getHelpStr()}\n"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=send)

if __name__ == '__main__':

    validateParameter()

    application = ApplicationBuilder().token(API_KEY).build()
    
    # default handler
    application.add_handler(CommandHandler('help', help))
    
    # mensa command handler
    mensa.RegisterCmds()
    
    # poll handler
    polls.RegisterCmds()
    
    # ics handler
    ics.RegisterCmds(application)

    cmds = GetCmds()
    for cmd in cmds:
        logging.info(f"Registering {cmd.getName()}")
        application.add_handler(CommandHandler(cmd.getName(), cmd.handler))

    logging.info("Config finished.")
    application.run_polling()