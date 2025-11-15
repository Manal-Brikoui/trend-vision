import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { Home } from './home/home';
import { Login } from './login/login';
import { Sidebar } from './sidebar/sidebar';
import { Dashboard } from './dashboard/dashboard';
import { Github } from './github/github';
import { Reddit } from './reddit/reddit';
import { News } from './news/news';
import { Favoris } from './favoris/favoris';
import { Historique } from './historique/historique';
import { Parametres } from './parametres/parametres';
import { Youtube } from './youtube/youtube';
import { Football } from './football/football';
import { AuthGuard } from './auth/auth.guard';

export const routes: Routes = [
  { path: '', component: Home },
  { path: 'login', component: Login },
  { path: 'sidebar', component: Sidebar},
  { path: 'dashboard', component: Dashboard },
  { path: 'github', component: Github },
  { path: 'reddit', component: Reddit },
  { path: 'news', component: News},
  { path: 'youtube', component: Youtube },
  { path: 'football', component: Football },

  { path: 'favoris', component: Favoris },
  { path: 'historique', component: Historique },

  { path: 'parametres', component: Parametres },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
