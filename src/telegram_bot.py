from datetime import datetime
from email import message
import subprocess
import sys
from typing import Callable, Dict, List, Tuple, Type
from src.config import DEFAULT_VALUES
from src.interface_database import DBInterface

from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, filters
from telegram import Update

from selenium import webdriver
from selenium.webdriver.common.by import By

from src.web_scraping import url_to_detector
from src.utils import to_right_type, command_signature_to_description

from dotenv import dotenv_values

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
            update.message.reply_text(f"Python error :\n{e}", disable_web_page_preview=True)
            print("Python error : ", e)
            return 
    
    return decorated_execute_something



class TelegramBot():

    def  __init__(self):
        # Get webdriver
        self.driver = webdriver.Firefox("driver")
        # Connect to database and initialize parameters
        self.db_interface = DBInterface()
        for parameter_name, default_parameter_value in DEFAULT_VALUES.items():
            assert type(default_parameter_value) == str, f"Default value of parameter {parameter_name} is not a string in the config file."
            if self.get_parameter_from_db(parameter_name) is None:
                self.db_interface.execute(f"INSERT INTO parameters (name, value) VALUES ('{parameter_name}', '{default_parameter_value}')")
                self.db_interface.commit()
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
        self.updater.bot.send_message(chat_id=CHAT_ID, text="Bot is running.", disable_web_page_preview=True)
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
                sys.exit()
            
            # Check tickets every checking_frequency seconds
            now = datetime.now()
            if last_global_check is None or (now - last_global_check).seconds > checking_frequency:
                last_global_check = now
                tickets_urls = self.get_ticket_urls()
                for ticket_url in tickets_urls:
                    detector = url_to_detector(ticket_url)
                    if detector.is_soldout(url=ticket_url, driver=self.driver):
                        # Send message
                        print(f"Ticket {ticket_url} is sold out !")
                        self.updater.bot.send_message(chat_id=CHAT_ID, text=f"Ticket {ticket_url} is sold out !", disable_web_page_preview=True)
                        # Remove ticket from watch list
                        self.db_interface.execute(f"DELETE FROM tickets_url WHERE url = '{ticket_url}'")
                        self.db_interface.commit()
                # Update parameters of the python side from the database
                checking_frequency = to_right_type(self.get_parameter_from_db("checking_frequency"))
                stop = to_right_type(self.get_parameter_from_db("stop"))


    def idle(self):
        self.updater.idle()


    def get_parameter_from_db(self, parameter_name : str) -> str:
        self.db_interface.execute(f"SELECT value FROM parameters WHERE name = '{parameter_name}'")
        list_of_rows_with_correct_name = self.db_interface.fetchall()
        if len(list_of_rows_with_correct_name) == 0:
            return None
        else:
            value = list_of_rows_with_correct_name[0][0]
            return value
        
    def set_parameter_in_db(self, parameter_name : str, parameter_value : str):
        self.db_interface.execute(f"UPDATE parameters SET value = '{parameter_value}' WHERE name = '{parameter_name}'")
        self.db_interface.commit()
    
    def is_ticket_existing(self, ticket_url : str) -> bool:
        self.db_interface.execute(f"SELECT url FROM tickets_url WHERE url = '{ticket_url}'")
        list_of_rows_with_correct_url = self.db_interface.fetchall()
        if len(list_of_rows_with_correct_url) == 0:
            return False
        else:
            return True
        
    def get_ticket_urls(self) -> List[str]:
        self.db_interface.execute(f"SELECT url FROM tickets_url")
        list_of_rows = self.db_interface.fetchall()
        return [row[0] for row in list_of_rows]
        
    def get_parameters(self) -> Dict[str, str]:
        self.db_interface.execute(f"SELECT name, value FROM parameters")
        list_of_rows = self.db_interface.fetchall()
        return {row[0] : row[1] for row in list_of_rows}



    ### ========== Main commands ========== ###

    @command_execution_method
    def execute_help(self, update : Update, context : CallbackContext):
        message_text = update.message.text
        command_signature, *args = message_text.split(" ")
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
        message_text = update.message.text
        command_name, *args = message_text.split(" ")
        if len(args) != 1:
            update.message.reply_text("Error : Invalid number of arguments (should be exactly 1)", disable_web_page_preview=True)
            return
        
        ticket_url = args[0]
        # Check if ticket is already in watch list
        if self.is_ticket_existing(ticket_url):
            update.message.reply_text(f"Warning : Ticket {ticket_url} already in watch list.", disable_web_page_preview=True)
            return
        # Check if url's associated site is detected
        detector = url_to_detector(ticket_url)
        if detector is None:
            update.message.reply_text(f"Error : Site not detected.", disable_web_page_preview=True)
            return
        # Add ticket to watch list
        self.db_interface.execute(f"INSERT INTO tickets_url (url) VALUES ('{ticket_url}')")
        self.db_interface.commit()
        update.message.reply_text(f"Info : Ticket {ticket_url} added to watch list.", disable_web_page_preview=True)



    @command_execution_method
    def execute_unwatch(self, update : Update, context : CallbackContext):
        message_text = update.message.text
        command_name, *args = message_text.split(" ")
        if len(args) != 1:
            update.message.reply_text("Error : Invalid number of arguments (should be exactly 1)", disable_web_page_preview=True)
            return
        
        ticket_url = args[0]
        # Check if indeed ticket is in watch list
        if not self.is_ticket_existing(ticket_url):
            update.message.reply_text(f"Error : Ticket {ticket_url} not in watch list.", disable_web_page_preview=True)
            return
        # Remove ticket from watch list
        self.db_interface.execute(f"DELETE FROM tickets_url WHERE url = '{ticket_url}'")
        self.db_interface.commit()
        update.message.reply_text(f"Info : Ticket {ticket_url} removed from watch list.", disable_web_page_preview=True)



    @command_execution_method
    def execute_check(self, update : Update, context : CallbackContext):
        message_text = update.message.text
        command_name, *args = message_text.split(" ")
        if len(args) != 1:
            update.message.reply_text("Error : Invalid number of arguments (should be exactly 1)", disable_web_page_preview=True)
            return
        
        ticket_url = args[0]
        # Check if ticket is in watch list
        if not self.is_ticket_existing(ticket_url):
            update.message.reply_text(f"Ticket is NOT in watch list.")
        else:
            update.message.reply_text(f"Ticket is in watch list.")
        
        detector = url_to_detector(ticket_url)
        # Check if url's associated site is detected
        if detector is None:
            update.message.reply_text(f"Error : Site not detected.")
            return
        # Check if ticket is sold out or not
        if detector.is_soldout(url=ticket_url, driver=self.driver):
            update.message.reply_text(f"Ticket is sold out :(")
        else:
            update.message.reply_text(f"Ticket is NOT sold out :D")
            


    @command_execution_method
    def execute_list(self, update : Update, context : CallbackContext):
        message_text = update.message.text
        command_name, *args = message_text.split(" ")
        if len(args) != 0:
            update.message.reply_text("Error : Invalid number of arguments (should be exactly 0)", disable_web_page_preview=True)
            return
        
        tickets_urls = self.get_ticket_urls()
        answer = "Tickets watched:\n"
        for ticket_url in tickets_urls:
            answer += f"- {ticket_url}\n"
        update.message.reply_text(answer, disable_web_page_preview=True)



    @command_execution_method
    def execute_status(self, update : Update, context : CallbackContext):
        message_text = update.message.text
        command_name, *args = message_text.split(" ")
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
        message_text = update.message.text
        command_name, *args = message_text.split(" ")
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
        message_text = update.message.text
        command_name, *args = message_text.split(" ")
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
        message_text = update.message.text
        command_name, *args = message_text.split(" ")
        if len(args) != 0:
            update.message.reply_text("Error : Invalid number of arguments (should be exactly 0)", disable_web_page_preview=True)
            return
        
        self.db_interface.remove_tables()
        self.db_interface.create_tables()
        update.message.reply_text("Database is reset.")
        print("Database is reset.")



    @command_execution_method
    def execute_stop(self, update : Update, context : CallbackContext):
        message_text = update.message.text
        command_name, *args = message_text.split(" ")
        if len(args) != 0:
            update.message.reply_text("Error : Invalid number of arguments (should be exactly 0)", disable_web_page_preview=True)
            return
        
        self.set_parameter_in_db("stop", "True")
        update.message.reply_text("Stopping the program. The program will then have to be restarted manually from the machine.", disable_web_page_preview=True)
        print("Stopping the program. The program will then have to be restarted manually from the machine.")



    ### ========== Minor commands ========== ###
    @command_execution_method
    def execute_print(self, update : Update, context : CallbackContext):
        message_text = update.message.text
        print(f"Print command received: {message_text}")
        update.message.reply_text("Message printed on machine.")