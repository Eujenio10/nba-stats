import tkinter as tk
from tkinter import ttk, messagebox
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamgamelog, scoreboardv2, playercareerstats, playergamelog, commonteamroster
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import locale
from PIL import Image, ImageTk
import io
import urllib.request
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import threading
import re
import pytz
from nba_api.stats.endpoints import leaguedashplayerstats
import hashlib
import json
import os
import uuid
import platform
import sys
import math

# Impostazione locale italiana per la formattazione delle date
try:
    locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')  # Linux/Mac
except:
    try:
        locale.setlocale(locale.LC_TIME, 'ita_ita')  # Windows
    except:
        pass  # Se fallisce, utilizzeremo una formattazione manuale

# Configurazione timeout e headers per le richieste NBA API
from nba_api.stats.library.http import NBAStatsHTTP
NBAStatsHTTP.timeout = 60  # Aumentiamo il timeout a 60 secondi

# Dizionario per tradurre i nomi delle squadre NBA in italiano
traduzioni_squadre = {
    "Atlanta Hawks": "Atlanta Hawks",
    "Boston Celtics": "Boston Celtics",
    "Brooklyn Nets": "Brooklyn Nets",
    "Charlotte Hornets": "Charlotte Hornets",
    "Chicago Bulls": "Chicago Bulls",
    "Cleveland Cavaliers": "Cleveland Cavaliers",
    "Dallas Mavericks": "Dallas Mavericks",
    "Denver Nuggets": "Denver Nuggets",
    "Detroit Pistons": "Detroit Pistons",
    "Golden State Warriors": "Golden State Warriors",
    "Houston Rockets": "Houston Rockets",
    "Indiana Pacers": "Indiana Pacers",
    "LA Clippers": "LA Clippers",
    "Los Angeles Lakers": "Los Angeles Lakers",
    "Memphis Grizzlies": "Memphis Grizzlies",
    "Miami Heat": "Miami Heat",
    "Milwaukee Bucks": "Milwaukee Bucks",
    "Minnesota Timberwolves": "Minnesota Timberwolves",
    "New Orleans Pelicans": "New Orleans Pelicans",
    "New York Knicks": "New York Knicks",
    "Oklahoma City Thunder": "Oklahoma City Thunder",
    "Orlando Magic": "Orlando Magic",
    "Philadelphia 76ers": "Philadelphia 76ers",
    "Phoenix Suns": "Phoenix Suns",
    "Portland Trail Blazers": "Portland Trail Blazers",
    "Sacramento Kings": "Sacramento Kings",
    "San Antonio Spurs": "San Antonio Spurs",
    "Toronto Raptors": "Toronto Raptors",
    "Utah Jazz": "Utah Jazz",
    "Washington Wizards": "Washington Wizards"
}

# Dizionario per tradurre i mesi in italiano
traduzioni_mesi = {
    "Jan": "Gen",
    "Feb": "Feb",
    "Mar": "Mar",
    "Apr": "Apr",
    "May": "Mag",
    "Jun": "Giu",
    "Jul": "Lug",
    "Aug": "Ago",
    "Sep": "Set",
    "Oct": "Ott",
    "Nov": "Nov",
    "Dec": "Dic"
}

# Costanti per il tema magico
MAGIC_COLORS = {
    'background': '#1a1a1a',    # Sfondo scuro
    'text': '#FFD700',         # Testo dorato
    'button': '#4B0082',       # Bottone indaco
    'button_hover': '#6A5ACD', # Bottone hover viola chiaro
    'error': '#FF4444',        # Errori in rosso
    'success': '#4CAF50',      # Successo in verde
    'primary': '#4B0082',      # Colore primario (indaco)
    'secondary': '#9400D3',    # Colore secondario (viola)
    'accent': '#FFD700',       # Colore accent (oro)
    'header_bg': '#2E1A47',    # Sfondo header (viola scuro)
    'card_bg': '#2D2D2D',      # Sfondo card (grigio scuro)
    'hover_bg': '#3D2A5A',     # Sfondo hover (viola medio)
    'border': '#6A5ACD',       # Bordi (viola chiaro)
    'warning': '#FFA500',      # Warning (arancione)
    'disabled': '#666666',     # Elementi disabilitati (grigio)
    'highlight': '#9370DB'     # Evidenziazione (viola medio chiaro)
}

MAGIC_FONTS = {
    'title': ('Papyrus', 24, 'bold'),
    'subtitle': ('Papyrus', 16),
    'normal': ('Papyrus', 12),
    'small': ('Papyrus', 10)
}

def create_magic_button(parent, text, command, width=20):
    """Crea un bottone con effetti magici"""
    button = tk.Button(
        parent,
        text=text,
        font=("Papyrus", 10, "bold"),
        bg="#4B0082",
        fg="#FFD700",
        activebackground="#6A5ACD",
        activeforeground="#FFD700",
                    width=width,
        relief="ridge",
        bd=3
    )
    
    def on_enter(e):
        button.config(bg="#6A5ACD")
        # Aggiungi simboli magici
        button.config(text=f"✨ {text} ✨")
    
    def on_leave(e):
        button.config(bg="#4B0082")
        button.config(text=text)
    
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    button.config(command=command)
    
    return button

def create_magic_label(parent, text, font_type='normal'):
    """Crea una label con stile magico"""
    return tk.Label(parent, text=text,
                   font=MAGIC_FONTS[font_type],
                   bg=MAGIC_COLORS['background'],
                   fg=MAGIC_COLORS['text'])

def create_magic_frame(parent):
    """Crea un frame con stile magico"""
    return tk.Frame(parent, bg=MAGIC_COLORS['background'])

def create_magic_card(parent):
    """Crea un frame con stile card magico"""
    card = tk.Frame(parent, bg=MAGIC_COLORS['card_bg'], relief='raised', bd=1)
    return card

def show_magic_loading(parent, message="✨ Invocazione statistiche in corso... ✨"):
    """Crea una finestra di caricamento magica"""
    loading_frame = tk.Frame(parent, bg="#1a1a1a")
    loading_frame.place(relx=0.5, rely=0.5, anchor="center")
    
    # Simboli magici per l'animazione
    magic_symbols = ["✨", "🌟", "💫", "⭐", "🔮"]
    current_symbol_index = [0]  # Lista per permettere la modifica nella funzione interna
    
    # Label principale con font magico
    loading_label = tk.Label(
        loading_frame,
        text=message,
        font=("Papyrus", 16, "bold"),
        fg="#FFD700",
        bg="#1a1a1a"
    )
    loading_label.pack(pady=10)
    
    # Frame per il cerchio magico
    circle_frame = tk.Frame(loading_frame, bg="#1a1a1a")
    circle_frame.pack(pady=10)
    
    # Crea 8 label disposte in cerchio per l'animazione
    circle_labels = []
    for i in range(8):
        label = tk.Label(
            circle_frame,
            text="✨",
            font=("Papyrus", 20),
            fg="#FFD700",
            bg="#1a1a1a"
        )
        # Calcola la posizione nel cerchio
        angle = i * (360/8)
        x = 50 * math.cos(math.radians(angle)) + 60
        y = 50 * math.sin(math.radians(angle)) + 60
        label.place(x=x, y=y)
        circle_labels.append(label)
    
    # Label per il dettaglio dell'operazione
    detail_label = tk.Label(
        loading_frame,
        text="Preparazione incantesimo...",
        font=("Papyrus", 10),
        fg="#B8860B",
        bg="#1a1a1a"
    )
    detail_label.pack(pady=5)
    
    def animate():
        # Aggiorna il simbolo corrente
        current_symbol_index[0] = (current_symbol_index[0] + 1) % len(magic_symbols)
        
        # Anima le label del cerchio
        for i, label in enumerate(circle_labels):
            # Crea un effetto di onda
            delay = i * 100
            loading_frame.after(delay, lambda l=label, s=magic_symbols[current_symbol_index[0]]: 
                              l.config(text=s))
        
        # Programma la prossima animazione
        loading_frame.after(800, animate)
    
    # Avvia l'animazione
    animate()
    
    def update_message(new_message, detail=""):
        loading_label.config(text=new_message)
        if detail:
            detail_label.config(text=detail)
    
    loading_frame.update_message = update_message
    return loading_frame

def show_web_magic_loading(parent, message="✨ Consultazione del Grimorio Web... ✨"):
    """Crea una finestra di caricamento specifica per le operazioni web"""
    loading_frame = tk.Frame(parent, bg="#1a1a1a")
    loading_frame.place(relx=0.5, rely=0.5, anchor="center")
    
    # Effetto portale magico
    portal_canvas = tk.Canvas(loading_frame, width=150, height=150, bg="#1a1a1a", highlightthickness=0)
    portal_canvas.pack(pady=10)
    
    # Crea cerchi concentrici per il portale
    circles = []
    for i in range(3):
        circle = portal_canvas.create_oval(
            75-30*(i+1), 75-30*(i+1),
            75+30*(i+1), 75+30*(i+1),
            outline="#4B0082",
            width=2
        )
        circles.append(circle)
    
    # Label principale
    loading_label = tk.Label(
        loading_frame,
        text=message,
        font=("Papyrus", 16, "bold"),
        fg="#9400D3",
        bg="#1a1a1a"
    )
    loading_label.pack(pady=10)
    
    # Label per il dettaglio
    detail_label = tk.Label(
        loading_frame,
        text="Apertura portale magico...",
        font=("Papyrus", 10),
        fg="#8A2BE2",
        bg="#1a1a1a"
    )
    detail_label.pack(pady=5)
    
    def animate_portal():
        # Ruota i cerchi del portale
        for i, circle in enumerate(circles):
            angle = (datetime.now().timestamp() * (i+1) * 30) % 360
            portal_canvas.itemconfig(
                circle,
                outline=f"#{int(abs(math.sin(math.radians(angle)))*255):02x}00{int(abs(math.cos(math.radians(angle)))*255):02x}"
            )
        loading_frame.after(50, animate_portal)
    
    # Avvia l'animazione
    animate_portal()
    
    def update_message(new_message, detail=""):
        loading_label.config(text=new_message)
        if detail:
            detail_label.config(text=detail)
    
    loading_frame.update_message = update_message
    return loading_frame

def create_magic_window(title, size="800x600"):
    """Crea una finestra principale con stile magico"""
    window = tk.Toplevel()
    window.title(f"✨ {title} ✨")
    window.geometry(size)
    window.configure(bg=MAGIC_COLORS['background'])
    
    # Frame principale con sfondo gradiente
    main_frame = create_magic_frame(window)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Header con sfondo blu scuro
    header_frame = tk.Frame(main_frame, bg=MAGIC_COLORS['header_bg'])
    header_frame.pack(fill=tk.X, pady=(0, 20))
    
    # Titolo in bianco
    title_label = tk.Label(header_frame, text=title,
                          font=MAGIC_FONTS['title'],
                          bg=MAGIC_COLORS['header_bg'],
                          fg='white')
    title_label.pack(pady=10)
    
    # Frame per il contenuto
    content_frame = create_magic_frame(main_frame)
    content_frame.pack(fill="both", expand=True)
    
    return window, content_frame

def main():
    root = tk.Tk()
    root.title("✨ BOT DEL MAGO ✨")
    root.geometry("400x600")
    root.configure(bg=MAGIC_COLORS['background'])
    
    # Frame principale con sfondo gradiente
    main_frame = create_magic_frame(root)
    main_frame.pack(expand=True, fill="both", padx=20, pady=20)
    
    # Header con sfondo blu scuro
    header_frame = tk.Frame(main_frame, bg=MAGIC_COLORS['header_bg'])
    header_frame.pack(fill=tk.X, pady=(0, 20))
    
    # Titolo in bianco
    title_label = tk.Label(header_frame, text="BOT DEL MAGO",
                          font=MAGIC_FONTS['title'],
                          bg=MAGIC_COLORS['header_bg'],
                          fg='white')
    title_label.pack(pady=10)
    
    # Sottotitolo
    subtitle_label = create_magic_label(main_frame, 
                                      "Il tuo assistente magico per il basket", 
                                      font_type='subtitle')
    subtitle_label.pack(pady=(0, 30))
    
    # Frame per i bottoni
    buttons_frame = create_magic_frame(main_frame)
    buttons_frame.pack(fill="both", expand=True)
    
    # Bottoni con stile magico
    buttons = [
        ("🏀 Statistiche Difensive Generali", show_general_defensive_stats),
        ("🏀 Statistiche Difensive per Ruolo", show_defensive_stats),
        ("🏥 Lista Infortunati", show_injured_players),
        ("📅 Calendario Partite", show_upcoming_games),
        ("👤 Statistiche Giocatore", show_player_stats_window),
        ("🔮 Proiezioni Props", show_props_window),
        ("📊 Trend Giocatori", show_consistent_players),
        ("💡 Curiosità Giocatori", show_player_insights)
    ]
    
    for text, command in buttons:
        btn = create_magic_button(buttons_frame, text, command)
        btn.pack(fill="x", pady=5)
    
    # Footer con sfondo blu scuro
    footer_frame = tk.Frame(main_frame, bg=MAGIC_COLORS['header_bg'])
    footer_frame.pack(fill=tk.X, side="bottom", pady=10)
    
    footer_label = tk.Label(footer_frame, 
                           text="✨ Poteri Magici Attivi ✨", 
                           font=MAGIC_FONTS['small'],
                           bg=MAGIC_COLORS['header_bg'],
                           fg='white')
    footer_label.pack(pady=5)
    
    return root

def retry_api_call(func, max_retries=3, delay=2):
    """Funzione helper per ritentare le chiamate API in caso di errore"""
    for attempt in range(max_retries):
        try:
            time.sleep(delay)  # Aspetta prima di ogni tentativo
            return func()
        except Exception as e:
            if attempt == max_retries - 1:  # Ultimo tentativo
                raise e
            print(f"Tentativo {attempt + 1} fallito, riprovo tra {delay} secondi...")
            time.sleep(delay)  # Aspetta prima di riprovare
    return None

