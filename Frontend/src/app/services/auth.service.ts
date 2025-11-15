import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://127.0.0.1:5000/api';

  private isAuthenticatedSubject = new BehaviorSubject<boolean>(false);
  isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

  private userEmailSubject = new BehaviorSubject<string | null>(null);
  userEmail$ = this.userEmailSubject.asObservable();

  constructor(private http: HttpClient) {
    this.checkSession(); // Vérifie la session dès le démarrage
  }

  private setAuthenticatedState(isAuthenticated: boolean, email: string | null = null): void {
    this.isAuthenticatedSubject.next(isAuthenticated);
    this.userEmailSubject.next(email);
  }

  isLoggedIn(): boolean {
    return this.isAuthenticatedSubject.value;
  }

  checkSession(): void {
    this.http.get<any>(`${this.apiUrl}/session_test`, { withCredentials: true }).pipe(
      tap(response => {
        if (response.username) {
          this.setAuthenticatedState(true, response.username);
        } else {
          this.setAuthenticatedState(false, null);
        }
      }),
      catchError(() => {
        this.setAuthenticatedState(false, null);
        return of(null);
      })
    ).subscribe();
  }

  // Connexion utilisateur
  login(email: string, password: string): Observable<any> {
    const payload = { username: email, password: password };
    return this.http.post<any>(`${this.apiUrl}/login`, payload, { withCredentials: true }).pipe(
      tap(response => {
        if (response.success) {
          this.setAuthenticatedState(true, email);
        }
      }),
      catchError(error => {
        this.setAuthenticatedState(false, null);
        return of({ success: false, message: 'Erreur de connexion', error });
      })
    );
  }

  //  Déconnexion
  logout(): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/logout`, {}, { withCredentials: true }).pipe(
      tap(() => this.setAuthenticatedState(false, null)),
      catchError(error => {
        console.error('Erreur lors de la déconnexion', error);
        this.setAuthenticatedState(false, null);
        return of({ success: false, message: 'Erreur lors de la déconnexion', error });
      })
    );
  }

  // 🔹 Changement de mot de passe
  changePassword(oldPassword: string, newPassword: string): Observable<any> {
    const payload = {
      current_password: oldPassword,
      new_password: newPassword,
      confirm_password: newPassword
    };

    return this.http.post<any>(`${this.apiUrl}/change-password`, payload, { withCredentials: true }).pipe(
      catchError(error => {
        console.error('Erreur de changement de mot de passe', error);
        return of({ success: false, message: 'Erreur serveur', error });
      })
    );
  }

  //  Enregistrement d'un nouvel utilisateur
  register(email: string, password: string): Observable<any> {
    const payload = { username: email, password: password };
    return this.http.post<any>(`${this.apiUrl}/register`, payload).pipe(
      catchError(error => {
        console.error("Erreur lors de l'enregistrement", error);
        return of({ success: false, message: "Erreur lors de l'inscription", error });
      })
    );
  }

  //  Réinitialisation du mot de passe oublié
  resetPassword(email: string, newPassword: string): Observable<any> {
    const payload = { email: email, new_password: newPassword };
    return this.http.post<any>(`${this.apiUrl}/reset-password`, payload).pipe(
      catchError(error => {
        console.error("Erreur lors de la réinitialisation", error);
        return of({ success: false, message: "Erreur lors de la réinitialisation", error });
      })
    );
  }

  //  Vérifie si l'utilisateur est connecté via OAuth
  checkOAuthUser(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/check-oauth-user`, { withCredentials: true }).pipe(
      catchError(error => {
        console.error("Erreur lors de la vérification OAuth", error);
        return of({ success: false, message: "Erreur lors de la vérification OAuth", error });
      })
    );
  }
}
