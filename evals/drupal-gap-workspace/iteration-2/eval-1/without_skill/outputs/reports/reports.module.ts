import { Module } from '@nestjs/common';
import { ReportsController } from './reports.controller';
import { ReportsService } from './reports.service';
import { ReportsGuard } from './reports.guard';

@Module({
  controllers: [ReportsController],
  providers: [ReportsService, ReportsGuard],
  exports: [ReportsService],
})
export class ReportsModule {}
