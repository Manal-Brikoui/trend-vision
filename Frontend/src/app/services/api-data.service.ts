import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ChartDataset } from 'chart.js';

// L'URL de  backend Flask
const API_URL = 'http://127.0.0.1:5000/api';

// Interface pour les données brutes reçues du backend Flask
export interface TrendResult {
  date: string;
  category: string;
  count: number;
}


export interface ChartData {
  labels: string[]; // Les jours
  datasets: ChartDataset<'bar'>[];
}

@Injectable({
  providedIn: 'root'
})
export class ApiDataService {

  constructor(private http: HttpClient) { }

  getGlobalTrends(): Observable<{ success: boolean, data: TrendResult[] }> {
    return this.http.get<{ success: boolean, data: TrendResult[] }>(`${API_URL}/trends/global`);
  }
}
