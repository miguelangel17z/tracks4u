FROM python:3.11-slim

WORKDIR /app

# instalar dependencias del sistema primero
RUN apt-get update && apt-get install -y gettext && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]