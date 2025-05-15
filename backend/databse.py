import mysql.connector
from datetime import datetime, timedelta
from config import app_config

class Database:
    """Database connection manager and helper functions."""
    
    @staticmethod
    def get_connection():
        """Create and return a new database connection."""
        return mysql.connector.connect(
            host=app_config.DB_HOST,
            user=app_config.DB_USER,
            password=app_config.DB_PASSWORD,
            database=app_config.DB_NAME
        )
    
    @staticmethod
    def execute_query(query, params=None, fetch=False, fetch_one=False, commit=False):
        """
        Execute a database query with parameters.
        
        Args:
            query (str): SQL query to execute
            params (tuple, list, dict): Parameters for the query
            fetch (bool): Whether to fetch all results
            fetch_one (bool): Whether to fetch one result
            commit (bool): Whether to commit the transaction
            
        Returns:
            Result data if fetch or fetch_one is True, otherwise None
        """
        conn = Database.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute(query, params)
            
            if fetch:
                result = cursor.fetchall()
            elif fetch_one:
                result = cursor.fetchone()
            else:
                result = None
                
            if commit:
                conn.commit()
                
            return result
        
        except Exception as e:
            if commit:
                conn.rollback()
            raise e
        
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def insert(table, data):
        """
        Insert data into a table.
        
        Args:
            table (str): Table name
            data (dict): Dictionary of column_name: value pairs
            
        Returns:
            int: Last insert ID
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, list(data.values()))
            conn.commit()
            return cursor.lastrowid
        
        except Exception as e:
            conn.rollback()
            raise e
        
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def update(table, data, condition, condition_params):
        """
        Update data in a table.
        
        Args:
            table (str): Table name
            data (dict): Dictionary of column_name: value pairs to update
            condition (str): WHERE condition
            condition_params (tuple): Parameters for the condition
            
        Returns:
            int: Number of rows affected
        """
        set_clause = ', '.join([f"{column} = %s" for column in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        
        params = list(data.values()) + list(condition_params)
        
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        
        except Exception as e:
            conn.rollback()
            raise e
        
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def delete(table, condition, params):
        """
        Delete data from a table.
        
        Args:
            table (str): Table name
            condition (str): WHERE condition
            params (tuple): Parameters for the condition
            
        Returns:
            int: Number of rows affected
        """
        query = f"DELETE FROM {table} WHERE {condition}"
        
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        
        except Exception as e:
            conn.rollback()
            raise e
        
        finally:
            cursor.close()
            conn.close()