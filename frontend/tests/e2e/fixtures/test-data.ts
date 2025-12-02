/**
 * E2E Test Fixtures - Reusable Test Data
 * Centralized test data for consistent E2E testing across all test suites
 */

export const TEST_USERS = {
  admin: {
    email: 'admin@efir.local',
    password: 'password123',
    role: 'Admin',
  },
  manager: {
    email: 'manager@efir.local',
    password: 'password123',
    role: 'Finance Director',
  },
  user: {
    email: 'user@efir.local',
    password: 'password123',
    role: 'Viewer',
  },
  hr: {
    email: 'hr@efir.local',
    password: 'password123',
    role: 'HR',
  },
  academic: {
    email: 'academic@efir.local',
    password: 'password123',
    role: 'Academic',
  },
} as const

export const TEST_BUDGET_VERSION = {
  name: `E2E Test Budget ${Date.now()}`,
  fiscal_year: '2025',
  academic_year: '2024-2025',
  description: 'Automated E2E test budget version',
  status: 'WORKING',
}

export const TEST_ENROLLMENT_DATA = {
  maternelle: {
    PS: { French: 20, Saudi: 5, Other: 3 },
    MS: { French: 22, Saudi: 6, Other: 4 },
    GS: { French: 24, Saudi: 7, Other: 5 },
  },
  elementaire: {
    CP: { French: 25, Saudi: 8, Other: 6 },
    CE1: { French: 26, Saudi: 8, Other: 7 },
    CE2: { French: 27, Saudi: 9, Other: 7 },
    CM1: { French: 28, Saudi: 9, Other: 8 },
    CM2: { French: 28, Saudi: 10, Other: 8 },
  },
  college: {
    '6ème': { French: 90, Saudi: 25, Other: 15 },
    '5ème': { French: 88, Saudi: 24, Other: 14 },
    '4ème': { French: 85, Saudi: 23, Other: 13 },
    '3ème': { French: 82, Saudi: 22, Other: 12 },
  },
  lycee: {
    '2nde': { French: 75, Saudi: 20, Other: 10 },
    '1ère': { French: 72, Saudi: 19, Other: 9 },
    Terminale: { French: 70, Saudi: 18, Other: 8 },
  },
}

export const TEST_CLASS_STRUCTURE_PARAMS = {
  maternelle: {
    min_class_size: 18,
    target_class_size: 22,
    max_class_size: 25,
    atsem_required: true,
  },
  elementaire: {
    min_class_size: 20,
    target_class_size: 24,
    max_class_size: 28,
    atsem_required: false,
  },
  college: {
    min_class_size: 25,
    target_class_size: 28,
    max_class_size: 32,
    atsem_required: false,
  },
  lycee: {
    min_class_size: 25,
    target_class_size: 30,
    max_class_size: 35,
    atsem_required: false,
  },
}

export const TEST_SUBJECT_HOURS = {
  college: {
    '6ème': {
      Mathématiques: 4.5,
      Français: 4.5,
      'Histoire-Géographie': 3.0,
      LV1: 4.0,
      SVT: 1.5,
      'Physique-Chimie': 1.5,
      Technologie: 1.5,
      'Arts Plastiques': 1.0,
      'Éducation Musicale': 1.0,
      EPS: 4.0,
    },
    '5ème': {
      Mathématiques: 3.5,
      Français: 4.5,
      'Histoire-Géographie': 3.0,
      LV1: 3.0,
      LV2: 2.5,
      SVT: 1.5,
      'Physique-Chimie': 1.5,
      Technologie: 1.5,
      'Arts Plastiques': 1.0,
      'Éducation Musicale': 1.0,
      EPS: 3.0,
    },
  },
  lycee: {
    '2nde': {
      Mathématiques: 4.0,
      Français: 4.0,
      'Histoire-Géographie': 3.0,
      LV1: 2.5,
      LV2: 2.0,
      SVT: 1.5,
      'Physique-Chimie': 3.0,
      SES: 1.5,
      EPS: 2.0,
    },
  },
}

export const TEST_DHG_CONSTANTS = {
  primary_standard_hours: 24,
  secondary_standard_hours: 18,
  max_hsa_hours: 4,
  prrd_cost_eur: 41863,
  eur_to_sar_rate: 4.5,
}

export const TEST_TEACHER_COSTS = {
  aefe_detached: {
    prrd_eur: 41863,
    social_charges_percent: 0,
    currency: 'EUR',
  },
  local_certified: {
    annual_salary_sar: 180000,
    social_charges_percent: 0.21,
    currency: 'SAR',
  },
  local_contractual: {
    annual_salary_sar: 120000,
    social_charges_percent: 0.21,
    currency: 'SAR',
  },
}

export const TEST_FEE_STRUCTURE = {
  tuition: {
    French: {
      Maternelle: 28500, // SAR per year
      Élémentaire: 32000,
      Collège: 36000,
      Lycée: 40000,
    },
    Saudi: {
      Maternelle: 24000,
      Élémentaire: 27000,
      Collège: 30000,
      Lycée: 33000,
    },
    Other: {
      Maternelle: 28500,
      Élémentaire: 32000,
      Collège: 36000,
      Lycée: 40000,
    },
  },
  registration: {
    all: 2500, // SAR, same for all nationalities
  },
  dai: {
    all: 1500, // SAR, annual enrollment fee
  },
}

export const TEST_REVENUE_DISTRIBUTION = {
  T1: 0.4, // 40% in Trimester 1
  T2: 0.3, // 30% in Trimester 2
  T3: 0.3, // 30% in Trimester 3
}

export const TEST_ACCOUNT_CODES = {
  revenue: {
    tuition_t1: '70110',
    tuition_t2: '70120',
    tuition_t3: '70130',
    registration: '70200',
    cafeteria: '70300',
    transport: '70400',
  },
  expenses: {
    teaching_salaries: '64110',
    admin_salaries: '64120',
    support_salaries: '64130',
    social_charges: '64500',
    rent: '61300',
    utilities: '61400',
    supplies: '60600',
    maintenance: '61500',
  },
}

export const TEST_KPI_TARGETS = {
  enrollment_capacity_percent: 85, // Target 85% capacity utilization
  h_e_ratio_college: 1.25, // Target 1.25 hours per student for collège
  h_e_ratio_lycee: 1.35, // Target 1.35 hours per student for lycée
  e_d_ratio: 28, // Target 28 students per class
  operating_margin_percent: 5, // Target 5% operating margin
  teacher_retention_percent: 90, // Target 90% teacher retention
}

/**
 * Helper function to generate unique test budget version name
 */
export function generateTestBudgetName(prefix: string = 'E2E Test'): string {
  return `${prefix} ${Date.now()}-${Math.floor(Math.random() * 1000)}`
}

/**
 * Helper function to calculate expected class count
 */
export function calculateExpectedClasses(studentCount: number, targetClassSize: number): number {
  return Math.ceil(studentCount / targetClassSize)
}

/**
 * Helper function to calculate expected DHG FTE
 */
export function calculateExpectedFTE(totalHours: number, standardHours: number = 18): number {
  return totalHours / standardHours
}

/**
 * Helper function to wait for element with retry
 */
export function getRetryDelay(attempt: number): number {
  return Math.min(1000 * Math.pow(2, attempt), 5000) // Exponential backoff, max 5s
}
