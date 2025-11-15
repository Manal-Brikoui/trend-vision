import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Sidebar } from '../sidebar/sidebar';
import { FavoriteService, FavoriteItem } from '../services/favorite.service';
import { HttpClientModule } from '@angular/common/http';
import HistoriqueService from '../services/historique.service';
import { AuthService } from '../services/auth.service';

interface YoutubeVideo {
  category: string;
  channel: string;
  title: string;
  url: string;
  views: string;
  isFavorite: boolean;
  favoriteId: number | null;
}

@Component({
  selector: 'app-youtube',
  standalone: true,
  imports: [CommonModule, FormsModule, Sidebar, HttpClientModule],
  templateUrl: './youtube.html',
  styleUrls: ['./youtube.css']
})
export class Youtube implements OnInit {
  allVideos: YoutubeVideo[] = [];
  filteredVideos: YoutubeVideo[] = [];
  searchTerm: string = '';
  showModal: boolean = false;
  selectedVideo: YoutubeVideo | null = null;
  private currentFavorites: FavoriteItem[] = []; // Cache local des favoris du backend

  isLoading: boolean = true;

  constructor(
    private favoriteService: FavoriteService,
    private historiqueService: HistoriqueService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadCurrentFavorites().then(() => {
      this.fetchYoutubeTrends("morocco");
    });
  }

  //  Chargement asynchrone des favoris depuis le backend
  async loadCurrentFavorites(): Promise<void> {
    return new Promise((resolve) => {
      this.favoriteService.getFavorites().subscribe({
        next: (data) => {
          this.currentFavorites = data.filter(fav => fav.source === 'youtube');
          resolve();
        },
        error: (err) => {
          console.error("Erreur de chargement des favoris:", err);
          resolve();
        }
      });
    });
  }

  private checkIfFavorite(video: any): { isFavorite: boolean, favoriteId: number | null } {
    const favorite = this.currentFavorites.find(fav => fav.url === video.url);

    return {
      isFavorite: !!favorite,
      favoriteId: favorite ? favorite.id : null
    };
  }

  //  Récupère les vidéos tendances pour un pays donné
  fetchYoutubeTrends(country: string): void {
    fetch(`http://127.0.0.1:5000/api/youtube/${country}`)
      .then(response => response.json())
      .then((data: any[]) => {
        this.allVideos = data.map(video => ({
          category: video.category,
          channel: video.channel,
          title: video.title,
          url: video.url,
          views: video.views,
          ...this.checkIfFavorite(video)
        }));
        this.filteredVideos = this.allVideos;
        this.isLoading = false;
      })
      .catch(error => {
        console.error(' Erreur lors du chargement des tendances YouTube:', error);
        this.isLoading = false;
      });
  }

  // Filtrer localement les vidéos par titre ou chaîne
  filterVideos(): void {
    if (this.searchTerm.trim() === '') {
      this.filteredVideos = this.allVideos;
    } else {
      const term = this.searchTerm.toLowerCase();
      this.filteredVideos = this.allVideos.filter(video =>
        video.title.toLowerCase().includes(term) ||
        video.channel.toLowerCase().includes(term)
      );
    }
  }

  searchVideosBackend(): void {
    if (this.searchTerm.trim() === '') {
      this.filteredVideos = this.allVideos;
      return;
    }

    // On met à jour l'état de chargement si une recherche démarre
    this.isLoading = true;

    fetch(`http://127.0.0.1:5000/api/search/${this.searchTerm}`)
      .then(response => response.json())
      .then((data: any[]) => {
        this.filteredVideos = data.map(video => ({
          category: video.category,
          channel: video.channel,
          title: video.title,
          url: video.url,
          views: video.views,
          ...this.checkIfFavorite(video)
        }));
        this.isLoading = false;
      })
      .catch(error => {
        console.error(' Erreur lors de la recherche YouTube:', error);
        this.isLoading = false;
      });
  }

  //  Gestion de la fenêtre modale
  openModal(video: YoutubeVideo): void {
    this.selectedVideo = video;
    this.showModal = true;

    if (this.authService.isLoggedIn()) {
      this.historiqueService.trackVisit(
        video.title,
        video.url,
        'youtube', // Source
        video.category || 'trending'
      );
    }
  }

  closeModal(): void {
    this.showModal = false;
    this.selectedVideo = null;
  }

  // Logique de favori mise à jour (asynchrone)
  toggleFavorite(video: YoutubeVideo): void {
    video.isFavorite = !video.isFavorite; // Mise à jour optimiste

    if (!video.isFavorite) {
      // Suppression du favori
      if (video.favoriteId !== null) {
        this.favoriteService.removeFavorite(video.favoriteId).subscribe({
          next: () => {
            video.favoriteId = null;
          },
          error: (err) => {
            console.error('Erreur de suppression:', err);
            video.isFavorite = true; // Rollback
            alert(`Erreur de suppression: ${err.message}`);
          }
        });
      } else {
        console.warn("Impossible de supprimer le favori car l'ID BDD est manquant.");
      }

    } else {
      // Ajout du favori
      const title = video.title;
      const url = video.url;
      const category = video.category || 'youtube';
      const source = video.channel;

      this.favoriteService.addFavorite(title, url, category, source).subscribe({
        next: (response) => {
          // L'ajout a réussi, on recharge les favoris pour récupérer l'ID généré
          this.loadCurrentFavorites().then(() => {
            // Mettre à jour l'état de la vidéo pour obtenir le nouvel ID
            const updatedState = this.checkIfFavorite(video);
            video.favoriteId = updatedState.favoriteId;
          });
        },
        error: (err) => {
          console.error('Erreur d\'ajout:', err);
          video.isFavorite = false; // Rollback
          alert(`Erreur d'ajout aux favoris: ${err.message}`);
        }
      });
    }
  }
}
