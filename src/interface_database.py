import sqlite3
from typing import Dict, List
from src.config import DEFAULT_VALUES
DATABASE_PATH = "database.db"



class DBInterface:

    def __init__(self):
        # Create SQL objects
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        for parameter_name, default_parameter_value in DEFAULT_VALUES.items():
            assert type(default_parameter_value) == str, f"Default value of parameter {parameter_name} is not a string in the config file."
            if self.get_parameter_from_db(parameter_name) is None:
                self.execute(f"INSERT INTO parameters (name, value) VALUES ('{parameter_name}', '{default_parameter_value}')")
                self.commit()

    def create_tables(self):
        # Create empty ticket table
        self.execute('''CREATE TABLE IF NOT EXISTS tickets_url
                (url TEXT PRIMARY KEY)''')
        # Create parameters table and add the default values
        self.execute('''CREATE TABLE IF NOT EXISTS parameters
                (name TEXT PRIMARY KEY, value TEXT)''')
        for name, value in DEFAULT_VALUES.items():
            self.execute(f"INSERT OR IGNORE INTO parameters (name, value) VALUES ('{name}', '{value}')")
        self.commit()

    def remove_tables(self):
        self.execute("DROP TABLE IF EXISTS tickets_url")
        self.execute("DROP TABLE IF EXISTS parameters")
        self.commit()

    def get_parameter_from_db(self, parameter_name : str) -> str:
        """Get the parameter value (string) corresponding to the parameter name in the database.

        Args:
            parameter_name (str): the name of the parameter

        Returns:
            str: the parameter value, as a string, or None, if the parameter is not found
        """
        self.execute(f"SELECT value FROM parameters WHERE name = '{parameter_name}'")
        list_of_rows_with_correct_name = self.fetchall()
        if len(list_of_rows_with_correct_name) == 0:
            return None
        else:
            value = list_of_rows_with_correct_name[0][0]
            return value
        
    def set_parameter_in_db(self, parameter_name : str, parameter_value : str):
        """Update the parameter value (string) corresponding to the parameter name in the database. The parameter must already exist.

        Args:
            parameter_name (str): the name of the parameter
            parameter_value (str): the new value of the parameter, as a string
        """
        self.execute(f"UPDATE parameters SET value = '{parameter_value}' WHERE name = '{parameter_name}'")
        self.commit()

    def is_ticket_existing(self, ticket_url : str) -> bool:
        """Return True if the ticket is already in the watch list, False otherwise.

        Args:
            ticket_url (str): the url of the ticket

        Returns:
            bool: whether the ticket is already in the watch list
        """
        self.execute(f"SELECT url FROM tickets_url WHERE url = '{ticket_url}'")
        list_of_rows_with_correct_url = self.fetchall()
        if len(list_of_rows_with_correct_url) == 0:
            return False
        else:
            return True
        
    def get_ticket_urls(self) -> List[str]:
        """Get a list of the urls of the tickets in the watch list.

        Returns:
            List[str]: the list of the urls of the tickets in the watch list
        """
        self.execute(f"SELECT url FROM tickets_url")
        list_of_rows = self.fetchall()
        return [row[0] for row in list_of_rows]
        
    def get_parameters(self) -> Dict[str, str]:
        """Get the dictionary of the parameters.

        Returns:
            Dict[str, str]: a dict with the parameters names as keys and the parameters values as values (string)
        """
        self.execute(f"SELECT name, value FROM parameters")
        list_of_rows = self.fetchall()
        return {row[0] : row[1] for row in list_of_rows}
    
    def close(self):
        self.cursor.close()
        self.conn.close()

    def execute(self, query : str):
        self.cursor.execute(query)

    def commit(self):
        self.conn.commit()

    def fetchall(self):
        return self.cursor.fetchall()