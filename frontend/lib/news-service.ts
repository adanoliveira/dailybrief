import apiService from "./api-service"

export interface Article {
  id: string
  title: string
  description: string
  content: string
  url: string
  urlToImage?: string
  publishedAt: string
  source: {
    id?: string
    name: string
  }
  category?: string
  abstract?: string
}

export interface NewsResponse {
  articles: Article[]
  totalResults: number
}

export interface UserPreferences {
  topics: string[]
  region: string
  publishers: string[]
  languages: string[]
}

export interface DigestArticle extends Article {
  summary: string
}

export interface Digest {
  id: string
  date: string
  articles: DigestArticle[]
  categories: {
    [category: string]: DigestArticle[]
  }
}

class NewsService {
  private static instance: NewsService

  private constructor() {}

  public static getInstance(): NewsService {
    if (!NewsService.instance) {
      NewsService.instance = new NewsService()
    }
    return NewsService.instance
  }

  public async getTopHeadlines(params?: {
    category?: string
    country?: string
    q?: string
    pageSize?: number
    page?: number
  }): Promise<NewsResponse> {
    const response = await apiService.get<NewsResponse>("/news/top-headlines", params as Record<string, string>)

    if (response.error) {
      throw new Error(response.error)
    }

    return response.data!
  }

  public async getPersonalizedFeed(params?: {
    category?: string
    pageSize?: number
    page?: number
  }): Promise<NewsResponse> {
    const response = await apiService.get<NewsResponse>("/news/personalized", params as Record<string, string>)

    if (response.error) {
      throw new Error(response.error)
    }

    return response.data!
  }

  public async getArticle(id: string): Promise<Article> {
    const response = await apiService.get<Article>(`/news/articles/${id}`)

    if (response.error) {
      throw new Error(response.error)
    }

    return response.data!
  }

  public async getLatestDigest(): Promise<Digest> {
    const response = await apiService.get<Digest>("/news/digest/latest")

    if (response.error) {
      throw new Error(response.error)
    }

    return response.data!
  }

  public async getDigestArchive(): Promise<Digest[]> {
    const response = await apiService.get<Digest[]>("/news/digest/archive")

    if (response.error) {
      throw new Error(response.error)
    }

    return response.data!
  }

  public async getUserPreferences(): Promise<UserPreferences> {
    const response = await apiService.get<UserPreferences>("/user/preferences")

    if (response.error) {
      throw new Error(response.error)
    }

    return response.data!
  }

  public async updateUserPreferences(preferences: Partial<UserPreferences>): Promise<UserPreferences> {
    const response = await apiService.put<UserPreferences>("/user/preferences", preferences)

    if (response.error) {
      throw new Error(response.error)
    }

    return response.data!
  }

  // For offline support
  public async saveArticleOffline(article: Article): Promise<void> {
    if (typeof window === "undefined") return

    const savedArticles = this.getSavedArticles()
    const exists = savedArticles.some((a) => a.id === article.id)

    if (!exists) {
      savedArticles.push(article)
      localStorage.setItem("saved_articles", JSON.stringify(savedArticles))
    }
  }

  public getSavedArticles(): Article[] {
    if (typeof window === "undefined") return []

    const saved = localStorage.getItem("saved_articles")
    return saved ? JSON.parse(saved) : []
  }

  public removeSavedArticle(id: string): void {
    if (typeof window === "undefined") return

    const savedArticles = this.getSavedArticles()
    const filtered = savedArticles.filter((a) => a.id !== id)
    localStorage.setItem("saved_articles", JSON.stringify(filtered))
  }
}

export default NewsService.getInstance()
