FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
COPY src/package*.json ./src/
RUN npm install

# Copy project files
COPY . .

# Expose port
EXPOSE 3000

# Set host for Next.js to listen on all interfaces
ENV NEXT_TELEMETRY_DISABLED 1
ENV HOST 0.0.0.0

# Start development server
CMD ["npm", "run", "dev"] 