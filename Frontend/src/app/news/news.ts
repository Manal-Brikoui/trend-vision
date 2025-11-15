import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Sidebar } from '../sidebar/sidebar';
import { FavoriteService, FavoriteItem } from '../services/favorite.service';
import { HttpClientModule } from '@angular/common/http';

import HistoriqueService from '../services/historique.service';

import { AuthService } from '../services/auth.service';

interface NewsArticle {
  author: string;
  category: string;
  source: string;
  title: string;
  url: string;
  isFavorite: boolean;
  favoriteId: number | null;
}

@Component({
  selector: 'app-news',
  standalone: true,
  imports: [CommonModule, FormsModule, Sidebar, HttpClientModule],
  templateUrl: './news.html',
  styleUrls: ['./news.css']
})
export class News implements OnInit {
  allArticles: NewsArticle[] = [];
  filteredArticles: NewsArticle[] = [];
  searchTerm: string = '';
  showModal: boolean = false;
  selectedArticle: NewsArticle | null = null;
  private currentFavorites: FavoriteItem[] = [];

  isLoading: boolean = true;

  constructor(
    private favoriteService: FavoriteService,
    private historiqueService: HistoriqueService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadCurrentFavorites().then(() => {
      this.fetchArticles();
    });
  }

  //  Chargement asynchrone des favoris depuis le backend
  async loadCurrentFavorites(): Promise<void> {
    return new Promise((resolve) => {
      this.favoriteService.getFavorites().subscribe({
        next: (data) => {
          this.currentFavorites = data.filter(fav => fav.source === 'news'); // Filtrage spécifique
          resolve();
        },
        error: (err) => {
          console.error("Erreur de chargement des favoris:", err);
          resolve();
        }
      });
    });
  }

  //  Vérification de l'état "Favori" pour un article
  private checkIfFavorite(article: any): { isFavorite: boolean, favoriteId: number | null } {
    const favorite = this.currentFavorites.find(fav => fav.url === article.url);

    return {
      isFavorite: !!favorite,
      favoriteId: favorite ? favorite.id : null
    };
  }

  //  Récupération des articles et initialisation de l'état "Favori"
  fetchArticles(): void {
    this.isLoading = true; //  Début du chargement
    fetch('http://127.0.0.1:5000/api/news')
      .then(res => res.json())
      .then((data: any) => {
        console.log("Données reçues du backend (news):", data);

        const articles = Array.isArray(data) ? data : data.all_articles;

        this.allArticles = articles.map((article: any) => ({
          author: article.author || "Inconnu",
          category: article.category || "general_news",
          source: article.source || "Unknown",
          title: article.title,
          url: article.url,
          ...this.checkIfFavorite(article)
        }));

        this.filteredArticles = this.allArticles;
        this.isLoading = false; //  Fin du chargement
      })
      .catch(err => {
        console.error("Erreur lors du chargement des articles:", err);
        this.isLoading = false; //  Fin du chargement même en cas d'erreur
      });
  }

  filterArticles(): void {
    if (this.searchTerm.trim() === '') {
      this.filteredArticles = this.allArticles;
    } else {
      const searchTermLower = this.searchTerm.toLowerCase();
      this.filteredArticles = this.allArticles.filter(article =>
        article.title.toLowerCase().includes(searchTermLower) ||
        article.author.toLowerCase().includes(searchTermLower) ||
        article.source.toLowerCase().includes(searchTermLower)
      );
    }
  }

  openModal(article: NewsArticle): void {
    this.selectedArticle = article;
    this.showModal = true;

    if (this.authService.isLoggedIn()) {
      const source: any = 'news';
      this.historiqueService.trackVisit(
        article.title,
        article.url,
        source,
        article.category
      );
    }
  }

  closeModal(): void {
    this.showModal = false;
    this.selectedArticle = null;
  }

  //  Logique de favori mise à jour (asynchrone)
  toggleFavorite(article: NewsArticle): void {
    article.isFavorite = !article.isFavorite; // Mise à jour optimiste

    if (!article.isFavorite) {
      // Suppression du favori
      if (article.favoriteId !== null) {
        this.favoriteService.removeFavorite(article.favoriteId).subscribe({
          next: () => {
            article.favoriteId = null; // Supprime l'ID local
          },
          error: (err) => {
            console.error('Erreur de suppression:', err);
            article.isFavorite = true; // Rollback
            alert(`Erreur de suppression: ${err.message}`);
          }
        });
      } else {
        console.warn("Impossible de supprimer le favori car l'ID BDD est manquant.");
      }

    } else {
      // Ajout du favori
      const title = article.title;
      const url = article.url;
      const category = article.category;
      const source = article.source;

      this.favoriteService.addFavorite(title, url, category, source).subscribe({
        next: (response) => {
          this.loadCurrentFavorites().then(() => {
            // Mettre à jour l'état de l'article pour obtenir le nouvel ID
            const updatedState = this.checkIfFavorite(article);
            article.favoriteId = updatedState.favoriteId;
          });
        },
        error: (err) => {
          console.error('Erreur d\'ajout:', err);
          article.isFavorite = false; // Rollback
          alert(`Erreur d'ajout aux favoris: ${err.message}`);
        }
      });
    }
  }
}
