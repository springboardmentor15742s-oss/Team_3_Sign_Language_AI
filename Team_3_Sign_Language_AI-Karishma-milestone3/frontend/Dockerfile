# --- build stage ---
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
# react-scripts@5.0.1 (unmaintained since 2022) declares a peer on
# typescript ^3.2.1||^4; package.json's "overrides" field forces the real
# ^5.9.3 through that stale declaration via npm's normal resolver.
RUN npm ci

COPY . .
RUN npm run build

# --- serve stage ---
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
