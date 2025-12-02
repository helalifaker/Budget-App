import { describe, it, expect, vi, beforeEach } from 'vitest'
import { toast } from 'sonner'
import { toastMessages, handleAPIErrorToast, entityNames } from '../toast-messages'
import { AxiosError, type AxiosResponse } from 'axios'

// Mock sonner
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    loading: vi.fn(),
  },
}))

function createMockResponse(status: number, data?: { detail?: string }): Partial<AxiosResponse> {
  return { status, data } as Partial<AxiosResponse>
}

describe('toast-messages', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('toastMessages.success', () => {
    it('should show saved message', () => {
      toastMessages.success.saved()
      expect(toast.success).toHaveBeenCalledWith('Sauvegardé avec succès')
    })

    it('should show created message with entity', () => {
      toastMessages.success.created('Test Entity')
      expect(toast.success).toHaveBeenCalledWith('Test Entity créé avec succès')
    })

    it('should show updated message with entity', () => {
      toastMessages.success.updated('Test Entity')
      expect(toast.success).toHaveBeenCalledWith('Test Entity mis à jour avec succès')
    })

    it('should show deleted message with entity', () => {
      toastMessages.success.deleted('Test Entity')
      expect(toast.success).toHaveBeenCalledWith('Test Entity supprimé avec succès')
    })

    it('should show imported message with count (singular)', () => {
      toastMessages.success.imported(1)
      expect(toast.success).toHaveBeenCalledWith('1 enregistrement importé')
    })

    it('should show imported message with count (plural)', () => {
      toastMessages.success.imported(5)
      expect(toast.success).toHaveBeenCalledWith('5 enregistrements importés')
    })

    it('should show calculated message', () => {
      toastMessages.success.calculated()
      expect(toast.success).toHaveBeenCalledWith('Calcul terminé avec succès')
    })

    it('should show submitted message', () => {
      toastMessages.success.submitted()
      expect(toast.success).toHaveBeenCalledWith('Soumis avec succès')
    })

    it('should show approved message', () => {
      toastMessages.success.approved()
      expect(toast.success).toHaveBeenCalledWith('Approuvé avec succès')
    })

    it('should show cloned message', () => {
      toastMessages.success.cloned()
      expect(toast.success).toHaveBeenCalledWith('Copie créée avec succès')
    })
  })

  describe('toastMessages.error', () => {
    it('should show generic error', () => {
      toastMessages.error.generic()
      expect(toast.error).toHaveBeenCalledWith('Une erreur est survenue')
    })

    it('should show network error', () => {
      toastMessages.error.network()
      expect(toast.error).toHaveBeenCalledWith('Erreur réseau - Vérifiez votre connexion')
    })

    it('should show auth error', () => {
      toastMessages.error.auth()
      expect(toast.error).toHaveBeenCalledWith('Session expirée - Veuillez vous reconnecter')
    })

    it('should show forbidden error', () => {
      toastMessages.error.forbidden()
      expect(toast.error).toHaveBeenCalledWith("Vous n'avez pas les permissions nécessaires")
    })

    it('should show not found error with entity', () => {
      toastMessages.error.notFound('Test Entity')
      expect(toast.error).toHaveBeenCalledWith('Test Entity introuvable')
    })

    it('should show validation error with message', () => {
      toastMessages.error.validation('Invalid field')
      expect(toast.error).toHaveBeenCalledWith('Validation échouée: Invalid field')
    })

    it('should show server error', () => {
      toastMessages.error.serverError()
      expect(toast.error).toHaveBeenCalledWith('Erreur serveur - Réessayez plus tard')
    })
  })

  describe('toastMessages.warning', () => {
    it('should show select version warning', () => {
      toastMessages.warning.selectVersion()
      expect(toast.warning).toHaveBeenCalledWith('Veuillez sélectionner une version budgétaire')
    })

    it('should show unsaved changes warning', () => {
      toastMessages.warning.unsavedChanges()
      expect(toast.warning).toHaveBeenCalledWith('Modifications non sauvegardées')
    })
  })

  describe('handleAPIErrorToast', () => {
    it('should show custom message when provided', () => {
      handleAPIErrorToast(new Error('Test'), 'Custom message')
      expect(toast.error).toHaveBeenCalledWith('Custom message')
    })

    it('should show network error for AxiosError without response', () => {
      const error = new AxiosError('Network Error')
      error.response = undefined
      handleAPIErrorToast(error)
      expect(toast.error).toHaveBeenCalledWith('Erreur réseau - Vérifiez votre connexion')
    })

    it('should show auth error for 401', () => {
      const error = new AxiosError('Unauthorized')
      error.response = createMockResponse(401) as AxiosResponse
      handleAPIErrorToast(error)
      expect(toast.error).toHaveBeenCalledWith('Session expirée - Veuillez vous reconnecter')
    })

    it('should show forbidden error for 403', () => {
      const error = new AxiosError('Forbidden')
      error.response = createMockResponse(403) as AxiosResponse
      handleAPIErrorToast(error)
      expect(toast.error).toHaveBeenCalledWith("Vous n'avez pas les permissions nécessaires")
    })

    it('should show not found error for 404', () => {
      const error = new AxiosError('Not Found')
      error.response = createMockResponse(404) as AxiosResponse
      handleAPIErrorToast(error)
      expect(toast.error).toHaveBeenCalledWith('Ressource introuvable')
    })

    it('should show validation error for 422', () => {
      const error = new AxiosError('Validation Error')
      error.response = createMockResponse(422, { detail: 'Invalid data' }) as AxiosResponse
      handleAPIErrorToast(error)
      expect(toast.error).toHaveBeenCalledWith('Validation échouée: Invalid data')
    })

    it('should show server error for 500', () => {
      const error = new AxiosError('Server Error')
      error.response = createMockResponse(500) as AxiosResponse
      handleAPIErrorToast(error)
      expect(toast.error).toHaveBeenCalledWith('Erreur serveur - Réessayez plus tard')
    })

    it('should show error message for generic Error', () => {
      const error = new Error('Something went wrong')
      handleAPIErrorToast(error)
      expect(toast.error).toHaveBeenCalledWith('Something went wrong')
    })

    it('should show generic error for unknown error type', () => {
      handleAPIErrorToast('unknown error')
      expect(toast.error).toHaveBeenCalledWith('Une erreur est survenue')
    })
  })

  describe('entityNames', () => {
    it('should have French entity names', () => {
      expect(entityNames.budgetVersion).toBe('Version budgétaire')
      expect(entityNames.enrollment).toBe('Effectif')
      expect(entityNames.classStructure).toBe('Structure de classe')
      expect(entityNames.strategicPlan).toBe('Plan stratégique')
    })
  })
})
