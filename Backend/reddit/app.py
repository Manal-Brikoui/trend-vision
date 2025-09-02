from flask import Flask, jsonify, request
import praw
import datetime

app = Flask(__name__)

# -------------------------
# CONFIG REDDIT API
# -------------------------
reddit = praw.Reddit(
    client_id="1zbOVzH-mpZqZpHBdiIYDw",
    client_secret="NbPUOA8hjW0zj-EaJSrFmqWnKszg8w",
    user_agent="TrendsApp/0.1 by Diligent_Ad9933"
)

# -------------------------
# SUBREDDITS VALIDES PAR CATÉGORIE
# -------------------------
VALID_SUBREDDITS = {
    "Technologie": ["technology", "programming", "gadgets", "computers"],
    "Science": ["science", "space", "biology", "physics"],
    "Actualités": ["news", "worldnews", "politics", "UpliftingNews"],
    "Gaming": ["gaming", "pcgaming", "leagueoflegends", "FortniteBR"],
    "Sports": ["sports", "soccer", "nba", "tennis"],
    "Divertissement": ["movies", "funny", "memes", "television"],
    "Musique": ["music", "hiphopheads", "indieheads", "kpop"],
    "Lifestyle": ["fitness", "food", "travel", "relationships"],
    "Finance": ["stocks", "cryptocurrency", "investing", "personalfinance"]
}

# -------------------------
# FONCTIONS UTILITAIRES
# -------------------------
def is_valid_subreddit(subreddit_name):
    """Vérifie que le subreddit choisi est dans la liste validée"""
    for subs in VALID_SUBREDDITS.values():
        if subreddit_name.lower() in subs:
            return True
    return False

def get_reddit_posts(subreddit_name="technology", method="hot", limit=10):
    """
    Récupère les posts d'un subreddit donné selon le type de trend
    """
    subreddit = reddit.subreddit(subreddit_name)
    
    if method == "hot":
        posts = subreddit.hot(limit=limit)
    elif method == "new":
        posts = subreddit.new(limit=limit)
    elif method == "rising":
        posts = subreddit.rising(limit=limit)
    elif method == "top":
        posts = subreddit.top(limit=limit)
    else:
        return []

    trends = []
    for post in posts:
        trends.append({
            "id": post.id,
            "title": post.title,
            "author": str(post.author),
            "subreddit": post.subreddit.display_name,
            "upvotes": post.score,
            "comments_count": post.num_comments,
            "created_date": datetime.datetime.utcfromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
            "reddit_link": f"https://www.reddit.com{post.permalink}",
            "external_url": post.url,
            "is_nsfw": post.over_18,
            "text_content": post.selftext if post.selftext else None,
            "thumbnail": post.thumbnail if post.thumbnail and post.thumbnail != "self" else None,
            "awards": post.total_awards_received,
            "stickied": post.stickied
        })
    return trends

# -------------------------
# ROUTES REDDIT PAR TYPE
# -------------------------
@app.route("/api/reddit_hot/<subreddit_name>", methods=["GET"])
def reddit_hot(subreddit_name):
    if not is_valid_subreddit(subreddit_name):
        return jsonify({"error": "Subreddit invalide ou non autorisé"}), 400
    return jsonify(get_reddit_posts(subreddit_name=subreddit_name, method="hot"))

@app.route("/api/reddit_new/<subreddit_name>", methods=["GET"])
def reddit_new(subreddit_name):
    if not is_valid_subreddit(subreddit_name):
        return jsonify({"error": "Subreddit invalide ou non autorisé"}), 400
    return jsonify(get_reddit_posts(subreddit_name=subreddit_name, method="new"))

@app.route("/api/reddit_rising/<subreddit_name>", methods=["GET"])
def reddit_rising(subreddit_name):
    if not is_valid_subreddit(subreddit_name):
        return jsonify({"error": "Subreddit invalide ou non autorisé"}), 400
    return jsonify(get_reddit_posts(subreddit_name=subreddit_name, method="rising"))

@app.route("/api/reddit_top/<subreddit_name>", methods=["GET"])
def reddit_top(subreddit_name):
    if not is_valid_subreddit(subreddit_name):
        return jsonify({"error": "Subreddit invalide ou non autorisé"}), 400
    return jsonify(get_reddit_posts(subreddit_name=subreddit_name, method="top"))

# -------------------------
# ROUTE POUR LES CATEGORIES / SUBREDDITS VALIDES
# -------------------------
@app.route("/api/reddit_categories", methods=["GET"])
def reddit_categories():
    """Renvoie toutes les catégories et les subreddits valides pour le front-end"""
    return jsonify(VALID_SUBREDDITS)

# -------------------------
# ROUTE DE RECHERCHE PAR MOT-CLÉ
# -------------------------
@app.route("/api/reddit_search", methods=["GET"])
def reddit_search():
    keyword = request.args.get("keyword")
    if not keyword:
        return jsonify({"error": "Le mot-clé est requis"}), 400

    # Recherche dans tous les subreddits valides
    all_results = []
    for category, subreddits in VALID_SUBREDDITS.items():
        for subreddit_name in subreddits:
            posts = get_reddit_posts(subreddit_name=subreddit_name, method="hot", limit=10)
            # Filtrer les posts en fonction du mot-clé
            for post in posts:
                if keyword.lower() in post["title"].lower() or (post["text_content"] and keyword.lower() in post["text_content"].lower()):
                    all_results.append(post)

    return jsonify(all_results)

# -------------------------
# EXPLICATION POUR L'UTILISATEUR
# -------------------------
@app.route("/api/reddit_info", methods=["GET"])
def reddit_info():
    """
    Renvoie un paragraphe explicatif pour l'utilisateur
    """
    info = (
        "Bienvenue sur la section Reddit Trends ! Ici, vous pouvez explorer "
        "les posts les plus populaires de Reddit selon différents types de trends : "
        "Hot (populaire actuellement), New (nouveaux posts), Rising (posts qui montent rapidement), "
        "et Top (posts les mieux votés). Vous choisissez également la catégorie qui vous intéresse, "
        "comme Technologie, Science, Gaming, Actualités, etc. Seuls les subreddits validés et existants "
        "sont disponibles pour éviter les erreurs et garantir que vous obtenez toujours des données fiables."
    )
    return jsonify({"info": info})

# -------------------------
# LANCEMENT DE L'APPLICATION
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
