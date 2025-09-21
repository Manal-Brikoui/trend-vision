from flask import Flask, jsonify
from flask_cors import CORS
import requests
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Permettre les requêtes cross-origin

class TrendScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_reddit_trends(self):
        
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
        
        trends = []
        
        try:
            # 1. Récupérer Reddit WorldNews
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
            
            # 2. Récupérer Hacker News
            try:
                hn_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
                response = requests.get(hn_url, headers=self.headers)
                
                if response.status_code == 200:
                    story_ids = response.json()[:25]  # Plus de stories
                    
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
                        
                        time.sleep(0.1)  # Plus rapide
            except Exception as e:
                print(f"Erreur Hacker News: {e}")
                
            # 3. Reddit Technology
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
                
            # 4. Reddit Programming 
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
                
            # 5. Reddit Science
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
                
            # 6. Reddit Business
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
                
            # 7. Reddit Gaming
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
                
            # 8. NewsAPI - Top Headlines
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
                
            # 9. NewsAPI - Business Headlines
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
                
            # 10. NewsAPI - Technology Headlines
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
        
        # Mélanger
        import random
        random.shuffle(trends)
        return trends  

    def search_by_keyword(self, keyword):
        
        results = []
        
        try:
            # 1. Recherche Reddit
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
            
            # 2. Recherche Hacker News
            try:
                # Rechercher dans les stories récentes de HN
                hn_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
                response = requests.get(hn_url, headers=self.headers)
                
                if response.status_code == 200:
                    story_ids = response.json()[:50]  # Plus de stories pour la recherche
                    
                    for story_id in story_ids:
                        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                        story_response = requests.get(story_url, headers=self.headers)
                        
                        if story_response.status_code == 200:
                            story_data = story_response.json()
                            story_title = story_data.get('title', '').lower()
                            
                            # Vérifier si le keyword est dans le titre
                            if keyword.lower() in story_title:
                                result = {
                                    "author": story_data.get('by', ''),
                                    "category": "hackernews_search",
                                    "keyword": keyword,
                                    "subreddit": "hackernews",  # Pour garder la structure
                                    "title": story_data.get('title', ''),
                                    "url": story_data.get('url', f"https://news.ycombinator.com/item?id={story_id}")
                                }
                                results.append(result)
                        
                        time.sleep(0.1)
            except Exception as e:
                print(f"Erreur recherche Hacker News: {e}")
            
            # 3. Recherche NewsAPI
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
                            "subreddit": article.get('source', {}).get('name', 'newsapi'),  # Source comme subreddit
                            "title": article.get('title', ''),
                            "url": article.get('url', '')
                        }
                        results.append(result)
            except Exception as e:
                print(f"Erreur recherche NewsAPI: {e}")
                
        except Exception as e:
            print(f"Erreur recherche globale: {e}")
        
        # Mélanger les résultats de toutes les sources
        import random
        random.shuffle(results)
        return results

    def get_sports_results(self):
        """Récupère les vrais résultats sportifs actuels"""
        sports_data = []
        try:
            # API-Football pour les résultats en temps réel
            url = "https://api.football-data.org/v2/matches"
            headers = {
                'X-Auth-Token': '7062ca4d0e8547dca47cfd24d06e3831',  # Remplace par ta vraie clé
                **self.headers
            }
            
            response = requests.get(url, headers=headers)
            
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
        """Récupère les tendances YouTube par pays"""
        
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
        
        # Convertir le nom du pays en code
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

# Instance du scraper
scraper = TrendScraper()

# Routes API
@app.route('/')
def home():
    return {"message": "API Trends Backend actif"}

@app.route('/api/reddit')
def reddit_trends():
    data = scraper.get_reddit_trends()
    return jsonify(data)

@app.route('/api/github')
def github_trends():
    data = scraper.get_github_trends()
    return jsonify(data)

@app.route('/api/news')
def news_trends():
    data = scraper.get_news_trends()
    return jsonify(data)

@app.route('/api/search/<keyword>')
def search_keyword(keyword):
    data = scraper.search_by_keyword(keyword)
    return jsonify(data)

@app.route('/api/sports')
def sports_results():
    data = scraper.get_sports_results()
    return jsonify(data)

@app.route('/api/youtube')
@app.route('/api/youtube/<country>')
def youtube_trends(country="United States"):
    data = scraper.get_youtube_trends(country)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)