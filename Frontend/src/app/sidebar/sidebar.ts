import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.css']
})
export class Sidebar {
  isDropdownOpen: { [key: string]: boolean } = {
    tendance: false
  };

  // Injectez le Router dans le constructeur
  constructor(private router: Router) { }

  toggleDropdown(dropdownName: string) {
    this.isDropdownOpen[dropdownName] = !this.isDropdownOpen[dropdownName];
  }

  toggleSidebar() {
    console.log('Toggle sidebar clicked');
  }

  navigateTo(path: string) {
    this.router.navigate([path]);
  }
}
