


from typing import Dict


def to_right_type(string : str):
    try:
        number = int(string)  # Try converting to int
        return number
    except ValueError:
        try:
            number = float(string)  # Try converting to float
            return number
        except ValueError:
            if string == "None":
                return None
            elif string in ["False", "false", "0"]:
                return False
            elif string in ["True", "true", "1"]:
                return True
            else:
                return string  # Return string if it can't be converted to a number
            


command_signature_to_description : Dict[str, str] = {
    "/help" : "Display this message",
    "/watch <url>" : "Add a new ticket's url to watch",
    "/unwatch <url>" : "Remove a ticket's url from the watchlist",
    "/list" : "List all the tickets currently being watched",
    "/check <url>" : "Check instantly if the ticket is watched and if it is soldout",
    "/set <parameter name> <value>" : "Set a parameter to a new value",
    "/get <parameter name>" : "Get the value of a parameter",
    "/status" : "Get the status of the bot",
    "/reset_db" : "Delete the whole database (tickets and parameters) and recreate a new one",
    "/print <anything>" : "Print this command in the console",
    "/stop" : "Stop the program. The program will then have to be restarted manually from the machine",
}