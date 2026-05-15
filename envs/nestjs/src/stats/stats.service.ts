import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Item } from '../items/item.entity';
import { StatsResponseDto } from './dto/stats-response.dto';

@Injectable()
export class StatsService {
  constructor(
    @InjectRepository(Item)
    private readonly itemRepository: Repository<Item>,
  ) {}

  async getStats(status?: string): Promise<StatsResponseDto> {
    const query = this.itemRepository.createQueryBuilder('item');

    if (status) {
      query.where('item.slug LIKE :status', { status: `%${status}%` });
    }

    const items = await query.getMany();

    const byStatus: Record<string, number> = {};
    for (const item of items) {
      const key = item.slug ? 'slugged' : 'unslugged';
      byStatus[key] = (byStatus[key] || 0) + 1;
    }

    return {
      byStatus,
      total: items.length,
      timestamp: new Date().toISOString(),
    };
  }
}
