from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_cors import CORS
from flask_dance.contrib.google import make_google_blueprint, google
import mysql.connector
import hashlib
import os
import requests
import time
from datetime import datetime, timedelta
import random
from flask_dance.contrib.github import make_github_blueprint, github
from dotenv import load_dotenv
import os

load_dotenv()  # Charge les variables du fichier .env


# Désactiver la vérification HTTPS pour le développement local
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


# CONFIGURATION DE L'APPLICATION

app = Flask(__name__)
app.secret_key = "secret_key"

# Configuration des cookies de session
app.config.update(
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False  # À activer en production avec HTTPS
)

# Configuration CORS pour permettre les requêtes depuis Angular
CORS(app,
     supports_credentials=True,
     origins=["http://127.0.0.1:4200"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# CONFIGURATION BASE DE DONNÉES

DB_CONFIG = {
    'host': 'localhost',
    'database': 'flask_app',
    'user': 'root',
    'password': ''
}

def get_db():
    """Établit et retourne une connexion à la base de données"""
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    """Initialise la base de données avec les tables nécessaires"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Création de la table des utilisateurs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        email VARCHAR(100) PRIMARY KEY,
        password VARCHAR(100) NOT NULL
    )
    """)
    
    # Création de la table des favoris avec contrainte d'unicité
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_email VARCHAR(100) NOT NULL,
        title VARCHAR(100) NOT NULL,
        url VARCHAR(100) NOT NULL,
        category VARCHAR(100),
        source VARCHAR(100),
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_email) REFERENCES users(email) ON DELETE CASCADE,
        UNIQUE KEY unique_favorite (user_email(50), url(100))
    )
    """)
    
    # Création de la table de l'historique de navigation
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_email VARCHAR(100) NOT NULL,
        title VARCHAR(100) NOT NULL,
        url VARCHAR(100) NOT NULL,
        category VARCHAR(40),
        source VARCHAR(40),
        visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_email) REFERENCES users(email) ON DELETE CASCADE,
        INDEX idx_user_visited (user_email(50), visited_at)
    )
    """)
    
    # Insertion des utilisateurs de démonstration
    admin_pass = hashlib.sha256("1234".encode()).hexdigest()
    user_pass = hashlib.sha256("password".encode()).hexdigest()
    
    cursor.execute("INSERT IGNORE INTO users VALUES (%s, %s)", ("admin@example.com", admin_pass))
    cursor.execute("INSERT IGNORE INTO users VALUES (%s, %s)", ("user@gmail.com", user_pass))
    
    conn.commit()
    conn.close()

def verify_user(email, password):
    """Vérifie les identifiants d'un utilisateur"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE email = %s", (email,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0] == hashlib.sha256(password.encode()).hexdigest():
        return True
    return False

def create_user(email, password):
    """Crée un nouvel utilisateur dans la base de données"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Vérification de l'existence de l'utilisateur
    cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        conn.close()
        return False
    
    # Insertion du nouvel utilisateur avec mot de passe hashé
    hashed = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("INSERT INTO users VALUES (%s, %s)", (email, hashed))
    conn.commit()
    conn.close()
    return True


# CONFIGURATION GOOGLE OAUTH
app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
google_bp = make_google_blueprint(
    client_id=app.config["GOOGLE_OAUTH_CLIENT_ID"],
    client_secret=app.config["GOOGLE_OAUTH_CLIENT_SECRET"],
    redirect_to="google_callback",
    scope=["https://www.googleapis.com/auth/userinfo.email",
           "https://www.googleapis.com/auth/userinfo.profile",
           "openid"]
)
app.register_blueprint(google_bp, url_prefix="/google_login")


# CONFIGURATION GITHUB OAUTH

app.config["GITHUB_OAUTH_CLIENT_ID"] = "Ov23li1oaxN196z8bXsS"
app.config["GITHUB_OAUTH_CLIENT_SECRET"] = "2d33f312ea818d9339ff390aa1d5cee5e0bd3a24"

github_bp = make_github_blueprint(
    client_id=app.config["GITHUB_OAUTH_CLIENT_ID"],
    client_secret=app.config["GITHUB_OAUTH_CLIENT_SECRET"],
    redirect_to="github_callback",
    scope="user:email"
)
app.register_blueprint(github_bp, url_prefix="/github_login")

