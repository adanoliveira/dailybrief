FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy the entire project
COPY . .

# Install dependencies
WORKDIR /app/src
RUN npm install --legacy-peer-deps
RUN npm install --save-dev typescript @types/react @types/node @types/react-dom --legacy-peer-deps

# Expose port
EXPOSE 3000

# Set host for Next.js to listen on all interfaces
ENV NEXT_TELEMETRY_DISABLED 1
ENV HOST 0.0.0.0

# Keep src as working directory
WORKDIR /app/src

# Start development server
CMD ["npm", "run", "dev"] 