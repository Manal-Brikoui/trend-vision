import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Sidebar } from '../sidebar/sidebar';
import { FavoriteService, FavoriteItem } from '../services/favorite.service';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import HistoriqueService from '../services/historique.service';
import { AuthService } from '../services/auth.service';


interface TrendingPost {
  author: string;
  title: string;
  url: string;
  isFavorite: boolean;
  favoriteId: number | null;
}

@Component({
  selector: 'app-reddit',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    Sidebar,
    HttpClientModule
  ],
  templateUrl: './reddit.html',
  styleUrls: ['./reddit.css']
})
export class Reddit implements OnInit {
  allPosts: TrendingPost[] = [];
  filteredPosts: TrendingPost[] = [];
  searchTerm: string = '';
  showModal: boolean = false;
  selectedPost: TrendingPost | null = null;
  private currentFavorites: FavoriteItem[] = [];


  isLoading: boolean = true;

  constructor(
    private favoriteService: FavoriteService,
    private http: HttpClient,
    private historiqueService: HistoriqueService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    // Charger les favoris actuels avant de charger les posts
    this.loadCurrentFavorites().then(() => {
      this.fetchRedditTrends();
    });
  }

  async loadCurrentFavorites(): Promise<void> {
    return new Promise((resolve) => {
      this.favoriteService.getFavorites().subscribe({
        next: (data) => {
          this.currentFavorites = data.filter(fav => fav.category === 'reddit');
          resolve();
        },
        error: (err) => {
          console.error("Erreur de chargement des favoris:", err);
          resolve();
        }
      });
    });
  }

  //  Vérification de l'état "Favori" pour un post
  private checkIfFavorite(post: any): { isFavorite: boolean, favoriteId: number | null } {
    const favorite = this.currentFavorites.find(fav => fav.url === post.url);

    return {
      isFavorite: !!favorite,
      favoriteId: favorite ? favorite.id : null
    };
  }

  //  Récupération des tendances Reddit depuis le backend Flask
  fetchRedditTrends(): void {
    this.http.get<any[]>('http://localhost:5000/api/reddit')
      .subscribe({
        next: (data) => {
          console.log(" Données reçues du backend:", data);
          this.allPosts = data.map(post => ({
            author: post.author,
            title: post.title,
            url: post.url,
            ...this.checkIfFavorite(post)
          }));
          this.filteredPosts = this.allPosts;
          this.isLoading = false;
        },
        error: (error) => {
          console.error(" Erreur lors de la récupération des tendances Reddit:", error);
          this.isLoading = false;
        }
      });
  }

  filterPosts(): void {
    if (this.searchTerm.trim() === '') {
      this.filteredPosts = this.allPosts;
    } else {
      const searchTermLower = this.searchTerm.toLowerCase();
      this.filteredPosts = this.allPosts.filter(post =>
        post.title.toLowerCase().includes(searchTermLower) ||
        post.author.toLowerCase().includes(searchTermLower)
      );
    }
  }

  //  Ouvrir la fenêtre modale
  openModal(post: TrendingPost): void {
    this.selectedPost = post;
    this.showModal = true;

    // Enregistrement dans l'historique
    if (this.authService.isLoggedIn()) {
      this.historiqueService.trackVisit(
        post.title,
        post.url,
        'reddit', // Source
        'trending' // Catégorie
      );
    }
  }

  // Fermer la fenêtre modale
  closeModal(): void {
    this.showModal = false;
    this.selectedPost = null;
  }

  //  Logique de favori mise à jour (asynchrone)
  toggleFavorite(post: TrendingPost): void {
    post.isFavorite = !post.isFavorite; // Mise à jour optimiste

    if (!post.isFavorite) {
      // Suppression du favori
      if (post.favoriteId !== null) {
        this.favoriteService.removeFavorite(post.favoriteId).subscribe({
          next: () => {
            post.favoriteId = null; // Supprime l'ID local
          },
          error: (err) => {
            console.error('Erreur de suppression:', err);
            post.isFavorite = true; // Rollback
            alert(`Erreur de suppression: ${err.message}`);
          }
        });
      } else {
        console.warn("Impossible de supprimer le favori car l'ID BDD est manquant.");
      }

    } else {
      // Ajout du favori
      const title = post.title;
      const url = post.url;
      const category = 'reddit';
      const source = post.author;

      this.favoriteService.addFavorite(title, url, category, source).subscribe({
        next: (response) => {
          // L'ajout a réussi, on recharge les favoris pour récupérer l'ID généré
          this.loadCurrentFavorites().then(() => {
            // Mettre à jour l'état du post pour obtenir le nouvel ID
            const updatedState = this.checkIfFavorite(post);
            post.favoriteId = updatedState.favoriteId;
          });
        },
        error: (err) => {
          console.error('Erreur d\'ajout:', err);
          post.isFavorite = false; // Rollback
          alert(`Erreur d'ajout aux favoris: ${err.message}`);
        }
      });
    }
  }
}
