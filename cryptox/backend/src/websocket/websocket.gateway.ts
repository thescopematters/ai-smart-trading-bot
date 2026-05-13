import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  ConnectedSocket,
  MessageBody,
  OnGatewayConnection,
  OnGatewayDisconnect,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { OnEvent } from '@nestjs/event-emitter';

@WebSocketGateway({
  cors: { origin: 'http://localhost:5173', credentials: true },
})
export class WebsocketGateway
  implements OnGatewayConnection, OnGatewayDisconnect
{
  @WebSocketServer()
  server: Server;

  handleConnection(client: Socket) {
    console.log(`🔌 Client connected: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    console.log(`❌ Client disconnected: ${client.id}`);
  }

  // ✅ Fix: use @ConnectedSocket() to get the client properly
  @SubscribeMessage('subscribe')
  handleSubscribe(
    @ConnectedSocket() client: Socket,
    @MessageBody() symbol: string,
  ) {
    client.join(`room:${symbol}`);
    console.log(`📡 ${client.id} subscribed to ${symbol}`);
  }

  @OnEvent('trade.executed')
  handleTradeExecuted(payload: { trade: any; symbol: string }) {
    this.server.to(`room:${payload.symbol}`).emit('trade:new', payload.trade);
    this.server.to(`room:${payload.symbol}`).emit('orderbook:update');
    console.log(`📤 Trade broadcast to room:${payload.symbol}`);
  }
}
