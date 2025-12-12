# EFIR Enrollment Analysis & Modeling Framework

## Executive Summary

This document presents a comprehensive analysis of EFIR's historical enrollment data (2021-2025) and provides a **dynamic modeling framework** for enrollment projections with full override capability at every level.

**Key Findings:**
- School grew from 1,434 to 1,747 students (2021-2025), CAGR of 5.1%
- Growth primarily driven by Collège (+32%) and Lycée (+50%)
- High lateral entry in Maternelle (PS→MS: 138% progression rate)
- Four distinct entry points: PS (primary), CP, 6ème, and 2nde
- **Current utilization: 94.4% of 1,850 maximum capacity**

**Model Capabilities:**
- Dynamic parameters with per-grade override capability
- Adjustable class size ceiling by level (default: 25)
- School-wide capacity constraint (1,850 students)
- Five scenarios: Worst Case → Best Case

---

## 1. Historical Enrollment Overview

### 1.1 Enrollment by Grade (2021-2025)

| Grade | 2021 | 2022 | 2023 | 2024 | 2025 | Trend |
|-------|------|------|------|------|------|-------|
| PS | 60 | 67 | 68 | 59 | 65 | Stable |
| MS | 94 | 85 | 86 | 109 | 71 | Volatile |
| GS | 97 | 115 | 95 | 123 | 124 | Growing |
| CP | 118 | 103 | 126 | 116 | 126 | Stable |
| CE1 | 119 | 116 | 108 | 140 | 118 | Volatile |
| CE2 | 113 | 120 | 122 | 126 | 132 | Growing |
| CM1 | 108 | 123 | 125 | 124 | 121 | Stable |
| CM2 | 98 | 112 | 126 | 145 | 121 | Growing |
| 6EME | 115 | 99 | 112 | 146 | 151 | Strong Growth |
| 5EME | 90 | 117 | 102 | 121 | 139 | Growing |
| 4EME | 98 | 96 | 126 | 104 | 120 | Volatile |
| 3EME | 86 | 101 | 110 | 128 | 103 | Volatile |
| 2NDE | 77 | 90 | 104 | 130 | 125 | Strong Growth |
| 1ERE | 87 | 77 | 102 | 114 | 120 | Growing |
| TERM | 74 | 78 | 75 | 109 | 111 | Strong Growth |

### 1.2 Enrollment by Educational Level

| Level | 2021 | 2022 | 2023 | 2024 | 2025 | Change | CAGR |
|-------|------|------|------|------|------|--------|------|
| Maternelle | 251 | 267 | 249 | 291 | 260 | +3.6% | +0.9% |
| Élémentaire | 556 | 574 | 607 | 651 | 618 | +11.2% | +2.7% |
| Collège | 389 | 413 | 450 | 499 | 513 | +31.9% | +7.2% |
| Lycée | 238 | 245 | 281 | 353 | 356 | +49.6% | +10.6% |
| **TOTAL** | **1,434** | **1,499** | **1,587** | **1,794** | **1,747** | **+21.8%** | **+5.1%** |

**Insight:** Growth is concentrated in secondary education (Collège and Lycée), suggesting the school's reputation has matured and families are staying longer.

---

## 2. Cohort Progression Analysis

### 2.1 Progression Rate Formula

```
Progression_Rate[G→G+1] = Students[G+1, Year Y] / Students[G, Year Y-1]
```

A rate >100% indicates net new students joining; <100% indicates net attrition.

### 2.2 Progression Rates by Transition

