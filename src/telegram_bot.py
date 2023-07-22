from datetime import datetime
import re
import sys
from typing import Callable, Dict, List
from dotenv import dotenv_values

from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update

from src.interface_database import DBInterface
from src.web_scraping import url_to_detector, get_driver
from src.config import DEFAULT_VALUES
from src.utils import to_right_type, command_signature_to_description


# Load environment variables
env_values = dotenv_values(".env")
CHAT_ID = env_values["CHAT_ID"]
BOT_TOKEN = env_values["BOT_TOKEN"]



def command_execution_method(execute_something : Callable[[Update, CallbackContext], None]) -> Callable[[Update, CallbackContext], None]:
    """A decorator for command execution methods that will be called on commands. Purposes are :
    - Check if the chat is authorized.
    - Check if the user is admin.

    Args:
        execute_something (Callable[[Update, CallbackContext], None]): _description_

    Returns:
        Callable[[Update, CallbackContext], None]: _description_
    """
    def decorated_execute_something(self, update : Update, context : CallbackContext):
        try:
            # Check if chat is authorized.
            if update.message.chat_id != int(CHAT_ID):
                update.message.reply_text(
                    f"Error : You must use this bot on the authorized chat. \n"
                    + f"Authorized chat ID in your environment : {CHAT_ID} \n"
                    + f"This chat's ID : {update.message.chat_id}"
                )
                return
            return execute_something(self, update, context)
        # In case of exception, reply with a message.
        except Exception as e:
            update.message.reply_text(f"Python error in command function:\n{e}", disable_web_page_preview=True)
            print("Python error : ", e)
            return 
    
    return decorated_execute_something