# CLASSE DE SCRAPING DES TENDANCES

class TrendScraper:
    def __init__(self):
        """Initialise le scraper avec les headers nécessaires pour les requêtes HTTP"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_reddit_trends(self):
        """Récupère les posts tendances de Reddit"""
        trends = []
        try:
            url = "https://www.reddit.com/r/all/hot.json?limit=15"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                posts = data['data']['children']
                
                for post in posts[:10]:
                    post_data = post['data']
                    trend = {
                        "author": post_data.get('author', ''),
                        "title": post_data.get('title', ''),
                        "url": f"https://reddit.com{post_data.get('permalink', '')}"
                    }
                    trends.append(trend)
        except Exception as e:
            print(f"Erreur Reddit: {e}")
        
        return trends

    def get_github_trends(self):
        """Récupère les dépôts GitHub tendances"""
        trends = []
        try:
            url = "https://api.github.com/search/repositories"
            params = {
                'q': 'created:>2025-09-01',
                'sort': 'stars',
                'order': 'desc',
                'per_page': 10
            }
            
            response = requests.get(url, params=params, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                repos = data.get('items', [])
                
                for repo in repos:
                    trend = {
                        "category": "trending_python",
                        "created_at": repo.get('created_at', ''),
                        "description": repo.get('description', ''),
                        "full_name": repo.get('full_name', ''),
                        "url": repo.get('html_url', ''),
                        "owner": repo.get('owner', {}).get('login', ''),
                        "stars": repo.get('stargazers_count', 0),
                        "watchers": repo.get('watchers_count', 0)
                    }
                    trends.append(trend)
        except Exception as e:
            print(f"Erreur GitHub: {e}")
        
        return trends

    def get_news_trends(self):
        """Agrège les actualités depuis plusieurs sources (Reddit, Hacker News, NewsAPI)"""
        trends = []
        
        try:
            # Récupération des actualités mondiales depuis Reddit
            try:
                url = "https://www.reddit.com/r/worldnews/hot.json?limit=20"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data['data']['children']
                    
                    for post in posts:
                        post_data = post['data']
                        trend = {
                            "author": post_data.get('author', ''),
                            "category": "world_news",
                            "source": "Reddit WorldNews",
                            "title": post_data.get('title', ''),
                            "url": f"https://reddit.com{post_data.get('permalink', '')}"
                        }
                        trends.append(trend)
                        
            except Exception as e:
                print(f"Erreur Reddit WorldNews: {e}")
            
            # Récupération des actualités tech depuis Hacker News
            try:
                hn_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
                response = requests.get(hn_url, headers=self.headers)
                
                if response.status_code == 200:
                    story_ids = response.json()[:25]
                    
                    for story_id in story_ids:
                        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                        story_response = requests.get(story_url, headers=self.headers)
                        
                        if story_response.status_code == 200:
                            story_data = story_response.json()
                            
                            trend = {
                                "author": story_data.get('by', ''),
                                "category": "tech_news",
                                "source": "Hacker News",
                                "title": story_data.get('title', ''),
                                "url": story_data.get('url', f"https://news.ycombinator.com/item?id={story_id}")
                            }
                            trends.append(trend)
                        
                        time.sleep(0.1)
            except Exception as e:
                print(f"Erreur Hacker News: {e}")
                
            # Récupération des actualités tech depuis Reddit Technology
            try:
                url = "https://www.reddit.com/r/technology/hot.json?limit=20"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data['data']['children']
                    
                    for post in posts:
                        post_data = post['data']
                        trend = {
                            "author": post_data.get('author', ''),
                            "category": "tech_news", 
                            "source": "Reddit Technology",
                            "title": post_data.get('title', ''),
                            "url": f"https://reddit.com{post_data.get('permalink', '')}"
                        }
                        trends.append(trend)
                        
            except Exception as e:
                print(f"Erreur Reddit Technology: {e}")
                
            # Récupération des actualités de programmation
            try:
                url = "https://www.reddit.com/r/programming/hot.json?limit=15"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data['data']['children']
                    
                    for post in posts:
                        post_data = post['data']
                        trend = {
                            "author": post_data.get('author', ''),
                            "category": "programming_news", 
                            "source": "Reddit Programming",
                            "title": post_data.get('title', ''),
                            "url": f"https://reddit.com{post_data.get('permalink', '')}"
                        }
                        trends.append(trend)
                        
            except Exception as e:
                print(f"Erreur Reddit Programming: {e}")
                
            # Récupération des actualités scientifiques
            try:
                url = "https://www.reddit.com/r/science/hot.json?limit=15"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data['data']['children']
                    
                    for post in posts:
                        post_data = post['data']
                        trend = {
                            "author": post_data.get('author', ''),
                            "category": "science_news", 
                            "source": "Reddit Science",
                            "title": post_data.get('title', ''),
                            "url": f"https://reddit.com{post_data.get('permalink', '')}"
                        }
                        trends.append(trend)
                        
            except Exception as e:
                print(f"Erreur Reddit Science: {e}")
                
            # Récupération des actualités business
            try:
                url = "https://www.reddit.com/r/business/hot.json?limit=10"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data['data']['children']
                    
                    for post in posts:
                        post_data = post['data']
                        trend = {
                            "author": post_data.get('author', ''),
                            "category": "business_news", 
                            "source": "Reddit Business",
                            "title": post_data.get('title', ''),
                            "url": f"https://reddit.com{post_data.get('permalink', '')}"
                        }
                        trends.append(trend)
                        
            except Exception as e:
                print(f"Erreur Reddit Business: {e}")
                
            # Récupération des actualités gaming
            try:
                url = "https://www.reddit.com/r/gaming/hot.json?limit=10"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data['data']['children']
                    
                    for post in posts:
                        post_data = post['data']
                        trend = {
                            "author": post_data.get('author', ''),
                            "category": "gaming_news", 
                            "source": "Reddit Gaming",
                            "title": post_data.get('title', ''),
                            "url": f"https://reddit.com{post_data.get('permalink', '')}"
                        }
                        trends.append(trend)
                        
            except Exception as e:
                print(f"Erreur Reddit Gaming: {e}")
                
            # Récupération des gros titres via NewsAPI
            try:
                api_key = "pub_1d67b28b400148238f8c5ab0b1f28d6c"
                url = "https://newsapi.org/v2/top-headlines"
                params = {
                    'country': 'us',
                    'pageSize': 20,
                    'apiKey': api_key
                }
                
                response = requests.get(url, params=params, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    
                    for article in articles:
                        trend = {
                            "author": article.get('author', ''),
                            "category": "breaking_news", 
                            "source": "NewsAPI",
                            "title": article.get('title', ''),
                            "url": article.get('url', '')
                        }
                        trends.append(trend)
                        
            except Exception as e:
                print(f"Erreur NewsAPI: {e}")
                
            # Récupération des actualités business via NewsAPI
            try:
                api_key = "pub_1d67b28b400148238f8c5ab0b1f28d6c"
                url = "https://newsapi.org/v2/top-headlines"
                params = {
                    'country': 'us',
                    'category': 'business',
                    'pageSize': 15,
                    'apiKey': api_key
                }
                
                response = requests.get(url, params=params, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    
                    for article in articles:
                        trend = {
                            "author": article.get('author', ''),
                            "category": "business_news", 
                            "source": "NewsAPI Business",
                            "title": article.get('title', ''),
                            "url": article.get('url', '')
                        }
                        trends.append(trend)
                        
            except Exception as e:
                print(f"Erreur NewsAPI Business: {e}")
                
            # Récupération des actualités tech via NewsAPI
            try:
                api_key = "pub_1d67b28b400148238f8c5ab0b1f28d6c"
                url = "https://newsapi.org/v2/top-headlines"
                params = {
                    'country': 'us',
                    'category': 'technology',
                    'pageSize': 15,
                    'apiKey': api_key
                }
                
                response = requests.get(url, params=params, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    
                    for article in articles:
                        trend = {
                            "author": article.get('author', ''),
                            "category": "tech_news", 
                            "source": "NewsAPI Tech",
                            "title": article.get('title', ''),
                            "url": article.get('url', '')
                        }
                        trends.append(trend)
                        
            except Exception as e:
                print(f"Erreur NewsAPI Tech: {e}")
                
        except Exception as e:
            print(f"Erreur lors de la récupération des news trends: {e}")
        
        # Mélange aléatoire des résultats pour varier l'affichage
        random.shuffle(trends)
        return trends  

    def search_by_keyword(self, keyword):
        """Recherche des contenus par mot-clé sur plusieurs plateformes"""
        results = []
        
        try:
            # Recherche sur Reddit
            try:
                reddit_url = f"https://www.reddit.com/search.json?q={keyword}&sort=hot&limit=20"
                response = requests.get(reddit_url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    for post in posts:
                        post_data = post['data']
                        result = {
                            "author": post_data.get('author', ''),
                            "category": "reddit_search",
                            "keyword": keyword,
                            "subreddit": post_data.get('subreddit', ''),
                            "title": post_data.get('title', ''),
                            "url": f"https://reddit.com{post_data.get('permalink', '')}"
                        }
                        results.append(result)
            except Exception as e:
                print(f"Erreur recherche Reddit: {e}")
            
            # Recherche sur Hacker News
            try:
                hn_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
                response = requests.get(hn_url, headers=self.headers)
                
                if response.status_code == 200:
                    story_ids = response.json()[:50]
                    
                    for story_id in story_ids:
                        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                        story_response = requests.get(story_url, headers=self.headers)
                        
                        if story_response.status_code == 200:
                            story_data = story_response.json()
                            story_title = story_data.get('title', '').lower()
                            
                            # Vérification de la présence du mot-clé dans le titre
                            if keyword.lower() in story_title:
                                result = {
                                    "author": story_data.get('by', ''),
                                    "category": "hackernews_search",
                                    "keyword": keyword,
                                    "subreddit": "hackernews",
                                    "title": story_data.get('title', ''),
                                    "url": story_data.get('url', f"https://news.ycombinator.com/item?id={story_id}")
                                }
                                results.append(result)
                        
                        time.sleep(0.1)
            except Exception as e:
                print(f"Erreur recherche Hacker News: {e}")
            
            # Recherche via NewsAPI
            try:
                api_key = "pub_1d67b28b400148238f8c5ab0b1f28d6c"
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': keyword,
                    'sortBy': 'publishedAt',
                    'language': 'en',
                    'pageSize': 20,
                    'apiKey': api_key
                }
                
                response = requests.get(url, params=params, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    
                    for article in articles:
                        result = {
                            "author": article.get('author', ''),
                            "category": "news_search",
                            "keyword": keyword,
                            "subreddit": article.get('source', {}).get('name', 'newsapi'),
                            "title": article.get('title', ''),
                            "url": article.get('url', '')
                        }
                        results.append(result)
            except Exception as e:
                print(f"Erreur recherche NewsAPI: {e}")
                
        except Exception as e:
            print(f"Erreur recherche globale: {e}")
        
        # Mélange aléatoire des résultats de recherche
        random.shuffle(results)
        return results

    def get_sports_results(self):
        """Récupère les résultats sportifs actuels ou récents"""
        sports_data = []
        try:
            # Tentative de récupération des matchs du jour
            today = datetime.now().strftime('%Y-%m-%d')
            
            url = f"https://api.football-data.org/v2/matches?dateFrom={today}&dateTo={today}"
            headers = {
                'X-Auth-Token': '7062ca4d0e8547dca47cfd24d06e3a831',
                **self.headers
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                
                # Si aucun match aujourd'hui, recherche sur les 7 derniers jours
                if len(matches) == 0:
                    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                    url = f"https://api.football-data.org/v2/matches?dateFrom={week_ago}&dateTo={today}&status=FINISHED"
                    response = requests.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        matches = data.get('matches', [])
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                
                for match in matches[:10]:
                    competition = match.get('competition', {})
                    home_team = match.get('homeTeam', {})
                    away_team = match.get('awayTeam', {})
                    score = match.get('score', {}).get('fullTime', {})
                    
                    result = {
                        "away_team": away_team.get('name', ''),
                        "category": "sports",
                        "competition": competition.get('name', ''),
                        "date": match.get('utcDate', ''),
                        "home_team": home_team.get('name', ''),
                        "score": f"{score.get('homeTeam', 0)}-{score.get('awayTeam', 0)}",
                        "status": match.get('status', 'SCHEDULED')
                    }
                    sports_data.append(result)
           
        except Exception as e:
            print(f"Erreur sports API: {e}")
            
        return sports_data

    def get_youtube_trends(self, country="United States"):
        """Récupère les vidéos tendances sur YouTube par pays"""
        
        # Mapping des noms de pays vers leurs codes ISO
        country_codes = {
            "United States": "US",
            "France": "FR", 
            "United Kingdom": "GB",
            "Germany": "DE",
            "Japan": "JP",
            "South Korea": "KR",
            "Canada": "CA",
            "Australia": "AU",
            "Brazil": "BR",
            "Mexico": "MX",
            "India": "IN",
            "Italy": "IT",
            "Spain": "ES",
            "Russia": "RU",
            "China": "CN"
        }
        
        # Conversion du nom de pays en code région
        region_code = country_codes.get(country, "US")
        
        try:
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "regionCode": region_code,
                "maxResults": 10,
                "key": "AIzaSyA2tus_vy-7RPBGYhFfMBVYDI0PT7ew2e0"
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json().get("items", [])
                return [
                    {
                        "title": v["snippet"]["title"],
                        "url": f"https://youtube.com/watch?v={v['id']}",
                        "channel": v["snippet"]["channelTitle"],
                        "views": v["statistics"].get("viewCount", 0),
                        "category": "youtube_trends"
                    }
                    for v in data
                ]
        except Exception as e:
            print("Erreur YouTube:", e)
        return []

# Instanciation du scraper
scraper = TrendScraper()

# ROUTES POUR LES PAGES HTML

@app.route("/")
def index():
    """Redirige vers la page de connexion"""
    return redirect("/login")

@app.route("/login")
def login_page():
    """Affiche la page de connexion"""
    return render_template("login.html")

@app.route("/register")
def register_page():
    """Affiche la page d'inscription"""
    return render_template("register.html")

