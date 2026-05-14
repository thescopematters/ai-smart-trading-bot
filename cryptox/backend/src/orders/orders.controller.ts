import {
  Controller,
  Get,
  Post,
  Delete,
  Body,
  Param,
  UseGuards,
  Request,
} from '@nestjs/common';
import { OrdersService } from './orders.service';
import { CreateOrderDto } from './dto/create-order.dto';
import { JwtAuthGuard } from '../common/jwt-auth.guard';
import { JwtService } from '@nestjs/jwt';

@Controller('api/orders')
export class OrdersController {
  constructor(
    private readonly ordersService: OrdersService,
    private readonly jwtService: JwtService,
  ) {}

  // POST /api/orders
  @UseGuards(JwtAuthGuard)
  @Post()
  createOrder(@Request() req, @Body() dto: CreateOrderDto) {
    return this.ordersService.createOrder(req.user.sub, dto);
  }

  // GET /api/orders
  @UseGuards(JwtAuthGuard)
  @Get()
  getMyOrders(@Request() req) {
    return this.ordersService.getUserOrders(req.user.sub);
  }

  // DELETE /api/orders/:id
  @UseGuards(JwtAuthGuard)
  @Delete(':id')
  cancelOrder(@Request() req, @Param('id') id: string) {
    return this.ordersService.cancelOrder(req.user.sub, id);
  }

  // GET /api/orders/orderbook/:symbol
  @Get('orderbook/:symbol')
  getOrderBook(@Param('symbol') symbol: string) {
    return this.ordersService.getOrderBook(decodeURIComponent(symbol));
  }
}
