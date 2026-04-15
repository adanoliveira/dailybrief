import apiClient from './api-client'

export interface Topic {
  id: string
  name: string
  slug: string
}

export interface Region {
  id: string
  name: string
  code: string
}

export interface Language {
  id: string
  name: string
  iso_code: string
}

export interface Publication {
  id: string
  name: string
  description: string
  website_url: string
  logo_url?: string
  news_api_id: string
  authority?: number
  topics?: Topic[]
  regions?: Region[]
  languages?: Language[]
}

export interface ReferenceData {
  topics: Topic[]
  regions: Region[]
  languages: Language[]
  publications: Publication[]
}

export async function getReferenceData(): Promise<ReferenceData> {
  return apiClient.get<ReferenceData>('/feeds/basic-data/')
}

export async function getTopics(): Promise<Topic[]> {
  return apiClient.get<Topic[]>('/feeds/topics/')
}

export async function getRegions(): Promise<Region[]> {
  return apiClient.get<Region[]>('/feeds/regions/')
}

export async function getLanguages(): Promise<Language[]> {
  return apiClient.get<Language[]>('/feeds/languages/')
}

export async function getPublications(): Promise<Publication[]> {
  return apiClient.get<Publication[]>('/feeds/publications/')
}
