import { CanActivate, ExecutionContext, Injectable, UnauthorizedException } from '@nestjs/common';

@Injectable()
export class AuthGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    const authHeader = request.headers['authorization'];

    if (!authHeader || authHeader !== 'Bearer valid-token') {
      throw new UnauthorizedException('Missing or invalid authorization token');
    }

    return true;
  }
}
