import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class SettingsService {
  constructor(private readonly configService: ConfigService) {}

  getBannerMessage(): string {
    return this.configService.get<string>('BANNER_MESSAGE', 'Welcome to our site!');
  }

  getSettings(): Record<string, unknown> {
    return {
      bannerMessage: this.getBannerMessage(),
      bannerEnabled: this.configService.get<boolean>('BANNER_ENABLED', true),
    };
  }
}
