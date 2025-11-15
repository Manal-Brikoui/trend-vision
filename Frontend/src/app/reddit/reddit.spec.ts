import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Reddit } from './reddit';

describe('Reddit', () => {
  let component: Reddit;
  let fixture: ComponentFixture<Reddit>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Reddit]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Reddit);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
