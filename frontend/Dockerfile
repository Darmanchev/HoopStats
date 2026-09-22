FROM node:22-alpine AS dependencies

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci


FROM dependencies AS development

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


FROM dependencies AS builder

COPY . .

ARG VITE_API_URL=/api
ARG VITE_DASHBOARD_REFRESH_MS=300000
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_DASHBOARD_REFRESH_MS=${VITE_DASHBOARD_REFRESH_MS}

RUN npm run build


FROM nginxinc/nginx-unprivileged:1.27-alpine AS production

USER root

ARG APP_HOST
COPY nginx.conf /tmp/default.conf.template
RUN test -n "${APP_HOST}" \
    && envsubst '${APP_HOST}' \
        < /tmp/default.conf.template \
        > /etc/nginx/conf.d/default.conf \
    && rm /tmp/default.conf.template

COPY --from=builder /app/dist /usr/share/nginx/html

USER 101

EXPOSE 8080
