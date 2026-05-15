import { Injectable } from '@nestjs/common';

export interface ReportItem {
  id: number;
  title: string;
  status: string;
  createdAt: Date;
}

@Injectable()
export class ReportsService {
  private readonly reports: ReportItem[] = [
    { id: 1, title: 'Quarterly Report', status: 'published', createdAt: new Date() },
    { id: 2, title: 'Annual Summary', status: 'published', createdAt: new Date() },
  ];

  findAll(): ReportItem[] {
    return this.reports.filter((r) => r.status === 'published');
  }
}