# Funzione per ottenere la classifica delle squadre per statistiche difensive
def get_team_defensive_ranking(sort_by_points=True):
    team_stats = []
    errors = []

    # Aggiorniamo il titolo della finestra di attesa
    loading_window = tk.Toplevel()
    loading_window.title("Caricamento in corso")
    loading_window.geometry("300x100")
    loading_window.configure(bg="#E6F2FF")
    loading_window.resizable(False, False)
    
    loading_frame = tk.Frame(loading_window, bg="#E6F2FF")
    loading_frame.pack(fill="x")
    
    loading_label = tk.Label(loading_frame, text="Recupero statistiche difensive...", 
                            font=("Verdana", 10), bg="#E6F2FF", fg="#0047AB")
    loading_label.pack(pady=10)
    
    progress = ttk.Progressbar(loading_frame, orient="horizontal", 
                              length=250, mode="indeterminate")
    progress.pack(pady=10)
    progress.start(10)
    loading_window.update()

    try:
        # Ottieni i dati dei rimbalzi da TeamRankings
        rebounds_url = "https://www.teamrankings.com/nba/stat/opponent-total-rebounds-per-game"
        points_url = "https://www.teamrankings.com/nba/stat/opponent-points-per-game"
        
        # Funzione per estrarre dati da TeamRankings
        def get_teamrankings_data(url):
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            data = {}
            table = soup.find('table', {'class': 'tr-table datatable scrollable'})
            if table:
                rows = table.find_all('tr')[1:]  # Salta l'intestazione
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        team_name = cols[1].text.strip()
                        value = float(cols[2].text.strip())
                        data[team_name] = value
            return data

        # Dizionario per mappare i nomi di TeamRankings ai nostri nomi
        teamrankings_mapping = {
            "LA Clippers": "LA Clippers",
            "LA Lakers": "Los Angeles Lakers",
            "Golden State": "Golden State Warriors",
            "Brooklyn": "Brooklyn Nets",
            "New York": "New York Knicks",
            "Philadelphia": "Philadelphia 76ers",
            "Oklahoma City": "Oklahoma City Thunder",
            "Portland": "Portland Trail Blazers",
            "San Antonio": "San Antonio Spurs",
            "New Orleans": "New Orleans Pelicans",
            "Minnesota": "Minnesota Timberwolves",
            "Milwaukee": "Milwaukee Bucks",
            "Memphis": "Memphis Grizzlies",
            "Miami": "Miami Heat",
            "Phoenix": "Phoenix Suns",
            "Sacramento": "Sacramento Kings",
            "Toronto": "Toronto Raptors",
            "Utah": "Utah Jazz",
            "Washington": "Washington Wizards",
            "Atlanta": "Atlanta Hawks",
            "Boston": "Boston Celtics",
            "Charlotte": "Charlotte Hornets",
            "Chicago": "Chicago Bulls",
            "Cleveland": "Cleveland Cavaliers",
            "Dallas": "Dallas Mavericks",
            "Denver": "Denver Nuggets",
            "Detroit": "Detroit Pistons",
            "Houston": "Houston Rockets",
            "Indiana": "Indiana Pacers"
        }

        # Ottieni entrambi i set di dati
        rebounds_data = get_teamrankings_data(rebounds_url)
        points_data = get_teamrankings_data(points_url)

        # Processa i dati per ogni squadra
        for tr_name, full_name in teamrankings_mapping.items():
            try:
                team_name_it = traduzioni_squadre.get(full_name, full_name)
                
                # Cerca il nome della squadra nei dati di TeamRankings
                points_against = None
                rebounds_against = None
                
                # Cerca nei dati di TeamRankings
                for tr_key in points_data.keys():
                    if tr_name in tr_key:
                        points_against = points_data[tr_key]
                        break
                
                for tr_key in rebounds_data.keys():
                    if tr_name in tr_key:
                        rebounds_against = rebounds_data[tr_key]
                        break
                
                if points_against is not None and rebounds_against is not None:
                    team_stats.append((team_name_it, points_against, rebounds_against))
                else:
                    print(f"Dati mancanti per {full_name}")
            
            except Exception as e:
                error_msg = f"Errore per {full_name}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                continue

    except Exception as e:
        loading_window.destroy()
        return f"Errore nel recupero dei dati: {str(e)}"

    # Chiudi la finestra di caricamento
    loading_window.destroy()

    if not team_stats:
        if errors:
            return "Si sono verificati errori nel recupero dei dati:\n" + "\n".join(errors)
        return "Nessun dato disponibile"

    # Ordiniamo le squadre in base al criterio selezionato
    if sort_by_points:
        # Ordiniamo per punti subiti (dal peggiore al migliore in difesa)
        sorted_teams = sorted(team_stats, key=lambda x: x[1], reverse=True)
        result = "🏀 Classifica squadre per punti subiti:\n\n"
        for rank, (team, pts, rebs) in enumerate(sorted_teams, start=1):
            result += f"{rank}. {team}: {pts:.1f} PTS subiti\n"
    else:
        # Ordiniamo per rimbalzi concessi (dal peggiore al migliore)
        sorted_teams = sorted(team_stats, key=lambda x: x[2], reverse=True)
        result = "🏀 Classifica squadre per rimbalzi concessi:\n\n"
        for rank, (team, pts, rebs) in enumerate(sorted_teams, start=1):
            result += f"{rank}. {team}: {rebs:.1f} REB concessi\n"
    
    if errors:
        result += "\nNota: Alcuni dati potrebbero essere incompleti a causa di errori di connessione."
    
    return result

