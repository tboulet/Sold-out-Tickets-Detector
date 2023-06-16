import sqlite3



DATABASE_PATH = "database.db"



class DBInterface:

    def __init__(self):
        # Create SQL objects
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.execute('''CREATE TABLE IF NOT EXISTS tickets_url
                (url TEXT PRIMARY KEY)''')
        self.execute('''CREATE TABLE IF NOT EXISTS parameters
                (name TEXT PRIMARY KEY, value TEXT)''')
        self.commit()

    def remove_tables(self):
        self.execute("DROP TABLE IF EXISTS tickets_url")
        self.execute("DROP TABLE IF EXISTS parameters")
        self.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()

    def execute(self, query : str):
        self.cursor.execute(query)

    def commit(self):
        self.conn.commit()

    def fetchall(self):
        return self.cursor.fetchall()