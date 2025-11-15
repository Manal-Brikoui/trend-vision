import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Dashboard} from './dashboard/dashboard';
import { Sidebar } from './sidebar/sidebar';
import { ApiDataService } from './services/api-data.service';
import { NgChartsModule } from 'ng2-charts';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    NgChartsModule,

  ],
  providers: [ApiDataService],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App {

}
