import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.html',
  styleUrls: ['./login.css']
})
export class Login {

  // Router pour naviguer après login
  private router = inject(Router);

  // URL du backend Flask
  private readonly FLASK_AUTH_BASE_URL = 'http://127.0.0.1:5000';

  // Signaux (pour gérer l’état de l’UI)
  isLoginMode = signal(true);
  message = signal('');
  isSuccess = signal(false);

  // Formulaires
  loginForm = {
    email: '',
    password: ''
  };

  registerForm = {
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  };

  toggleMode() {
    this.isLoginMode.set(!this.isLoginMode());
    this.message.set('');
  }

  private setStatusMessage(msg: string, success: boolean) {
    this.isSuccess.set(success);
    this.message.set(msg);
  }

  // Utilitaire fetch avec retry
  private async fetchWithBackoff(url: string, options: RequestInit, retries = 3): Promise<Response> {
    for (let i = 0; i < retries; i++) {
      try {
        return await fetch(url, options);
      } catch (error) {
        if (i === retries - 1) throw error;
        const delay = Math.pow(2, i) * 1000 + Math.random() * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    throw new Error('Fetch failed after retries');
  }

  //  LOGIN
  async onLogin() {
    this.message.set('');

    const payload = {
      username: this.loginForm.email,
      password: this.loginForm.password
    };

    try {
      this.setStatusMessage('Connexion en cours...', true);

      const response = await this.fetchWithBackoff(`${this.FLASK_AUTH_BASE_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'include'           //  pour envoyer/recevoir le cookie de session
      });

      const data = await response.json();

      if (response.ok && data.success) {
        this.setStatusMessage('Connexion réussie ! Redirection...', true);
        console.log('Utilisateur connecté :', this.loginForm.email);

        await this.router.navigate(['/dashboard']);
      } else {
        this.setStatusMessage(data.message || 'Échec de la connexion.', false);
      }
    } catch (error) {
      console.error('Erreur de connexion au backend:', error);
      this.setStatusMessage(
        'Erreur réseau. Le serveur d’authentification (port 5001) est-il démarré ?',
        false
      );
    }
  }

  //  REGISTER
  async onRegister() {
    this.message.set('');

    if (this.registerForm.password !== this.registerForm.confirmPassword) {
      this.setStatusMessage('Les mots de passe ne correspondent pas !', false);
      return;
    }

    const payload = {
      username: this.registerForm.email,
      password: this.registerForm.password
    };

    try {
      this.setStatusMessage('Inscription en cours...', true);

      const response = await this.fetchWithBackoff(`${this.FLASK_AUTH_BASE_URL}/api/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'include'           //  utile si le backend définit un cookie
      });

      const data = await response.json();

      if (response.ok && data.success) {
        this.setStatusMessage('Inscription réussie ! Vous pouvez vous connecter.', true);
        this.toggleMode();
      } else {
        this.setStatusMessage(data.message || 'Échec de l’inscription.', false);
      }
    } catch (error) {
      console.error('Erreur lors de l’inscription:', error);
      this.setStatusMessage('Erreur réseau. Le serveur est-il démarré ?', false);
    }
  }

  //  Login via Google
  onGoogleLogin() {
    window.location.href = `${this.FLASK_AUTH_BASE_URL}/google_login/login`;
  }

  onGoogleRegister() {
    this.onGoogleLogin();
  }

  //  Login via GitHub
  onGithubLogin() {
    window.location.href = `${this.FLASK_AUTH_BASE_URL}/github_login/login`;
  }

  onGithubRegister() {
    this.onGithubLogin();
  }
}