@app.route("/home")
def home_page():
    """Affiche la page d'accueil pour les utilisateurs connectés"""
    if "username" not in session:
        return redirect("/login")
    return render_template("home.html", username=session["username"])


# ROUTES API AUTHENTIFICATION

@app.route("/api/login", methods=["POST"])
def api_login():
    """Gère la connexion des utilisateurs"""
    data = request.get_json()
    email = data.get("username")
    password = data.get("password")
    
    if verify_user(email, password):
        session["username"] = email
        print("=" * 50)
        print(f"Connexion reussie pour: {email}")
        print(f"Session creee: {dict(session)}")
        print(f"Session ID: {session.sid if hasattr(session, 'sid') else 'N/A'}")
        print("=" * 50)
        return jsonify({"success": True, "message": "Connexion réussie"})
    else:
        print(f"Connexion echouee pour: {email}")
        return jsonify({"success": False, "message": "Identifiants incorrects"}), 401

@app.route("/api/register", methods=["POST"])
def api_register():
    """Gère l'inscription de nouveaux utilisateurs"""
    data = request.get_json()
    email = data.get("username")
    password = data.get("password")
    
    if create_user(email, password):
        return jsonify({"success": True, "message": "Inscription réussie"})
    else:
        return jsonify({"success": False, "message": "Utilisateur déjà existant"}), 400