| Transition | 2021→22 | 2022→23 | 2023→24 | 2024→25 | Average | Std Dev |
|------------|---------|---------|---------|---------|---------|---------|
| PS→MS | 141.7% | 128.4% | 160.3% | 120.3% | **137.7%** | 15.1% |
| MS→GS | 122.3% | 111.8% | 143.0% | 113.8% | **122.7%** | 12.4% |
| GS→CP | 106.2% | 109.6% | 122.1% | 102.4% | **110.1%** | 7.4% |
| CP→CE1 | 98.3% | 104.9% | 111.1% | 101.7% | **104.0%** | 4.7% |
| CE1→CE2 | 100.8% | 105.2% | 116.7% | 94.3% | **104.2%** | 8.2% |
| CE2→CM1 | 108.9% | 104.2% | 101.6% | 96.0% | **102.7%** | 4.6% |
| CM1→CM2 | 103.7% | 102.4% | 116.0% | 97.6% | **104.9%** | 6.8% |
| CM2→6EME | 101.0% | 100.0% | 115.9% | 104.1% | **105.3%** | 6.3% |
| 6EME→5EME | 101.7% | 103.0% | 108.0% | 95.2% | **102.0%** | 4.6% |
| 5EME→4EME | 106.7% | 107.7% | 102.0% | 99.2% | **103.9%** | 3.5% |
| 4EME→3EME | 103.1% | 114.6% | 101.6% | 99.0% | **104.6%** | 6.0% |
| 3EME→2NDE | 104.7% | 103.0% | 118.2% | 97.7% | **105.9%** | 7.6% |
| 2NDE→1ERE | 100.0% | 113.3% | 109.6% | 92.3% | **103.8%** | 8.2% |
| 1ERE→TERM | 89.7% | 97.4% | 106.9% | 97.4% | **97.8%** | 6.1% |

### 2.3 Key Observations

1. **Maternelle "Funnel" Effect**
   - PS→MS (138%) and MS→GS (123%) show massive lateral entry
   - Families often join after PS (perhaps due to waiting lists or late decisions)

2. **Entry Points Identified**
   - **Primary**: PS (age 3) - base entry ~64 students/year
   - **Secondary**: CP (age 6) - ~14% additional vs GS
   - **Tertiary**: 6ème (age 11) - ~9% additional vs CM2
   - **Quaternary**: 2nde (age 15) - ~10% additional vs 3ème

3. **Attrition Point**
   - 1ère→Terminale (98%) - only transition consistently below 100%
   - Some students leave before Baccalauréat (perhaps to local/French schools)

---

## 3. Decomposition: Retention vs. Lateral Entry

### 3.1 Model Decomposition

Using industry benchmark (96% retention for quality international schools):

```
Progression_Rate = Retention_Rate + Lateral_Entry_Rate
```

| Grade | Est. Retention | Est. Lateral Entry | Notes |
|-------|---------------|-------------------|-------|
| PS | N/A | 100% (Entry) | Primary entry point |
| MS | 96% | ~42% | Major lateral entry |
| GS | 96% | ~27% | Continued lateral entry |
| CP | 96% | ~14% | Secondary entry point |
| CE1 | 96% | ~8% | Moderate lateral entry |
| CE2 | 96% | ~8% | Moderate lateral entry |
| CM1 | 96% | ~7% | Low lateral entry |
| CM2 | 96% | ~9% | Low lateral entry |
| 6EME | 96% | ~9% | Transition entry point |
| 5EME | 96% | ~6% | Low lateral entry |
| 4EME | 96% | ~8% | Low lateral entry |
| 3EME | 96% | ~9% | Low lateral entry |
| 2NDE | 96% | ~10% | Lycée entry point |
| 1ERE | 96% | ~8% | Low lateral entry |
| TERM | 98% | ~0% | Terminal grade, minimal entry |

### 3.2 Base Lateral Entry Values (Absolute Numbers)

| Grade | Base Lateral Entry (students/year) |
|-------|-----------------------------------|
| MS | 27 |
| GS | 20 |
| CP | 12 |
| CE1 | 7 |
| CE2 | 6 |
| CM1 | 5 |
| CM2 | 7 |
| 6EME | 8 |
| 5EME | 5 |
| 4EME | 6 |
| 3EME | 6 |
| 2NDE | 8 |
| 1ERE | 6 |
| TERM | 1 |

---

## 4. Capacity Analysis

### 4.1 School Capacity Constraints

