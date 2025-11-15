import { Injectable, Renderer2, RendererFactory2 } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private renderer: Renderer2;
  private currentTheme: 'light' | 'dark' = 'light';

  constructor(private rendererFactory: RendererFactory2) {
    this.renderer = this.rendererFactory.createRenderer(null, null);
    this.loadTheme();
  }

  private loadTheme(): void {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      this.currentTheme = 'dark';
      this.applyTheme(this.currentTheme);
    } else {
      this.currentTheme = 'light';
    }
  }
  private applyTheme(theme: 'light' | 'dark'): void {
    if (theme === 'dark') {
      // Ajoute la classe 'dark-theme' au corps du document
      this.renderer.addClass(document.body, 'dark-theme');
    } else {
      // Retire la classe 'dark-theme'
      this.renderer.removeClass(document.body, 'dark-theme');
    }
  }

  toggleTheme(): void {
    this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    this.applyTheme(this.currentTheme);
    localStorage.setItem('theme', this.currentTheme);
  }

  isDarkMode(): boolean {
    return this.currentTheme === 'dark';
  }
}
