
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './modal.html',
  styleUrls: ['./modal.css']
})
export class Modal {
  @Input() topic: any;
  @Output() close = new EventEmitter<void>();

  onClose(): void {
    this.close.emit();
  }
}
