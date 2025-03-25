# NBA Stats API

This is the web API version of the NBA Stats application, designed to be deployed on Render.

## Setup

1. Create a new web service on Render
2. Connect your GitHub repository
3. Configure the following environment variables in Render:
   - `DATABASE_URL`: Your PostgreSQL database URL (Render will provide this automatically if you create a PostgreSQL database)
   - `PORT`: Will be set automatically by Render

## Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with:
```
DATABASE_URL=sqlite:///keys.db
```

4. Run the application:
```bash
python main.py
```

## API Endpoints

All endpoints except `/api/verify-key` require an API key to be passed in the `X-API-Key` header.

- `POST /api/verify-key`: Verify an API key
- `GET /api/stats/defensive-ranking`: Get team defensive rankings
- `GET /api/stats/injured-players`: Get list of injured players
- `GET /api/stats/upcoming-games`: Get upcoming games
- `GET /api/health`: Health check endpoint

## Database

The application uses SQLAlchemy with PostgreSQL in production and SQLite for local development. The database stores API keys and their expiration dates. 