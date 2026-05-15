import { Injectable, Logger } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import { ItemsService } from '../items/items.service';

@Injectable()
export class TasksService {
  private readonly logger = new Logger(TasksService.name);

  constructor(private readonly itemsService: ItemsService) {}

  @Cron(CronExpression.EVERY_DAY_AT_MIDNIGHT)
  async handleDailyCount() {
    const items = await this.itemsService.findAll();
    this.logger.log(`[Daily] Total items: ${items.length}`);
  }
}
