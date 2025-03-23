from abc import ABC, abstractmethod
from typing import Callable, Awaitable
from typing import TypeVar, Generic
from telegram import Update
from telegram.ext import ContextTypes

class TelegramCommand(ABC):
    @abstractmethod
    def getName(self) -> str:
        pass
    @abstractmethod
    def getHelpStr(self) -> str:
        pass
    @abstractmethod
    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass

# Create a generic type variable for the custom list
T = TypeVar("T", bound=TelegramCommand)
class CmdList(Generic[T], list):
    def append(self, item: T):
        if not isinstance(item, TelegramCommand):
            print(item)
            raise TypeError(f"Item must be an instance of {TelegramCommand.__name__}")
        super().append(item)

# All commands should register themselves here
listOfCommands = CmdList[TelegramCommand]()

# name: the name of the command
# help: the help text of the command
# handler: the handler function being called when the command is recieved
def CmdFactory(name: str, help: str, handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]):
    def ret_name(self):
        return name
    def ret_help(self):
        return help
    async def ret_handler(self, update, context):
        await  handler(update, context)
    # methods
    m = {
        'getName': ret_name,
        'getHelpStr': ret_help,
        'handler': ret_handler,
    }
    # Add to commands
    listOfCommands.append(type(name+"_cmd", (TelegramCommand,), m)())

def GetCmds():
    return listOfCommands