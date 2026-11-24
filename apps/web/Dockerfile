FROM node:20-alpine
WORKDIR /app
COPY apps/web/package.json ./package.json
RUN npm install --no-audit --no-fund
COPY apps/web/ ./
ENV NEXT_TELEMETRY_DISABLED=1
EXPOSE 3000
CMD ["npm", "run", "dev"]
