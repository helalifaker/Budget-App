import { useQuery } from '@tanstack/react-query'
import { configurationApi } from '@/services/configuration'

export const configurationKeys = {
  all: ['configuration'] as const,
  levels: () => [...configurationKeys.all, 'levels'] as const,
  level: (id: string) => [...configurationKeys.levels(), id] as const,
  levelsByCycle: (cycleId: string) => [...configurationKeys.levels(), 'cycle', cycleId] as const,
  nationalityTypes: () => [...configurationKeys.all, 'nationality-types'] as const,
  nationalityType: (id: string) => [...configurationKeys.nationalityTypes(), id] as const,
  cycles: () => [...configurationKeys.all, 'cycles'] as const,
}

export function useLevels() {
  return useQuery({
    queryKey: configurationKeys.levels(),
    queryFn: () => configurationApi.levels.getAll(),
    staleTime: 30 * 60 * 1000, // 30 minutes - configuration data changes rarely
  })
}

export function useLevel(id: string) {
  return useQuery({
    queryKey: configurationKeys.level(id),
    queryFn: () => configurationApi.levels.getById(id),
    enabled: !!id,
    staleTime: 30 * 60 * 1000,
  })
}

export function useLevelsByCycle(cycleId: string) {
  return useQuery({
    queryKey: configurationKeys.levelsByCycle(cycleId),
    queryFn: () => configurationApi.levels.getByCycle(cycleId),
    enabled: !!cycleId,
    staleTime: 30 * 60 * 1000,
  })
}

export function useNationalityTypes() {
  return useQuery({
    queryKey: configurationKeys.nationalityTypes(),
    queryFn: () => configurationApi.nationalityTypes.getAll(),
    staleTime: 30 * 60 * 1000,
  })
}

export function useNationalityType(id: string) {
  return useQuery({
    queryKey: configurationKeys.nationalityType(id),
    queryFn: () => configurationApi.nationalityTypes.getById(id),
    enabled: !!id,
    staleTime: 30 * 60 * 1000,
  })
}

export function useCycles() {
  return useQuery({
    queryKey: configurationKeys.cycles(),
    queryFn: () => configurationApi.cycles.getAll(),
    staleTime: 30 * 60 * 1000,
  })
}
