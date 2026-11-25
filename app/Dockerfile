# Loan EMI Calculator - simple Dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies first (better layer caching)
COPY package.json ./
RUN npm install --omit=dev

# Copy application code
COPY server.js ./
COPY public ./public

# Run as the built-in non-root "node" user
USER node

EXPOSE 3000
CMD ["node", "server.js"]