@app.route("/api/logout", methods=["POST"])
def api_logout():
    """Déconnecte l'utilisateur en supprimant sa session"""
    session.pop("username", None)
    return jsonify({"success": True, "message": "Déconnexion réussie"})


# ROUTES GESTION DES FAVORIS

@app.route("/api/favorites", methods=["GET"])
def get_favorites():
    """Récupère la liste des favoris de l'utilisateur connecté"""
    print("=" * 50)
    print("Requete /api/favorites")
    print(f"Cookies recus: {request.cookies}")
    print(f"Session actuelle: {dict(session)}")
    print(f"'username' dans session? {'username' in session}")
    print(f"Headers: {dict(request.headers)}")
    print("=" * 50)
    
    if "username" not in session:
        print("Pas de username dans session - Rejet 401")
        return jsonify({"success": False, "message": "Non authentifié"}), 401
    
    print(f"Utilisateur authentifie: {session['username']}")
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, title, url, category, source, added_at 
        FROM favorites 
        WHERE user_email = %s 
        ORDER BY added_at DESC
    """, (session["username"],))
    favorites = cursor.fetchall()
    conn.close()
    
    return jsonify({"success": True, "data": favorites})


@app.route("/api/favorites", methods=["POST"])
def add_favorite():
    """Ajoute un nouvel élément aux favoris de l'utilisateur"""
    if "username" not in session:
        return jsonify({"success": False, "message": "Non authentifié"}), 401
    
    data = request.get_json()
    title = data.get("title")
    url = data.get("url")
    category = data.get("category", "")
    source = data.get("source", "")
    
    if not title or not url:
        return jsonify({"success": False, "message": "Titre et URL requis"}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO favorites (user_email, title, url, category, source) 
            VALUES (%s, %s, %s, %s, %s)
        """, (session["username"], title, url, category, source))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Ajouté aux favoris"})
    except mysql.connector.IntegrityError:
        conn.close()
        return jsonify({"success": False, "message": "Déjà dans les favoris"}), 400

@app.route("/api/favorites/<int:favorite_id>", methods=["DELETE"])
def delete_favorite(favorite_id):
    """Supprime un favori spécifique de l'utilisateur"""
    if "username" not in session:
        return jsonify({"success": False, "message": "Non authentifié"}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM favorites 
        WHERE id = %s AND user_email = %s
    """, (favorite_id, session["username"]))
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"success": False, "message": "Favori non trouvé"}), 404
    
    conn.close()
    return jsonify({"success": True, "message": "Favori supprimé"})


# ROUTES GESTION DE L'HISTORIQUE

@app.route("/api/history", methods=["GET"])
def get_history():
    """Récupère l'historique de navigation de l'utilisateur"""
    print("=" * 50)
    print("Requete /api/history")
    print(f"Cookies recus: {request.cookies}")
    print(f"Session actuelle: {dict(session)}")
    print(f"'username' dans session? {'username' in session}")
    print("=" * 50)

    if "username" not in session:
        print("Pas de username dans session - Rejet 401")
        return jsonify({"success": False, "message": "Non authentifié"}), 401

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, title, url, category, source, visited_at 
        FROM history 
        WHERE user_email = %s 
        ORDER BY visited_at DESC 
        LIMIT 100
    """, (session["username"],))
    history = cursor.fetchall()
    conn.close()
    print("Historique retourne:", history)
    
    return jsonify({"success": True, "data": history})

@app.route("/api/history", methods=["POST"])
def add_history():
    """Ajoute un nouvel élément à l'historique de navigation"""
    if "username" not in session:
        return jsonify({"success": False, "message": "Non authentifié"}), 401
    
    data = request.get_json()
    print("Donnees recues pour historique:", data)

    title = data.get("title")
    url = data.get("url")
    category = data.get("category", "")
    source = data.get("source", "")
    
    if not title or not url:
        return jsonify({"success": False, "message": "Titre et URL requis"}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO history (user_email, title, url, category, source) 
        VALUES (%s, %s, %s, %s, %s)
    """, (session["username"], title, url, category, source))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Ajouté à l'historique"})

@app.route("/api/history", methods=["DELETE"])
def clear_history():
    """Efface tout l'historique de navigation de l'utilisateur"""
    if "username" not in session:
        return jsonify({"success": False, "message": "Non authentifié"}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history WHERE user_email = %s", (session["username"],))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Historique effacé"})

@app.route("/api/history/<int:history_id>", methods=["DELETE"])
def delete_history_item(history_id):
    """Supprime un élément spécifique de l'historique"""
    if "username" not in session:
        return jsonify({"success": False, "message": "Non authentifié"}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM history 
        WHERE id = %s AND user_email = %s
    """, (history_id, session["username"]))
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"success": False, "message": "Élément non trouvé"}), 404
    
    conn.close()
    return jsonify({"success": True, "message": "Élément supprimé"})


# ROUTES API POUR LES TENDANCES

@app.route('/api/reddit')
def reddit_trends():
    """Retourne les tendances Reddit"""
    data = scraper.get_reddit_trends()
    return jsonify(data)

@app.route('/api/github')
def github_trends():
    """Retourne les dépôts GitHub tendances"""
    data = scraper.get_github_trends()
    return jsonify(data)

@app.route('/api/news')
def news_trends():
    """Retourne les actualités agrégées de plusieurs sources"""
    data = scraper.get_news_trends()
    return jsonify(data)

@app.route('/api/search/<keyword>')
def search_keyword(keyword):
    """Effectue une recherche par mot-clé sur plusieurs plateformes"""
    data = scraper.search_by_keyword(keyword)
    return jsonify(data)

@app.route('/api/sports')
def sports_results():
    """Retourne les résultats sportifs récents"""
    data = scraper.get_sports_results()
    return jsonify(data)

@app.route('/api/youtube')
@app.route('/api/youtube/<country>')
def youtube_trends(country="United States"):
    """Retourne les vidéos YouTube tendances par pays"""
    data = scraper.get_youtube_trends(country)
    return jsonify(data)

@app.route("/api/session_test")
def session_test():
    """Endpoint de test pour vérifier l'état de la session"""
    return jsonify({
        "username": session.get("username"),
        "session": dict(session),
        "cookies": request.cookies
    })

@app.route('/api/trends/global')
def trends_global():
    """Récupère les statistiques globales des tendances consultées par tous les utilisateurs"""
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Agrégation des données d'historique des 7 derniers jours pour tous les utilisateurs
    cursor.execute("""
        SELECT 
            DATE(visited_at) as date,
            category,
            COUNT(*) as count
        FROM history
        WHERE visited_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY DATE(visited_at), category
        ORDER BY date ASC
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    return jsonify({"success": True, "data": results})


# AUTHENTIFICATION GOOGLE

@app.route("/google_login/login")
def google_login_redirect():
    """Redirige vers le processus d'authentification Google"""
    return redirect(url_for("google.login"))

@app.route("/google_callback")
def google_callback():
    """Gère le retour de l'authentification Google"""
    if not google.authorized:
        return redirect(url_for("google.login"))

    # Récupération des informations utilisateur depuis l'API Google
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return redirect("/login")

    user_info = resp.json()
    email = user_info.get("email")
    name = user_info.get("name")

    # Création ou mise à jour de l'utilisateur dans la base
    create_user(email, "google_user")

    session["username"] = email
    session["name"] = name

    # Redirection vers l'interface Angular
    return redirect("http://127.0.0.1:4200/dashboard")


# AUTHENTIFICATION GITHUB

@app.route("/github_login/login")
def github_login_redirect():
    """Redirige vers le processus d'authentification GitHub"""
    return redirect(url_for("github.login"))

@app.route("/github_callback")
def github_callback():
    """Gère le retour de l'authentification GitHub"""
    
    if not github.authorized:
        print("GitHub: Utilisateur non autorise")
        return redirect(url_for("github.login"))
    
    try:
        # Récupération du profil utilisateur GitHub
        resp = github.get("/user")
        
        if not resp.ok:
            print(f"GitHub: Erreur profil - Status {resp.status_code}")
            return redirect("/login")
        
        user_info = resp.json()
        
        email = user_info.get("email")
        name = user_info.get("name") or user_info.get("login")
        
        # Gestion des emails privés sur GitHub
        if not email:
            print("GitHub: Email prive, recuperation via API /user/emails")
            email_resp = github.get("/user/emails")
            
            if email_resp.ok:
                emails = email_resp.json()
                # Recherche de l'email principal vérifié
                primary_email = next(
                    (e for e in emails if e.get("primary") and e.get("verified")), 
                    None
                )
                
                if primary_email:
                    email = primary_email.get("email")
                else:
                    # Fallback sur le premier email vérifié disponible
                    verified_email = next(
                        (e for e in emails if e.get("verified")), 
                        None
                    )
                    if verified_email:
                        email = verified_email.get("email")
        
        if not email:
            print("GitHub: Aucun email trouve")
            return redirect("/login")
        
        # Création ou mise à jour de l'utilisateur
        create_user(email, "github_user")
        
        session["username"] = email
        session["name"] = name
        
        print("=" * 50)
        print(f"Connexion GitHub reussie")
        print(f"Email: {email}")
        print(f"Nom: {name}")
        print(f"GitHub Username: {user_info.get('login')}")
        print("=" * 50)
        
        # Redirection vers l'interface Angular
        return redirect("http://127.0.0.1:4200/dashboard")
        
    except Exception as e:
        print(f"Erreur GitHub callback: {e}")
        import traceback
        traceback.print_exc()
        return redirect("/login")



# ROUTES MODIFICATION DU MOT DE PASSE

@app.route("/api/change-password", methods=["POST"])
def change_password():
    """Permet à l'utilisateur de modifier son mot de passe"""
    
    if "username" not in session:
        return jsonify({"success": False, "message": "Non authentifié"}), 401
    
    data = request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")
    
    # Validation des champs requis
    if not current_password or not new_password or not confirm_password:
        return jsonify({"success": False, "message": "Tous les champs sont requis"}), 400
    
    # Vérification de la correspondance des nouveaux mots de passe
    if new_password != confirm_password:
        return jsonify({"success": False, "message": "Les nouveaux mots de passe ne correspondent pas"}), 400
    
    # Validation de la longueur minimale
    if len(new_password) < 6:
        return jsonify({"success": False, "message": "Le mot de passe doit contenir au moins 6 caractères"}), 400
    
    # Vérification de l'ancien mot de passe
    if not verify_user(session["username"], current_password):
        return jsonify({"success": False, "message": "Mot de passe actuel incorrect"}), 401
    
    # Mise à jour du mot de passe dans la base
    conn = get_db()
    cursor = conn.cursor()
    
    new_hashed = hashlib.sha256(new_password.encode()).hexdigest()
    
    cursor.execute("""
        UPDATE users 
        SET password = %s 
        WHERE email = %s
    """, (new_hashed, session["username"]))
    
    conn.commit()
    conn.close()
    
    print(f"Mot de passe change pour: {session['username']}")
    
    return jsonify({"success": True, "message": "Mot de passe modifié avec succès"})


@app.route("/api/reset-password", methods=["POST"])
def reset_password():
    """Réinitialise le mot de passe sans vérification de l'ancien"""
    
    data = request.get_json()
    email = data.get("email")
    new_password = data.get("new_password")
    
    # Note: En production, il faudrait implémenter un système de token par email
    # pour sécuriser la réinitialisation du mot de passe
    
    if not email or not new_password:
        return jsonify({"success": False, "message": "Email et mot de passe requis"}), 400
    
    if len(new_password) < 6:
        return jsonify({"success": False, "message": "Le mot de passe doit contenir au moins 6 caractères"}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Vérification de l'existence de l'utilisateur
    cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
    
    # Mise à jour du mot de passe
    new_hashed = hashlib.sha256(new_password.encode()).hexdigest()
    
    cursor.execute("""
        UPDATE users 
        SET password = %s 
        WHERE email = %s
    """, (new_hashed, email))
    
    conn.commit()
    conn.close()
    
    print(f"Mot de passe reinitialise pour: {email}")
    
    return jsonify({"success": True, "message": "Mot de passe réinitialisé avec succès"})


@app.route("/api/check-oauth-user", methods=["GET"])
def check_oauth_user():
    """Vérifie si l'utilisateur s'est connecté via OAuth"""
    
    if "username" not in session:
        return jsonify({"success": False, "message": "Non authentifié"}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT password FROM users WHERE email = %s", (session["username"],))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
    
    # Vérification du type d'authentification
    stored_password = result[0]
    google_hash = hashlib.sha256("google_user".encode()).hexdigest()
    github_hash = hashlib.sha256("github_user".encode()).hexdigest()
    
    is_oauth = (stored_password == google_hash or stored_password == github_hash)
    
    return jsonify({
        "success": True,
        "is_oauth_user": is_oauth,
        "can_change_password": not is_oauth
    })
    

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)