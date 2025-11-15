import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Sidebar } from '../sidebar/sidebar';
import { FavoriteService, FavoriteItem } from '../services/favorite.service';
import { HttpClientModule } from '@angular/common/http';
import { AuthService } from '../services/auth.service';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-favorites',
  standalone: true,
  imports: [CommonModule, Sidebar, HttpClientModule],
  templateUrl: './favoris.html',
  styleUrls: ['./favoris.css']
})
export class Favoris implements OnInit, OnDestroy {
  favorites: FavoriteItem[] = [];
  isLoading = true;
  errorMessage: string | null = null;

  private authSubscription!: Subscription;

  constructor(
    private favoriteService: FavoriteService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    // On attend que l’utilisateur soit authentifié
    this.authSubscription = this.authService.isAuthenticated$
      .pipe(filter(isAuthenticated => isAuthenticated))
      .subscribe(() => {
        this.loadFavorites();
      });
  }

  ngOnDestroy(): void {
    if (this.authSubscription) {
      this.authSubscription.unsubscribe();
    }
  }

  loadFavorites(): void {
    this.errorMessage = null;
    this.isLoading = true;

    this.favoriteService.getFavorites().subscribe({
      next: (data) => {
        this.favorites = data;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Erreur lors du chargement des favoris:', err);
        this.errorMessage = err.error?.message || 'Impossible de charger les favoris.';
        this.favorites = [];
        this.isLoading = false;
      }
    });
  }

  removeFromFavorites(id: number): void {
    this.favoriteService.removeFavorite(id).subscribe({
      next: () => {
        this.favorites = this.favorites.filter(item => item.id !== id);
      },
      error: (err) => {
        console.error('Erreur de suppression:', err);
        this.errorMessage = err.error?.message || 'Erreur lors de la suppression du favori.';
      }
    });
  }
}
