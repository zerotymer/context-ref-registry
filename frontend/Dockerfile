# syntax=docker/dockerfile:1
#
# Package sources come from the builder's own npm config (registry + auth),
# mounted as a BuildKit secret so it never lands in an image layer:
#   docker build --secret id=npmrc,src=$HOME/.npmrc ./frontend

FROM node:20-alpine AS base

FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml* ./
# pnpm is installed with npm (not corepack) so it also honors the mounted .npmrc.
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm install -g --no-fund --no-audit pnpm@10.33.0 \
    && pnpm install --frozen-lockfile

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
