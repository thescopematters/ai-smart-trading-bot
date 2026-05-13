import { Module } from '@nestjs/common';
import { MatchingEngineService } from './matching-engine.service';
import { BalancesModule } from '../balances/balances.module';
import { EventEmitterModule } from '@nestjs/event-emitter';

@Module({
  imports: [BalancesModule, EventEmitterModule],
  providers: [MatchingEngineService],
  exports: [MatchingEngineService],
})
export class MatchingEngineModule {}