# Funzione per ottenere la lista dei giocatori infortunati da Dunkest
def get_injured_players():
    """Funzione per ottenere la lista dei giocatori infortunati da Dunkest"""
    url = "https://www.dunkest.com/it/nba/infortuni"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    # Lista completa delle squadre NBA
    all_nba_teams = [
        "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets",
        "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets",
        "Detroit Pistons", "Golden State Warriors", "Houston Rockets", "Indiana Pacers",
        "LA Clippers", "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat",
        "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans", "New York Knicks",
        "Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers", "Phoenix Suns",
        "Portland Trail Blazers", "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors",
        "Utah Jazz", "Washington Wizards"
    ]
    
    try:
        print("\nInizio recupero dati infortunati...")
        response = requests.get(url, headers=headers)
        print(f"Status code: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        print("HTML scaricato correttamente")
        
        injured_players = {}
        found_teams = set()  # Per tenere traccia delle squadre trovate
        
        # Trova tutte le tabelle con la classe injuries__table
        tables = soup.find_all('table', class_='injuries__table')
        print(f"\nTrovate {len(tables)} tabelle injuries__table")
        
        for table_idx, table in enumerate(tables):
            print(f"\nAnalisi tabella {table_idx + 1}:")
            
            # Trova il nome della squadra
            team_name = None
            team_header = table.find_previous(['h2', 'h3', 'h4', 'div'], class_=lambda x: x and ('team' in str(x).lower() or 'header' in str(x).lower()))
            if team_header:
                team_name = team_header.text.strip()
                print(f"Nome squadra trovato: {team_name}")
            
            if not team_name:
                # Prova a trovare il nome della squadra nella prima riga della tabella
                first_row = table.find('tr')
                if first_row:
                    first_cell = first_row.find('td')
                    if first_cell:
                        team_name = first_cell.text.strip()
                        print(f"Nome squadra trovato nella prima cella: {team_name}")
            
            if team_name:
                found_teams.add(team_name)  # Aggiungi alla lista delle squadre trovate
                if team_name not in injured_players:
                    injured_players[team_name] = []
                
                # Analizza le righe della tabella
                rows = table.find_all('tr')
                print(f"Trovate {len(rows)} righe per {team_name}")
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:  # Dovrebbero esserci almeno nome e status
                        try:
                            player_name = cells[0].text.strip()
                            # Lo status potrebbe essere nella seconda o terza colonna
                            status = cells[-1].text.strip() if len(cells) > 2 else cells[1].text.strip()
                            
                            if player_name and status and not player_name.lower().startswith(('squadra', 'team')):
                                print(f"Giocatore trovato: {player_name} - Status: {status}")
                                injured_players[team_name].append({
                                    'name': player_name,
                                    'status': status
                                })
                        except Exception as e:
                            print(f"Errore nel processare la riga: {e}")
                            continue
            else:
                print("Nome squadra non trovato per questa tabella")
                print("Contenuto tabella:")
                print(table.prettify()[:500])
        
        # Rimuovi le squadre senza giocatori
        injured_players = {k: v for k, v in injured_players.items() if v}
        
        # Stampa il riepilogo finale
        print("\nRiepilogo finale:")
        if injured_players:
            for team, players in injured_players.items():
                print(f"\n{team}:")
                for player in players:
                    print(f"  - {player['name']}: {player['status']}")
        else:
            print("Nessun giocatore infortunato trovato!")
            
            # Debug: mostra un esempio di struttura HTML
            print("\nEsempio struttura HTML di una tabella:")
            if tables:
                print(tables[0].prettify())
        
        # Controlla le squadre mancanti
        print("\nControllo squadre mancanti:")
        missing_teams = set(all_nba_teams) - found_teams
        if missing_teams:
            print("\nSquadre non trovate nella pagina:")
            for team in sorted(missing_teams):
                print(f"- {team}")
        else:
            print("Tutte le squadre NBA sono presenti nella pagina!")
        
        return injured_players
    except Exception as e:
        print(f"Errore nel recupero degli infortunati: {e}")
        print("Traceback completo:")
        import traceback
        print(traceback.format_exc())
        return {}

def show_injured_players():
    """Mostra la lista degli infortunati in una nuova finestra"""
    window, main_frame = create_magic_window("Lista Infortunati NBA")
    
    # Frame per il caricamento
    loading_frame = create_magic_frame(main_frame)
    loading_frame.pack(fill="x")
    
    loading_label = create_magic_label(loading_frame, "Recupero dati infortunati...", font_type='subtitle')
    loading_label.pack(pady=10)
    
    progress = ttk.Progressbar(loading_frame, orient="horizontal", 
                             length=250, mode="indeterminate")
    progress.pack(pady=10)
    progress.start(10)
    main_frame.update()

    # Recupera la lista degli infortunati
    injured_players = get_injured_players()
    
    # Chiudi la finestra di caricamento
    loading_frame.destroy()
    
    if not injured_players:
        tk.Label(main_frame, text="Nessun dato disponibile", 
                font=("Helvetica", 12), bg="#FFFFFF", fg="#1E3D6B").pack(pady=10)
        return

    # Frame contenitore per la lista scrollabile
    container_frame = tk.Frame(main_frame, bg="#FFFFFF")
    container_frame.pack(fill="both", expand=True)

    # Canvas e scrollbar
    canvas = tk.Canvas(container_frame, bg="#FFFFFF")
    scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Crea i frame per ogni squadra
    for team in sorted(injured_players.keys()):
        # Frame per ogni squadra
        team_frame = tk.Frame(scrollable_frame, bg="#FFFFFF", relief="ridge", bd=1)
        team_frame.pack(fill="x", pady=5, padx=5)
        
        # Header della squadra con sfondo colorato
        team_header = tk.Frame(team_frame, bg="#F0F4F8")
        team_header.pack(fill="x")
        
        tk.Label(team_header, 
                text=team, 
                font=("Helvetica", 12, "bold"), 
                bg="#F0F4F8", 
                fg="#1E3D6B").pack(anchor="w", padx=10, pady=5)
        
        # Frame per i giocatori
        players_frame = tk.Frame(team_frame, bg="#FFFFFF")
        players_frame.pack(fill="x", padx=5)
        
        # Lista dei giocatori della squadra
        for player in sorted(injured_players[team], key=lambda x: x['name']):
            player_frame = tk.Frame(players_frame, bg="#FFFFFF")
            player_frame.pack(fill="x", pady=2)
            
            tk.Label(player_frame, 
                    text=f"• {player['name']}", 
                    font=("Helvetica", 10), 
                    bg="#FFFFFF", 
                    fg="#333333").pack(side="left", padx=(20, 10))
            
            status_label = tk.Label(player_frame, 
                                  text=player['status'], 
                                  font=("Helvetica", 10), 
                                  bg="#FFFFFF", 
                                  fg="#E74C3C")
            status_label.pack(side="left")

    # Configura il layout finale
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

# Funzione per ottenere le prossime partite NBA utilizzando l'API ESPN.
def get_upcoming_games():
    """
    Funzione per ottenere le prossime partite NBA utilizzando l'API ESPN.
    Include anche dati hardcoded di fallback in caso di problemi con l'API.
    """
    # Dizionario per organizzare le partite per data
    upcoming_games = {}
    
    # Finestra di caricamento
    loading_window = tk.Toplevel()
    loading_window.title("Caricamento in corso")
    loading_window.geometry("300x100")
    loading_window.configure(bg="#E6F2FF")
    loading_window.resizable(False, False)
    
    loading_label = tk.Label(loading_window, text="Recupero calendario partite...", 
                            font=("Verdana", 10), bg="#E6F2FF", fg="#0047AB")
    loading_label.pack(pady=10)
    
    progress = ttk.Progressbar(loading_window, orient="horizontal", 
                              length=250, mode="indeterminate")
    progress.pack(pady=10)
    progress.start(10)
    loading_window.update()

    try:
        # Ottieni le partite per oggi e i prossimi 5 giorni
        today = datetime.now()
        
        for day_offset in range(6):  # Oggi + 5 giorni
            current_date = today + timedelta(days=day_offset)
            date_str = current_date.strftime("%Y%m%d")
            
            # Aggiorna la label di caricamento
            loading_label.config(text=f"Recupero partite del {current_date.strftime('%d/%m/%Y')}...")
            loading_window.update()
            
            # URL dell'API ESPN per le partite NBA con data specifica
            espn_api_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str}"
            
            # Effettua la richiesta all'API
            response = requests.get(espn_api_url)
            data = response.json()
            
            # Verifica se ci sono eventi
            if 'events' in data and data['events']:
                # Fuso orario italiano
                italian_tz = pytz.timezone('Europe/Rome')
                
                for event in data['events']:
                    try:
                        # Estrai data e ora dell'evento
                        date_str = event['date']
                        date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%MZ")
                        
                        # Converti da UTC a ora italiana
                        date_obj = date_obj.replace(tzinfo=pytz.UTC)
                        date_obj_it = date_obj.astimezone(italian_tz)
                        
                        # Verifica se la partita è già iniziata
                        now = datetime.now(italian_tz)
                        if date_obj_it < now:
                            # Salta le partite già iniziate
                            continue
                        
                        # Formatta la data in formato italiano
                        date_ita = date_obj_it.strftime("%d/%m/%Y")
                        time_ita = date_obj_it.strftime("%H:%M")
                        
                        # Estrai i nomi delle squadre
                        home_team = event['competitions'][0]['competitors'][0]['team']['displayName']
                        away_team = event['competitions'][0]['competitors'][1]['team']['displayName']
                        
                        # Traduci i nomi delle squadre se disponibili
                        home_team = traduzioni_squadre.get(home_team, home_team)
                        away_team = traduzioni_squadre.get(away_team, away_team)
                        
                        # Aggiungi la partita al dizionario
                        if date_ita not in upcoming_games:
                            upcoming_games[date_ita] = []
                        
                        upcoming_games[date_ita].append(f"{away_team} @ {home_team} - {time_ita}")
                    except Exception as e:
                        print(f"Errore nel processare la partita: {str(e)}")
                        continue
        
        # Se non ci sono partite dall'API, usa i dati di fallback
        if not upcoming_games:
            print("Nessuna partita trovata dall'API, uso dati di fallback")
            # Dati hardcoded di fallback
            today = datetime.today()
            tomorrow = today + timedelta(days=1)
            day_after = today + timedelta(days=2)
            
            today_str = today.strftime("%d/%m/%Y")
            tomorrow_str = tomorrow.strftime("%d/%m/%Y")
            day_after_str = day_after.strftime("%d/%m/%Y")
            
            upcoming_games[today_str] = [
                "Boston Celtics @ Miami Heat - 21:30",
                "Los Angeles Lakers @ Phoenix Suns - 03:00"
            ]
            
            upcoming_games[tomorrow_str] = [
                "Brooklyn Nets @ New York Knicks - 01:30",
                "Golden State Warriors @ Dallas Mavericks - 02:30"
            ]
            
            upcoming_games[day_after_str] = [
                "Milwaukee Bucks @ Chicago Bulls - 20:00",
                "Denver Nuggets @ LA Clippers - 04:00"
            ]
        
        loading_window.destroy()
        
        if not upcoming_games:
            return "Nessuna partita programmata per i prossimi giorni"
        
        result = "📅 CALENDARIO PROSSIME PARTITE NBA 📅\n\n"
        
        # Ordina le date
        sorted_dates = sorted(upcoming_games.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        
        for date in sorted_dates:
            result += f"🏀 {date}:\n"
            for game in upcoming_games[date]:
                result += f"  • {game}\n"
            result += "\n"  # Spazio tra le date
        
        return result
    
    except Exception as e:
        loading_window.destroy()
        print(f"Errore nel recupero del calendario: {str(e)}")
        
        # Usa dati hardcoded in caso di errore
        today = datetime.today()
        tomorrow = today + timedelta(days=1)
        day_after = today + timedelta(days=2)
        
        today_str = today.strftime("%d/%m/%Y")
        tomorrow_str = tomorrow.strftime("%d/%m/%Y")
        day_after_str = day_after.strftime("%d/%m/%Y")
        
        upcoming_games[today_str] = [
            "Boston Celtics @ Miami Heat - 21:30",
            "Los Angeles Lakers @ Phoenix Suns - 03:00"
        ]
        
        upcoming_games[tomorrow_str] = [
            "Brooklyn Nets @ New York Knicks - 01:30",
            "Golden State Warriors @ Dallas Mavericks - 02:30"
        ]
        
        upcoming_games[day_after_str] = [
            "Milwaukee Bucks @ Chicago Bulls - 20:00",
            "Denver Nuggets @ LA Clippers - 04:00"
        ]
        
        result = "📅 CALENDARIO PROSSIME PARTITE NBA 📅\n\n"
        result += "(Dati di fallback - Impossibile connettersi all'API)\n\n"
        
        # Ordina le date
        sorted_dates = sorted(upcoming_games.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        
        for date in sorted_dates:
            result += f"🏀 {date}:\n"
            for game in upcoming_games[date]:
                result += f"  • {game}\n"
            result += "\n"  # Spazio tra le date
        
        return result

def show_upcoming_games():
    """Mostra le prossime partite in una nuova finestra"""
    window, main_frame = create_magic_window("Calendario Partite NBA")
    
    # Area di testo per i risultati con scrollbar
    text_frame = create_magic_frame(main_frame)
    text_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")
    
    text_area = tk.Text(text_frame, wrap="word", bg="white", fg="#333333",
                      font=("Consolas", 11), yscrollcommand=scrollbar.set)
    text_area.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=text_area.yview)
    
    result = get_upcoming_games()
    text_area.insert("1.0", result)
    text_area.config(state="disabled")  # Rendi il testo di sola lettura
    
    # Bottone per chiudere
    close_button = tk.Button(main_frame, text="Chiudi", font=("Verdana", 10),
                            command=main_frame.destroy, bg="#0047AB", fg="white")
    close_button.pack(pady=15)

def show_general_defensive_stats():
    """Mostra le statistiche difensive generali in una nuova finestra"""
    window, main_frame = create_magic_window("Statistiche Difensive Generali NBA")
    
    # Frame per i controlli
    control_frame = create_magic_frame(main_frame)
    control_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # Variabile per il filtro punti/rimbalzi
    filter_var = tk.StringVar(value="points")
    
    # Label per il filtro
    ttk.Label(control_frame, text="Mostra:").pack(side=tk.LEFT, padx=5)
    
    # Radio buttons per il filtro
    ttk.Radiobutton(control_frame, text="Punti Concessi", variable=filter_var, 
                    value="points").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(control_frame, text="Rimbalzi Concessi", variable=filter_var, 
                    value="rebounds").pack(side=tk.LEFT, padx=5)
    
    # Frame per i risultati
    results_frame = create_magic_frame(main_frame)
    results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Scrollbar e canvas per i risultati
    canvas = tk.Canvas(results_frame, bg=MAGIC_COLORS['background'])
    scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollable_frame = create_magic_frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    def update_stats(*args):
        # Pulisci i risultati precedenti
        for widget in scrollable_frame.winfo_children():
            widget.destroy()
        
        # Mostra loading
        loading_label = ttk.Label(scrollable_frame, text="Caricamento statistiche...")
        loading_label.pack(pady=10)
        scrollable_frame.update()
        
        # Recupera i dati
        if filter_var.get() == "points":
            season_data = get_points_season()
            last3_data = get_points_last3()
            stat_name = "Punti"
        else:
            season_data = get_rebounds_season()
            last3_data = get_rebounds_last3()
            stat_name = "Rimbalzi"
        
        loading_label.destroy()
        
        if season_data:
            # Header
            ttk.Label(scrollable_frame, 
                     text=f"Classifica {stat_name} Concessi:", 
                     font=('Helvetica', 12, 'bold')).pack(anchor="w", pady=5)
            
            # Crea una tabella con i dati
            header_frame = ttk.Frame(scrollable_frame)
            header_frame.pack(fill=tk.X, padx=5, pady=5)
            ttk.Label(header_frame, text="Squadra", width=30).pack(side=tk.LEFT)
            ttk.Label(header_frame, text="Stagione", width=15).pack(side=tk.LEFT)
            ttk.Label(header_frame, text="Ultime 3", width=15).pack(side=tk.LEFT)
            
            # Ordina le squadre per valore stagionale (dal più alto al più basso)
            sorted_teams = sorted(season_data.items(), key=lambda x: x[1], reverse=True)
            
            for team, season_value in sorted_teams:
                row_frame = ttk.Frame(scrollable_frame)
                row_frame.pack(fill=tk.X, padx=5)
                ttk.Label(row_frame, text=team, width=30).pack(side=tk.LEFT)
                ttk.Label(row_frame, text=f"{season_value:.1f}", width=15).pack(side=tk.LEFT)
                last3_value = last3_data.get(team, "-")
                if isinstance(last3_value, (int, float)):
                    last3_text = f"{last3_value:.1f}"
                else:
                    last3_text = last3_value
                ttk.Label(row_frame, text=last3_text, width=15).pack(side=tk.LEFT)
    
    # Aggiorna quando cambia il filtro
    filter_var.trace('w', update_stats)
    
    # Bottone per aggiornare
    ttk.Button(control_frame, text="Aggiorna Statistiche", command=update_stats).pack(pady=10)
    
    # Configura il layout finale
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Mostra i dati iniziali
    update_stats()

def show_defensive_stats():
    """Mostra le statistiche difensive in una nuova finestra"""
    window, main_frame = create_magic_window("Statistiche Difensive NBA")

    # Frame per i controlli
    control_frame = create_magic_frame(main_frame)
    control_frame.pack(fill=tk.X, padx=5, pady=5)

    # Variabili per i filtri
    role_var = tk.StringVar(value='PG')
    stat_var = tk.StringVar(value='points')

    # Frame per i filtri
    filters_frame = create_magic_frame(control_frame)
    filters_frame.pack(fill=tk.X, pady=5)

    # Filtro per ruolo
    ttk.Label(filters_frame, text="Ruolo:").pack(side=tk.LEFT, padx=5)
    role_menu = ttk.Combobox(filters_frame, textvariable=role_var, 
                            values=['PG', 'SG', 'SF', 'PF', 'C'],
                            width=10)
    role_menu.pack(side=tk.LEFT, padx=5)

    # Filtro per statistica
    ttk.Label(filters_frame, text="Statistica:").pack(side=tk.LEFT, padx=5)
    stat_menu = ttk.Combobox(filters_frame, textvariable=stat_var,
                            values=['points', 'rebounds', 'assists', 'steals', 'blocks', 'threes'],
                            width=15)
    stat_menu.pack(side=tk.LEFT, padx=5)

    # Frame per i risultati
    results_frame = create_magic_frame(main_frame)
    results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Frame per il loading
    loading_frame = create_magic_frame(results_frame)
    loading_label = ttk.Label(loading_frame, text="Caricamento statistiche...")

    # Scrollbar e canvas per i risultati
    canvas = tk.Canvas(results_frame, bg=MAGIC_COLORS['background'])
    scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollable_frame = create_magic_frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Dizionario per memorizzare i dati
    cached_data = {'position_data': None}

    def show_loading():
        # Nascondi canvas e scrollbar
        canvas.pack_forget()
        scrollbar.pack_forget()
        
        # Mostra loading frame
        loading_frame.pack(fill=tk.BOTH, expand=True)
        loading_label.pack(pady=10)
        window.update()

    def hide_loading():
        # Nascondi loading frame
        loading_frame.pack_forget()
        loading_label.pack_forget()
        
        # Mostra canvas e scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        window.update()

    def update_display(*args):
        # Pulisci i risultati precedenti
        for widget in scrollable_frame.winfo_children():
            widget.destroy()

        position = role_var.get()
        stat = stat_var.get()

        if not cached_data['position_data']:
            show_loading()
            cached_data['position_data'] = get_defense_vs_position()
            hide_loading()

        position_data = cached_data['position_data']
        if position_data and position in position_data and stat in position_data[position]:
            # Mappa dei nomi delle statistiche in italiano
            stat_names = {
                'points': 'Punti', 
                'rebounds': 'Rimbalzi', 
                'assists': 'Assist',
                'steals': 'Palle Rubate',
                'blocks': 'Stoppate',
                'threes': 'Tiri da 3'
            }

            # Header
            ttk.Label(scrollable_frame, 
                     text=f"Classifica difensiva contro {position} - {stat_names[stat]}:", 
                     font=('Helvetica', 12, 'bold')).pack(anchor="w", pady=5)

            # Crea una tabella con i dati
            table_frame = ttk.Frame(scrollable_frame)
            table_frame.pack(fill=tk.X, padx=5, pady=5)

            # Header della tabella
            ttk.Label(table_frame, text="Posizione", width=10).grid(row=0, column=0, padx=2)
            ttk.Label(table_frame, text="Squadra", width=30).grid(row=0, column=1, padx=2)
            ttk.Label(table_frame, text="Valore", width=10).grid(row=0, column=2, padx=2)

            # Popola la tabella
            sorted_teams = sorted(position_data[position][stat].items(), 
                               key=lambda x: x[1],
                               reverse=True)  # Ordine decrescente

            for rank, (team, value) in enumerate(sorted_teams, 1):
                ttk.Label(table_frame, text=f"#{rank}", width=10).grid(row=rank, column=0, padx=2)
                ttk.Label(table_frame, text=team, width=30).grid(row=rank, column=1, padx=2)
                ttk.Label(table_frame, text=f"{value:.1f}", width=10).grid(row=rank, column=2, padx=2)

    # Aggiorna quando cambiano i filtri
    role_var.trace('w', update_display)
    stat_var.trace('w', update_display)

    # Configura il layout finale
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Carica i dati iniziali
    update_display()

def get_player_stats(player_name):
    from nba_api.stats.static import players
    from nba_api.stats.endpoints import playercareerstats
    import time
    
    # Cerca il giocatore
    player_dict = players.find_players_by_full_name(player_name)
    
    if not player_dict:
        return None
        
    player = player_dict[0]  # Prendi il primo risultato
    time.sleep(1)  # Piccola pausa per evitare rate limiting
    
    # Ottieni le statistiche della carriera
    career = playercareerstats.PlayerCareerStats(player_id=player['id'])
    career_stats = career.get_data_frames()[0]
    
    # Filtra per la stagione corrente
    current_season_stats = career_stats[career_stats['SEASON_ID'] == '2024-25']
    
    if current_season_stats.empty:
        return None
    
    stats = current_season_stats.iloc[0]
    games_played = stats['GP']
    
    if games_played == 0:
        return None
        
    # Calcola le medie
    calculated_stats = {
        'GP': games_played,
        'MPG': round(stats['MIN'] / games_played, 1),
        'PPG': round(stats['PTS'] / games_played, 1),
        'RPG': round(stats['REB'] / games_played, 1),
        'APG': round(stats['AST'] / games_played, 1),
        'SPG': round(stats['STL'] / games_played, 1),
        'BPG': round(stats['BLK'] / games_played, 1),
        'TOPG': round(stats['TOV'] / games_played, 1),
        'PFG': round(stats['PF'] / games_played, 1),
        'FG_PCT': stats['FG_PCT'],
        'FG3_PCT': stats['FG3_PCT'],
        'FT_PCT': stats['FT_PCT']
    }
    
    return calculated_stats

def get_player_last_games(player_name, num_games=10):
    """Ottiene le statistiche delle ultime N partite di un giocatore"""
    from nba_api.stats.static import players
    
    # Trova il giocatore
    player = next((p for p in players.get_active_players() 
                  if p['full_name'].lower() == player_name.lower()), None)
    
    if not player:
        return None
        
    # Ottieni il game log del giocatore
    game_log = playergamelog.PlayerGameLog(player_id=player['id'])
    games_df = game_log.get_data_frames()[0]
    
    # Prendi solo le ultime N partite
    last_games = games_df.head(num_games)
    
    if last_games.empty:
        return None
    
    # Calcola le medie delle ultime partite
    avg_stats = {
        'PPG': round(last_games['PTS'].mean(), 1),
        'RPG': round(last_games['REB'].mean(), 1),
        'APG': round(last_games['AST'].mean(), 1),
        'MPG': round(last_games['MIN'].astype(float).mean(), 1)
    }
    
    # Prepara i dati delle singole partite
    game_stats = []
    for _, game in last_games.iterrows():
        game_stats.append({
            'DATA': game['GAME_DATE'],
            'VS': game['MATCHUP'],
            'MIN': game['MIN'],
            'PTS': game['PTS'],
            'REB': game['REB'],
            'AST': game['AST'],
            'STL': game['STL'],
            'BLK': game['BLK'],
            'FG_PCT': f"{float(game['FG_PCT']):.1%}" if game['FG_PCT'] else "0.0%",
            'FG3M': game['FG3M']  # Aggiungiamo i tiri da 3 realizzati
        })
    
    return {'averages': avg_stats, 'games': game_stats}

def analyze_player_trends(player_name, prop_type, line_value):
    """Analizza se un giocatore ha superato una certa linea nelle ultime 5 partite"""
    try:
        print(f"\nAnalizzando {player_name} per {prop_type} > {line_value}")
        last_games = get_player_last_games(player_name, 5)
        if not last_games or 'games' not in last_games:
            print(f"Nessun dato trovato per {player_name}")
            return False
            
        # Mappa delle statistiche nel game log
        stat_mapping = {
            'Points': 'PTS',
            'Rebounds': 'REB',
            'Assists': 'AST',
            'Blocks': 'BLK',
            'Steals': 'STL',
            '3-Pointers Made': 'FG3M'
        }
        
        stat_key = stat_mapping.get(prop_type)
        if not stat_key:
            print(f"Tipo di statistica non supportata: {prop_type}")
            return False
            
        # Controlla se ha superato la linea in tutte le ultime 5 partite
        print(f"Ultime partite di {player_name}:")
        for game in last_games['games'][:5]:
            try:
                stat_value = float(game.get(stat_key, 0))
                print(f"- {game['DATA']} vs {game['VS']}: {stat_value} {prop_type}")
                if stat_value <= line_value:
                    print(f"Non ha superato la linea ({line_value})")
                    return False
            except (ValueError, TypeError) as e:
                print(f"Errore nel convertire il valore per {player_name}, {prop_type}: {str(e)}")
                return False
        
        print(f"✅ {player_name} ha superato {line_value} {prop_type} in tutte le ultime 5 partite!")
        return True
        
    except Exception as e:
        print(f"Errore nell'analisi di {player_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def find_consistent_players():
    """Trova giocatori che hanno superato costantemente le loro linee"""
    try:
        # Ottieni le props da SportItalia invece che da Pine Sports
        props = get_sportitalia_props()
        if not props:
            print("Nessuna prop trovata")
            return []
        
        print(f"Analizzando {len(props)} giocatori...")
        consistent_players = []
        
        for prop in props:
            try:
                player_name = prop['player']
                stats = prop.get('stats', {})
                print(f"\nAnalizzando {player_name} con stats: {stats}")
                
                for stat_type, value in stats.items():
                    try:
                        line_value = float(value)
                        print(f"Controllando {stat_type}: {line_value}")
                        if analyze_player_trends(player_name, stat_type, line_value):
                            consistent_players.append({
                                'player': player_name,
                                'stat_type': stat_type,
                                'line': value,
                                'streak': '5 partite consecutive'
                            })
                    except ValueError as e:
                        print(f"Errore nel convertire il valore della prop per {player_name}: {str(e)}")
                        continue
            except Exception as e:
                print(f"Errore nell'analisi del giocatore {player_name}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        return consistent_players
        
    except Exception as e:
        print(f"Errore generale in find_consistent_players: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def show_consistent_players():
    """Mostra una finestra con i giocatori che hanno trend consistenti"""
    window, main_frame = create_magic_window("Trend Giocatori (100% Last 5)")
    
    # Frame per i controlli
    control_frame = create_magic_frame(main_frame)
    control_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # Variabile per il filtro Under/Over
    filter_var = tk.StringVar(value="all")
    
    # Label per il filtro
    ttk.Label(control_frame, text="Filtra per:").pack(side=tk.LEFT, padx=5)
    
    # Radio buttons per il filtro
    ttk.Radiobutton(control_frame, text="Tutti", variable=filter_var, 
                    value="all").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(control_frame, text="Solo Over", variable=filter_var, 
                    value="over").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(control_frame, text="Solo Under", variable=filter_var, 
                    value="under").pack(side=tk.LEFT, padx=5)
    
    # Scrollbar e canvas
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Label di caricamento
    loading_label = ttk.Label(scrollable_frame, text="Recupero dati in corso...")
    loading_label.pack(pady=10)
    main_frame.update()
    
    try:
        # Recupera i dati da propchasers
        props_data = get_propchasers_data()
        
        # Rimuovi label di caricamento
        loading_label.destroy()
        
        if not props_data:
            ttk.Label(scrollable_frame,
                     text="Nessun giocatore trovato con 100% nelle ultime 5 partite",
                     font=('Helvetica', 10, 'bold')).pack(pady=10)
        else:
            # Crea una tabella
            columns = ('Player', 'Prop', 'Line', 'Under/Over', 'Last 5')
            tree = ttk.Treeview(scrollable_frame, columns=columns, show='headings')
            
            # Configura le colonne
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=150)
            
            # Aggiungi i dati
            for prop in props_data:
                # Determina se è Over o Under
                is_over = 'o' in prop['last5'].lower() if prop['last5'] else False
                over_under = "Over" if is_over else "Under"
                
                tree.insert('', 'end', values=(
                    prop['player'],
                    prop['prop'],
                    prop['line'],
                    over_under,
                    prop['last5']
                ))
            
            # Aggiungi la tabella al frame
            tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Aggiungi una label con il numero di risultati
            ttk.Label(scrollable_frame,
                     text=f"Trovati {len(props_data)} giocatori con 100% nelle ultime 5 partite",
                     font=('Helvetica', 10, 'bold')).pack(pady=5)
            
            def filter_tree():
                # Pulisci la tabella
                for item in tree.get_children():
                    tree.delete(item)
                
                current_filter = filter_var.get()
                
                # Aggiungi i dati filtrati
                for prop in props_data:
                    is_over = 'o' in prop['last5'].lower() if prop['last5'] else False
                    over_under = "Over" if is_over else "Under"
                    
                    # Applica il filtro
                    if current_filter == "all" or \
                       (current_filter == "over" and over_under == "Over") or \
                       (current_filter == "under" and over_under == "Under"):
                        tree.insert('', 'end', values=(
                            prop['player'],
                            prop['prop'],
                            prop['line'],
                            over_under,
                            prop['last5']
                        ))
            
            # Collega il filtro alla variabile
            filter_var.trace('w', lambda *args: filter_tree())
    
    except Exception as e:
        error_msg = f"Errore durante l'analisi: {str(e)}\n"
        import traceback
        error_msg += traceback.format_exc()
        ttk.Label(scrollable_frame,
                 text=error_msg,
                 foreground="red").pack(pady=10)
    
    # Configura il layout finale
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def show_player_stats_window():
    """Mostra la finestra delle statistiche del giocatore"""
    window, main_frame = create_magic_window("Statistiche Giocatore")
    
    # Frame per la ricerca
    search_frame = create_magic_frame(main_frame)
    search_frame.pack(pady=10, padx=10, fill="x")
    
    # Entry per la ricerca con autocompletamento
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var)
    search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
    
    # Listbox per i suggerimenti (inizialmente nascosta)
    suggestion_listbox = tk.Listbox(search_frame, height=5)
    
    # Frame per i risultati
    results_frame = tk.Frame(search_frame, bg="#E6F2FF")
    results_frame.pack(pady=10, padx=10, fill="both", expand=True)
    
    def update_suggestions(*args):
        search_text = search_var.get().lower()
        suggestion_listbox.delete(0, tk.END)
        
        if len(search_text) < 2:
            suggestion_listbox.pack_forget()
            return
            
        # Cerca i giocatori che corrispondono al testo inserito
        from nba_api.stats.static import players
        all_players = players.get_active_players()
        matching_players = [
            p['full_name'] 
            for p in all_players 
            if search_text in p['full_name'].lower()
        ]
        
        if matching_players:
            suggestion_listbox.pack(pady=(0, 10), padx=10, fill="x")
            for player in matching_players[:10]:  # Limita a 10 suggerimenti
                suggestion_listbox.insert(tk.END, player)
        else:
            suggestion_listbox.pack_forget()
    
    def select_suggestion(event):
        if suggestion_listbox.curselection():
            selected = suggestion_listbox.get(suggestion_listbox.curselection())
            search_var.set(selected)
            suggestion_listbox.pack_forget()
    
    def show_stats():
        player_name = search_var.get()
        if not player_name:
            messagebox.showwarning("Attenzione", "Inserisci il nome di un giocatore")
            return
            
        # Mostra finestra di caricamento
        loading_window = tk.Toplevel(main_frame)
        loading_window.title("Caricamento")
        loading_window.geometry("200x100")
        loading_label = tk.Label(loading_window, text="Caricamento statistiche...")
        loading_label.pack(pady=20)
        loading_window.update()

        try:
            # Pulisci i widget esistenti nel results_frame
            for widget in results_frame.winfo_children():
                widget.destroy()
            
            stats = get_player_stats(player_name)
            last_games_stats = get_player_last_games(player_name, 10)
            
            # Ottieni la prossima squadra avversaria
            next_opponent_info = get_next_opponent(player_name)
            vs_team_stats = None
            
            if next_opponent_info:
                # Ottieni le statistiche contro questa squadra
                vs_team_stats = get_player_vs_team_games(
                    player_name, 
                    next_opponent_info['opponent']['abbreviation'], 
                    10
                )
            
            loading_window.destroy()
            
            if stats is None:
                messagebox.showerror("Errore", "Nessuna statistica trovata per questo giocatore")
                return
                
            # Crea una nuova Text widget per le statistiche
            result_text = tk.Text(results_frame, height=40, width=80)
            result_text.pack(pady=10, padx=10, fill="both", expand=True)
            result_text.delete(1.0, tk.END)
            
            # Formatta e mostra le statistiche stagionali
            stats_text = f"""Statistiche di {player_name} (2024-25):

GP (Partite Giocate): {stats['GP']}
MPG (Minuti Per Partita): {stats['MPG']}
PPG (Punti Per Partita): {stats['PPG']}
RPG (Rimbalzi Per Partita): {stats['RPG']}
APG (Assist Per Partita): {stats['APG']}
SPG (Palle Rubate Per Partita): {stats['SPG']}
BPG (Stoppate Per Partita): {stats['BPG']}
FG% (Percentuale Dal Campo): {stats['FG_PCT']:.1%}
3P% (Percentuale Da Tre): {stats['FG3_PCT']:.1%}
FT% (Percentuale Tiri Liberi): {stats['FT_PCT']:.1%}
TOPG (Palle Perse Per Partita): {stats['TOPG']}
PFG (Falli Per Partita): {stats['PFG']}
"""
            if last_games_stats:
                avg = last_games_stats['averages']
                stats_text += f"""
Medie ultime 10 partite:
PPG: {avg['PPG']}  RPG: {avg['RPG']}  APG: {avg['APG']}  MPG: {avg['MPG']}

Dettaglio ultime 10 partite:
{'DATA':<12} {'VS':<20} {'MIN':<6} {'PTS':<5} {'REB':<5} {'AST':<5} {'STL':<5} {'BLK':<5} {'FG%':<6}
{'-'*75}"""
                
                for game in last_games_stats['games']:
                    stats_text += f"""
{game['DATA']:<12} {game['VS']:<20} {game['MIN']:<6} {game['PTS']:<5} {game['REB']:<5} {game['AST']:<5} {game['STL']:<5} {game['BLK']:<5} {game['FG_PCT']:<6}"""
            
            # Aggiungi le statistiche contro la prossima squadra avversaria
            if next_opponent_info and vs_team_stats:
                opponent_name = next_opponent_info['opponent']['full_name']
                game_date = next_opponent_info['game_date']
                location = "in casa" if next_opponent_info['is_home'] else "in trasferta"
                
                avg = vs_team_stats['averages']
                stats_text += f"""

🏀 Prossima partita: {opponent_name} ({location}) - {game_date}

Medie ultime 10 partite contro {opponent_name}:
PPG: {avg['PPG']}  RPG: {avg['RPG']}  APG: {avg['APG']}  MPG: {avg['MPG']}

Dettaglio ultime 10 partite contro {opponent_name}:
{'DATA':<12} {'VS':<20} {'MIN':<6} {'PTS':<5} {'REB':<5} {'AST':<5} {'STL':<5} {'BLK':<5} {'FG%':<6}
{'-'*75}"""
                
                for game in vs_team_stats['games']:
                    stats_text += f"""
{game['DATA']:<12} {game['VS']:<20} {game['MIN']:<6} {game['PTS']:<5} {game['REB']:<5} {game['AST']:<5} {game['STL']:<5} {game['BLK']:<5} {game['FG_PCT']:<6}"""

            result_text.insert(1.0, stats_text)
            result_text.configure(state='disabled')
            
        except Exception as e:
            loading_window.destroy()
            messagebox.showerror("Errore", f"Errore nel recupero delle statistiche: {str(e)}")
    
    # Collega l'aggiornamento dei suggerimenti all'input
    search_var.trace('w', update_suggestions)
    suggestion_listbox.bind('<<ListboxSelect>>', select_suggestion)
    
    # Bottone per cercare
    search_button = ttk.Button(search_frame, text="Cerca", command=show_stats)
    search_button.pack(side="right")

def get_player_props():
    """Recupera e analizza le props dei giocatori da Pine Sports"""
    global props_cache
    
    # Controlla se abbiamo dati in cache validi
    current_time = time.time()
    if props_cache['data'] is not None and props_cache['timestamp'] is not None:
        if current_time - props_cache['timestamp'] < props_cache['cache_duration']:
            print("Utilizzando dati dalla cache...")
            return props_cache['data']
    
    url = "https://www.pine-sports.com/PrizePicks/NBA/"
    
    try:
        print("\nRecupero props dei giocatori...")
        
        # Configura Chrome in modalità headless con ottimizzazioni
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--enable-javascript')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        # Inizializza il driver con webdriver_manager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Imposta un timeout più breve
        driver.set_page_load_timeout(15)
        driver.implicitly_wait(5)
        
        driver.get(url)
        
        # Ridotto il tempo di attesa iniziale
        print("Attendo il caricamento della pagina...")
        time.sleep(5)  # Ridotto da 10 a 5 secondi
        
        print(f"Titolo pagina: {driver.title}")
        print(f"URL corrente: {driver.current_url}")
        
        props_data = []
        
        try:
            # Cerca la tabella delle props con timeout ridotto
            print("Cerco la tabella delle props...")
            table = WebDriverWait(driver, 10).until(  # Ridotto da 20 a 10 secondi
                EC.presence_of_element_located((By.ID, "myTable"))
            )
            
            if table:
                print("Tabella trovata, analizzo le righe...")
                # Trova tutte le righe della tabella
                rows = table.find_elements(By.TAG_NAME, "tr")
                print(f"Trovate {len(rows)} righe nella tabella")
                
                for i, row in enumerate(rows[1:], 1):  # Salta l'header
                    try:
                        # Ottieni tutte le celle della riga
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 9:
                            game = cells[0].text.strip()
                            player_name = cells[1].text.strip()
                            prop = cells[2].text.strip()
                            line = cells[3].text.strip()
                            projection = cells[4].text.strip()
                            over_count = float(cells[7].text.strip())
                            under_count = float(cells[8].text.strip())
                            robot_likes = cells[9].text.strip() if len(cells) > 9 else ""
                            
                            # Verifica se almeno uno dei count è >= 9
                            if over_count >= 9 or under_count >= 9:
                                prop_info = {
                                    'game': game,
                                    'player': player_name,
                                    'prop': prop,
                                    'line': line,
                                    'projection': projection,
                                    'robot_likes': robot_likes
                                }
                                props_data.append(prop_info)
                                
                    except Exception as e:
                        print(f"Errore nell'analisi della riga #{i}: {e}")
                        continue
                
                print(f"\nTrovate {len(props_data)} props valide")
                
                # Aggiorna la cache
                props_cache['data'] = props_data
                props_cache['timestamp'] = current_time
                
            else:
                print("Tabella non trovata")
            
        except Exception as e:
            print(f"Errore nell'analisi delle props: {e}")
            print("Stacktrace completo:")
            traceback.print_exc()
        
        finally:
            # Chiudi subito il driver
            driver.quit()
        
        return props_data
        
    except Exception as e:
        print(f"Errore nell'inizializzazione di Selenium: {e}")
        print("Stacktrace completo:")
        traceback.print_exc()
        return []

# Cache per i dati delle props
props_cache = {
    'data': None,
    'timestamp': None,
    'cache_duration': 60  # Durata della cache in secondi
}

def get_sportitalia_props():
    """Recupera le linee proposte da SportItalia"""
    try:
        url = "https://www.sportitaliabet.it/it/sport/pallacanestro/nba"
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        
        # Inizializza il driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        print("Recupero props da SportItalia...")
        
        try:
            driver.get(url)
            time.sleep(5)  # Attendi il caricamento della pagina
            
            # Trova tutti i mercati dei giocatori
            props = []
            
            # Cerca i mercati "almeno X punti/rimbalzi/assist"
            print("Cerco i mercati dei giocatori...")
            page_source = driver.page_source
            print(f"Contenuto della pagina: {page_source[:500]}...")  # Stampa i primi 500 caratteri per debug
            
            # Prova diversi selettori
            markets = driver.find_elements(By.XPATH, "//*[contains(text(), 'almeno')]")
            
            for market in markets:
                try:
                    market_text = market.text
                    print(f"Analizzando mercato: {market_text}")
                    
                    # Estrai il nome del giocatore e la linea
                    if "punti" in market_text.lower():
                        stat_type = "Points"
                    elif "rimbalzi" in market_text.lower():
                        stat_type = "Rebounds"
                    elif "assist" in market_text.lower():
                        stat_type = "Assists"
                    else:
                        print(f"Mercato non rilevante: {market_text}")
                        continue
                        
                    # Estrai il valore della linea (il numero dopo "almeno")
                    match = re.search(r'almeno (\d+\.?\d*)', market_text.lower())
                    if not match:
                        print(f"Non riesco a trovare il valore numerico in: {market_text}")
                        continue
                        
                    line_value = float(match.group(1))
                    
                    # Estrai il nome del giocatore (assumiamo sia all'inizio del testo)
                    player_name = market_text.split(" almeno")[0].strip()
                    print(f"Trovato: {player_name} - {stat_type} - {line_value}")
                    
                    props.append({
                        'player': player_name,
                        'stats': {stat_type: line_value}
                    })
                    
                except Exception as e:
                    print(f"Errore nel processare un mercato: {str(e)}")
                    continue
            
            print(f"Props trovate: {props}")
            return props
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"Errore nel recupero delle props da SportItalia: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def show_props_window():
    """Mostra la finestra delle proiezioni props"""
    window, main_frame = create_magic_window("Proiezioni Props NBA")

    # Variabile per mantenere i dati in memoria
    cached_props_data = []

    # Frame per i controlli
    control_frame = create_magic_frame(main_frame)
    control_frame.pack(fill=tk.X, padx=5, pady=5)

    # Variabile per il filtro Over/Under
    filter_var = tk.StringVar(value="all")
    
    # Label per il filtro
    ttk.Label(control_frame, text="Filtra per:").pack(side=tk.LEFT, padx=5)
    
    # Radio buttons per il filtro
    ttk.Radiobutton(control_frame, text="Tutti", variable=filter_var, 
                    value="all").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(control_frame, text="Solo Over", variable=filter_var, 
                    value="over").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(control_frame, text="Solo Under", variable=filter_var, 
                    value="under").pack(side=tk.LEFT, padx=5)

    # Frame per il contenuto principale (risultati o loading)
    content_frame = create_magic_frame(main_frame)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Frame per l'animazione di caricamento
    loading_frame = create_magic_frame(content_frame)
    loading_symbols = ["🌟", "✨", "💫", "⭐", "🔮", "🎯"]
    loading_label = None
    current_symbol = 0

    def animate_loading():
        nonlocal current_symbol, loading_label
        if loading_label and loading_label.winfo_exists():
            current_symbol = (current_symbol + 1) % len(loading_symbols)
            loading_label.config(text=f"\n{loading_symbols[current_symbol]} L'AI Mago sta analizzando le props {loading_symbols[current_symbol]}\n")
            window.after(500, animate_loading)

    # Scrollbar e canvas per i risultati
    canvas = tk.Canvas(content_frame, bg=MAGIC_COLORS['background'])
    scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollable_frame = create_magic_frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Frame per i risultati
    results_frame = create_magic_frame(scrollable_frame)
    results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def show_loading():
        nonlocal loading_label
        # Nascondi il canvas e la scrollbar
        canvas.pack_forget()
        scrollbar.pack_forget()
        
        # Mostra il frame di caricamento
        loading_frame.pack(fill=tk.BOTH, expand=True)
        loading_label = create_magic_label(loading_frame, 
                                        "\n🌟 L'AI Mago sta analizzando le props 🌟\n",
                                        font_type='title')
        loading_label.pack(expand=True)
        animate_loading()
        # Forza l'aggiornamento della finestra
        window.update()

    def hide_loading():
        nonlocal loading_label
        # Nascondi il frame di caricamento
        loading_frame.pack_forget()
        if loading_label:
            loading_label.destroy()
            loading_label = None
            
        # Mostra il canvas e la scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Forza l'aggiornamento della finestra
        window.update()

    def update_props():
        # Mostra l'animazione di caricamento solo se stiamo effettivamente scaricando nuovi dati
        show_loading()
        
        def fetch_data():
            nonlocal cached_props_data
            # Scarica nuovi dati
            cached_props_data = get_player_props()
            # Aggiorna l'UI nel thread principale
            window.after(0, lambda: post_fetch_update())

        def post_fetch_update():
            # Aggiorna la visualizzazione con i dati filtrati
            display_filtered_props()
            # Nascondi l'animazione di caricamento
            hide_loading()

        # Avvia il recupero dei dati in un thread separato
        threading.Thread(target=fetch_data, daemon=True).start()

    def display_filtered_props():
        # Pulisci il frame dei risultati
        for widget in results_frame.winfo_children():
            widget.destroy()
        
        current_filter = filter_var.get()
        
        if cached_props_data:
            # Header
            header_frame = create_magic_frame(results_frame)
            header_frame.pack(fill=tk.X, padx=5)
            create_magic_label(header_frame, "Partita", width=30).pack(side=tk.LEFT)
            create_magic_label(header_frame, "Giocatore", width=25).pack(side=tk.LEFT)
            create_magic_label(header_frame, "Prop", width=15).pack(side=tk.LEFT)
            create_magic_label(header_frame, "Linea", width=10).pack(side=tk.LEFT)
            create_magic_label(header_frame, "Proiezione", width=10).pack(side=tk.LEFT)
            create_magic_label(header_frame, "AI Mago suggerisce", width=15).pack(side=tk.LEFT)
            
            # Mostra tutte le props, senza filtrare per count
            filtered_props = []
            if current_filter == "all":
                filtered_props = cached_props_data
            elif current_filter == "over":
                filtered_props = [p for p in cached_props_data if "Over" in p.get('robot_likes', '')]
            elif current_filter == "under":
                filtered_props = [p for p in cached_props_data if "Under" in p.get('robot_likes', '')]
            
            if filtered_props:
                for prop in filtered_props:
                    prop_frame = create_magic_frame(results_frame)
                    prop_frame.pack(fill=tk.X, padx=5)
                    create_magic_label(prop_frame, prop.get('game', ''), width=30).pack(side=tk.LEFT)
                    create_magic_label(prop_frame, prop.get('player', ''), width=25).pack(side=tk.LEFT)
                    create_magic_label(prop_frame, prop.get('prop', ''), width=15).pack(side=tk.LEFT)
                    create_magic_label(prop_frame, prop.get('line', ''), width=10).pack(side=tk.LEFT)
                    create_magic_label(prop_frame, prop.get('projection', ''), width=10).pack(side=tk.LEFT)
                    create_magic_label(prop_frame, prop.get('robot_likes', ''), width=15).pack(side=tk.LEFT)
            else:
                create_magic_label(results_frame, "Nessuna prop trovata per il filtro selezionato").pack(pady=20)
        else:
            create_magic_label(results_frame, "Nessuna prop trovata").pack(pady=20)
    
    # Bottone di aggiornamento con stile magico
    update_button = create_magic_button(main_frame, "🔮 Aggiorna Props", update_props)
    update_button.pack(pady=10)

    # Aggiorna il filtro quando cambia la selezione
    filter_var.trace('w', lambda *args: display_filtered_props())

    # Aggiorna le props all'apertura della finestra
    update_props()

def get_player_vs_team_games(player_name, team_abbr, num_games=10):
    """Ottiene le statistiche delle ultime N partite di un giocatore contro una specifica squadra"""
    from nba_api.stats.static import players, teams
    
    # Trova il giocatore
    player = next((p for p in players.get_active_players() 
                  if p['full_name'].lower() == player_name.lower()), None)
    
    if not player:
        return None
        
    # Trova la squadra
    team = next((t for t in teams.get_teams() 
                if t['abbreviation'] == team_abbr), None)
    
    if not team:
        return None
    
    # Ottieni il game log completo del giocatore
    game_log = playergamelog.PlayerGameLog(player_id=player['id'], season='ALL')
    games_df = game_log.get_data_frames()[0]
    
    # Filtra le partite contro la squadra specificata
    team_games = games_df[games_df['MATCHUP'].str.contains(team['abbreviation'])]
    
    # Prendi solo le ultime N partite
    last_team_games = team_games.head(num_games)
    
    if last_team_games.empty:
        return None
    
    # Calcola le medie delle partite contro questa squadra
    avg_stats = {
        'PPG': round(last_team_games['PTS'].mean(), 1),
        'RPG': round(last_team_games['REB'].mean(), 1),
        'APG': round(last_team_games['AST'].mean(), 1),
        'MPG': round(last_team_games['MIN'].astype(float).mean(), 1)
    }
    
    # Prepara i dati delle singole partite
    game_stats = []
    for _, game in last_team_games.iterrows():
        game_stats.append({
            'DATA': game['GAME_DATE'],
            'VS': game['MATCHUP'],
            'MIN': game['MIN'],
            'PTS': game['PTS'],
            'REB': game['REB'],
            'AST': game['AST'],
            'STL': game['STL'],
            'BLK': game['BLK'],
            'FG_PCT': f"{float(game['FG_PCT']):.1%}" if game['FG_PCT'] else "0.0%",
            'FG3M': game['FG3M']
        })
    
    return {'averages': avg_stats, 'games': game_stats}

def get_next_opponent(player_name):
    """Trova la prossima squadra contro cui giocherà il giocatore usando l'API NBA"""
    from nba_api.stats.static import players, teams
    from nba_api.stats.endpoints import scoreboardv2
    import datetime
    import pytz
    
    try:
        # Trova il giocatore
        player = next((p for p in players.get_active_players() 
                      if p['full_name'].lower() == player_name.lower()), None)
        
        if not player:
            print(f"Giocatore non trovato: {player_name}")
            return None
        
        # Ottieni la squadra del giocatore
        player_stats = playercareerstats.PlayerCareerStats(player_id=player['id'])
        player_df = player_stats.get_data_frames()[0]
        
        if player_df.empty:
            print(f"Nessuna statistica trovata per: {player_name}")
            return None
        
        # Prendi l'ultima riga per la stagione corrente
        current_season_stats = player_df[player_df['SEASON_ID'] == '2024-25']
        
        if current_season_stats.empty:
            print(f"Nessuna statistica per la stagione corrente trovata per: {player_name}")
            # Prova con l'ultima stagione disponibile
            current_team_id = player_df.iloc[-1]['TEAM_ID']
        else:
            current_team_id = current_season_stats.iloc[0]['TEAM_ID']
        
        # Ottieni il nome della squadra
        team = next((t for t in teams.get_teams() 
                    if t['id'] == current_team_id), None)
        
        if not team:
            print(f"Squadra non trovata per il giocatore: {player_name}")
            return None
        
        print(f"Squadra attuale del giocatore: {team['full_name']} ({team['abbreviation']})")
        
        # Ottieni le partite per oggi e i prossimi 7 giorni
        today = datetime.datetime.now()
        italian_tz = pytz.timezone('Europe/Rome')
        
        for day_offset in range(8):  # Controlla 8 giorni
            current_date = today + datetime.timedelta(days=day_offset)
            date_str = current_date.strftime("%Y%m%d")
            
            # URL dell'API ESPN per le partite NBA con data specifica
            espn_api_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str}"
            
            # Effettua la richiesta all'API
            response = requests.get(espn_api_url)
            data = response.json()
            
            # Verifica se ci sono eventi
            if 'events' in data and data['events']:
                for event in data['events']:
                    try:
                        # Estrai data e ora dell'evento
                        date_str = event['date']
                        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%MZ")
                        
                        # Converti da UTC a ora italiana
                        date_obj = date_obj.replace(tzinfo=pytz.UTC)
                        date_obj_it = date_obj.astimezone(italian_tz)
                        
                        # Verifica se la partita è già iniziata
                        now = datetime.datetime.now(italian_tz)
                        if date_obj_it < now:
                            continue
                        
                        # Estrai i nomi delle squadre
                        home_team = event['competitions'][0]['competitors'][0]['team']['displayName']
                        away_team = event['competitions'][0]['competitors'][1]['team']['displayName']
                        
                        # Verifica se la squadra del giocatore è coinvolta
                        if team['full_name'] in [home_team, away_team]:
                            # Determina se è una partita in casa o in trasferta
                            is_home = team['full_name'] == home_team
                            opponent = away_team if is_home else home_team
                            
                            # Trova la squadra avversaria nei dati delle squadre NBA
                            opponent_team = next((t for t in teams.get_teams() 
                                                if t['full_name'] == opponent), None)
                            
                            if opponent_team:
                                print(f"Prossima partita trovata: {team['abbreviation']} vs {opponent_team['abbreviation']} il {date_obj_it.strftime('%d/%m/%Y')} alle {date_obj_it.strftime('%H:%M')}")
                                return {
                                    'team': team,
                                    'opponent': opponent_team,
                                    'game_date': date_obj_it.strftime('%d/%m/%Y'),
                                    'game_time': date_obj_it.strftime('%H:%M'),
                                    'is_home': is_home
                                }
                    except Exception as e:
                        print(f"Errore nel processare la partita: {str(e)}")
                        continue
        
        print(f"Nessuna partita programmata trovata per: {team['abbreviation']}")
        return None
    
    except Exception as e:
        print(f"Errore generale in get_next_opponent: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_rebounds_last3():
    """Recupera i rimbalzi concessi nelle ultime 3 partite da TeamRankings"""
    url = "https://www.teamrankings.com/nba/stat/opponent-total-rebounds-per-game"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rebounds_data = {}
        table = soup.find('table', {'class': 'tr-table'})
        
        if table:
            rows = table.find_all('tr')[1:]  # Salta l'header
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    team = cells[1].text.strip()
                    last3 = cells[3].text.strip()
                    rebounds_data[team] = float(last3)
        
        return rebounds_data
    except Exception as e:
        print(f"Errore nel recupero dei rimbalzi (ultime 3): {e}")
        return {}

def get_rebounds_season():
    """Recupera i rimbalzi concessi nella stagione da TeamRankings"""
    url = "https://www.teamrankings.com/nba/stat/opponent-total-rebounds-per-game"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("\nRecupero dati rimbalzi stagionali...")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'tr-table'})
            
            rebounds_data = {}
            
            if table:
                rows = table.find_all('tr')[1:]  # Salta l'header
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:  # Ci servono almeno 3 colonne
                        try:
                            team = cells[1].text.strip()
                            season_value = cells[2].text.strip()  # Colonna 2024
                            if season_value and season_value != '-':
                                rebounds_data[team] = float(season_value)
                        except Exception as e:
                            print(f"Errore nel processare riga: {e}")
            
            return rebounds_data
        else:
            print(f"Errore nella richiesta HTTP: {response.status_code}")
            return {}
            
    except Exception as e:
        print(f"Errore nel recupero dei rimbalzi: {e}")
        return {}

