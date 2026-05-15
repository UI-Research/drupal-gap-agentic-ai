import { Injectable } from '@nestjs/common';

@Injectable()
export class ReportsService {
  findAll() {
    return [
      { id: 1, title: 'Annual Report', status: 'published' },
      { id: 2, title: 'Quarterly Summary', status: 'draft' },
      { id: 3, title: 'Monthly Metrics', status: 'published' },
    ];
  }
}
