import { Module } from '@nestjs/common';
import { PairsController } from './pairs.controller';
import { PairsService } from './pairs.service';

@Module({
  controllers: [PairsController],
  providers: [PairsService],
  exports: [PairsService],
})
export class PairsModule {}