| Parameter | Value |
|-----------|-------|
| **Maximum School Capacity** | **1,850 students** |
| **Default Class Size** | **25 students** |
| **Class Size Range** | 20-30 (adjustable by level) |

### 4.2 Class Size Configuration (Default: 25, Adjustable)

| Level | Default | Min | Max | Grades |
|-------|---------|-----|-----|--------|
| Maternelle | 25 | 20 | 28 | PS, MS, GS |
| Élémentaire | 25 | 22 | 28 | CP, CE1, CE2, CM1, CM2 |
| Collège | 25 | 22 | 30 | 6ème, 5ème, 4ème, 3ème |
| Lycée | 25 | 22 | 30 | 2nde, 1ère, Terminale |

### 4.3 Current Divisions (2025, with 25 students/class)

| Grade | Students | Divisions | Students/Class | Capacity |
|-------|----------|-----------|----------------|----------|
| PS | 65 | 3 | 21.7 | 75 |
| MS | 71 | 3 | 23.7 | 75 |
| GS | 124 | 5 | 24.8 | 125 |
| CP | 126 | 6 | 21.0 | 150 |
| CE1 | 118 | 5 | 23.6 | 125 |
| CE2 | 132 | 6 | 22.0 | 150 |
| CM1 | 121 | 5 | 24.2 | 125 |
| CM2 | 121 | 5 | 24.2 | 125 |
| 6EME | 151 | 7 | 21.6 | 175 |
| 5EME | 139 | 6 | 23.2 | 150 |
| 4EME | 120 | 5 | 24.0 | 125 |
| 3EME | 103 | 5 | 20.6 | 125 |
| 2NDE | 125 | 5 | 25.0 | 125 |
| 1ERE | 120 | 5 | 24.0 | 125 |
| TERM | 111 | 5 | 22.2 | 125 |
| **TOTAL** | **1,747** | **76** | **23.0** | **1,900** |

### 4.4 Capacity Utilization

| Year | Students | vs. 1,850 Max | Status |
|------|----------|---------------|--------|
| 2021 | 1,434 | 77.5% | Comfortable |
| 2022 | 1,499 | 81.0% | Comfortable |
| 2023 | 1,587 | 85.8% | Moderate |
| 2024 | 1,794 | 97.0% | Near Capacity |
| 2025 | 1,747 | **94.4%** | **Near Capacity** |

---

## 5. Dynamic Enrollment Projection Model

### 5.1 Model Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  DYNAMIC ENROLLMENT MODEL WITH OVERRIDE CAPABILITY                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  LAYER 1: SCENARIO DEFAULTS                                                     │
│  ─────────────────────────────────────────────────────────────────────────────  │
│  Select from: Worst Case | Conservative | Base | Optimistic | Best Case         │
│                                                                                 │
│  LAYER 2: GLOBAL OVERRIDES                                                      │
│  ─────────────────────────────────────────────────────────────────────────────  │
│  • PS Entry adjustment (±20 from scenario default)                              │
│  • Global retention adjustment (±5%)                                            │
│  • Lateral entry multiplier (0.5x - 1.5x)                                       │
│  • Default class size (20-30)                                                   │
│                                                                                 │
│  LAYER 3: LEVEL OVERRIDES                                                       │
│  ─────────────────────────────────────────────────────────────────────────────  │
│  Per level (Maternelle, Élémentaire, Collège, Lycée):                          │
│  • Class size ceiling                                                           │
│  • Maximum divisions                                                            │
│                                                                                 │
│  LAYER 4: GRADE OVERRIDES (Highest Priority)                                    │
│  ─────────────────────────────────────────────────────────────────────────────  │
│  Per grade:                                                                     │
│  • Specific retention rate                                                      │
│  • Specific lateral entry count                                                 │
│  • Maximum divisions                                                            │
│  • Class size ceiling                                                           │
│                                                                                 │
│  CONSTRAINT: School Maximum = 1,850 students                                    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Calculation Formula

