import { PrismaClient } from '../src/generated/prisma'

// Define a global object that can hold our PrismaClient instance
const globalForPrisma = global as unknown as { prisma: PrismaClient }

// Try to initialize Prisma safely with error handling
let prisma: PrismaClient

try {
  if (process.env.NODE_ENV === 'production') {
    // In production, create a new instance every time
    prisma = new PrismaClient({
      log: ['error'],
    })
  } else {
    // In development, reuse the same instance to avoid multiple connections
    if (!globalForPrisma.prisma) {
      globalForPrisma.prisma = new PrismaClient({
        log: ['query', 'error', 'warn'],
      })
    }
    prisma = globalForPrisma.prisma
  }
} catch (error) {
  console.error('Failed to initialize Prisma Client:', error)
  throw new Error('Database connection failed')
}

export { prisma } 