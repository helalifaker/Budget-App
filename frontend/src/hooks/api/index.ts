// Versions (with backward compatibility aliases)
export {
  useVersions,
  useVersionById,
  useCreateVersion,
  useUpdateVersion,
  useDeleteVersion,
  useSubmitVersion,
  useApproveVersion,
  useCloneVersion,
  useRejectVersion,
  useSupersedeVersion,
  versionKeys,
  // Backward compatibility aliases
  useBudgetVersions,
  useBudgetVersion,
  useCreateBudgetVersion,
  useUpdateBudgetVersion,
  useDeleteBudgetVersion,
  useSubmitBudgetVersion,
  useApproveBudgetVersion,
  useCloneBudgetVersion,
  useRejectBudgetVersion,
  useSupersedeBudgetVersion,
  budgetVersionKeys,
} from './useVersions'

// Enrollment
export {
  useEnrollments,
  useCreateEnrollment,
  useUpdateEnrollment,
  useDeleteEnrollment,
  useEnrollmentSummary,
  useProjectEnrollment,
  enrollmentKeys,
} from './useEnrollment'

// Class Structure
export {
  useClassStructures,
  useUpdateClassStructure,
  useCalculateClassStructure,
  classStructureKeys,
} from './useClassStructure'

// Configuration
export {
  useLevels,
  useLevel,
  useLevelsByCycle,
  useNationalityTypes,
  useNationalityType,
  useCycles,
  useClassSizeParams,
  useUpdateClassSizeParam,
  useSubjects,
  useSubjectHours,
  useUpdateSubjectHours,
  useTeacherCategories,
  useTeacherCosts,
  useUpdateTeacherCost,
  useFeeCategories,
  useFeeStructure,
  useUpdateFeeStructure,
  configurationKeys,
} from './useConfiguration'