**For PS (Entry Grade):**
```
Students[PS, Y] = PS_Entry × (1 + Entry_Growth_Rate)^(Y - Base_Year)
```

**For Other Grades:**
```
Students[G, Y] = min(
    Students[G-1, Y-1] × Retention_Rate[G] + Lateral_Entry[G],
    Max_Divisions[G] × Class_Size_Ceiling[G]
)
```

**School Constraint:**
```
IF Total > 1,850 THEN scale all grades proportionally
```

### 5.3 Override Priority (Highest to Lowest)

1. **Grade-level override** (most specific)
2. **Level-level override** (e.g., all Collège grades)
3. **Global override** (applies to all)
4. **Scenario default** (fallback)

---

## 6. Five Scenario Definitions

### 6.1 Scenario Parameters

| Parameter | Worst Case | Conservative | Base | Optimistic | Best Case |
|-----------|------------|--------------|------|------------|-----------|
| **PS Entry** | 45 | 55 | 65 | 75 | 85 |
| **Entry Growth** | -2%/year | 0% | 0% | +2%/year | +3%/year |
| **Retention** | 90% | 94% | 96% | 98% | 99% |
| **Retention (TERM)** | 92% | 96% | 98% | 99% | 100% |
| **Lateral Multiplier** | 0.3x | 0.6x | 1.0x | 1.3x | 1.5x |

### 6.2 Scenario Descriptions

**WORST CASE**
- Economic downturn, expat departures, competitive pressure from new schools
- Significant reduction in new enrollments and retention
- Use for: Stress testing, minimum staffing planning

**CONSERVATIVE**
- Cautious assumptions, below-average performance
- Moderate decline in demand
- Use for: Budget floor, risk management

**BASE**
- Historical average continuation
- No significant changes in market conditions
- Use for: Standard planning, baseline projections

**OPTIMISTIC**
- Strong demand continues, improved retention
- Positive market conditions
- Use for: Growth planning, resource allocation

**BEST CASE**
- Maximum growth, full demand utilization
- School reaches near-capacity
- Use for: Capacity ceiling, infrastructure planning

### 6.3 Projection Results (2026-2030)

| Scenario | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 | CAGR | Δ Students |
|----------|------|------|------|------|------|------|------|------------|
| Worst Case | 1,747 | 1,556 | 1,382 | 1,229 | 1,116 | 1,007 | **-10.4%** | -740 |
| Conservative | 1,747 | 1,671 | 1,594 | 1,520 | 1,471 | 1,414 | **-4.1%** | -333 |
| Base | 1,747 | 1,761 | 1,766 | 1,767 | 1,784 | 1,785 | **+0.4%** | +38 |
| Optimistic | 1,747 | 1,841 | 1,850 | 1,848 | 1,848 | 1,850 | **+1.2%** | +103 |
| Best Case | 1,747 | 1,850 | 1,850 | 1,850 | 1,850 | 1,850 | **+1.1%** | +103 |

**Note:** Optimistic and Best Case scenarios hit the 1,850 capacity ceiling by 2027.

### 6.4 Base Scenario - Grade Detail

| Grade | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 |
|-------|------|------|------|------|------|------|
| PS | 65 | 65 | 65 | 65 | 65 | 65 |
| MS | 71 | 89 | 89 | 89 | 89 | 89 |
| GS | 124 | 88 | 105 | 105 | 105 | 105 |
| CP | 126 | 131 | 96 | 113 | 113 | 113 |
| CE1 | 118 | 128 | 133 | 99 | 115 | 115 |
| CE2 | 132 | 119 | 129 | 134 | 101 | 116 |
| CM1 | 121 | 132 | 119 | 129 | 134 | 102 |
| CM2 | 121 | 123 | 134 | 121 | 131 | 136 |
| 6EME | 151 | 124 | 126 | 137 | 124 | 134 |
| 5EME | 139 | 150 | 124 | 126 | 137 | 124 |
| 4EME | 120 | 139 | 150 | 125 | 127 | 138 |
| 3EME | 103 | 121 | 139 | 150 | 126 | 128 |
| 2NDE | 125 | 107 | 124 | 141 | 152 | 129 |
| 1ERE | 120 | 126 | 109 | 125 | 141 | 152 |
| TERM | 111 | 119 | 124 | 108 | 124 | 139 |
| **TOTAL** | **1,747** | **1,761** | **1,766** | **1,767** | **1,784** | **1,785** |

