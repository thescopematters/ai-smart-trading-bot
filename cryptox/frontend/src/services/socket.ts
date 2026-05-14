import { io, Socket } from 'socket.io-client';

let socket: Socket | null = null;

export const connectSocket = (): Socket => {
  if (!socket) {
    socket = io('http://localhost:3000', {
      transports: ['websocket'],
    });

    socket.on('connect', () => {
      console.log('🔌 WebSocket connected');
    });

    socket.on('disconnect', () => {
      console.log('❌ WebSocket disconnected');
    });
  }
  return socket;
};

export const subscribeToSymbol = (symbol: string) => {
  if (socket) {
    socket.emit('subscribe', symbol);
    console.log(`📡 Subscribed to ${symbol}`);
  }
};

export const getSocket = (): Socket | null => socket;

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};