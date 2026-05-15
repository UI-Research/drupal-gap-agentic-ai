export class StatsResponseDto {
  byStatus: Record<string, number>;
  total: number;
  timestamp: string;
}