---

## 7. Implementation Specifications

### 7.1 Data Model (TypeScript)

```typescript
interface EnrollmentModelConfig {
  // School constraints
  school: {
    maxCapacity: number;           // 1850
    defaultClassSize: number;      // 25
  };
  
  // Structure
  grades: Grade[];
  levels: Level[];
  
  // Scenarios
  scenarios: Record<ScenarioKey, ScenarioConfig>;
  
  // Current state
  activeScenario: ScenarioKey;
  overrides: OverrideConfig;
}

interface ScenarioConfig {
  name: string;
  description: string;
  entry: {
    psEntry: number;
    growthRate: number;
  };
  retention: {
    default: number;
    terminal: number;
  };
  lateralMultiplier: number;
}

interface OverrideConfig {
  // Global overrides
  global?: {
    psEntryAdjustment?: number;
    retentionAdjustment?: number;
    lateralMultiplier?: number;
    defaultClassSize?: number;
  };
  
  // Level overrides
  levels?: Record<LevelCode, {
    classSize?: number;
    maxDivisions?: number;
  }>;
  
  // Grade overrides (highest priority)
  grades?: Record<GradeCode, {
    retention?: number;
    lateralEntry?: number;
    maxDivisions?: number;
    classSize?: number;
  }>;
}

type ScenarioKey = 'worst_case' | 'conservative' | 'base' | 'optimistic' | 'best_case';
```

### 7.2 Calculation Algorithm

```typescript
function projectEnrollment(
  baseYearData: Record<string, number>,
  config: EnrollmentModelConfig,
  targetYear: number
): ProjectionResult {
  
  const scenario = config.scenarios[config.activeScenario];
  const overrides = config.overrides;
  
  // Calculate effective parameters with override cascade
  function getEffectiveParam(grade: string, param: string): number {
    // Priority: Grade > Level > Global > Scenario
    const gradeOverride = overrides.grades?.[grade]?.[param];
    if (gradeOverride !== undefined) return gradeOverride;
    
    const level = getLevelForGrade(grade);
    const levelOverride = overrides.levels?.[level]?.[param];
    if (levelOverride !== undefined) return levelOverride;
    
    const globalOverride = overrides.global?.[param];
    if (globalOverride !== undefined) return globalOverride;
    
    return scenario[param]; // Scenario default
  }
  
  // Project each grade
  const result: Record<string, number> = {};
  
  // PS entry
  const yearsDiff = targetYear - BASE_YEAR;
  const psEntry = scenario.entry.psEntry + (overrides.global?.psEntryAdjustment ?? 0);
  const growth = scenario.entry.growthRate;
  result['PS'] = Math.round(psEntry * Math.pow(1 + growth, yearsDiff));
  
  // Other grades: cohort progression
  for (let i = 1; i < GRADE_SEQUENCE.length; i++) {
    const grade = GRADE_SEQUENCE[i];
    const prevGrade = GRADE_SEQUENCE[i - 1];
    
    const retention = getEffectiveParam(grade, 'retention');
    const baseLateral = BASE_LATERAL_ENTRY[grade];
    const lateralMult = getEffectiveParam(grade, 'lateralMultiplier');
    const lateral = baseLateral * lateralMult;
    
    const projected = baseYearData[prevGrade] * retention + lateral;
    
    // Apply grade capacity constraint
    const maxDiv = getEffectiveParam(grade, 'maxDivisions');
    const classSize = getEffectiveParam(grade, 'classSize');
    const gradeCapacity = maxDiv * classSize;
    
    result[grade] = Math.min(Math.round(projected), gradeCapacity);
  }
  
  // Apply school capacity constraint
  const total = Object.values(result).reduce((a, b) => a + b, 0);
  if (total > config.school.maxCapacity) {
    const scale = config.school.maxCapacity / total;
    for (const grade of Object.keys(result)) {
      result[grade] = Math.round(result[grade] * scale);
    }
  }
  
  return {
    enrollment: result,
    total: Object.values(result).reduce((a, b) => a + b, 0),
    utilizationRate: total / config.school.maxCapacity
  };
}
```

