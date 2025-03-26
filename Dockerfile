# Usa un'immagine di base Python
FROM python:3.9-slim

# Crea una cartella di lavoro all'interno del contenitore
WORKDIR /app

# Copia i file del progetto nella cartella di lavoro
COPY . .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Espone la porta su cui l'app ascolterà (5000 per Flask)
EXPOSE 5000

# Comando per avviare l'app
CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]

