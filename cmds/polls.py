from telegram import Update
from telegram.ext import ContextTypes
from cmd_base import CmdFactory


async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):

    quotes = False
    question = ""
    options = []
    standardoptions = ["11:30","11:45","12:00", "12:15", "12:35", "12:45", "13:00"]


    for arg in context.args:

        if len(arg) > 100:
            arg = arg[:100]

        ## allow for "_Custom Questions_" with whitespaces
        if quotes == False: ##if we are not in within _ _ we check for _ at the start and append the rest to questions
            if len(arg) > 1:
                if arg[0] == '_':
                    quotes = True
                    question += arg[1: -1]

                    ## allow one word questions
                    if arg[-1] == '_':
                        quotes = False
                        question += " "
                    else: ## add the last char
                        question += arg[-1] + " "

                else:
                    options.append(arg)
            else:
                options.append(arg)
        else:
            ##check if arg ends with "_"
            if arg[len(arg)-1] == "_":
                quotes = False
                ## append everything but last char to last string
                question += arg[:len(arg)-1]
            else: ##append whole arg
                question += arg + " "
                
    options = options + standardoptions
    options.append("Heute nicht.")

    if question == "":
        question = "Wann Mensa?"

    await context.bot.sendPoll(chat_id=update.effective_chat.id, question=question, options=options, is_anonymous=False, allows_multiple_answers=True)

# 
def RegisterCmds():
    CmdFactory("poll", "Erstellt einen Poll.\nZusätzliche Zeiten als Argument mit Leerzeichen getrennt nach dem Command hinzufügbar.\nArgumente zwischen zwei _ werden als Frage des Polls eingesetzt.", poll)