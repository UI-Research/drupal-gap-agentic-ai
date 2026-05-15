import { Module } from '@nestjs/common';
import { ItemsModule } from '../items/items.module';
import { TasksService } from './tasks.service';

@Module({
  imports: [ItemsModule],
  providers: [TasksService],
})
export class TasksModule {}
