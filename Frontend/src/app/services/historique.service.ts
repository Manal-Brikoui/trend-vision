import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';

export interface HistoriqueItem {
  id?: number;
  title: string;
  source: 'github' | 'reddit' | 'news' | 'football'|'youtube';
  author?: string;
  url: string;
  category?: string;
  visited_at?: string;
}

@Injectable({ providedIn: 'root' })
class HistoriqueService {
  /**  URL de ton backend Flask */
  private apiUrl = 'http://127.0.0.1:5000/api/history';

  constructor(private http: HttpClient) {}

  /**  Récupérer tout l’historique */
  getHistory(): Observable<HistoriqueItem[]> {
    return this.http
      .get<{ success: boolean; data: HistoriqueItem[] }>(this.apiUrl, {
        withCredentials: true,
      })
      .pipe(
        map((response) => {
          if (response.success && Array.isArray(response.data)) {
            return response.data;
          }
          return [];
        }),
        catchError(error => {
          console.error(' Erreur lors de la récupération de l’historique', error);
          return of([]);
        })
      );
  }

  /** Ajouter un élément à l’historique */
  addToHistory(item: HistoriqueItem): Observable<{ success: boolean; message?: string }> {
    return this.http.post<{ success: boolean; message?: string }>(
      this.apiUrl,
      item,
      { withCredentials: true }
    ).pipe(
      catchError(error => {
        console.error(' Erreur lors de l’ajout à l’historique', error);
        return of({ success: false, message: 'Erreur réseau ou serveur' });
      })
    );
  }

  /**  Supprimer un élément spécifique */
  deleteItem(id: number): Observable<{ success: boolean; message?: string }> {
    return this.http.delete<{ success: boolean; message?: string }>(
      `${this.apiUrl}/${id}`,
      { withCredentials: true }
    ).pipe(
      catchError(error => {
        console.error(' Erreur lors de la suppression d’un élément', error);
        return of({ success: false, message: 'Erreur réseau ou serveur' });
      })
    );
  }

  /** Effacer tout l’historique */
  clearHistory(): Observable<{ success: boolean; message?: string }> {
    return this.http.delete<{ success: boolean; message?: string }>(
      this.apiUrl,
      { withCredentials: true }
    ).pipe(
      catchError(error => {
        console.error(' Erreur lors de l’effacement de l’historique', error);
        return of({ success: false, message: 'Erreur réseau ou serveur' });
      })
    );
  }

  /**  Enregistrer automatiquement une visite */
  trackVisit(title: string, url: string, source: 'github' | 'reddit' | 'news' | 'football'|'youtube', category?: string): void {
    const item: HistoriqueItem = {
      title,
      url,
      source,
      category: category || ''
    };

    this.addToHistory(item).subscribe(response => {
      if (response.success) {
        console.log(' Visite enregistrée dans l’historique');
      } else {
        console.warn(' Échec de l’enregistrement de la visite');
      }
    });
  }
}

export default HistoriqueService
