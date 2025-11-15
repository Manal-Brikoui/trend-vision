import { Component, OnInit, ViewChild, ElementRef, OnDestroy, AfterViewInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiDataService, TrendResult, ChartData } from '../services/api-data.service';
import { Sidebar } from '../sidebar/sidebar';
import { Chart, registerables, ChartDataset } from 'chart.js';

Chart.register(...registerables);

// Couleurs spécifiques pour les catégories
const CHART_COLORS: { [key: string]: string } = {
  'technologie': 'rgba(174,196,211,0.9)',
  'finance': 'rgba(9,79,79,0.9)',
  'sport': 'rgba(19,55,197,0.9)',
  'santé': 'rgba(11,217,123,0.9)',
  'autre': 'rgb(79,217,205, 0.9)',
};

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, Sidebar],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css']
})
export class Dashboard implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('barChart') chartRef!: ElementRef<HTMLCanvasElement>;
  chartInstance: Chart | undefined;

  public data: ChartData | null = null;
  public isLoading: boolean = true;
  public error: string | null = null;

  private _chartData: ChartData | null = null;

  constructor(
    private apiDataService: ApiDataService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadData();
  }

  ngAfterViewInit(): void {
    if (this._chartData) {
      this.renderChart();
    }
  }

  ngOnDestroy(): void {
    if (this.chartInstance) {
      this.chartInstance.destroy();
    }
  }

  loadData(): void {
    this.isLoading = true;
    this.error = null;

    this.apiDataService.getGlobalTrends().subscribe({
      next: (apiResponse) => {
        console.log("Réponse API brute reçue:", apiResponse);

        if (apiResponse && apiResponse.success && apiResponse.data) {
          this._chartData = this.transformDataForChart(apiResponse.data);
          this.data = this._chartData;

          this.cdr.detectChanges();

          console.log(" Données transformées (ChartData):", this.data);

          if (this.data.labels.length > 0) {
            setTimeout(() => {
              if (this.chartRef) {
                this.renderChart();
              } else {
                console.error(" ViewChild non prêt pour le rendu du graphique.");
              }
            }, 0);
          } else {
            this.error = 'Aucune donnée trouvée pour la période sélectionnée.';
          }
        } else {
          this.error = 'Les données reçues sont invalides ou non réussies.';
        }
        this.isLoading = false;
      },
      error: (err) => {
        this.error = 'Erreur lors du chargement des tendances globales.';
        this.isLoading = false;
        console.error(' Erreur API (HTTP):', err);
      }
    });
  }

  /**
   * Calcule le total des consultations pour chaque catégorie sur toute la période.
   */
  private transformDataForChart(results: TrendResult[]): ChartData {
    const totalCountsByCategory = new Map<string, number>();
    const allCategories = new Set<string>();

    results.forEach(item => {
      const category = item.category.trim();
      const count = Number(item.count);

      // Assurer que le compte est valide et positif
      if (!isNaN(count) && count > 0) {
        allCategories.add(category);
        const currentTotal = totalCountsByCategory.get(category) || 0;
        totalCountsByCategory.set(category, currentTotal + count);
      }
    });

    const categoriesArray = Array.from(allCategories);
    const dataSet: number[] = [];
    const backgroundColors: string[] = [];

    categoriesArray.forEach(category => {
      const count = totalCountsByCategory.get(category) || 0;
      dataSet.push(count);

      const colorKey = category.toLowerCase();
      const backgroundColor = CHART_COLORS[colorKey] || this.getRandomBlueShade();
      backgroundColors.push(backgroundColor);
    });

    return {
      labels: categoriesArray,
      datasets: [
        {
          label: 'Consultations totales',
          data: dataSet,
          backgroundColor: backgroundColors,
          borderColor: '#ffffff',
          borderWidth: 2,
          hoverOffset: 4,
        } as ChartDataset<'pie'> as ChartDataset<'bar'>
      ],
    };
  }

  private getRandomBlueShade(): string {
    const blues = [
      'rgba(54, 162, 235, 0.9)',
      'rgba(30, 144, 255, 0.9)',
      'rgba(70, 130, 180, 0.9)',
      'rgba(100, 149, 237, 0.9)',
      'rgba(65, 105, 225, 0.9)',
      'rgba(123, 104, 238, 0.9)'
    ];
    return blues[Math.floor(Math.random() * blues.length)];
  }


  renderChart(): void {
    if (!this.chartRef || !this.data) return;

    console.log(" Rendu du graphique en cours (type: pie)...");

    if (this.chartInstance) this.chartInstance.destroy();

    const ctx = this.chartRef.nativeElement.getContext('2d');
    if (ctx) {
      this.chartInstance = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: this.data.labels,
          datasets: this.data.datasets as ChartDataset<'pie'>[]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'right',
              labels: {
                color: '#0F172A',
              }
            },
            title: {
              display: true,
              text: 'Distribution des consultations par catégorie (Total)',
              color: '#1E40AF',
              font: { size: 16, weight: 'bold' }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  let label = context.label || '';
                  if (label) {
                    label += ': ';
                  }
                  const total = context.dataset.data.reduce((acc: any, value: any) => acc + value, 0);
                  const value = context.parsed;
                  const percentage = ((value / total) * 100).toFixed(1) + '%';
                  return label + value + ' (' + percentage + ')';
                }
              }
            }
          }
        }
      });
    }
  }
}