def get_points_last3():
    """Recupera i punti concessi nelle ultime 3 partite da TeamRankings"""
    url = "https://www.teamrankings.com/nba/stat/opponent-points-per-game"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        points_data = {}
        table = soup.find('table', {'class': 'tr-table'})
        
        if table:
            rows = table.find_all('tr')[1:]  # Salta l'header
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:  # Ci servono almeno 4 colonne
                    try:
                        team = cells[1].text.strip()
                        last3 = cells[3].text.strip()  # Colonna Last 3
                        if last3 and last3 != '-':
                            points_data[team] = float(last3)
                    except Exception as e:
                        print(f"Errore nel processare riga: {e}")
                        continue
        
        return points_data
    except Exception as e:
        print(f"Errore nel recupero dei punti (ultime 3): {e}")
        return {}

def get_points_season():
    """Recupera i punti concessi nella stagione da TeamRankings"""
    url = "https://www.teamrankings.com/nba/stat/opponent-points-per-game"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        points_data = {}
        table = soup.find('table', {'class': 'tr-table'})
        
        if table:
            rows = table.find_all('tr')[1:]  # Salta l'header
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:  # Ci servono almeno 3 colonne
                    try:
                        team = cells[1].text.strip()
                        season = cells[2].text.strip()  # Colonna 2024
                        if season and season != '-':
                            points_data[team] = float(season)
                    except Exception as e:
                        print(f"Errore nel processare riga: {e}")
                        continue
        
        return points_data
    except Exception as e:
        print(f"Errore nel recupero dei punti (stagione): {e}")
        return {}

