FROM node:18-alpine AS base

# 1. Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Copy package.json and related files
COPY package.json ./

# Install dependencies with legacy peer deps flag
RUN npm install --legacy-peer-deps --frozen-lockfile --production=false

# 2. Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set build-time environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED 1

# Generate Prisma client
RUN npx prisma generate

# Build Next.js
RUN npm run build

# 3. Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

# Set runtime environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder /app/prisma ./prisma

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Ensure prisma client is regenerated at runtime
COPY docker-entrypoint.sh ./
RUN chmod +x ./docker-entrypoint.sh

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

ENTRYPOINT ["./docker-entrypoint.sh"]

# Start the server
CMD ["node", "server.js"] 