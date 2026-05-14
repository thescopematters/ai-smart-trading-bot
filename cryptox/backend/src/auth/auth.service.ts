import {
  Injectable,
  BadRequestException,
  UnauthorizedException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { PrismaService } from '../prisma/prisma.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';
import * as bcrypt from 'bcrypt';

@Injectable()
export class AuthService {
  constructor(
    private prisma: PrismaService,
    private jwtService: JwtService,
  ) {}

  // ── REGISTER ──────────────────────────────
  async register(dto: RegisterDto) {
    // 1. Check if email already exists
    const existingUser = await this.prisma.user.findUnique({
      where: { email: dto.email },
    });
    if (existingUser) {
      throw new BadRequestException('Email already registered');
    }

    // 2. Check if username already exists
    const existingUsername = await this.prisma.user.findUnique({
      where: { username: dto.username },
    });
    if (existingUsername) {
      throw new BadRequestException('Username already taken');
    }

    // 3. Hash the password (never store plain text!)
    const hashedPassword = await bcrypt.hash(dto.password, 10);

    // 4. Create user in database
    const user = await this.prisma.user.create({
      data: {
        email: dto.email,
        username: dto.username,
        password: hashedPassword,
      },
    });

    // 5. Give new user dummy balances (USDT + BTC + ETH)
    await this.prisma.balance.createMany({
      data: [
        { userId: user.id, currency: 'USDT', available: 50000 },
        { userId: user.id, currency: 'BTC', available: 1 },
        { userId: user.id, currency: 'ETH', available: 10 },
      ],
    });

    // 6. Generate JWT token
    const token = this.generateToken(user.id, user.email);

    return {
      message: 'Registration successful',
      token,
      user: {
        id: user.id,
        email: user.email,
        username: user.username,
      },
    };
  }

  // ── LOGIN ─────────────────────────────────
  async login(dto: LoginDto) {
    // 1. Find user by email
    const user = await this.prisma.user.findUnique({
      where: { email: dto.email },
    });
    if (!user) {
      throw new UnauthorizedException('Invalid email or password');
    }

    // 2. Compare password with hashed version
    const passwordMatch = await bcrypt.compare(dto.password, user.password);
    if (!passwordMatch) {
      throw new UnauthorizedException('Invalid email or password');
    }

    // 3. Generate JWT token
    const token = this.generateToken(user.id, user.email);

    return {
      message: 'Login successful',
      token,
      user: {
        id: user.id,
        email: user.email,
        username: user.username,
      },
    };
  }

  // ── HELPER: Generate JWT ──────────────────
  private generateToken(userId: string, email: string) {
    return this.jwtService.sign({ sub: userId, email });
  }
}
