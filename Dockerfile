# Usa un'immagine Python ufficiale come base
FROM python:3.9-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file del progetto nella directory di lavoro
COPY . /app

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Esponi la porta su cui l'app ascolterà
EXPOSE 5000

# Imposta la variabile d'ambiente per Flask
ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0

# Comando per eseguire l'app Flask
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
