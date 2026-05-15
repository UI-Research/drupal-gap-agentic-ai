import { Controller, Get, UseGuards } from '@nestjs/common';
import { ReportsService } from './reports.service';
import { ReportsGuard } from './reports.guard';

@Controller('reports')
export class ReportsController {
  constructor(private readonly reportsService: ReportsService) {}

  @Get()
  @UseGuards(ReportsGuard)
  findAll() {
    return this.reportsService.findAll();
  }
}
