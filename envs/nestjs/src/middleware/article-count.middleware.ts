import { Injectable, NestMiddleware, Logger } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';

@Injectable()
export class ArticleCountMiddleware implements NestMiddleware {
  private readonly logger = new Logger(ArticleCountMiddleware.name);

  use(req: Request, res: Response, next: NextFunction): void {
    res.setHeader('X-Powered-By', 'NestJS');
    res.setHeader('X-Request-Time', new Date().toISOString());
    this.logger.log(`${req.method} ${req.path}`);
    next();
  }
}
