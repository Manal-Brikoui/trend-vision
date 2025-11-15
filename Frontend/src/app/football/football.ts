import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Sidebar } from '../sidebar/sidebar';
import { FavoriteService, FavoriteItem } from '../services/favorite.service';
import { HttpClientModule } from '@angular/common/http'; 
import HistoriqueService from '../services/historique.service';
import { AuthService } from '../services/auth.service';

interface FootballMatch {
  away_team: string;
  category: string;
  competition: string;
  date: string;
  home_team: string;
  score: string;
  status: string;
  favoriteId: number | null;
  isFavorite: boolean;
  url: string;
}

@Component({
  selector: 'app-football',
  standalone: true,
  imports: [CommonModule, FormsModule, Sidebar, HttpClientModule],
  templateUrl: './football.html',
  styleUrls: ['./football.css']
})
export class Football implements OnInit {
  allMatches: FootballMatch[] = [];
  filteredMatches: FootballMatch[] = [];
  searchTerm: string = '';
  showModal: boolean = false;
  selectedMatch: FootballMatch | null = null;
  private currentFavorites: FavoriteItem[] = [];

  isLoading: boolean = true;

  constructor(
    private favoriteService: FavoriteService,
    private historiqueService: HistoriqueService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadCurrentFavorites().then(() => {
      this.fetchMatches();
    });
  }

  async loadCurrentFavorites(): Promise<void> {
    return new Promise((resolve) => {
      this.favoriteService.getFavorites().subscribe({
        next: (data) => {
          this.currentFavorites = data.filter(fav => fav.source === 'football'); // Filtrage spécifique
          console.log("Favoris chargés:", data.length);
          resolve();
        },
        error: (err) => {
          console.error("Erreur de chargement des favoris:", err);
          resolve(); // Continuer même en cas d'erreur
        }
      });
    });
  }

  // Récupération des matchs et vérification de l'état "Favori"
  fetchMatches(): void {
    this.isLoading = true; 
    fetch('http://127.0.0.1:5000/api/sports')
      .then(res => res.json())
      .then((data: any) => {
        const matches = Array.isArray(data) ? data : data.all_matches;

        this.allMatches = matches.map((match: any) => {
          const matchTitle = this.generateMatchTitle(match);
          const matchUrl = this.generateMatchUrl(matchTitle);

          const formatted: FootballMatch = {
            away_team: match.away_team,
            category: match.category ?? "sports",
            competition: match.competition,
            date: match.date,
            home_team: match.home_team,
            score: match.score,
            status: match.status,
            url: matchUrl,
            ...this.checkIfFavorite({title: matchTitle, url: matchUrl})
          };
          return formatted;
        });

        this.filteredMatches = this.allMatches;
        this.isLoading = false;
      })
      .catch(err => {
        console.error("Erreur chargement des matchs:", err);
        this.isLoading = false;
      });
  }

  private checkIfFavorite(item: {title: string, url: string}): { isFavorite: boolean, favoriteId: number | null } {
    const favorite = this.currentFavorites.find(fav => fav.url === item.url);

    return {
      isFavorite: !!favorite,
      favoriteId: favorite ? favorite.id : null
    };
  }

  filterMatches(): void {
    if (this.searchTerm.trim() === '') {
      this.filteredMatches = this.allMatches;
    } else {
      this.filteredMatches = this.allMatches.filter(match =>
        match.home_team.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        match.away_team.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        match.competition.toLowerCase().includes(this.searchTerm.toLowerCase())
      );
    }
  }

  openModal(match: FootballMatch): void {
    this.selectedMatch = match;
    this.showModal = true;

    if (this.authService.isLoggedIn()) {
      const source: any = 'football';
      this.historiqueService.trackVisit(
        this.generateMatchTitle(match),
        match.url,
        source,
        match.competition
      );
    }
  }

  closeModal(): void {
    this.showModal = false;
    this.selectedMatch = null;
  }

  toggleFavorite(match: FootballMatch): void {
    match.isFavorite = !match.isFavorite; // Optimistic UI update

    if (!match.isFavorite) {
      // Suppression du favori (si un ID est disponible)
      if (match.favoriteId !== null) {
        this.favoriteService.removeFavorite(match.favoriteId).subscribe({
          next: () => {
            match.favoriteId = null; // Supprime l'ID local
          },
          error: (err) => {
            console.error('Erreur de suppression:', err);
            match.isFavorite = true; // Rollback
            alert(`Erreur de suppression: ${err.message}`);
          }
        });
      } else {
        console.warn("Impossible de supprimer le favori car l'ID est manquant.");
      }

    } else {
      // Ajout du favori
      const title = this.generateMatchTitle(match);
      const url = match.url; // Utilise l'URL déjà calculée
      const category = match.competition;
      const source = match.category;


      this.favoriteService.addFavorite(title, url, category, source).subscribe({
        next: (response) => {
          // L'ajout a réussi, on recharge les favoris pour récupérer l'ID généré
          this.loadCurrentFavorites().then(() => {
            const updatedState = this.checkIfFavorite({ title: title, url: url });
            match.favoriteId = updatedState.favoriteId;
          });
        },
        error: (err) => {
          console.error('Erreur d\'ajout:', err);
          match.isFavorite = false; // Rollback
          alert(`Erreur d'ajout aux favoris: ${err.message}`);
        }
      });
    }
  }

  private generateMatchTitle(match: any): string {
    return `${match.home_team} vs ${match.away_team} - ${match.date}`;
  }

  private generateMatchUrl(title: string): string {
    return `https://sports.example.com/match/${title.replace(/[^a-zA-Z0-9]/g, '_')}`;
  }
}
