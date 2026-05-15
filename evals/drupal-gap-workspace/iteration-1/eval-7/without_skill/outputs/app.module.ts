import { Module } from '@nestjs/common';
import { ScheduleModule } from '@nestjs/schedule';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ItemsModule } from './items/items.module';
import { TasksModule } from './tasks/tasks.module';
import { Item } from './items/item.entity';

@Module({
  imports: [
    TypeOrmModule.forRoot({
      type: 'sqljs',
      entities: [Item],
      synchronize: true,
    }),
    ScheduleModule.forRoot(),
    ItemsModule,
    TasksModule,
  ],
})
export class AppModule {}
