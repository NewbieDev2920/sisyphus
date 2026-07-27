import sqlite3
import os
from domain.ports.database_models import BotLog
from domain.ports.database_models import PriceRecord
#db_path debe estar en el .env
class CRUDHandler:
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

    def create_logs_table(self):

        #POSTMAN IS THE CLASS/OBJECT TYPE THAT REPORTED THE MESSAGE.

        #Possible types
        #1) Order
        #2) Trade
        #3) Notification (Example: "STOP-LOSS EXECUTED SYMBOL SOLD", "EWMA WARNING",etc...)
        #4) Error messages

        query = '''
        CREATE TABLE IF NOT EXISTS bot_logs (
        id INTEGER PRIMARY KEY,
        date TEXT NOT NULL,
        postman TEXT,
        value TEXT NOT NULL,
        purgeable INTEGER NOT NULL,
        log_type INTEGER
        )
        '''

        self.cursor.execute(query)
        self.connection.commit()

    def create_prices_table(self):
        
        query = '''
        CREATE TABLE IF NOT EXISTS price_records (
        id INTEGER PRIMARY KEY,
        date TEXT NOT NULL,
        symbol TEXT,
        value REAL NOT NULL,
        purgeable INT NOT NULL
        )
        '''

        self.cursor.execute(query)
        self.connection.commit()

    def create_bot_log(self, log : BotLog):
        
        query = '''
        INSERT INTO bot_logs (date, postman, value, purgeable, log_type) VALUES (?,?,?,?,?)
        '''
        instance_data = (log.date,log.postman,log.value,log.purgeable,log.log_type)
        self.cursor.execute(query, instance_data)
        self.connection.commit()

    def create_price_record(self, price : PriceRecord):
        
        query = '''
        INSERT INTO price_records (date,symbol,value,purgeable) VALUES (?,?,?,?)
        '''

        instance_data = (price.date,price.symbol,price.value,price.purgeable)
        self.cursor.execute(query, instance_data)
        self.connection.commit()

    def read_all_bot_logs(self):
        """
        WARNING.
        THIS METHOD CAN BE COMPUTATIONALLY EXPENSIVE. IT CAN AFFECT IN SEVERE MANNER THE RUNTIME.
        """
        query='''
        SELECT * FROM bot_logs
        '''

        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        return rows

    def read_all_price_records(self):
        """
        WARNING.
        THIS METHOD CAN BE COMPUTATIONALLY EXPENSIVE. IT CAN AFFECT IN SEVERE MANNER THE RUNTIME.
        """

        query = '''
        SELECT * FROM price_records
        '''

        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        return rows

    #It is possible update of information is unnecessary for this project.
    def update_bot_log(self):
        pass

    #It is possible update of information is unnecessary for this project.
    def update_price_record(self):
        pass

    def delete_bot_log(self, id : int):

        """
        DO NOT RUN BEFORE CHECKING IF ROW IS "PURGEABLE". POSSIBLE COMPROMISING DATA LOSS.
        """

        query = '''
        DELETE FROM bot_logs WHERE id = ?
        '''

        self.cursor.execute(query, id)
        self.connection.commit()

    def delete_price_record(self, id: int):

        """
        DO NOT RUN BEFORE CHECKING IF ROW IS "PURGEABLE". POSSIBLE COMPROMISING DATA LOSS.
        """

        query = '''
        DELETE FROM price_records WHERE id = ?
        '''

        self.cursor.execute(query, id)
        self.connection.commit()

    def bot_logs_length(self) -> int:

        """
        Time complexity : O(n)
        """

        query = """
        SELECT COUNT(*) FROM bot_logs
        """

        self.cursor.execute(query)
        row_length = self.cursor.fetchone()[0]
        return row_length

    def price_records_length(self) -> int:

        """
        Time Complexity: O(n)
        """

        query = """
        SELECT COUNT(*) FROM price_records
        """

        self.cursor.execute(query)
        row_length = self.cursor.fetchone()[0]
        return row_length

    def database_size(self):
        """
        O(1)
        """
        return os.path.getsize(self.db_path)

    def approximate_bot_logs_size(self):
        """
        This method returns an approximation of the table size.
        O(n)
        """
        query = """
        SELECT SUM(LENGTH(id) + LENGTH(date)+ LENGTH(postman) +  LENGTH(value) +  LENGTH(purgeable) + LENGTH(log_type)) FROM bot_logs
        """

        self.cursor.execute(query)
        return self.cursor.fetchone()[0]
        

    def approximate_price_records_size(self):
        """
        This method returns an approximation of the table size.
        O(n)
        """

        query = """
        SELECT SUM(LENGTH(id)+LENGTH(date)+LENGTH()+LENGTH(symbol)+LENGTH(value)+LENGTH(purgeable)) FROM price_records
        """
        self.cursor.execute(query)
        return self.cursor.fetchone()[0]
    
    def execute_query(self, query):
        """
        Avoid using this method.
        """
        self.cursor.execute(query)
        response = self.cursor.fetchall()
        self.connection.commit()
        return response
            





    


    