def get_propchasers_data():
    """Recupera i dati delle props da propchasers.com"""
    try:
        url = "https://propchasers.com/NBA/HitRate"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        props_data = []
        
        # Trova la tabella con i dati
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]  # Salta l'header
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 8:  # Assicurati che ci siano abbastanza colonne
                    try:
                        player_name = cols[0].text.strip()
                        prop = cols[1].text.strip()
                        line = cols[2].text.strip()
                        last5 = cols[4].text.strip()
                        
                        # Estrai la percentuale dalle ultime 5 partite
                        last5_match = re.search(r'%(\d+)', last5)
                        if last5_match:
                            last5_percentage = int(last5_match.group(1))
                            # Aggiungi solo se è 100%
                            if last5_percentage == 100:
                                props_data.append({
                                    'player': player_name,
                                    'prop': prop,
                                    'line': line,
                                    'last5': last5
                                })
                    except Exception as e:
                        print(f"Errore nel processare una riga: {e}")
                        continue
        
        return props_data
        
    except Exception as e:
        print(f"Errore nel recupero dei dati da propchasers: {e}")
        return []

def extract_rank(text):
    """Estrae il rank numerico dal testo nel formato '#number'"""
    try:
        # Cerca il pattern '#numero'
        match = re.search(r'#(\d+)', text.strip())
        if match:
            return int(match.group(1))
        return None
    except (ValueError, TypeError, AttributeError):
        return None

