/**
 * Composable para gerenciar sessões de scraping
 */

import { useScraperApi, type ScraperSession } from '../services/api/scraper'

export function useScraperSession() {
  const { startScraper, getScraperResults } = useScraperApi()

  const isCreating = ref(false)
  const currentSession = ref<ScraperSession | null>(null)
  const error = ref<string | null>(null)

  /**
   * Gerar um novo session ID único
   */
  function generateSessionId(): string {
    return crypto.randomUUID()
  }

  /**
   * Criar nova sessão de scraping
   */
  async function createSession(searchTerm: string): Promise<string | null> {
    if (!searchTerm.trim()) {
      error.value = 'Termo de busca é obrigatório'
      return null
    }

    isCreating.value = true
    error.value = null

    try {
      const sessionId = generateSessionId()

      const response = await startScraper(sessionId, searchTerm.trim())

      if (response.error) {
        error.value = response.error
        return null
      }

      // Criar objeto da sessão
      currentSession.value = {
        id: sessionId,
        status: 'running',
        search_term: searchTerm.trim(),
        created_at: new Date().toISOString(),
      }

      return sessionId

    } catch (err) {
      console.error('Erro ao criar sessão:', err)
      error.value = 'Erro ao iniciar scraping'
      return null
    } finally {
      isCreating.value = false
    }
  }

  /**
   * Carregar dados de uma sessão existente
   */
  async function loadSession(sessionId: string): Promise<boolean> {
    try {
      const response = await getScraperResults(sessionId)

      if (response.error) {
        error.value = response.error
        return false
      }

      // Atualizar dados da sessão
      currentSession.value = {
        id: sessionId,
        status: response.data?.status || 'unknown',
        created_at: new Date().toISOString(), // TODO: pegar do backend
        results_count: response.data?.count || 0,
      }

      return true

    } catch (err) {
      console.error('Erro ao carregar sessão:', err)
      error.value = 'Erro ao carregar dados da sessão'
      return false
    }
  }

  /**
   * Limpar sessão atual
   */
  function clearSession() {
    currentSession.value = null
    error.value = null
  }

  return {
    isCreating: readonly(isCreating),
    currentSession: readonly(currentSession),
    error: readonly(error),
    generateSessionId,
    createSession,
    loadSession,
    clearSession,
  }
}
