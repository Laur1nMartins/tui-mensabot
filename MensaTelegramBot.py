from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import urlencode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
import os, sys, datetime, re, logging, pytz

API_KEY = os.environ['TELEGRAM_API_KEY']
ENDPOINT_URL = 'https://www.stw-thueringen.de/xhr/loadspeiseplan.html'
CANTEEN_DATA = {46 : 'Mensa', 
                53: 'Cafeteria',
                55: 'Nanoteria',
                57: 'Roentgen'
                }
CANTEEN_DEFAULT = [46, 53]
user_data = dict()

# matches two digit prices such as 1,23 or 23,41 (hoping for low inflation)
PRICE_REGEX = re.compile(r'\d{1,2},\d{1,2}')

CANTEEN_HEADER="\n<b>{canteen}</b>: \n"
MEAL_TEXT_LAYOUT = "- {meal_name} \n({meal_price}€) {misc} \n"

DAYTIME_NOON = "Mittag: \n"
DAYTIME_EVENING = "Abend: \n"
CANTEEN_CLOSED = "Heute gibts hier nichts (╯°□°）╯︵ ┻━┻"
MESSAGE_EMPTY = "Du hast alle Kantinen abgewählt. :)"
GREEN_CHECKMARK = u'\U00002705'
RED_CROSS = u'\U0000274C'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def validateParameter():
    if API_KEY == "":
        sys.exit("missing api key")

def get_document(canteen_id, date):
    """
    Retrieves a document from a remote server based on the given canteen ID and date.
    """
    post_args = [('resources_id', canteen_id),('date', date)]
    return BeautifulSoup(urlopen(ENDPOINT_URL, data=urlencode(post_args).encode('utf-8')).read(), 'lxml')


def parse_closed(document):
    """
    Check if the given document indicates that the establishment is closed for the selected date.
    """
    return bool(document.find_all('h2', string='Zum gewählten Datum werden in dieser Einrichtung keine Essen angeboten.'))

def parse_meals(document):
    """
    Parses meals from a document and extracts their names, miscellaneous categories, and prices.
    """
    meals = document.find_all(class_='rowMealInner')
    for meal in meals:
        name = meal.find_next(class_='mealText').string.strip()

        misc = []
        for misc_category in meal.find_all(class_='splIconMeal'):
            misc.append(misc_category['title'])

        prices_element = meal.find_next(class_='mealPreise')
        prices = PRICE_REGEX.findall(prices_element.string) if prices_element else None

        # check for non-empty name
        if len(name):
            yield (name, misc, prices)

def parse_single_canteen(document, canteen_name):
    """
    Parses a single canteen document and formats the meal information based on the canteen name.
    """
    retval = ""
    retval += CANTEEN_HEADER.format(canteen=canteen_name)
    noon_amount = -1

    if canteen_name == 'Cafeteria':
        element_evening = document.find('div', class_='splGroupAbendmensa')
        if element_evening is not None:
            noon_amount = len(element_evening.find_all_previous(class_='rowMealInner'))
        else:
            noon_amount = -1
        if noon_amount > 0 or noon_amount == -1:
            retval += DAYTIME_NOON
    i = 0
    for (name, misc, prices) in parse_meals(document):
        if i == noon_amount:
            if i > 0:
                retval += "\n"
            retval += DAYTIME_EVENING
        i += 1
        meal_veg = ""
        if 'Vegane Speisen (V*)' in misc:
            meal_veg = "Vegan"
        elif 'Vegetarische Speisen (V)' in misc:
            meal_veg = "Vegetarisch"
        retval += MEAL_TEXT_LAYOUT.format(meal_name=name, meal_price=prices[0] if prices else "nicht angegeben", misc=meal_veg)

    return retval

def parse_for_date(chat_id, date_offset):
    """
    Parses the menu for a given date offset.
    """
    if user_data.get(chat_id) is not None:
        user_canteen = user_data.get(chat_id)
        if not user_canteen:
            return MESSAGE_EMPTY
    else:
        user_canteen = CANTEEN_DEFAULT


    date = datetime.datetime.now().astimezone(datetime.UTC) + datetime.timedelta(days=date_offset)
    date_berlin = date.astimezone(pytz.timezone('Europe/Berlin')).strftime("%d.%m.%Y")
    retval = ""
    for i in range(len(user_canteen)):
        document = get_document(user_canteen[i], date_berlin)
        if not parse_closed(document):
            retval += parse_single_canteen(document, CANTEEN_DATA.get(user_canteen[i]))
    if (retval == ""):
        retval = CANTEEN_CLOSED
    return retval


async def heute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=parse_for_date(update.effective_chat.id, 0), parse_mode="HTML")

async def morgen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=parse_for_date(update.effective_chat.id, 1), parse_mode="HTML")

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

def get_keyboard(chat_id):
    data = user_data.get(chat_id)
    if data is None:
        user_data[chat_id] = []
        user_data[chat_id].extend(CANTEEN_DEFAULT)
        data = CANTEEN_DEFAULT
        
    keyboard = [
    ]

    for key in CANTEEN_DATA:
        if key in data:
            emoji = GREEN_CHECKMARK
        else:
            emoji = RED_CROSS
        keyboard.append([InlineKeyboardButton(emoji + CANTEEN_DATA.get(key), callback_data=key)])
    keyboard.append([InlineKeyboardButton("Fertig", callback_data="done")])
    return InlineKeyboardMarkup(keyboard)

async def modify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id 
    reply_markup = get_keyboard(chat_id)
    await update.message.reply_text("Bitte auswählen:", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Parses the CallbackQuery and updates the message text."""

    query = update.callback_query

    if query.data == "done":
        await query.message.delete()
        return
    else:
        key = int(query.data)
        chat_id = query.message.chat_id
        data = user_data[chat_id]
        
        if key in data:
            data.remove(key)
            changes = " abgewählt."
        else:
            data.append(key)
            changes = " hinzugefügt."
        user_data[chat_id] = data

    await query.answer()

    reply_markup = get_keyboard(chat_id)
    await query.edit_message_text("Du hast " + CANTEEN_DATA.get(key) + changes + "\n Bitte auswählen:", reply_markup=reply_markup)




async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    send = "Commands: \n"
    send += "- /heute : Zeigt alle heutigen Gerichte. \n \n"
    send += "- /morgen : Zeigt alle Gerichte für den nächsten Tag. \n \n"
    send += "- /poll : Erstellt einen Poll.\nZusätzliche Zeiten als Argument mit Leerzeichen getrennt nach dem Command hinzufügbar.\n"
    send += "- Argumente zwischen zwei _ werden als Frage des Polls eingesetzt."
    await context.bot.send_message(chat_id=update.effective_chat.id, text=send)

if __name__ == '__main__':

    validateParameter()

    application = ApplicationBuilder().token(API_KEY).build()

    start_handler = CommandHandler('heute', heute)
    application.add_handler(start_handler)

    start_handler = CommandHandler('morgen', morgen)
    application.add_handler(start_handler)

    poll_handler = CommandHandler('poll', poll)
    application.add_handler(poll_handler)

    poll_handler = CommandHandler('modify', modify)
    application.add_handler(poll_handler)
    application.add_handler(CallbackQueryHandler(button))

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    application.run_polling()