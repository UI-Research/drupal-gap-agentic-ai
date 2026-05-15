import { Module } from '@nestjs/common';
import { ItemsModule } from './items/items.module';
import { ReportsModule } from './reports/reports.module';

@Module({
  imports: [ItemsModule, ReportsModule],
})
export class AppModule {}
