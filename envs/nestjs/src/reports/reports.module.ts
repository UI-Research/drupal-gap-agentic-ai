import { Module } from '@nestjs/common';
import { ReportsController } from './reports.controller';
import { ReportsService } from './reports.service';
import { AuthGuard } from './auth.guard';

@Module({
  controllers: [ReportsController],
  providers: [ReportsService, AuthGuard],
  exports: [ReportsService],
})
export class ReportsModule {}
