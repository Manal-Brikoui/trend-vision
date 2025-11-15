import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { AuthService } from './auth.service';

export interface FavoriteItem {
  id: number;
  title: string;
  url: string;
  category: string;
  source: string;
  added_at: string;
}

// Interface pour la réponse des listes (GET)
interface FavoritesResponse {
  success: boolean;
  data: FavoriteItem[];
}

// Interface pour la réponse des opérations (POST/DELETE)
interface OperationResponse {
  success: boolean;
  message: string;
  id?: number;
}

@Injectable({
  providedIn: 'root'
})
export class FavoriteService {
  // URL du backend Flask
  private readonly baseApiUrl = 'http://127.0.0.1:5000/api';
  private readonly favoritesUrl = `${this.baseApiUrl}/favorites`;

  private readonly httpOptions = {
    withCredentials: true
  };

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {}

  // Gestion centralisée des erreurs
  private handleError(error: HttpErrorResponse): Observable<never> {
    const errorMsg = error.error?.message || `Erreur serveur (status: ${error.status})`;

    if (error.status === 401) {
      console.warn(' Erreur 401 : Session invalide ou expirée.', error);
      return throwError(() => new Error('Non authentifié'));
    }

    console.error('Erreur HTTP:', error);
    return throwError(() => new Error(errorMsg));
  }

  /**
   * Récupère la liste des favoris
   */
  getFavorites(): Observable<FavoriteItem[]> {
    return this.http.get<FavoritesResponse>(this.favoritesUrl, this.httpOptions).pipe(
      map(response => {
        if (response.success) return response.data;
        throw new Error('Échec de la récupération des favoris.');
      }),
      catchError(err => this.handleError(err))
    );
  }

  /**
   * Ajoute un favori
   */
  addFavorite(
    title: string,
    url: string,
    category: string = '',
    source: string = ''
  ): Observable<OperationResponse> {
    const payload = { title, url, category, source };

    return this.http.post<OperationResponse>(this.favoritesUrl, payload, this.httpOptions).pipe(
      catchError(err => this.handleError(err))
    );
  }

  /**
   * Supprime un favori
   */
  removeFavorite(id: number): Observable<OperationResponse> {
    const deleteUrl = `${this.favoritesUrl}/${id}`;

    return this.http.delete<OperationResponse>(deleteUrl, this.httpOptions).pipe(
      catchError(err => this.handleError(err))
    );
  }
}
