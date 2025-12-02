import { toast } from 'sonner'
import { AxiosError } from 'axios'
import {
  isAPIError,
  isUnauthorizedError,
  isForbiddenError,
  isNotFoundError,
  isValidationError,
} from './errors'

/**
 * Standardized toast messages for EFIR Budget App
 * All messages in French for consistency with EFIR requirements
 *
 * Usage:
 * - Import the functions you need from this module
 * - Call them directly to show toast notifications
 * - Use handleAPIErrorToast for automatic error handling in mutations
 */

export const toastMessages = {
  // Success messages
  success: {
    saved: () => toast.success('Sauvegardé avec succès'),
    created: (entity: string) => toast.success(`${entity} créé avec succès`),
    updated: (entity: string) => toast.success(`${entity} mis à jour avec succès`),
    deleted: (entity: string) => toast.success(`${entity} supprimé avec succès`),
    imported: (count: number) =>
      toast.success(
        `${count} enregistrement${count > 1 ? 's' : ''} importé${count > 1 ? 's' : ''}`
      ),
    exported: () => toast.success('Export terminé avec succès'),
    calculated: () => toast.success('Calcul terminé avec succès'),
    submitted: () => toast.success('Soumis avec succès'),
    approved: () => toast.success('Approuvé avec succès'),
    cloned: () => toast.success('Copie créée avec succès'),
  },

  // Error messages
  error: {
    generic: () => toast.error('Une erreur est survenue'),
    network: () => toast.error('Erreur réseau - Vérifiez votre connexion'),
    auth: () => toast.error('Session expirée - Veuillez vous reconnecter'),
    forbidden: () => toast.error("Vous n'avez pas les permissions nécessaires"),
    notFound: (entity: string) => toast.error(`${entity} introuvable`),
    validation: (message: string) => toast.error(`Validation échouée: ${message}`),
    conflict: (message: string) => toast.error(`Conflit: ${message}`),
    serverError: () => toast.error('Erreur serveur - Réessayez plus tard'),
    custom: (message: string) => toast.error(message),
  },

  // Info messages
  info: {
    loading: (action: string) => toast.loading(action),
    processing: () => toast.loading('Traitement en cours...'),
    calculating: () => toast.loading('Calcul en cours...'),
    saving: () => toast.loading('Sauvegarde en cours...'),
    importing: () => toast.loading('Importation en cours...'),
    exporting: () => toast.loading('Export en cours...'),
  },

  // Warning messages
  warning: {
    unsavedChanges: () => toast.warning('Modifications non sauvegardées'),
    dataLoss: () => toast.warning('Attention: Cette action est irréversible'),
    largeDataset: () => toast.warning('Données volumineuses - Le traitement peut prendre du temps'),
    selectVersion: () => toast.warning('Veuillez sélectionner une version budgétaire'),
  },
}

/**
 * Handle API errors with appropriate toast messages
 * Automatically determines the error type and shows the correct toast
 *
 * @param error - The error object from a mutation or API call
 * @param customMessage - Optional custom message to override default
 *
 * @example
 * ```typescript
 * useMutation({
 *   mutationFn: api.create,
 *   onError: (error) => handleAPIErrorToast(error)
 * })
 * ```
 */
export function handleAPIErrorToast(error: unknown, customMessage?: string) {
  // Use custom message if provided
  if (customMessage) {
    toast.error(customMessage)
    return
  }

  // Handle network errors (no response from server)
  if (isAPIError(error) && !error.response) {
    toastMessages.error.network()
    return
  }

  // Handle authentication errors
  if (isUnauthorizedError(error)) {
    toastMessages.error.auth()
    return
  }

  // Handle permission errors
  if (isForbiddenError(error)) {
    toastMessages.error.forbidden()
    return
  }

  // Handle not found errors
  if (isNotFoundError(error)) {
    toastMessages.error.notFound('Ressource')
    return
  }

  // Handle validation errors (422)
  if (isValidationError(error)) {
    const axiosError = error as AxiosError<{ detail?: string }>
    const detail = axiosError.response?.data?.detail
    if (detail) {
      toastMessages.error.validation(detail)
    } else {
      toastMessages.error.validation('Données invalides')
    }
    return
  }

  // Handle conflict errors (409)
  if (isAPIError(error) && error.response?.status === 409) {
    const detail = (error.response?.data as { detail?: string })?.detail
    if (detail) {
      toastMessages.error.conflict(detail)
    } else {
      toastMessages.error.conflict('La ressource existe déjà')
    }
    return
  }

  // Handle server errors (500+)
  if (isAPIError(error) && error.response && error.response.status >= 500) {
    toastMessages.error.serverError()
    return
  }

  // Handle generic error with message
  if (error instanceof Error) {
    toast.error(error.message || 'Erreur inconnue')
    return
  }

  // Fallback to generic error
  toastMessages.error.generic()
}

/**
 * Entity names in French for toast messages
 * Centralized to ensure consistency across the application
 */
export const entityNames = {
  budgetVersion: 'Version budgétaire',
  enrollment: 'Effectif',
  classStructure: 'Structure de classe',
  dhg: 'DHG',
  revenue: 'Revenu',
  cost: 'Coût',
  capex: 'CapEx',
  kpi: 'Indicateur',
  strategicPlan: 'Plan stratégique',
  configuration: 'Configuration',
  level: 'Niveau',
  nationalityType: 'Type de nationalité',
  subject: 'Matière',
  teacher: 'Enseignant',
  feeStructure: 'Structure tarifaire',
}
