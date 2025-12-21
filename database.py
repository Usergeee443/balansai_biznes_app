"""
Database connection module
Bot bilan bir xil MySQL database bilan ishlaydi
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """
    MySQL database connection yaratadi
    Environment variables orqali config qilinadi
    """
    try:
        connection = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'balansai_db'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30
        )
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """
    Database query'ni bajaradi
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                result = cursor.lastrowid
            connection.commit()
            return result
    except Exception as e:
        connection.rollback()
        print(f"Query execution error: {e}")
        raise
    finally:
        connection.close()

