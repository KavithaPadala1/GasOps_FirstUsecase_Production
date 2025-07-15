# import pymssql
import os
from dotenv import load_dotenv
import pyodbc
load_dotenv()

SERVER = os.getenv("SERVER")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
DATABASE_CEDEMO='CEDEMONEW0314'


USERNAME='QuadrantAIUser'


# dev

# # Connection string for Azure SQL Database
# SERVER='sql-dev-vm.eastus.cloudapp.azure.com'
# # SERVER = '10.1.0.5'
# DATABASE_CEDEMO='CEDEMO0418'
# DATABASE_OAMSCM='OAMSCM'
# USERNAME='QuadrantUser'
# PASSWORD='Quadrant25'

# SERVER='sql-dev-vm.eastus.cloudapp.azure.com'


print(f"Connecting to {SERVER} as {USERNAME} on database {DATABASE_CEDEMO}")


# testing with sql query
# sql_query = """
# SELECT DISTINCT crswf.WorkActivityFunctionID 
# FROM ContractorRouteSheetWorkDescription AS crswd
# JOIN ContractorRouteSheetWorkDescriptiontoWAFMap AS crswf
#   ON crswd.ContractorRouteSheetWorkDescriptionID = crswf.ContractorRouteSheetWorkDescriptionID
# WHERE crswd.WorkDescription LIKE '%Excavate%' AND crswf.IsActive = 1;
# """

sql_query = "SELECT distinct WorkDescription FROM ContractorRouteSheetWorkDescription "

try: 
    # SERVER = 'host.docker.internal'

    conn_str = (
    # "DRIVER={ODBC Driver 18 for SQL Server};"
    "DRIVER={FreeTDS};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE_CEDEMO};"
    f"UID={USERNAME};"
    f"PWD={PASSWORD};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)
    # conn_str = pyodbc.connect('DRIVER={FreeTDS};SERVER=10.0.1.9,1433;DATABASE=CEDEMONEW0314;UID=QuadrantAIUser;PWD=QU1R19T19E19@12;Encrypt=yes;TrustServerCertificate=yes;')

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    row = cursor.fetchone()
    print("Connection successful! SQL Server version:", row[0])
    
    
    # Execute your custom query
    cursor.execute(sql_query)
    results = cursor.fetchall()
    
    for result in results:
        print(f"Connecting to {SERVER} as {USERNAME} on database {DATABASE_CEDEMO}")
        print(result[0])
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")