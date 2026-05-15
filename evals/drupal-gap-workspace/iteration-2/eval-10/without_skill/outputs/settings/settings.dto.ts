import { IsString, IsBoolean, IsOptional } from 'class-validator';

export class UpdateSettingsDto {
  @IsString()
  @IsOptional()
  BANNER_MESSAGE?: string;

  @IsBoolean()
  @IsOptional()
  bannerEnabled?: boolean;
}
