import type { HoopData, UpcomingGame, PastGame, Team, TeamDetails } from '../types'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// базовая функция для всех запросов
async function fetcher<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`)

  if (!response.ok) {
    throw new Error(`Ошибка ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

// ── Матчи ──────────────────────────────────────────

// все предстоящие матчи
export async function getUpcomingGames(): Promise<UpcomingGame[]> {
  return fetcher('/matches/upcoming')
}

// матчи сегодня
export async function getTodayGames(): Promise<UpcomingGame[]> {
  return fetcher('/matches/today')
}

// прошедшие матчи
export async function getPastGames(): Promise<PastGame[]> {
  return fetcher('/matches/past')
}

// один матч по id
export async function getMatch(id: string): Promise<UpcomingGame> {
  return fetcher(`/matches/${id}`)
}

// ── Команды ────────────────────────────────────────

// все команды
export async function getTeams(): Promise<Record<string, Team>> {
  return fetcher('/teams')
}

// детали одной команды
export async function getTeamDetails(abbr: string): Promise<TeamDetails> {
  return fetcher(`/tea