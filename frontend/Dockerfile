# Node.js LTS base image
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application source code
COPY . .

# Expose port for Vite dev server
EXPOSE 3000

# Start Vite with host binding for Docker networking
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
