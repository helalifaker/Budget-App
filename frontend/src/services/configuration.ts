import { apiRequest } from '@/lib/api-client'
import { Level, NationalityType } from '@/types/api'

export const configurationApi = {
  levels: {
    getAll: async () => {
      return apiRequest<Level[]>({
        method: 'GET',
        url: '/configuration/levels',
      })
    },

    getById: async (id: string) => {
      return apiRequest<Level>({
        method: 'GET',
        url: `/configuration/levels/${id}`,
      })
    },

    getByCycle: async (cycleId: string) => {
      return apiRequest<Level[]>({
        method: 'GET',
        url: `/configuration/levels/cycle/${cycleId}`,
      })
    },
  },

  nationalityTypes: {
    getAll: async () => {
      return apiRequest<NationalityType[]>({
        method: 'GET',
        url: '/configuration/nationality-types',
      })
    },

    getById: async (id: string) => {
      return apiRequest<NationalityType>({
        method: 'GET',
        url: `/configuration/nationality-types/${id}`,
      })
    },
  },

  cycles: {
    getAll: async () => {
      return apiRequest<{ id: string; code: string; name: string }[]>({
        method: 'GET',
        url: '/configuration/cycles',
      })
    },
  },
}
