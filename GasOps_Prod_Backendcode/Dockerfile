# FROM python:3.10
 
# # Set environment variables
# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1
 
# # Set working directory
# WORKDIR /app
 
# # Install system dependencies
# RUN apt-get update && apt-get install -y \
#     curl \
#     gnupg \
#     apt-transport-https \
#     ca-certificates \
#     build-essential \
#     unixodbc-dev \
#     lsb-release
 
# # Install Microsoft ODBC 17 Driver and tools for Ubuntu
# RUN curl -sSL -O https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb \
#     && dpkg -i packages-microsoft-prod.deb \
#     && rm packages-microsoft-prod.deb \
#     && apt-get update \
#     && ACCEPT_EULA=Y apt-get install -y msodbcsql17 mssql-tools \
#     && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*
 
# # Install Python dependencies
# COPY requirements.txt .
# RUN pip install --upgrade pip && pip install -r requirements.txt
 
# # Copy application code
# COPY . .
 
# # Expose FastAPI port
# EXPOSE 8000
 
# # Start FastAPI app with Uvicorn
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gnupg \
    curl \
    unixodbc \
    unixodbc-dev \
    odbcinst \
    build-essential

# RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
#     curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
#     apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18

RUN apt install -y freetds-dev freetds-bin unixodbc unixodbc-dev tdsodbc

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "app:app"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

