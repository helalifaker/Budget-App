import { StepProgress } from '@/types/planning-progress'

interface HelpContentProps {
  stepId: StepProgress['step_id']
}

export function HelpContent({ stepId }: HelpContentProps) {
  const helpContent = getHelpContentForStep(stepId)

  return (
    <div className="prose prose-sm max-w-none">
      <div className="space-y-6">
        {/* What is this step? */}
        <section>
          <h4 className="text-base font-semibold text-text-primary mb-2">What is this step?</h4>
          <p className="text-text-secondary">{helpContent.overview}</p>
        </section>

        {/* Prerequisites */}
        <section>
          <h4 className="text-base font-semibold text-text-primary mb-2">Prerequisites</h4>
          <ul className="list-none space-y-1 text-text-secondary">
            {helpContent.prerequisites.map((prereq, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-success-600 mt-0.5">✓</span>
                <span>{prereq}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Instructions */}
        <section>
          <h4 className="text-base font-semibold text-text-primary mb-2">Instructions</h4>
          <ol className="list-decimal list-inside space-y-2 text-text-secondary">
            {helpContent.instructions.map((instruction, index) => (
              <li key={index}>{instruction}</li>
            ))}
          </ol>
        </section>

        {/* Business Rules */}
        <section>
          <h4 className="text-base font-semibold text-text-primary mb-2">Business Rules</h4>
          <ul className="list-none space-y-2 text-text-secondary">
            {helpContent.businessRules.map((rule, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-gold-600 mt-0.5">{rule.icon}</span>
                <div>
                  <strong>{rule.title}:</strong> {rule.description}
                </div>
              </li>
            ))}
          </ul>
        </section>

        {/* Expected Outcomes */}
        <section>
          <h4 className="text-base font-semibold text-text-primary mb-2">Expected Outcomes</h4>
          <p className="text-text-secondary mb-2">Once this step is complete:</p>
          <ul className="list-none space-y-1 text-text-secondary">
            {helpContent.outcomes.map((outcome, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-success-600 mt-0.5">✓</span>
                <span>{outcome}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Troubleshooting */}
        {helpContent.troubleshooting.length > 0 && (
          <section>
            <h4 className="text-base font-semibold text-text-primary mb-2">Troubleshooting</h4>
            <div className="space-y-3">
              {helpContent.troubleshooting.map((item, index) => (
                <details key={index} className="bg-subtle rounded-lg p-3">
                  <summary className="cursor-pointer text-sm font-medium text-text-secondary hover:text-text-primary">
                    ❓ {item.question}
                  </summary>
                  <p className="mt-2 text-sm text-text-secondary">{item.answer}</p>
                </details>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

// Help content for all 6 steps
function getHelpContentForStep(stepId: StepProgress['step_id']) {
  const content = {
    enrollment: {
      overview:
        'Project student enrollment by academic level and nationality type. This is the PRIMARY DRIVER for all downstream calculations - everything else depends on accurate enrollment data.',
      prerequisites: [
        'Budget version in "Draft" or "Working" state',
        'Academic levels configured in Configuration → Class Sizes',
        'Nationality types defined in system configuration',
      ],
      instructions: [
        'Select your budget version from the dropdown',
        'Click "Add Enrollment" button',
        'Choose academic level (e.g., CP, CE1, 6ème, etc.)',
        'Select nationality type (French, Saudi, Other)',
        'Enter projected student count for this combination',
        'Save and repeat for all level/nationality combinations',
        'Review capacity utilization percentage',
      ],
      businessRules: [
        {
          icon: '🎯',
          title: 'Capacity Limit',
          description:
            'Total enrollment must not exceed the configured school capacity (default 1,850 students)',
        },
        {
          icon: '📊',
          title: 'Minimum Recommended',
          description: 'At least 500 students for financial viability',
        },
        {
          icon: '🌍',
          title: 'Nationality Impact',
          description:
            'Different nationalities have different fee structures affecting revenue calculations',
        },
        {
          icon: '📈',
          title: 'Optimal Range',
          description: '1,000-1,700 students is considered optimal for operations',
        },
      ],
      outcomes: [
        'Class Structure can be calculated based on enrollment',
        'Revenue projections can be generated automatically',
        'Overall budget planning process is unlocked',
        'Enrollment statistics visible in dashboard',
      ],
      troubleshooting: [
        {
          question: 'Why does it say "Over capacity"?',
          answer:
            "Your total enrollment exceeds the school's configured maximum capacity (default 1,850 students). Reduce enrollment figures or adjust capacity parameters in projections.",
        },
        {
          question: 'Can I skip nationality types?',
          answer:
            'No - nationality type is required because it affects fee structures and revenue calculations. Make sure to enter enrollment for each nationality type at each academic level where students are enrolled.',
        },
        {
          question: 'How do I handle projected growth?',
          answer:
            'Use the "Calculate Projections" button to generate enrollment forecasts based on growth scenarios. You can apply conservative, moderate, or optimistic growth rates.',
        },
      ],
    },

    class_structure: {
      overview:
        'Calculate the number of classes needed based on enrollment and class size parameters. This determines how many classes will operate at each academic level.',
      prerequisites: [
        'Enrollment Planning must be completed',
        'Class size parameters configured (target, min, max per level)',
      ],
      instructions: [
        'Navigate to Class Structure page',
        'Click "Calculate from Enrollment" button',
        'System automatically creates class structure based on enrollment',
        'Review calculated number of classes and average class sizes',
        'Manually adjust if needed (override with specific values)',
        'Verify total students matches enrollment',
        'Check for ATSEM requirements (Maternelle classes)',
      ],
      businessRules: [
        {
          icon: '📏',
          title: 'Class Size Range',
          description: 'Classes must stay within configured min/max sizes (e.g., 20-30 students)',
        },
        {
          icon: '🎓',
          title: 'Calculation Method',
          description: 'Number of classes = ⌈Total Students ÷ Target Class Size⌉ (rounded up)',
        },
        {
          icon: '👶',
          title: 'ATSEM Requirement',
          description:
            'Maternelle (preschool) classes require 1 ATSEM (teaching assistant) per class',
        },
        {
          icon: '✓',
          title: 'Validation',
          description: 'Total students in classes must match enrollment (within 5% tolerance)',
        },
      ],
      outcomes: [
        'DHG Workforce Planning can proceed with class counts',
        'Teacher FTE requirements can be calculated',
        'Facility capacity requirements are defined',
        'ATSEM staffing needs are identified',
      ],
      troubleshooting: [
        {
          question: "Why doesn't the total match enrollment?",
          answer:
            'Check if you\'ve manually overridden class counts or sizes. The system expects: Number of Classes × Average Class Size = Total Students (within 5%). Use "Calculate from Enrollment" to reset to automatic calculation.',
        },
        {
          question: 'Can I have different class sizes per level?',
          answer:
            'Yes! Each academic level can have different average class sizes based on enrollment. The system calculates optimal class size while respecting configured min/max parameters.',
        },
      ],
    },

    dhg: {
      overview:
        'Calculate teacher FTE (Full-Time Equivalent) requirements using the French DHG (Dotation Horaire Globale) methodology. This determines how many teachers you need and identifies staffing gaps.',
      prerequisites: [
        'Class Structure must be completed',
        'Subject hours matrix configured (hours per subject per level)',
      ],
      instructions: [
        'Go to DHG Workforce Planning page',
        'Navigate to "Subject Hours" tab',
        'Click "Calculate FTE" to compute teaching hour requirements',
        'Review total hours per subject across all classes',
        'Switch to "Teacher FTE" tab to see FTE requirements',
        'Go to "TRMD" tab for gap analysis',
        'Enter AEFE (French positions) and Local staff allocations',
        'Review deficit/surplus analysis',
        'Use "HSA Planning" for overtime allocation if needed',
      ],
      businessRules: [
        {
          icon: '⏰',
          title: 'Standard Hours',
          description: 'Secondary teachers: 18 hours/week, Primary teachers: 24 hours/week',
        },
        {
          icon: '📐',
          title: 'FTE Calculation',
          description: 'FTE Required = Total Subject Hours ÷ Standard Hours',
        },
        {
          icon: '📊',
          title: 'TRMD Analysis',
          description: 'Besoins (Needs) - Moyens (Resources) = Deficit/Surplus',
        },
        {
          icon: '💼',
          title: 'HSA Limits',
          description: 'Overtime (HSA) limited to 2-4 hours per teacher per week',
        },
      ],
      outcomes: [
        'Teacher staffing requirements are defined',
        'AEFE position allocation is planned',
        'Local recruitment needs are identified',
        'Personnel cost calculations can proceed',
        'Staffing budget is established',
      ],
      troubleshooting: [
        {
          question: 'What is TRMD?',
          answer:
            'TRMD (Tableau de Répartition des Moyens par Discipline) is the gap analysis table showing Needs vs. Available resources. It helps identify staffing deficits that must be filled by recruitment or overtime.',
        },
        {
          question: 'How do I handle the deficit?',
          answer:
            'Deficits can be filled by: (1) AEFE detached positions (if available), (2) Local recruitment, or (3) HSA (overtime) up to 2-4 hours per teacher. Combine these strategies to close the gap.',
        },
      ],
    },

    revenue: {
      overview:
        'Project all revenue streams including tuition, enrollment fees, and other income. Revenue is automatically calculated from enrollment and fee structures.',
      prerequisites: ['Enrollment Planning must be completed', 'Fee structures configured'],
      instructions: [
        'Navigate to Revenue Planning page',
        'Click "Recalculate Revenue" to auto-generate from enrollment',
        'Review tuition revenue by nationality type',
        'Check enrollment/registration fees (new students only)',
        'Add other revenue sources (cafeteria, extracurricular, facilities)',
        'Review trimester allocation (T1: 40%, T2: 30%, T3: 30%)',
        'Verify account code mapping (70xxx revenue codes)',
        'Apply sibling discounts where applicable',
      ],
      businessRules: [
        {
          icon: '💰',
          title: 'Fee Structure',
          description: 'Different fees for French, Saudi, and Other nationalities',
        },
        {
          icon: '👨‍👩‍👧‍👦',
          title: 'Sibling Discount',
          description: '25% discount on tuition for 3rd+ child (not on registration/DAI)',
        },
        {
          icon: '📅',
          title: 'Trimester Recognition',
          description: 'T1 (40%), T2 (30%), T3 (30%) for cash flow planning',
        },
        {
          icon: '📊',
          title: 'Account Codes',
          description: 'Revenue uses PCG codes 70xxx-77xxx series',
        },
      ],
      outcomes: [
        'Total revenue projection is established',
        'Cash flow by trimester is planned',
        'Revenue budget is ready for consolidation',
        'Financial viability can be assessed',
      ],
      troubleshooting: [
        {
          question: 'Why is revenue lower than expected?',
          answer:
            'Check: (1) Enrollment counts are correct, (2) Fee structures are configured properly for each nationality, (3) Sibling discounts applied correctly. Revenue should be approximately 10,000+ SAR per student.',
        },
        {
          question: 'How are sibling discounts calculated?',
          answer:
            'The system automatically applies 25% discount on tuition fees for the 3rd child and beyond in the same family. This does NOT apply to DAI (enrollment fees) or registration fees.',
        },
      ],
    },

    costs: {
      overview:
        'Plan all operational costs including personnel (from DHG) and operating expenses. Personnel costs are automatically calculated from teacher FTE requirements.',
      prerequisites: [
        'DHG Workforce Planning must be completed (for personnel costs)',
        'Enrollment completed (for per-student operating costs)',
      ],
      instructions: [
        'Go to Cost Planning page',
        'Personnel Costs tab: Click "Recalculate Personnel Costs"',
        'Review salary costs by staff category (AEFE, Local, ATSEM)',
        'Verify social charges (42% of salaries)',
        'Check AEFE contribution costs (PRRD: ~41,863 EUR per teacher)',
        'Operating Costs tab: Enter supplies, utilities, services',
        'Use cost drivers (per student, per FTE) where applicable',
        'Allocate costs by period (P1, Summer, P2)',
      ],
      businessRules: [
        {
          icon: '👥',
          title: 'Personnel Costs',
          description: 'Typically 60-70% of total budget',
        },
        {
          icon: '💶',
          title: 'AEFE PRRD',
          description: '~41,863 EUR per detached teacher (school contribution)',
        },
        {
          icon: '📈',
          title: 'Social Charges',
          description: '42% of gross salaries (French system)',
        },
        {
          icon: '🔧',
          title: 'Operating Costs',
          description: 'Supplies (60xxx), utilities (61xxx-62xxx), services (63xxx-64xxx)',
        },
      ],
      outcomes: [
        'Personnel budget is established',
        'Operating budget is defined',
        'Total cost projection is complete',
        'Budget consolidation can proceed',
      ],
      troubleshooting: [
        {
          question: 'Why are personnel costs so high?',
          answer:
            'Personnel typically represents 60-70% of school budget. This includes: salaries, social charges (42%), AEFE contributions (PRRD), and ATSEM staff. Verify FTE counts from DHG are accurate.',
        },
        {
          question: 'What are account codes 641xx vs 645xx?',
          answer:
            '641xx are salaries and wages, 645xx are social security charges. Both are automatically calculated from DHG FTE and configured salary scales.',
        },
      ],
    },

    capex: {
      overview:
        'Plan capital expenditures (equipment, IT, facilities, furniture) and calculate depreciation. This step is OPTIONAL for budget completion but important for long-term planning.',
      prerequisites: ['None - CapEx planning is independent'],
      instructions: [
        'Navigate to CapEx Planning page',
        'Click "Add Capital Expenditure" button',
        'Enter asset description and category (Equipment, IT, Facilities, Furniture)',
        'Specify acquisition date and total cost (SAR)',
        'Define useful life (years) for depreciation',
        'System auto-calculates annual depreciation (straight-line method)',
        'Review depreciation schedule',
        'Check account code mapping (2xxx - fixed assets)',
      ],
      businessRules: [
        {
          icon: '💻',
          title: 'Asset Categories',
          description: 'Equipment, IT, Facilities, Furniture - each with standard useful life',
        },
        {
          icon: '📉',
          title: 'Depreciation Method',
          description: 'Straight-line: Annual Depreciation = Cost ÷ Useful Life',
        },
        {
          icon: '📊',
          title: 'Account Codes',
          description: 'Fixed assets use 2xxx series accounts',
        },
        {
          icon: '✅',
          title: 'Optional Step',
          description: 'CapEx planning does not block budget completion',
        },
      ],
      outcomes: [
        'Capital investment plan is documented',
        'Depreciation expenses are calculated',
        'Fixed asset register is established',
        'Multi-year investment planning is supported',
      ],
      troubleshooting: [
        {
          question: 'Is CapEx planning mandatory?',
          answer:
            "No - CapEx planning is optional. You can complete budget planning without it. However, it's recommended for accurate multi-year financial planning and asset tracking.",
        },
        {
          question: 'How is depreciation calculated?',
          answer:
            'The system uses straight-line depreciation: Annual Depreciation = Total Cost ÷ Useful Life (years). For example, a 50,000 SAR IT system with 5-year life = 10,000 SAR/year depreciation.',
        },
      ],
    },
  }

  return content[stepId]
}
