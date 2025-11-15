import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Football } from './football';

describe('Football', () => {
  let component: Football;
  let fixture: ComponentFixture<Football>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Football]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Football);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
