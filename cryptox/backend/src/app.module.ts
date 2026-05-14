import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { EventEmitterModule } from '@nestjs/event-emitter';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { PrismaModule } from './prisma/prisma.module';
import { AuthModule } from './auth/auth.module';
import { BalancesModule } from './balances/balances.module';
import { OrdersModule } from './orders/orders.module';
import { PairsModule } from './pairs/pairs.module';
import { TradesModule } from './trades/trades.module';
import { UsersModule } from './users/users.module';
import { WebsocketModule } from './websocket/websocket.module';
import { MatchingEngineModule } from './matching-engine/matching-engine.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    EventEmitterModule.forRoot(),
    PrismaModule,
    AuthModule,
    BalancesModule,
    OrdersModule,
    PairsModule,
    TradesModule,
    UsersModule,
    WebsocketModule,
    MatchingEngineModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
