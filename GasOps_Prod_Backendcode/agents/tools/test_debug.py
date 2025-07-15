# import pymssql
import os
from dotenv import load_dotenv
import pyodbc
load_dotenv()

SERVER = os.getenv("SERVER")
DATABASE_CEDEMO = os.getenv("DATABASE_CEDEMO")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# SERVER='10.0.1.9'
# DATABASE_CEDEMO='CEDEMONEW0314'
# DATABASE_OAMSCM='OAMSCM'
USERNAME='QuadrantAIUser'
# PASSWORD='QU1R19T19E19@12'

# dev

# Connection string for Azure SQL Database
# SERVER='sql-dev-vm.eastus.cloudapp.azure.com'
# DATABASE_CEDEMO='CEDEMONEW0314'
# DATABASE_OAMSCM='OAMSCM'
# USERNAME='QuadrantUser'
# PASSWORD='Quadrant25'

print(f"Connecting to {SERVER} as {USERNAME} on database {DATABASE_CEDEMO}")

try:
    # conn = pymssql.connect(
    #     server=SERVER,
    #     port=1433,
    #     user=USERNAME,
    #     password=PASSWORD,
    #     database=DATABASE_CEDEMO,
    #     login_timeout=10
    # )
    
    # print("Connection successful!")
    # conn.close()
    
    
    conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE_CEDEMO};"
    f"UID={USERNAME};"
    f"PWD={PASSWORD};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    row = cursor.fetchone()
    print("Connection successful! SQL Server version:", row[0])
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")