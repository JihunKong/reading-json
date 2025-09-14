# Frontend Dockerfile with multi-stage build
# Stage 1: Development
FROM node:18-alpine AS development

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Expose port for development server
EXPOSE 3000

# Development command
CMD ["npm", "start"]

# Stage 2: Build
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Stage 3: Production
FROM nginx:alpine AS production

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]