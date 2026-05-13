import { IsString, IsNumber, IsEnum, IsOptional, Min } from 'class-validator';

export enum OrderSide {
  BUY = 'BUY',
  SELL = 'SELL',
}
export enum OrderType {
  LIMIT = 'LIMIT',
  MARKET = 'MARKET',
}

export class CreateOrderDto {
  @IsString()
  symbol: string; // 'BTC/USDT'

  @IsEnum(OrderSide)
  side: OrderSide;

  @IsEnum(OrderType)
  type: OrderType;

  @IsOptional()
  @IsNumber()
  @Min(0)
  price?: number; // optional for market orders

  @IsNumber()
  @Min(0.0001)
  quantity: number;
}
