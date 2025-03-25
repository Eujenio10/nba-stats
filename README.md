# NBA Stats API

API per statistiche NBA con sistema di chiavi one-to-one.

## Funzionalità

- Sistema di autenticazione con chiavi uniche
- Protezione contro la condivisione delle chiavi (one device per key)
- Endpoint per statistiche NBA, inclusi:
  - Statistiche difensive delle squadre
  - Elenco giocatori infortunati
  - Partite in programma
  - Statistiche e analisi dei giocatori
  - Analisi delle tendenze e consistenza dei giocatori
- Supporto per deployment su Render

## Sistema di Chiavi

Questa API utilizza un sistema di chiavi one-to-one che:

1. Associa ogni chiave a un singolo dispositivo (machine ID)
2. Blocca automaticamente le chiavi utilizzate da dispositivi diversi
3. Tiene traccia dell'utilizzo delle chiavi
4. Supporta date di scadenza per le chiavi

## Struttura del Progetto

- `webapp.py`: Applicazione Flask principale che espone le API
- `nba_stats_appv.py`: Codice sorgente per le funzionalità di statistiche NBA
- `requirements.txt`: Dipendenze Python necessarie
- `render.yaml`: Configurazione per il deployment su Render
- `Procfile`: Configurazione per Gunicorn
- `.env`: Variabili d'ambiente (non committare su GitHub)

## API Endpoints

### Autenticazione

#### Verifica Chiave

```
POST /api/verify-key
Content-Type: application/json

{
  "key": "your-api-key",
  "machine_id": "unique-device-identifier"
}
```

#### Generazione Nuove Chiavi (Admin)

```
POST /api/admin/generate-key
Content-Type: application/json

{
  "admin_password": "your-admin-password",
  "expiry_days": 365
}
```

### Statistiche NBA

Tutti gli endpoint richiedono autenticazione tramite header:
```
X-API-Key: your-api-key
X-Machine-ID: your-machine-id
```

#### Squadre e Partite

```
GET /api/stats/team-defense?sort_by_points=true
```

```
GET /api/stats/injured-players
```

```
GET /api/stats/upcoming-games
```

#### Statistiche Giocatori

```
GET /api/stats/player?name=LeBron%20James
```

```
GET /api/stats/player/last-games?name=LeBron%20James&num_games=10
```

```
GET /api/stats/player/analyze-trends?name=LeBron%20James&prop_type=points&line_value=25.5
```

```
GET /api/stats/consistent-players
```

```
GET /api/stats/player-vs-team?name=LeBron%20James&team=LAL&num_games=10
```

```
GET /api/stats/next-opponent?name=LeBron%20James
```

### Controllo Stato

```
GET /api/health
```

## Deployment su Render

### Prerequisiti

- Account Render
- Repository GitHub con il codice

### Passaggi per il Deployment

1. Carica il codice su GitHub (assicurati di non includere .env)
2. Accedi a [Render](https://render.com)
3. Crea un nuovo Web Service
4. Collega il repository GitHub
5. Configura il servizio:
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn webapp:app`
6. Configura le variabili d'ambiente:
   - `ADMIN_PASSWORD`: Password per generare nuove chiavi API
   - `FLASK_ENV`: production
   - `PYTHON_VERSION`: 3.10.7

Alternativamente, puoi usare il Blueprint di Render che configurerà automaticamente il servizio e il database tramite il file `render.yaml`.

## Sviluppo Locale

1. Clona il repository
2. Crea un file `.env` con le variabili d'ambiente necessarie
3. Installa le dipendenze: `pip install -r requirements.txt`
4. Avvia il server: `python webapp.py`

## Licenza

MIT 