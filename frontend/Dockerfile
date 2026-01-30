FROM node:20-alpine AS builder

WORKDIR /app

# 依存関係のインストール
COPY package.json package-lock.json* ./
RUN npm ci

# アプリケーションコードのコピーとビルド
COPY . .
RUN npm run build

# 本番用イメージ
FROM nginx:alpine

# ビルド成果物をコピー
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx設定
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
