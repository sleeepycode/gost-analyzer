# Frontend (DO-04)
# Multi-stage: Vite build → nginx
# Host port: 3000 → container :80 | Check: GET / → 200

FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html ./
COPY vite.config.ts tsconfig.json tsconfig.node.json ./
COPY tailwind.config.js postcss.config.js ./
COPY public ./public
COPY src ./src

# Пустой VITE_API_BASE_URL → same-origin; nginx проксирует API на backend (Compose)
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
