# ==============================================================================
# AnalyzaX Frontend — Production Multi-Stage Dockerfile (Vite / Nitro)
# ==============================================================================

FROM node:22-alpine AS builder
WORKDIR /app

RUN apk add --no-cache libc6-compat

COPY package.json ./
RUN npm install

COPY . .

ENV NODE_ENV=production

RUN npm run build

# ------------------------------------------------------------------------------
# Production Runtime (Non-Root User)
# ------------------------------------------------------------------------------
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0

RUN addgroup --system --gid 10001 nodejs && \
    adduser --system --uid 10001 analyzax

COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/.output ./.output
COPY --from=builder /app/public ./public

USER analyzax:nodejs

EXPOSE 3000

HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "3000"]
