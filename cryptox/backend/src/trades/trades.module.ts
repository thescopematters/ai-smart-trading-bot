import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { TradesController } from './trades.controller';
import { TradesService } from './trades.service';

@Module({
  imports: [
    JwtModule.register({
      secret: process.env.JWT_SECRET || 'fallback-secret',
    }),
  ],
  controllers: [TradesController],
  providers: [TradesService],
  exports: [TradesService],
})
export class TradesModule {}
