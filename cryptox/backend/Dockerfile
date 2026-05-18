# ============================================
# STAGE 1: Builder — compile NestJS app and
# install dependencies
# ============================================
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npx prisma generate
RUN npm run build

# Prune devDependencies to keep production node_modules extremely slim (~80MB instead of ~519MB!)
RUN npm prune --omit=dev

# ============================================
# STAGE 2: Production — lightweight runner
# ============================================
FROM node:20-alpine

WORKDIR /app

# Copy compiled application code and slim production dependencies from builder
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/prisma ./prisma
COPY package*.json ./

EXPOSE 3001
CMD ["node", "dist/main"]