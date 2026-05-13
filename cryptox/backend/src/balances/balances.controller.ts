import {
  Controller,
  Get,
  Post,
  Body,
  UseGuards,
  Request,
} from '@nestjs/common';
import { BalancesService } from './balances.service';
import { JwtAuthGuard } from '../common/jwt-auth.guard';
import { JwtService } from '@nestjs/jwt';

@Controller('api/balances')
export class BalancesController {
  constructor(
    private readonly balancesService: BalancesService,
    private readonly jwtService: JwtService,
  ) {}

  // GET /api/balances
  @UseGuards(JwtAuthGuard)
  @Get()
  getBalances(@Request() req) {
    return this.balancesService.getUserBalances(req.user.sub);
  }

  // POST /api/balances/topup
  @UseGuards(JwtAuthGuard)
  @Post('topup')
  topUp(@Request() req, @Body() body: { currency: string; amount: number }) {
    return this.balancesService.topUp(req.user.sub, body.currency, body.amount);
  }
}
