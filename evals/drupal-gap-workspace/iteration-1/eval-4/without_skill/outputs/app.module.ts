import { Module } from '@nestjs/common';
import { ScheduleModule } from '@nestjs/schedule';
import { ItemsModule } from './items/items.module';
import { TasksModule } from './tasks/tasks.module';

@Module({
  imports: [ScheduleModule.forRoot(), ItemsModule, TasksModule],
})
export class AppModule {}
