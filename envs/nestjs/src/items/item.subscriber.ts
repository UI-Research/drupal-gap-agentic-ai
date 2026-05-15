import {
  DataSource,
  EntitySubscriberInterface,
  EventSubscriber,
  InsertEvent,
  UpdateEvent,
} from 'typeorm';
import { Item } from './item.entity';
import { Injectable } from '@nestjs/common';

@Injectable()
@EventSubscriber()
export class ItemSubscriber implements EntitySubscriberInterface<Item> {
  constructor(dataSource: DataSource) {
    dataSource.subscribers.push(this);
  }

  listenTo() {
    return Item;
  }

  beforeInsert(event: InsertEvent<Item>): void {
    const entity = event.entity;
    if (entity.name && !entity.slug) {
      entity.slug = Item.createSlug(entity.name);
    }
  }

  beforeUpdate(event: UpdateEvent<Item>): void {
    const entity = event.entity as Item;
    if (entity && entity.name) {
      entity.slug = Item.createSlug(entity.name);
    }
  }
}
