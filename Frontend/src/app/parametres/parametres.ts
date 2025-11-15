import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Sidebar } from '../sidebar/sidebar';
import { AuthService } from '../services/auth.service';
import { ThemeService } from '../services/theme.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-parametres',
  standalone: true,
  imports: [CommonModule, FormsModule, Sidebar],
  templateUrl: './parametres.html',
  styleUrls: ['./parametres.css']
})
export class Parametres implements OnInit {
  isDarkMode: boolean = false;
  oldPassword: string = '';
  newPassword: string = '';
  confirmPassword: string = '';
  passwordChangeMessage: string = '';

  constructor(
    private authService: AuthService,
    private themeService: ThemeService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.isDarkMode = this.themeService.isDarkMode();
  }

  //  Changement de mot de passe avec confirmation
  onChangePassword(): void {
    if (!this.oldPassword || !this.newPassword || !this.confirmPassword) {
      this.passwordChangeMessage = 'Veuillez remplir tous les champs.';
      return;
    }

    if (this.newPassword !== this.confirmPassword) {
      this.passwordChangeMessage = 'Les nouveaux mots de passe ne correspondent pas.';
      return;
    }

    this.authService.changePassword(this.oldPassword, this.newPassword).subscribe({
      next: (response) => {
        if (response.success) {
          this.passwordChangeMessage = ' Mot de passe changé avec succès.';
          this.oldPassword = '';
          this.newPassword = '';
          this.confirmPassword = '';
        } else {
          this.passwordChangeMessage = ` Erreur : ${response.message || 'Ancien mot de passe incorrect.'}`;
        }
      },
      error: (err) => {
        console.error(err);
        this.passwordChangeMessage = ' Erreur lors du changement de mot de passe.';
      }
    });
  }

  //  Bascule le thème (sombre/clair)
  toggleTheme(): void {
    this.themeService.toggleTheme();
    this.isDarkMode = this.themeService.isDarkMode();
  }

  //  Déconnexion
  logout(): void {
    this.authService.logout().subscribe({
      next: () => this.router.navigate(['/login']),
      error: (err) => {
        console.error('Erreur lors de la déconnexion', err);
        this.router.navigate(['/login']);
      }
    });
  }
}
