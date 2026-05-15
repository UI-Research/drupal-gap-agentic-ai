import { Injectable } from '@nestjs/common';

@Injectable()
export class ItemsService {
  findAll() {
    return [{ id: 1, name: 'Benchmark item' }];
  }
}