### 7.3 UI Configuration

```typescript
const UI_CONFIG = {
  // Global parameter sliders
  globalControls: {
    psEntryAdjustment: { min: -20, max: +20, step: 5, default: 0 },
    retentionAdjustment: { min: -0.05, max: +0.05, step: 0.01, default: 0 },
    lateralMultiplier: { min: 0.5, max: 1.5, step: 0.1, default: 1.0 },
    defaultClassSize: { min: 20, max: 30, step: 1, default: 25 }
  },
  
  // Level overrides
  levelControls: {
    classSize: { min: 20, max: 30, step: 1 },
    maxDivisions: { min: 2, max: 8, step: 1 }
  },
  
  // Grade overrides
  gradeControls: {
    retention: { min: 0.85, max: 1.00, step: 0.01 },
    lateralEntry: { min: 0, max: 50, step: 1 },
    maxDivisions: { min: 2, max: 8, step: 1 },
    classSize: { min: 20, max: 30, step: 1 }
  },
  
  // Projection display
  projectionYears: 5,
  displayOptions: ['byGrade', 'byLevel', 'totals', 'utilization']
};
```

---

## 8. Key Insights Summary

| Insight | Finding | Implication |
|---------|---------|-------------|
| **Growth Source** | Secondary education (+40% growth) | Reputation mature, retention improving |
| **Maternelle Funnel** | 138% PS→MS progression | Many families join after PS |
| **Entry Points** | PS, CP, 6ème, 2nde | Target marketing at these transitions |
| **Attrition** | Only at 1ère→Term (98%) | Pre-Bac departures |
| **Capacity** | 94.4% utilization | Near ceiling, manage growth |
| **Risk** | -10% CAGR in worst case | Plan for 1,000 minimum |
| **Upside** | Hits 1,850 ceiling by 2027 | Infrastructure is the constraint |

---

## 9. Appendix: Data Quality Notes

### 9.1 Observed Anomalies

1. **2024→2025 MS Drop**: MS dropped from 109 to 71 (-35%), unusual pattern
2. **2023→2024 CE1 Spike**: CE1 jumped from 108 to 140 (+30%), then back to 118
3. **2024 Peak Year**: 2024 shows highest enrollment (1,794), then declined in 2025

### 9.2 Recommendations for Data Collection

1. **Track Individual Students**: Enable true retention vs. lateral entry tracking
2. **Record Departure Reasons**: Capture why students leave
3. **Waiting List Data**: Track demand vs. capacity per grade
4. **Nationality Mix**: Track nationality for fee modeling

---

## 10. Glossary

| Term | French | Definition |
|------|--------|------------|
| PS | Petite Section | First year of maternelle (age 3) |
| MS | Moyenne Section | Second year of maternelle (age 4) |
| GS | Grande Section | Third year of maternelle (age 5) |
| CP | Cours Préparatoire | First year of élémentaire (age 6) |
| CE1/CE2 | Cours Élémentaire | Elementary grades (ages 7-8) |
| CM1/CM2 | Cours Moyen | Upper elementary (ages 9-10) |
| 6ème-3ème | Collège | Middle school (ages 11-14) |
| 2nde-Term | Lycée | High school (ages 15-17) |
| Retention | Rétention | % of students advancing to next grade |
| Lateral Entry | Entrée latérale | New students joining mid-cycle |
| Division | Division/Classe | A class section |

---

*Document generated: December 2025*
*Data source: EFIR historical enrollment 2021-2025*
*School capacity: 1,850 students maximum*
