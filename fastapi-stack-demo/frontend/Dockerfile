# Сборка: docker build --build-arg VITE_API_BASE_URL=/api -t fastapi-demo-frontend frontend
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Без явного значения сборка падает, а не подхватывает случайный .env разработчика
ARG VITE_API_BASE_URL
RUN test -n "$VITE_API_BASE_URL" || (echo "ERROR: передай --build-arg VITE_API_BASE_URL=..." && exit 1)
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