class TelegramBot():
    """This class is the Telegram bot. It is responsible for doing the interface between the database, the web scraping and the Telegram API.
    """
    def  __init__(self):
        # Get webdriver
        self.driver = get_driver()
        # Connect to database and initialize parameters
        self.db_interface = DBInterface()
        # Connect to telegram and register commands
        self.updater = Updater(BOT_TOKEN)
        self.dispatcher = self.updater.dispatcher
        self.dispatcher.add_handler(CommandHandler("help", self.execute_help))
        self.dispatcher.add_handler(CommandHandler("watch", self.execute_watch))
        self.dispatcher.add_handler(CommandHandler("unwatch", self.execute_unwatch))
        self.dispatcher.add_handler(CommandHandler("check", self.execute_check))
        self.dispatcher.add_handler(CommandHandler("list", self.execute_list))
        self.dispatcher.add_handler(CommandHandler("status", self.execute_status))
        self.dispatcher.add_handler(CommandHandler("set", self.execute_set))
        self.dispatcher.add_handler(CommandHandler("get", self.execute_get))
        self.dispatcher.add_handler(CommandHandler("reset_db", self.execute_reset_db))
        self.dispatcher.add_handler(CommandHandler("print", self.execute_print))
        self.dispatcher.add_handler(CommandHandler("stop", self.execute_stop))

        # Bot is initialized
        print("Bot initialized")


    def start(self):
        """Start the bot and the main loop.
        """
        try:
            self.updater.bot.send_message(chat_id=CHAT_ID, text="Bot is running.", disable_web_page_preview=True)
        except:
            print("Warning : Bot is not running on the authorized chat. Please check the CHAT_ID environment variable.")
        self.updater.start_polling()

        self.set_parameter_in_db("stop", "False")

        last_global_check = None
        checking_frequency = to_right_type(self.get_parameter_from_db("checking_frequency"))
        stop = to_right_type(self.get_parameter_from_db("stop"))
        print("Bot started")

        while True:
            
            # Stop program if necessary
            if stop:
                print("Stopping the program. The program will then have to be restarted manually from the machine.")
                self.updater.bot.send_message(chat_id=CHAT_ID, text="Stopping the program.")
                self.updater.stop()
                self.db_interface.close()
                sys.exit()
            
            # Check tickets every checking_frequency seconds
            now = datetime.now()
            try:
                if last_global_check is None or (now - last_global_check).seconds > checking_frequency:
                    last_global_check = now
                    tickets_urls = self.get_ticket_urls()
                    for ticket_url in tickets_urls:
                        try:
                            detector = url_to_detector(ticket_url)
                            if detector.is_soldout(url=ticket_url, driver=self.driver):
                                # Send message
                                print(f"Ticket {ticket_url} is sold out !")
                                self.updater.bot.send_message(chat_id=CHAT_ID, text=f"Ticket {ticket_url} is sold out !", disable_web_page_preview=True)
                                # Remove ticket from watch list
                                self.db_interface.execute(f"DELETE FROM tickets_url WHERE url = ?", (ticket_url,))
                                self.db_interface.commit()
                        except Exception as e:
                            print(f"Error : Exception while checking ticket {ticket_url} : {e}")
                            self.updater.bot.send_message(chat_id=CHAT_ID, text=f"Error : Exception while checking ticket {ticket_url} : {e}", disable_web_page_preview=True)
                    # Update parameters of the python side from the database
                    checking_frequency = to_right_type(self.get_parameter_from_db("checking_frequency"))
                    stop = to_right_type(self.get_parameter_from_db("stop"))
            except Exception as e:
                print("Python error in main loop : ", e)
                self.updater.bot.send_message(chat_id=CHAT_ID, text=f"Error : error happened in main loop : {e}", disable_web_page_preview=True)


    def idle(self):
        self.updater.idle()


    def get_parameter_from_db(self, parameter_name : str) -> str:
        """Get the parameter value (string) corresponding to the parameter name in the database.

        Args:
            parameter_name (str): the name of the parameter

        Returns:
            str: the parameter value, as a string, or None, if the parameter is not found
        """
        return self.db_interface.get_parameter_from_db(parameter_name)
        
    def set_parameter_in_db(self, parameter_name : str, parameter_value : str):
        """Update the parameter value (string) corresponding to the parameter name in the database. The parameter must already exist.

        Args:
            parameter_name (str): the name of the parameter
            parameter_value (str): the new value of the parameter, as a string
        """
        self.db_interface.set_parameter_in_db(parameter_name, parameter_value)
    
    def is_ticket_existing(self, ticket_url : str) -> bool:
        """Return True if the ticket is already in the watch list, False otherwise.

        Args:
            ticket_url (str): the url of the ticket

        Returns:
            bool: whether the ticket is already in the watch list
        """
        return self.db_interface.is_ticket_existing(ticket_url)
        
    def get_ticket_urls(self) -> List[str]:
        """Get a list of the urls of the tickets in the watch list.

        Returns:
            List[str]: the list of the urls of the tickets in the watch list
        """
        return self.db_interface.get_ticket_urls()
        
    def get_parameters(self) -> Dict[str, str]:
        """Get the dictionary of the parameters.

        Returns:
            Dict[str, str]: a dict with the parameters names as keys and the parameters values as values (string)
        """
        return self.db_interface.get_parameters()



    ### ========== Main commands ========== ###

    @command_execution_method
    def execute_help(self, update : Update, context : CallbackContext):
        """Display a list of commands as well as their description."""
        message_text = update.message.text
        command_signature, *args = message_text.split()
        if len(args) != 0:
            update.message.reply_text("Error : Invalid number of arguments (should be exactly 0)", disable_web_page_preview=True)
            return
    
        # Answer with an help message
        message = "List of commands:\n"
        for command_signature, command_description in command_signature_to_description.items():
            message += f"{command_signature} : {command_description}\n"
        update.message.reply_text(message, disable_web_page_preview=True)



    @command_execution_method
    def execute_watch(self, update : Update, context : CallbackContext):
        """Add one or several urls to the watch list."""
        message_text = update.message.text
        command_signature, *args = message_text.split()
        if len(args) == 0:
            update.message.reply_text("Error : Invalid number of arguments (should be at least 1)", disable_web_page_preview=True)
            return
        
        answer_message = ""
        for ticket_url in args:
            # Check if ticket is already in watch list
            if self.is_ticket_existing(ticket_url):
                answer_message += f"Warning : Ticket {ticket_url} already in watch list.\n"
                continue
            # Check if url's associated site is detected
            detector = url_to_detector(ticket_url)
            if detector is None:
                answer_message += f"Error : Site not detected for ticket {ticket_url}.\n"
                continue
            # Add ticket to watch list
            self.db_interface.execute(f"INSERT INTO tickets_url (url) VALUES (?)", (ticket_url,))
            self.db_interface.commit()
            answer_message += f"Info : Ticket {ticket_url} added to watch list.\n"
        
        update.message.reply_text(answer_message, disable_web_page_preview=True)



    @command_execution_method
    def execute_unwatch(self, update : Update, context : CallbackContext):
        """Remove one or several urls from the watch list."""
        message_text = update.message.text
        command_signature, *args = message_text.split()
        if len(args) == 0:
            update.message.reply_text("Error : Invalid number of arguments (should be at least 1)", disable_web_page_preview=True)
            return
        
        answer_message = ""
        for ticket_url in args:
            # Check if ticket is in watch list
            if not self.is_ticket_existing(ticket_url):
                answer_message += f"Warning : Ticket {ticket_url} not in watch list.\n"
                continue
            # Remove ticket from watch list
            self.db_interface.execute(f"DELETE FROM tickets_url WHERE url = ?", (ticket_url,))
            self.db_interface.commit()
            answer_message += f"Info : Ticket {ticket_url} removed from watch list.\n"

        update.message.reply_text(answer_message, disable_web_page_preview=True)



    @command_execution_method
    def execute_check(self, update : Update, context : CallbackContext):
        """Check if one or several tickets are in the watch list and if they are sold out."""
        message_text = update.message.text
        command_signature, *args = message_text.split()
        if len(args) == 0:
            update.message.reply_text("Error : Invalid number of arguments (should be at least 1)", disable_web_page_preview=True)
            return
        
        waiting_message = f"Checking presence in watchlist and soldout status of {len(args)} tickets..."
        update.message.reply_text(waiting_message, disable_web_page_preview=True)

        answer_message = ""
        for ticket_url in args:
            ticket_line = f"Ticket {ticket_url} :\n"

            # Check if ticket is in watch list
            if self.is_ticket_existing(ticket_url):
                ticket_line += "In watchlist : Yes, "
            else:
                ticket_line += "In watchlist : No,  "
                
            # Check ticket status
            detector = url_to_detector(ticket_url)
            if detector is None:
                # Case 1 : site not detected
                ticket_line += "Status : site not detected."

            else:
                ticket_line += f"Site : {detector.get_name()}, "
                try:
                    if detector.is_soldout(url=ticket_url, driver=self.driver):
                        # Case 2 : sold out
                        ticket_line += "Status : sold out."
                    else:
                        # Case 3 : available
                        ticket_line += "Status : available."
                except Exception as e:
                    # Case 4 : error during check
                    ticket_line += f"Status : error : {e}"

            answer_message += ticket_line + "\n\n"
        update.message.reply_text(answer_message, disable_web_page_preview=True)
            


    @command_execution_method
    def execute_list(self, update : Update, context : CallbackContext):
        """List the tickets in the watch list."""
        message_text = update.message.text
        command_signature, *args = message_text.split()
        if len(args) >= 2:
            update.message.reply_text("Error : Invalid number of arguments (should be 0 or 1)", disable_web_page_preview=True)
            return
        
        if len(args) == 1:
            try:
                n_last_tickets = int(args[0])
            except:
                update.message.reply_text(f"Error : Invalid argument {args[0]} (should be an integer)", disable_web_page_preview=True)
                return
        else:
            n_last_tickets = sys.maxsize
        
        tickets_urls = self.get_ticket_urls()
        if len(tickets_urls) == 0:
            update.message.reply_text("Watch list is empty.")
            return
                
        tickets_urls = self.get_ticket_urls()
        answer = "Tickets watched:\n"
        for ticket_url in tickets_urls[:n_last_tickets]:
            answer += f"- {ticket_url}\n"
        update.message.reply_text(answer, disable_web_page_preview=True)



    @command_execution_method
    def execute_status(self, update : Update, context : CallbackContext):
        """Display the status of the bot : if it is running, the number of tickets watched, and the parameters."""
        message_text = update.message.text
        command_signature, *args = message_text.split()
        if len(args) != 0:
            update.message.reply_text("Error : Invalid number of arguments (should be exactly 0)", disable_web_page_preview=True)
            return
        
        tickets_urls = self.get_ticket_urls()
        parameter_dict = self.get_parameters()
        answer = "Bot is running.\n"
        answer += f"Tickets watched: {len(tickets_urls)}\n\n"
        answer += "Parameters:\n"
        for parameter_name, parameter_value in parameter_dict.items():
            answer += f"- {parameter_name}: {parameter_value}\n"
        update.message.reply_text(answer, disable_web_page_preview=True)



    # ========== Admin commands ========== #

    @command_execution_method
    def execute_set(self, update : Update, context : CallbackContext):
        """Set the value of a parameter."""
        message_text = update.message.text
        command_signature, *args = message_text.split()
        if len(args) != 2:
            update.message.reply_text("Error : Invalid number of arguments (should be exactly 2)", disable_web_page_preview=True)
            return
        
        parameter_name, parameter_value = args
        parameter_value_old = self.get_parameter_from_db(parameter_name)
        # Check if the parameter exist
        if parameter_value_old is None:
            update.message.reply_text(f"Parameter {parameter_name} not found")
            return
        # Check if the parameter already has the same value
        if parameter_value == parameter_value_old:
            update.message.reply_text(f"Parameter {parameter_name} value unchanged ({parameter_value})", disable_web_page_preview=True)
            return
        # Change the parameter value
        self.set_parameter_in_db(parameter_name, parameter_value)
        update.message.reply_text(f"Parameter {parameter_name} value changed from {parameter_value_old} to {parameter_value}")



    @command_execution_method
    def execute_get(self, update : Update, context : CallbackContext):
        """Display the value of a parameter."""
        message_text = update.message.text
        command_signature, *args = message_text.split()
        if len(args) != 1:
            update.message.reply_text("Error : Invalid number of arguments (should be exactly 1)", disable_web_page_preview=True)
            return
        
        parameter_name = args[0]
        parameter_value = self.get_parameter_from_db(parameter_name)
        # Check if the parameter exist
        if parameter_value is None:
            update.message.reply_text(f"Parameter {parameter_name} not found", disable_web_page_preview=True)
            return
        # Return the parameter value
        update.message.reply_text(f"Parameter {parameter_name} value: {parameter_value}")



    @command_execution_method
    def execute_reset_db(self, update : Update, context : CallbackContext):
        """Reset the database."""
        message_text = update.message.text
        command_signature, *args = message_text.split()
        if len(args) != 0:
            update.message.reply_text("Error : Invalid number of arguments (should be exactly 0)", disable_web_page_preview=True)
            return
        
        self.db_interface.remove_tables()
        self.db_interface.create_tables()
        update.message.reply_text("Database is reset.")
        print("Database is reset.")



    @command_execution_method
    def execute_stop(self, update : Update, context : CallbackContext):
        """Stop the program."""
        message_text = update.message.text
        command_signature, *args = message_text.split()
        if len(args) != 0:
            update.message.reply_text("Error : Invalid number of arguments (should be exactly 0)", disable_web_page_preview=True)
            return
        
        self.set_parameter_in_db("stop", "True")
        update.message.reply_text("Stopping the program. The program will then have to be restarted manually from the machine.", disable_web_page_preview=True)
        print("Stopping the program. The program will then have to be restarted manually from the machine.")



    ### ========== Minor commands ========== ###
    @command_execution_method
    def execute_print(self, update : Update, context : CallbackContext):
        """Print a message on the machine."""
        message_text = update.message.text
        print(f"Print command received: {message_text}")
        update.message.reply_text("Message printed on machine.")