def get_defense_vs_position():
    """Recupera le statistiche difensive contro ogni ruolo da FantasyPros"""
    url = "https://www.fantasypros.com/nba/defense-vs-position.php"
    
    try:
        # Configurazione avanzata di Chrome
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--enable-javascript')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        prefs = {
            'profile.managed_default_content_settings.images': 2,
            'profile.default_content_setting_values.notifications': 2
        }
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Crea una finestra di caricamento globale
        loading_window = tk.Toplevel()
        loading_window.title("✨ Caricamento Statistiche ✨")
        loading_window.geometry("400x200")
        loading_window.configure(bg="#E6F2FF")
        loading_window.resizable(False, False)
        
        # Frame principale per il caricamento
        loading_frame = tk.Frame(loading_window, bg="#E6F2FF")
        loading_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Label per il titolo
        title_label = tk.Label(loading_frame, text="🔮 Analisi Statistiche Difensive 🔮",
                             font=("Verdana", 12, "bold"), bg="#E6F2FF", fg="#1E3D6B")
        title_label.pack(pady=(0, 10))
        
        # Label per lo stato corrente
        status_label = tk.Label(loading_frame, text="Inizializzazione...",
                              font=("Verdana", 10), bg="#E6F2FF", fg="#2C3E50")
        status_label.pack(pady=5)
        
        # Progress bar per il progresso totale
        total_progress = ttk.Progressbar(loading_frame, orient="horizontal",
                                       length=300, mode="determinate")
        total_progress.pack(pady=10)
        
        # Label per il dettaglio del progresso
        detail_label = tk.Label(loading_frame, text="",
                              font=("Verdana", 9), bg="#E6F2FF", fg="#666666")
        detail_label.pack(pady=5)
        
        # Funzione per aggiornare lo stato
        def update_status(message, progress_value=None, detail=""):
            status_label.config(text=message)
            if progress_value is not None:
                total_progress["value"] = progress_value
            detail_label.config(text=detail)
            loading_window.update()
        
        print("\nInizializzazione del driver Chrome...")
        update_status("Inizializzazione del browser...", 10)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        try:
            print("Accesso alla pagina...")
            update_status("Accesso alla pagina delle statistiche...", 20)
            driver.get(url)
            
            print("Attendo il caricamento completo della pagina...")
            update_status("Caricamento della pagina...", 30)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(3)
            
            # Inizializza il dizionario per i dati
            position_data = {
                'PG': {'points': {}, 'rebounds': {}, 'assists': {}, 'steals': {}, 'blocks': {}, 'threes': {}},
                'SG': {'points': {}, 'rebounds': {}, 'assists': {}, 'steals': {}, 'blocks': {}, 'threes': {}},
                'SF': {'points': {}, 'rebounds': {}, 'assists': {}, 'steals': {}, 'blocks': {}, 'threes': {}},
                'PF': {'points': {}, 'rebounds': {}, 'assists': {}, 'steals': {}, 'blocks': {}, 'threes': {}},
                'C': {'points': {}, 'rebounds': {}, 'assists': {}, 'steals': {}, 'blocks': {}, 'threes': {}}
            }
            
            # Lista delle posizioni da analizzare (escludi 'Overall')
            positions = ['PG', 'SG', 'SF', 'PF', 'C']
            
            # Mappa delle colonne per ogni statistica
            stat_columns = {
                'points': 1,    # PTS
                'rebounds': 2,  # REB
                'assists': 3,   # AST
                'threes': 4,    # 3PM
                'steals': 5,    # STL
                'blocks': 6     # BLK
            }
            
            # Calcola il progresso per posizione
            progress_per_position = 50 / len(positions)
            
            for pos_idx, position in enumerate(positions):
                try:
                    print(f"\nAnalisi posizione: {position}")
                    current_progress = 30 + (pos_idx * progress_per_position)
                    update_status(f"Analisi statistiche {position}...", 
                                current_progress,
                                f"Posizione {pos_idx + 1} di {len(positions)}")
                    
                    # Trova il tab della posizione
                    try:
                        # Prima prova con il testo esatto
                        position_tab = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, f"//a[text()='{position}']"))
                        )
                    except:
                        # Se non funziona, prova con contains
                        position_tab = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{position}')]"))
                        )
                    
                    # Scorri fino al tab e cliccalo
                    driver.execute_script("arguments[0].scrollIntoView(true);", position_tab)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", position_tab)
                    time.sleep(2)
                    
                    # Trova la tabella delle statistiche
                    table = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "table"))
                    )
                    
                    # Ottieni tutte le righe della tabella
                    rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Salta l'header
                    
                    # Calcola il progresso per riga
                    progress_per_row = progress_per_position / len(rows)
                    
                    for row_idx, row in enumerate(rows):
                        try:
                            row_progress = current_progress + (row_idx * progress_per_row)
                            update_status(f"Analisi statistiche {position}...", 
                                        row_progress,
                                        f"Analisi squadra {row_idx + 1} di {len(rows)}")
                            
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 7:  # Assicurati che ci siano abbastanza colonne
                                team_name = cells[0].text.strip()
                                if not team_name:  # Salta righe senza nome squadra
                                    continue
                                
                                # Estrai i valori per ogni statistica
                                for stat, col_idx in stat_columns.items():
                                    try:
                                        # Ottieni il testo della cella e rimuovi spazi
                                        cell_text = cells[col_idx].text.strip()
                                        
                                        # Se la cella è vuota o contiene solo spazi, salta
                                        if not cell_text:
                                            print(f"Cella vuota trovata per {team_name}, {stat}")
                                            continue
                                        
                                        # Rimuovi eventuali caratteri non numerici (tranne il punto decimale)
                                        clean_value = ''.join(c for c in cell_text if c.isdigit() or c == '.')
                                        
                                        # Se non abbiamo un valore valido dopo la pulizia, salta
                                        if not clean_value:
                                            print(f"Nessun valore numerico trovato per {team_name}, {stat}")
                                            continue
                                        
                                        # Converti in float
                                        value = float(clean_value)
                                        position_data[position][stat][team_name] = value
                                        
                                    except ValueError as e:
                                        print(f"Errore nella conversione del valore per {team_name}, {stat}: {str(e)}")
                                        continue
                                    except Exception as e:
                                        print(f"Errore generico per {team_name}, {stat}: {str(e)}")
                                        continue
                                
                        except Exception as e:
                            print(f"Errore nell'analisi di una riga: {str(e)}")
                            continue
                    
                except Exception as e:
                    print(f"Errore nell'analisi della posizione {position}: {str(e)}")
                    continue
            
            # Verifica se abbiamo raccolto dati
            update_status("Verifica dei dati raccolti...", 90)
            data_found = False
            for pos in position_data:
                for stat_type in position_data[pos]:
                    if position_data[pos][stat_type]:
                        data_found = True
                        print(f"\nDati trovati per {pos} - {stat_type}: {len(position_data[pos][stat_type])} squadre")
            
            if not data_found:
                print("Nessun dato trovato nelle tabelle")
                loading_window.destroy()
                return None
            
            # Ordina i dati per ogni statistica (dal più alto al più basso)
            update_status("Ordinamento dei dati...", 95)
            for pos in position_data:
                for stat_type in position_data[pos]:
                    position_data[pos][stat_type] = dict(
                        sorted(position_data[pos][stat_type].items(), 
                              key=lambda x: x[1], 
                              reverse=True)  # Ordine decrescente
                    )
            
            update_status("Completato!", 100, "Analisi completata con successo!")
            time.sleep(1)  # Mostra brevemente il completamento
            loading_window.destroy()
            return position_data
        
        finally:
            print("Chiusura del driver Chrome...")
            driver.quit()
    
    except Exception as e:
        print(f"Errore nel recupero dei dati difensivi per ruolo: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'loading_window' in locals():
            loading_window.destroy()
        return None

def get_team_players_by_position():
    """Ottiene i giocatori attivi per ogni squadra e ruolo usando l'API NBA"""
    from nba_api.stats.static import teams
    from nba_api.stats.endpoints import commonteamroster, leaguedashplayerstats
    import time
    
    try:
        print("\nRecupero roster aggiornati delle squadre...")
        team_players = {}
        all_teams = teams.get_teams()
        
        # Ottieni la lista dei giocatori infortunati
        print("Recupero lista giocatori infortunati...")
        try:
            injured_players = get_injured_players()
            # Verifica se injured_players è una lista di dizionari o una lista di stringhe
            if injured_players and isinstance(injured_players[0], dict):
                injured_names = [player.get('PLAYER', '') for player in injured_players]
            else:
                injured_names = [str(player).strip() for player in injured_players if player]
            print(f"Trovati {len(injured_names)} giocatori infortunati")
        except Exception as e:
            print(f"Errore nel recupero dei giocatori infortunati: {str(e)}")
            injured_names = []
        
        # Ottieni le statistiche dei minuti per tutti i giocatori
        print("Recupero statistiche dei minuti giocati...")
        player_stats = leaguedashplayerstats.LeagueDashPlayerStats(
            per_mode_detailed='PerGame',
            season='2023-24',
            season_type_all_star='Regular Season'
        )
        stats_df = player_stats.get_data_frames()[0]
        
        # Crea un dizionario dei minuti giocati per giocatore
        minutes_played = {
            player['PLAYER_NAME']: player['MIN']
            for _, player in stats_df.iterrows()
            if player['MIN'] is not None
        }
        
        # Mappa personalizzata per correggere i ruoli di alcuni giocatori
        player_position_overrides = {
            'Malik Beasley': 'SG',
            'Ausar Thompson': 'PF',
            'Jimmy Butler': 'SF',
            'Anthony Davis': 'C',
            'Paolo Banchero': 'PF',
            'Franz Wagner': 'SF',
            'Jalen Suggs': 'PG',
            'Scottie Barnes': 'PF',
            'Jalen Green': 'SG',
            'Alperen Sengun': 'C',
            'Jabari Smith Jr.': 'PF',
            'Victor Wembanyama': 'C',
            'Cade Cunningham': 'PG',
            'Jalen Duren': 'C'
        }
        
        # Mappa delle posizioni standard NBA
        position_mapping = {
            'G': ['PG'],
            'G-F': ['SG'],
            'F': ['SF'],
            'F-G': ['SF'],
            'F-C': ['PF'],
            'C': ['C'],
            'C-F': ['C']
        }
        
        for team in all_teams:
            try:
                print(f"\nRecupero roster per {team['full_name']}...")
                
                # Ottieni il roster aggiornato della squadra
                roster = commonteamroster.CommonTeamRoster(team_id=team['id'])
                roster_df = roster.get_data_frames()[0]
                
                # Inizializza il dizionario per questa squadra
                team_players[team['full_name']] = {
                    'PG': [], 'SG': [], 'SF': [], 'PF': [], 'C': []
                }
                
                # Processa ogni giocatore del roster
                for _, player in roster_df.iterrows():
                    try:
                        player_name = player['PLAYER']
                        position = player['POSITION']
                        
                        # Controlla se il giocatore è infortunato
                        if any(injured_name.lower() in player_name.lower() for injured_name in injured_names):
                            print(f"Saltato {player_name} - attualmente infortunato")
                            continue
                        
                        # Controlla i minuti giocati
                        minutes = minutes_played.get(player_name, 0)
                        if minutes < 20:
                            print(f"Saltato {player_name} - gioca solo {minutes} minuti per partita")
                            continue
                            
                        print(f"Processando {player_name} ({position}) - {minutes} MPG")
                        
                        # Usa l'override se disponibile
                        if player_name in player_position_overrides:
                            assigned_position = player_position_overrides[player_name]
                            team_players[team['full_name']][assigned_position].append(player_name)
                            print(f"Posizione corretta manualmente per {player_name}: {assigned_position}")
                            continue
                        
                        # Altrimenti usa la mappa delle posizioni standard
                        if position in position_mapping:
                            positions = position_mapping[position]
                            for pos in positions:
                                if player_name not in team_players[team['full_name']][pos]:
                                    team_players[team['full_name']][pos].append(player_name)
                                    print(f"Aggiunto {player_name} a {team['full_name']} come {pos}")
                    
                    except Exception as e:
                        print(f"Errore nel processare il giocatore {player_name}: {str(e)}")
                        continue
                
                # Piccola pausa per evitare rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"Errore nel recupero del roster per {team['full_name']}: {str(e)}")
                continue
        
        # Debug: stampa il riepilogo finale
        print("\nRIEPILOGO FINALE:")
        for team in team_players:
            print(f"\n{team}:")
            for pos in team_players[team]:
                print(f"  {pos}: {len(team_players[team][pos])} giocatori")
                print(f"    {', '.join(team_players[team][pos])}")
        
        return team_players
        
    except Exception as e:
        print(f"Errore nel recupero dei giocatori: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def analyze_player_insights():
    """Analizza le possibili over/under performance dei giocatori basandosi su vari fattori"""
    try:
        # 1. Ottieni le partite di oggi e domani
        today = datetime.now()
        games = {}
        
        # Finestra di caricamento
        loading_window = tk.Toplevel()
        loading_window.title("✨ Analisi Curiosità ✨")
        loading_window.geometry("400x200")
        loading_window.configure(bg="#E6F2FF")
        
        loading_frame = tk.Frame(loading_window, bg="#E6F2FF")
        loading_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        status_label = tk.Label(loading_frame, 
                              text="Recupero partite in programma...",
                              font=("Verdana", 10), bg="#E6F2FF")
        status_label.pack(pady=10)
        
        progress = ttk.Progressbar(loading_frame, orient="horizontal",
                                 length=300, mode="determinate")
        progress.pack(pady=10)
        
        def update_status(message, value):
            status_label.config(text=message)
            progress["value"] = value
            loading_window.update()
        
        # Mappa dei nomi delle squadre per standardizzazione
        team_name_mapping = {
            "LA Clippers": "Los Angeles Clippers",
            "LA Lakers": "Los Angeles Lakers",
            "Brooklyn": "Brooklyn Nets",
            "New York": "New York Knicks",
            "Philadelphia": "Philadelphia 76ers",
            "Golden State": "Golden State Warriors",
            "Oklahoma City": "Oklahoma City Thunder",
            "Portland": "Portland Trail Blazers",
            "San Antonio": "San Antonio Spurs",
            "New Orleans": "New Orleans Pelicans",
            # Aggiungi altre mappature se necessario
        }
        
        # Recupera le partite per oggi e domani
        update_status("Recupero calendario partite...", 10)
        for day_offset in range(2):  # Oggi e domani
            current_date = today + timedelta(days=day_offset)
            date_str = current_date.strftime("%Y%m%d")
            
            espn_api_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str}"
            response = requests.get(espn_api_url)
            data = response.json()
            
            if 'events' in data:
                for event in data['events']:
                    game_date = current_date.strftime("%d/%m/%Y")
                    home_team = event['competitions'][0]['competitors'][0]['team']['displayName']
                    away_team = event['competitions'][0]['competitors'][1]['team']['displayName']
                    
                    # Standardizza i nomi delle squadre
                    if home_team in team_name_mapping:
                        home_team = team_name_mapping[home_team]
                    if away_team in team_name_mapping:
                        away_team = team_name_mapping[away_team]
                    
                    games[game_date] = games.get(game_date, []) + [(away_team, home_team)]
        
        # Debug: stampa le partite trovate
        print("\nPartite trovate:")
        for date, matchups in games.items():
            print(f"{date}:")
            for away, home in matchups:
                print(f"  {away} @ {home}")
        
        # 2. Ottieni le statistiche difensive per ruolo
        update_status("Analisi statistiche difensive...", 30)
        defensive_stats = get_defense_vs_position()
        
        # Debug: stampa le squadre nelle statistiche difensive
        if defensive_stats:
            print("\nSquadre nelle statistiche difensive:")
            for pos in defensive_stats:
                print(f"\n{pos}:")
                for stat in defensive_stats[pos]:
                    print(f"  {stat}: {list(defensive_stats[pos][stat].keys())[:3]}...")
        
        # 3. Ottieni i giocatori per ogni squadra e ruolo
        update_status("Recupero roster delle squadre...", 40)
        team_players = get_team_players_by_position()
        
        # Debug: stampa i team trovati nel roster
        if team_players:
            print("\nSquadre nel roster:")
            print(list(team_players.keys()))
        
        if not team_players:
            raise Exception("Impossibile recuperare i roster delle squadre")
        
        # Dizionario per tenere traccia delle partite già analizzate
        analyzed_games = set()
        insights = []
        
        # Per ogni partita
        total_games = sum(len(g) for g in games.values())
        games_analyzed = 0
        
        for date, day_games in games.items():
            for away_team, home_team in day_games:
                game_key = f"{away_team}@{home_team}"
                if game_key in analyzed_games:
                    continue
                
                games_analyzed += 1
                progress_value = 50 + (40 * games_analyzed / total_games)
                update_status(f"Analisi {away_team} vs {home_team}...", progress_value)
                
                best_insight = None
                best_priority = 0  # Più basso è più alta è la priorità
                
                # Analizza i giocatori di entrambe le squadre
                for team, opponent in [(home_team, away_team), (away_team, home_team)]:
                    if team in team_players:
                        for position in ['PG', 'SG', 'SF', 'PF', 'C']:
                            if position in team_players[team] and defensive_stats and position in defensive_stats:
                                for player in team_players[team][position]:
                                    for stat in ['points', 'rebounds', 'assists']:
                                        if stat in defensive_stats[position]:
                                            stat_rankings = list(defensive_stats[position][stat].items())
                                            total_teams = len(stat_rankings)
                                            
                                            # Trova il rank della squadra avversaria
                                            for rank, (def_team, value) in enumerate(stat_rankings, 1):
                                                if def_team == opponent:
                                                    # Calcola la priorità per overperform (peggiori difese)
                                                    if rank <= 3:  # Top 3 peggiori difese
                                                        current_priority = rank  # 1, 2, o 3
                                                        is_bad_defense = True
                                                    # Calcola la priorità per underperform (migliori difese)
                                                    elif rank >= total_teams - 2:  # Top 3 migliori difese
                                                        current_priority = total_teams - rank + 1  # 1, 2, o 3
                                                        is_bad_defense = False
                                                    else:
                                                        continue  # Salta le difese nella media
                                                    
                                                    # Aggiorna l'insight se troviamo una priorità migliore (numero più basso)
                                                    if best_insight is None or current_priority < best_priority:
                                                        stat_name = {'points': 'punti', 'rebounds': 'rimbalzi', 'assists': 'assist'}[stat]
                                                        
                                                        # Crea il messaggio appropriato
                                                        if is_bad_defense:
                                                            rank_text = {1: "peggiore", 2: "seconda peggiore", 3: "terza peggiore"}[rank]
                                                        else:
                                                            inverse_rank = total_teams - rank + 1
                                                            rank_text = {1: "migliore", 2: "seconda migliore", 3: "terza migliore"}[inverse_rank]
                                                        
                                                        best_insight = {
                                                            'date': date,
                                                            'matchup': f"{away_team} @ {home_team}",
                                                            'player': player,
                                                            'position': position,
                                                            'stat': stat_name,
                                                            'type': 'overperform' if is_bad_defense else 'underperform',
                                                            'rank_text': rank_text,
                                                            'rank': rank,
                                                            'total_teams': total_teams,
                                                            'value': value
                                                        }
                                                        best_priority = current_priority
                
                if best_insight:
                    insights.append(best_insight)
                analyzed_games.add(game_key)
        
        update_status("Analisi completata!", 100)
        loading_window.destroy()
        
        # Debug: stampa gli insights trovati
        print(f"\nTotale insights trovati: {len(insights)}")
        for insight in insights:
            print(f"- {insight['player']} ({insight['matchup']})")
        
        return insights
        
    except Exception as e:
        print(f"Errore nell'analisi delle curiosità: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'loading_window' in locals():
            loading_window.destroy()
        return None

def show_player_insights():
    """Mostra la finestra delle curiosità sui giocatori"""
    window, main_frame = create_magic_window("Curiosità Giocatori NBA", "1000x800")
    
    # Frame per i controlli
    control_frame = create_magic_frame(main_frame)
    control_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # Variabili per i filtri
    filter_var = tk.StringVar(value="all")
    
    # Radio buttons per il filtro
    ttk.Radiobutton(control_frame, text="Tutte le curiosità", 
                    variable=filter_var, value="all").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(control_frame, text="Solo Overperform", 
                    variable=filter_var, value="over").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(control_frame, text="Solo Underperform", 
                    variable=filter_var, value="under").pack(side=tk.LEFT, padx=5)
    
    # Frame per i risultati con scrollbar
    results_frame = tk.Frame(main_frame, bg="#FFFFFF")
    results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    canvas = tk.Canvas(results_frame, bg="#FFFFFF")
    scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Variabile per memorizzare i dati
    cached_insights = []
    
    def display_insights():
        # Pulisci il frame dei risultati
        for widget in scrollable_frame.winfo_children():
            widget.destroy()
        
        # Usa i dati dalla cache se disponibili, altrimenti caricali
        nonlocal cached_insights
        if not cached_insights:
            cached_insights = analyze_player_insights()
        
        if not cached_insights:
            tk.Label(scrollable_frame, 
                    text="Nessuna curiosità trovata",
                    font=("Helvetica", 12), 
                    bg="#FFFFFF").pack(pady=20)
            return
        
        # Filtra in base alla selezione
        current_filter = filter_var.get()
        filtered_insights = cached_insights
        if current_filter == "over":
            filtered_insights = [i for i in cached_insights if i['type'] == 'overperform']
        elif current_filter == "under":
            filtered_insights = [i for i in cached_insights if i['type'] == 'underperform']
        
        # Raggruppa per data
        insights_by_date = {}
        for insight in filtered_insights:
            date = insight['date']
            if date not in insights_by_date:
                insights_by_date[date] = []
            insights_by_date[date].append(insight)
        
        # Mostra le curiosità raggruppate per data
        for date in sorted(insights_by_date.keys()):
            # Header della data
            date_frame = tk.Frame(scrollable_frame, bg="#F0F4F8")
            date_frame.pack(fill=tk.X, pady=(10,0))
            tk.Label(date_frame, 
                    text=f"📅 {date}",
                    font=("Helvetica", 12, "bold"),
                    bg="#F0F4F8",
                    fg="#1E3D6B").pack(anchor="w", padx=10, pady=5)
            
            for insight in insights_by_date[date]:
                # Frame per ogni curiosità
                insight_frame = tk.Frame(scrollable_frame, bg="#FFFFFF", relief="ridge", bd=1)
                insight_frame.pack(fill=tk.X, pady=2, padx=5)
                
                # Icona e colore in base al tipo
                icon = "🔥" if insight['type'] == 'overperform' else "❄️"
                color = "#2ECC71" if insight['type'] == 'overperform' else "#E74C3C"
                
                # Testo della curiosità
                if insight['type'] == 'overperform':
                    text = (f"{icon} {insight['player']} ({insight['matchup']}) affronta la {insight['rank_text']} "
                           f"difesa della lega sui {insight['stat']} concessi ai {insight['position']} "
                           f"(#{insight['rank']}/{insight['total_teams']})")
                else:
                    text = (f"{icon} {insight['player']} ({insight['matchup']}) affronta la {insight['rank_text']} "
                           f"difesa della lega sui {insight['stat']} concessi ai {insight['position']} "
                           f"(#{insight['rank']}/{insight['total_teams']})")
                
                tk.Label(insight_frame,
                        text=text,
                        font=("Helvetica", 10),
                        bg="#FFFFFF",
                        fg=color,
                        wraplength=900).pack(padx=10, pady=5)
    
    # Configura il layout finale
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Aggiorna quando cambia il filtro
    filter_var.trace('w', lambda *args: display_insights())
    
    # Mostra le curiosità iniziali
    display_insights()

def get_machine_id():
    """Ottiene un ID unico per la macchina corrente"""
    import uuid
    import platform
    
    # Combina informazioni del sistema per creare un ID unico
    system_info = [
        platform.node(),  # Nome del computer
        platform.machine(),  # Architettura
        platform.processor(),  # Processore
        str(uuid.getnode())  # MAC address
    ]
    
    # Crea un hash unico delle informazioni
    machine_id = hashlib.sha256(''.join(system_info).encode()).hexdigest()
    return machine_id

def get_app_data_path():
    """Ottiene il percorso della cartella dati dell'applicazione"""
    import os
    import sys
    
    if getattr(sys, 'frozen', False):
        # Se l'app è un exe (PyInstaller)
        app_data = os.path.join(os.environ['APPDATA'], 'NBAStatsPro')
    else:
        # Se l'app è in sviluppo
        app_data = os.path.dirname(__file__)
    
    # Crea la cartella se non esiste
    if not os.path.exists(app_data):
        os.makedirs(app_data)
    
    return app_data

def verify_key(key):
    """Verifica la validità della chiave di accesso"""
    try:
        # Hash della chiave per confronto sicuro
        valid_keys = {
            # Chiavi valide con scadenza estesa
            hashlib.sha256("NBA-MARIO-2024-PRO".encode()).hexdigest(): "2032-12-31",
            hashlib.sha256("NBA-GEATA-2024-PRO".encode()).hexdigest(): "2032-12-31",
            hashlib.sha256("NBA-VINCY-2024-PRO".encode()).hexdigest(): "2032-12-31",
            hashlib.sha256("NBA-NELLO-2024-PRO".encode()).hexdigest(): "2032-12-31",
            hashlib.sha256("NBA-GIAMM-2024-PRO".encode()).hexdigest(): "2032-12-31",
            hashlib.sha256("NBA-EUGEO-2024-PRO".encode()).hexdigest(): "2032-12-31",
            hashlib.sha256("NBA-MATTO-2024-PRO".encode()).hexdigest(): "2032-12-31",
            hashlib.sha256("NBA-STATS-2024-TRIAL".encode()).hexdigest(): "2024-04-31"
        }
        
        # Calcola l'hash della chiave inserita
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # Verifica se la chiave esiste e non è scaduta
        if key_hash in valid_keys:
            expiry_date = datetime.strptime(valid_keys[key_hash], "%Y-%m-%d")
            if expiry_date > datetime.now():
                # Salva la chiave se la verifica ha successo
                save_key(key)
                return True, ""
            else:
                return False, "La chiave è scaduta"
        return False, "Chiave non valida"
    except Exception as e:
        return False, f"Errore durante la verifica: {str(e)}"

def save_key_to_config(key):
    """Salva la chiave nel file di configurazione"""
    config = {
        'key': key,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'machine_id': get_machine_id(),
        'last_verified': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    config_path = os.path.join(get_app_data_path(), 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f)

def load_saved_key():
    """Carica la chiave salvata dal file di configurazione"""
    try:
        config_path = os.path.join(os.path.expanduser('~'), '.nba_stats_config')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return f.read().strip()
    except Exception:
        return None
    return None

def save_key(key):
    """Salva la chiave nel file di configurazione"""
    try:
        config_path = os.path.join(os.path.expanduser('~'), '.nba_stats_config')
        with open(config_path, 'w') as f:
            f.write(key)
        return True
    except Exception:
        return False

def extend_key_validity(key):
    """Estende la validità di una chiave esistente"""
    try:
        config_path = os.path.join(get_app_data_path(), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Aggiorna il timestamp
            config['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            config['last_verified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(config_path, 'w') as f:
                json.dump(config, f)
            return True
    except Exception:
        pass
    return False

def show_login_window():
    """Mostra la finestra di login"""
    login_window = tk.Toplevel()
    login_window.title("✨ NBA Stats Pro - Login ✨")
    login_window.geometry("400x300")
    
    # Centra la finestra
    window_width = 400
    window_height = 300
    screen_width = login_window.winfo_screenwidth()
    screen_height = login_window.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    login_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Configura lo stile
    login_window.configure(bg=MAGIC_COLORS['background'])
    
    # Frame principale
    main_frame = tk.Frame(login_window, bg=MAGIC_COLORS['background'])
    main_frame.pack(expand=True, fill='both', padx=20, pady=20)
    
    # Titolo
    title_label = tk.Label(
        main_frame,
        text="✨ NBA Stats Pro ✨",
        font=('Papyrus', 20, 'bold'),
        bg=MAGIC_COLORS['background'],
        fg=MAGIC_COLORS['text']
    )
    title_label.pack(pady=(0, 20))
    
    # Frame per l'input
    input_frame = tk.Frame(main_frame, bg=MAGIC_COLORS['background'])
    input_frame.pack(fill='x', padx=20)
    
    # Label per la chiave
    key_label = tk.Label(
        input_frame,
        text="Inserisci la tua chiave magica:",
        font=('Papyrus', 12),
        bg=MAGIC_COLORS['background'],
        fg=MAGIC_COLORS['text']
    )
    key_label.pack(pady=(0, 5))
    
    # Entry per la chiave
    key_entry = tk.Entry(
        input_frame,
        font=('Papyrus', 12),
        bg=MAGIC_COLORS['card_bg'],
        fg=MAGIC_COLORS['text'],
        insertbackground=MAGIC_COLORS['text']
    )
    key_entry.pack(fill='x', pady=(0, 20))
    
    # Label per gli errori
    error_label = tk.Label(
        main_frame,
        text="",
        font=('Papyrus', 10),
        bg=MAGIC_COLORS['background'],
        fg=MAGIC_COLORS['error']
    )
    error_label.pack(pady=10)
    
    login_success = [False]
    
    def try_login():
        key = key_entry.get().strip()
        if not key:
            error_label.config(text="Inserisci una chiave valida")
            return
        
        success, message = verify_key(key)
        if success:
            login_success[0] = True
            login_window.destroy()
        else:
            error_label.config(text=message)
    
    # Bottone di login
    login_button = tk.Button(
        main_frame,
        text="✨ Accedi ✨",
        font=('Papyrus', 12),
        bg=MAGIC_COLORS['button'],
        fg=MAGIC_COLORS['text'],
        activebackground=MAGIC_COLORS['button_hover'],
        activeforeground=MAGIC_COLORS['text'],
        command=try_login
    )
    login_button.pack(pady=10)
    
    # Binding del tasto Enter
    key_entry.bind('<Return>', lambda e: try_login())
    
    # Focus sulla finestra e sul campo di input
    login_window.focus_force()
    key_entry.focus()
    
    # Rendi la finestra modale
    login_window.grab_set()
    
    # Aspetta che la finestra venga chiusa
    login_window.wait_window()
    
    return login_success[0]

if __name__ == "__main__":
    # Inizializza la finestra di login
    login_window = tk.Tk()
    login_window.withdraw()
    
    # Forza la visualizzazione del login
    if show_login_window():
        # Se il login ha successo, avvia l'applicazione principale
        app_window = main()
        app_window.mainloop()
    else:
        # Se il login fallisce, chiudi tutto
        login_window.destroy()
        sys.exit()