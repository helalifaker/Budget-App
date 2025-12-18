# EFIR Budget Planning Application - Inventory

**Last Updated:** 2025-12-15

This document provides a comprehensive inventory of the codebase structure.

---

## Table of Contents

1. [Pydantic Schemas](#1-pydantic-schemas)
2. [API Routes](#2-api-routes)
3. [Services](#3-services)
4. [Calculation Engines](#4-calculation-engines)
5. [Database Models](#5-database-models)

---

## 1. Pydantic Schemas

### Location: `backend/app/schemas/`

| File | Schema Classes |
|------|----------------|
| `analysis.py` | `KPICategoryEnum`, `VarianceStatusEnum`, `ScenarioTypeEnum`, `AlertSeverityEnum`, `KPIDefinitionResponse`, `KPIValueResponse`, `KPIBenchmarkComparison`, `KPITrendPoint`, `KPITrendResponse`, `KPICalculationRequest`, `DashboardSummaryResponse`, `ChartDataResponse`, `AlertResponse`, `ActivityLogEntry`, `ComparisonResponse`, `VarianceReportResponse`, `ForecastRevisionResponse`, `StrategicPlanResponse`, `YearProjectionResponse`, `ScenarioComparisonResponse`, `StrategicInitiativeResponse`, `MessageResponse` |
| `configuration.py` | `SystemConfigCreate`, `SystemConfigResponse`, `BudgetVersionCreate`, `BudgetVersionUpdate`, `BudgetVersionClone`, `BudgetVersionResponse`, `AcademicCycleResponse`, `AcademicLevelResponse`, `ClassSizeParamCreate`, `ClassSizeParamResponse`, `SubjectCreateRequest`, `SubjectResponse`, `SubjectHoursCreate`, `SubjectHoursResponse`, `SubjectHoursMatrixResponse`, `SubjectHoursBatchRequest`, `SubjectHoursBatchResponse`, `TemplateInfo`, `ApplyTemplateRequest`, `ApplyTemplateResponse`, `TeacherCategoryResponse`, `TeacherCostParamCreate`, `TeacherCostParamResponse`, `FeeCategoryResponse`, `NationalityTypeResponse`, `FeeStructureCreate`, `FeeStructureResponse`, `TimetableConstraintCreate`, `TimetableConstraintResponse` |
| `consolidation.py` | `ConsolidationLineItemResponse`, `BudgetConsolidationResponse`, `ConsolidationValidationResponse`, `ModulesCompleteStatus`, `ConsolidationStatusResponse`, `ConsolidationRequest`, `FinancialStatementLineResponse`, `IncomeStatementResponse`, `BalanceSheetResponse`, `FinancialPeriodTotals`, `SubmitForApprovalRequest`, `ApprovebudgetRequest`, `WorkflowActionResponse`, `GenerateStatementRequest`, `StatementFormatOptions`, `ConsolidationVarianceItem`, `ConsolidationVarianceResponse`, `ConsolidationSummary` |
| `costs.py` | `RevenuePlanBase`, `RevenuePlanCreate`, `RevenuePlanUpdate`, `RevenuePlanResponse`, `RevenueBulkUpdateItem`, `RevenueBulkUpdateRequest`, `RevenueBulkUpdateResponse`, `RevenueCalculationRequest`, `RevenueCalculationResponse`, `PersonnelCostPlanBase`, `PersonnelCostPlanCreate`, `PersonnelCostPlanUpdate`, `PersonnelCostPlanResponse`, `PersonnelCostCalculationRequest`, `PersonnelCostCalculationResponse`, `OperatingCostPlanBase`, `OperatingCostPlanCreate`, `OperatingCostPlanUpdate`, `OperatingCostPlanResponse`, `OperatingCostCalculationRequest`, `OperatingCostCalculationResponse`, `CapExPlanBase`, `CapExPlanCreate`, `CapExPlanUpdate`, `CapExPlanResponse`, `DepreciationCalculationRequest`, `DepreciationCalculationResponse` |
| `enrollment_projection.py` | `EnrollmentScenarioResponse`, `ScenarioListResponse`, `GlobalOverridesUpdate`, `LevelOverrideItem`, `LevelOverridesUpdate`, `GradeOverrideItem`, `GradeOverridesUpdate`, `LevelOverrideResponse`, `GradeOverrideResponse`, `ProjectionConfigUpdate`, `ProjectionConfigResponse`, `GradeProjectionResponse`, `YearProjectionResponse`, `ProjectionSummaryResponse`, `HistoricalYearData`, `ProjectionResultsResponse`, `ValidationRequest`, `ValidationResponse`, `GradeLateralRateResponse`, `LateralRatesResponse`, `GradeLateralRateOverride`, `LateralRateOverrideRequest`, `GradeOptimizationResultResponse`, `NewStudentsSummaryRowResponse`, `NewStudentsSummaryResponse`, `LateralOptimizationResponse` |
| `enrollment_settings.py` | `CalibrationStatus`, `CalibrationRequest`, `CalibrationResult`, `DerivedParameterBase`, `DerivedParameterResponse`, `EntryPointRateBase`, `EntryPointRateResponse`, `EntryPointRateUpdate`, `IncidentalLateralBase`, `IncidentalLateralResponse`, `IncidentalLateralUpdate`, `ScenarioMultiplierBase`, `ScenarioMultiplierResponse`, `ScenarioMultiplierUpdate`, `ScenarioMultipliersBulkUpdate`, `ParameterOverrideBase`, `ParameterOverrideResponse`, `ParameterOverrideUpdate`, `ParameterOverridesBulkUpdate`, `EnrollmentSettingsResponse`, `HistoricalYearSummary`, `HistoricalDataSummary`, `EffectiveRates`, `AllEffectiveRates` |
| `historical.py` | `HistoricalDataPoint`, `HistoricalComparison`, `EnrollmentWithHistoryRow`, `EnrollmentWithHistoryResponse`, `ClassStructureWithHistoryRow`, `ClassStructureWithHistoryResponse`, `DHGWithHistoryRow`, `DHGWithHistoryResponse`, `RevenueWithHistoryRow`, `RevenueWithHistoryResponse`, `CostsWithHistoryRow`, `CostsWithHistoryResponse`, `CapExWithHistoryRow`, `CapExWithHistoryResponse`, `ImpactCalculationRequest`, `ImpactCalculationResponse`, `HistoricalImportRecord`, `HistoricalImportRequest`, `HistoricalImportResult`, `HistoricalQueryParams` |
| `integrations.py` | `OdooConnectionRequest`, `OdooConnectionResponse`, `OdooImportActualsRequest`, `OdooActualRecord`, `OdooImportActualsResponse`, `OdooSyncRequest`, `OdooActualsListResponse`, `SkolengoExportRequest`, `SkolengoEnrollmentRecord`, `SkolengoImportRequest`, `SkolengoImportResponse`, `SkolengoSyncRequest`, `EnrollmentVariance`, `SkolengoComparisonResponse`, `AEFEPositionRecord`, `AEFEImportRequest`, `AEFEImportResponse`, `AEFEPositionSummary`, `AEFEPositionListResponse`, `IntegrationSettingsCreate`, `IntegrationSettingsUpdate`, `IntegrationSettingsResponse`, `IntegrationLogResponse`, `IntegrationLogListResponse`, `AccountMappingConfig`, `LevelMappingConfig` |
| `personnel.py` | `EmployeeBase`, `EmployeeCreate`, `EmployeeUpdate`, `EmployeeResponse`, `EmployeeBulkResponse`, `PlaceholderEmployeeCreate`, `PlaceholderValidationRequest`, `EmployeeSalaryBase`, `EmployeeSalaryCreate`, `EmployeeSalaryUpdate`, `EmployeeSalaryResponse`, `SalaryBreakdownResponse`, `EOSProvisionBase`, `EOSProvisionCreate`, `EOSProvisionResponse`, `EOSCalculationRequest`, `EOSCalculationResponse`, `EOSSummaryResponse`, `AEFEPositionBase`, `AEFEPositionCreate`, `AEFEPositionUpdate`, `AEFEPositionResponse`, `AEFEPositionSummaryResponse`, `InitializeAEFEPositionsRequest`, `WorkforceSummaryResponse` |
| `planning.py` | `EnrollmentPlanBase`, `EnrollmentPlanCreate`, `EnrollmentPlanUpdate`, `EnrollmentPlanResponse`, `EnrollmentSummary`, `EnrollmentProjectionRequest`, `NationalityDistributionBase`, `NationalityDistributionCreate`, `NationalityDistributionUpdate`, `NationalityDistributionResponse`, `NationalityDistributionBulkUpdate`, `EnrollmentTotalCreate`, `EnrollmentTotalsBulkUpdate`, `EnrollmentBreakdownResponse`, `EnrollmentWithDistributionResponse`, `ClassStructureBase`, `ClassStructureCreate`, `ClassStructureUpdate`, `ClassStructureResponse`, `ClassStructureCalculationRequest`, `DHGSubjectHoursBase`, `DHGSubjectHoursCreate`, `DHGSubjectHoursUpdate`, `DHGSubjectHoursResponse`, `DHGHoursCalculationRequest`, `DHGTeacherRequirementBase`, `DHGTeacherRequirementCreate`, `DHGTeacherRequirementUpdate`, `DHGTeacherRequirementResponse`, `FTECalculationRequest`, `TeacherAllocationBase`, `TeacherAllocationCreate`, `TeacherAllocationUpdate`, `TeacherAllocationResponse`, `TeacherAllocationBulkUpdate`, `TRMDGapAnalysis`, `TRMDGapAnalysisResponse`, `ImpactCalculationRequest`, `ImpactCalculationResponse` |
| `planning_progress.py` | `StepValidation`, `StepBlocker`, `StepProgress`, `PlanningProgressResponse`, `StepMetadata`, `CascadeRequest`, `CascadeResponse` |
| `writeback.py` | `CellUpdateRequest`, `CellUpdateResponse`, `CellUpdate`, `BatchUpdateRequest`, `ConflictDetail`, `BatchUpdateResponse`, `CellChangeResponse`, `ChangeHistoryFilters`, `UndoRequest`, `UndoResponse`, `RedoRequest`, `RedoResponse`, `CommentRequest`, `CommentResponse`, `CommentListResponse`, `ResolveCommentRequest`, `LockRequest`, `UnlockRequest`, `CellLockResponse`, `BulkLockRequest`, `BulkLockResponse`, `CellCreateRequest`, `CellResponse`, `CellListResponse` |

---

## 2. API Routes

### 2.1 Configuration API (`/api/v1`)
**File:** `backend/app/api/v1/configuration.py`
**Service:** `ConfigurationService`

| Method | Endpoint | Handler | Request Schema | Response Schema |
|--------|----------|---------|----------------|-----------------|
| GET | `/debug-token` | `debug_token` | - | dict |
| GET | `/config/system` | `get_system_configs` | Query: category | `list[SystemConfigResponse]` |
| GET | `/config/system/{key}` | `get_system_config` | - | `SystemConfigResponse` |
| PUT | `/config/system/{key}` | `upsert_system_config` | `SystemConfigCreate` | `SystemConfigResponse` |
| GET | `/budget-versions` | `get_budget_versions` | Query: page, page_size, fiscal_year, status | `PaginatedResponse[BudgetVersionResponse]` |
| GET | `/budget-versions/{version_id}` | `get_budget_version` | - | `BudgetVersionResponse` |
| POST | `/budget-versions` | `create_budget_version` | `BudgetVersionCreate` | `BudgetVersionResponse` |
| PUT | `/budget-versions/{version_id}` | `update_budget_version` | `BudgetVersionUpdate` | `BudgetVersionResponse` |
| PUT | `/budget-versions/{version_id}/submit` | `submit_budget_version` | - | `BudgetVersionResponse` |
| PUT | `/budget-versions/{version_id}/approve` | `approve_budget_version` | - | `BudgetVersionResponse` |
| PUT | `/budget-versions/{version_id}/reject` | `reject_budget_version` | Query: reason | `BudgetVersionResponse` |
| PUT | `/budget-versions/{version_id}/supersede` | `supersede_budget_version` | - | `BudgetVersionResponse` |
| DELETE | `/budget-versions/{version_id}` | `delete_budget_version` | - | 204 No Content |
| POST | `/budget-versions/{version_id}/clone` | `clone_budget_version` | `BudgetVersionClone` | `BudgetVersionResponse` |
| GET | `/academic-cycles` | `get_academic_cycles` | - | `list[AcademicCycleResponse]` |
| GET | `/academic-levels` | `get_academic_levels` | Query: cycle_id | `list[AcademicLevelResponse]` |
| GET | `/class-size-params` | `get_class_size_params` | Query: version_id | `list[ClassSizeParamResponse]` |
| PUT | `/class-size-params` | `upsert_class_size_param` | `ClassSizeParamCreate` | `ClassSizeParamResponse` |
| DELETE | `/class-size-params/{param_id}` | `delete_class_size_param` | - | 204 No Content |
| GET | `/subjects` | `get_subjects` | - | `list[SubjectResponse]` |
| POST | `/subjects` | `create_subject` | `SubjectCreateRequest` | `SubjectResponse` |
| GET | `/subject-hours` | `get_subject_hours_matrix` | Query: version_id | `list[SubjectHoursResponse]` |
| PUT | `/subject-hours` | `upsert_subject_hours` | `SubjectHoursCreate` | `SubjectHoursResponse` |
| GET | `/subject-hours/matrix` | `get_subject_hours_matrix_by_cycle` | Query: version_id, cycle_code | `SubjectHoursMatrixResponse` |
| POST | `/subject-hours/batch` | `batch_save_subject_hours` | `SubjectHoursBatchRequest` | `SubjectHoursBatchResponse` |
| GET | `/subject-hours/templates` | `get_curriculum_templates` | - | `list[TemplateInfo]` |
| POST | `/subject-hours/apply-template` | `apply_curriculum_template` | `ApplyTemplateRequest` | `ApplyTemplateResponse` |
| GET | `/teacher-categories` | `get_teacher_categories` | - | `list[TeacherCategoryResponse]` |
| GET | `/teacher-costs` | `get_teacher_cost_params` | Query: version_id | `list[TeacherCostParamResponse]` |
| PUT | `/teacher-costs` | `upsert_teacher_cost_param` | `TeacherCostParamCreate` | `TeacherCostParamResponse` |
| GET | `/fee-categories` | `get_fee_categories` | - | `list[FeeCategoryResponse]` |
| GET | `/nationality-types` | `get_nationality_types` | - | `list[NationalityTypeResponse]` |
| GET | `/fee-structure` | `get_fee_structure` | Query: version_id | `list[FeeStructureResponse]` |
| PUT | `/fee-structure` | `upsert_fee_structure` | `FeeStructureCreate` | `FeeStructureResponse` |
| GET | `/timetable-constraints` | `get_timetable_constraints` | Query: version_id | `list[TimetableConstraintResponse]` |
| PUT | `/timetable-constraints` | `upsert_timetable_constraint` | `TimetableConstraintCreate` | `TimetableConstraintResponse` |

---

### 2.2 Planning API (`/api/v1/planning`)
**File:** `backend/app/api/v1/planning.py`
**Services:** `EnrollmentService`, `ClassStructureService`, `DHGService`, `PlanningProgressService`, `CascadeService`, `ImpactCalculatorService`

| Method | Endpoint | Handler | Request Schema | Response Schema |
|--------|----------|---------|----------------|-----------------|
| GET | `/enrollment/{version_id}` | `get_enrollment_plan` | - | `list[EnrollmentPlanResponse]` |
| POST | `/enrollment/{version_id}` | `create_enrollment` | `EnrollmentPlanCreate` | `EnrollmentPlanResponse` |
| PUT | `/enrollment/{enrollment_id}` | `update_enrollment` | `EnrollmentPlanUpdate` | `EnrollmentPlanResponse` |
| DELETE | `/enrollment/{enrollment_id}` | `delete_enrollment` | - | 204 No Content |
| GET | `/enrollment/{version_id}/summary` | `get_enrollment_summary` | - | `EnrollmentSummary` |
| POST | `/enrollment/{version_id}/project` | `project_enrollment` | `EnrollmentProjectionRequest` | list[dict] |
| GET | `/enrollment/{version_id}/with-distribution` | `get_enrollment_with_distribution` | - | `EnrollmentWithDistributionResponse` |
| POST/PUT | `/enrollment/{version_id}/bulk` | `bulk_upsert_enrollment_totals` | `EnrollmentTotalsBulkUpdate` | `list[EnrollmentPlanResponse]` |
| GET | `/distributions/{version_id}` | `get_distributions` | - | `list[NationalityDistributionResponse]` |
| POST/PUT | `/distributions/{version_id}` | `bulk_upsert_distributions` | `NationalityDistributionBulkUpdate` | `list[NationalityDistributionResponse]` |
| GET | `/class-structure/{version_id}` | `get_class_structure` | - | `list[ClassStructureResponse]` |
| POST | `/class-structure/{version_id}/calculate` | `calculate_class_structure` | `ClassStructureCalculationRequest` | `list[ClassStructureResponse]` |
| PUT | `/class-structure/{class_structure_id}` | `update_class_structure` | `ClassStructureUpdate` | `ClassStructureResponse` |
| GET | `/dhg/subject-hours/{version_id}` | `get_dhg_subject_hours` | - | `list[DHGSubjectHoursResponse]` |
| POST | `/dhg/subject-hours/{version_id}/calculate` | `calculate_dhg_subject_hours` | `DHGHoursCalculationRequest` | `list[DHGSubjectHoursResponse]` |
| GET | `/dhg/teacher-requirements/{version_id}` | `get_teacher_requirements` | - | `list[DHGTeacherRequirementResponse]` |
| POST | `/dhg/teacher-requirements/{version_id}/calculate` | `calculate_teacher_requirements` | `FTECalculationRequest` | `list[DHGTeacherRequirementResponse]` |
| GET | `/dhg/allocations/{version_id}` | `get_teacher_allocations` | - | `list[TeacherAllocationResponse]` |
| POST | `/dhg/allocations/{version_id}` | `create_teacher_allocation` | `TeacherAllocationCreate` | `TeacherAllocationResponse` |
| PUT | `/dhg/allocations/{allocation_id}` | `update_teacher_allocation` | `TeacherAllocationUpdate` | `TeacherAllocationResponse` |
| POST/PUT | `/dhg/allocations/{version_id}/bulk` | `bulk_update_teacher_allocations` | `TeacherAllocationBulkUpdate` | `list[TeacherAllocationResponse]` |
| DELETE | `/dhg/allocations/{allocation_id}` | `delete_teacher_allocation` | - | 204 No Content |
| POST | `/dhg/{version_id}/draft` | `save_dhg_draft` | `TeacherAllocationBulkUpdate` | `list[TeacherAllocationResponse]` |
| POST | `/dhg/{version_id}/apply` | `apply_dhg_and_calculate` | `TeacherAllocationBulkUpdate` | `TRMDGapAnalysisResponse` |
| GET | `/dhg/trmd/{version_id}` | `get_trmd_gap_analysis` | - | `TRMDGapAnalysisResponse` |
| GET | `/progress/{version_id}` | `get_planning_progress` | - | `PlanningProgressResponse` |
| POST | `/{version_id}/cascade` | `cascade_recalculate` | `CascadeRequest` | `CascadeResponse` |
| POST | `/{version_id}/impact` | `calculate_impact` | `ImpactCalculationRequest` | `ImpactCalculationResponse` |

---

### 2.3 Enrollment Projection API (`/api/v1/planning/enrollment-projection`)
**File:** `backend/app/api/v1/enrollment_projection.py`
**Service:** `EnrollmentProjectionService`

| Method | Endpoint | Handler | Request Schema | Response Schema |
|--------|----------|---------|----------------|-----------------|
| GET | `/scenarios` | `get_scenarios` | - | `ScenarioListResponse` |
| GET | `/{version_id}/config` | `get_projection_config` | - | `ProjectionConfigResponse` |
| PUT | `/{version_id}/config` | `update_projection_config` | `ProjectionConfigUpdate` | `ProjectionConfigResponse` |
| PUT | `/{version_id}/global-overrides` | `update_global_overrides` | `GlobalOverridesUpdate` | `ProjectionConfigResponse` |
| PUT | `/{version_id}/level-overrides` | `update_level_overrides` | `LevelOverridesUpdate` | `ProjectionConfigResponse` |
| PUT | `/{version_id}/grade-overrides` | `update_grade_overrides` | `GradeOverridesUpdate` | `ProjectionConfigResponse` |
| GET | `/{version_id}/results` | `get_projection_results` | Query: include_fiscal_proration | `ProjectionResultsResponse` |
| POST | `/{version_id}/calculate` | `calculate_projection` | - | `ProjectionResultsResponse` |
| POST | `/{version_id}/validate` | `validate_projection` | `ValidationRequest` | `ValidationResponse` |
| POST | `/{version_id}/unvalidate` | `unvalidate_projection` | - | `ProjectionConfigResponse` |
| POST | `/{version_id}/draft` | `save_draft` | `ProjectionConfigUpdate` | `ProjectionConfigResponse` |
| POST | `/{version_id}/apply` | `apply_and_calculate` | `ProjectionConfigUpdate` | `ProjectionResultsResponse` |
| GET | `/{version_id}/lateral-optimization` | `get_lateral_optimization` | - | `LateralOptimizationResponse` |

---

### 2.4 Enrollment Settings API (`/api/v1/enrollment/settings`)
**File:** `backend/app/api/v1/enrollment_settings.py`
**Service:** `EnrollmentCalibrationService`

| Method | Endpoint | Handler | Request Schema | Response Schema |
|--------|----------|---------|----------------|-----------------|
| GET | `` | `get_enrollment_settings` | Query: organization_id, scenario_code | `EnrollmentSettingsResponse` |
| GET | `/status` | `get_calibration_status` | Query: organization_id | `CalibrationStatus` |
| POST | `/calibrate` | `calibrate_parameters` | `CalibrationRequest`, Query: organization_id | `CalibrationResult` |
| GET | `/history` | `get_historical_data_summary` | Query: organization_id | `HistoricalDataSummary` |
| PUT | `/overrides/{grade_code}` | `update_parameter_override` | `ParameterOverrideUpdate`, Query: organization_id, scenario_code | `EnrollmentSettingsResponse` |
| PUT | `/overrides` | `update_parameter_overrides_bulk` | `ParameterOverridesBulkUpdate`, Query: organization_id, scenario_code | `EnrollmentSettingsResponse` |
| PUT | `/multipliers/{scenario_code}` | `update_scenario_multiplier` | `ScenarioMultiplierUpdate`, Query: organization_id | `EnrollmentSettingsResponse` |
| PUT | `/multipliers` | `update_scenario_multipliers_bulk` | `ScenarioMultipliersBulkUpdate`, Query: organization_id, scenario_code | `EnrollmentSettingsResponse` |
| POST | `/reset-overrides` | `reset_all_overrides` | Query: organization_id, scenario_code | `EnrollmentSettingsResponse` |
| POST | `/reset-multipliers` | `reset_scenario_multipliers` | Query: organization_id, scenario_code | `EnrollmentSettingsResponse` |

---

### 2.5 Costs & Revenue API (`/api/v1/planning`)
**File:** `backend/app/api/v1/costs.py`
**Services:** `RevenueService`, `CostService`, `CapExService`

| Method | Endpoint | Handler | Request Schema | Response Schema |
|--------|----------|---------|----------------|-----------------|
| GET | `/revenue/{version_id}` | `get_revenue_plan` | - | `list[RevenuePlanResponse]` |
| POST | `/revenue/{version_id}/calculate` | `calculate_revenue` | - | MessageResponse |
| POST | `/revenue/{version_id}` | `create_revenue_entry` | `RevenuePlanCreate` | `RevenuePlanResponse` |
| GET | `/revenue/{version_id}/summary` | `get_revenue_summary` | - | dict |
| GET | `/revenue/item/{item_id}` | `get_revenue_item` | - | `RevenuePlanResponse` |
| PUT | `/revenue/{item_id}` | `update_revenue_entry` | `RevenuePlanUpdate` | `RevenuePlanResponse` |
| DELETE | `/revenue/{item_id}` | `delete_revenue_entry` | - | 204 No Content |
| POST | `/revenue/{version_id}/bulk-update` | `bulk_update_revenue_entries` | `RevenueBulkUpdateRequest` | `RevenueBulkUpdateResponse` |
| GET | `/costs/personnel/{version_id}` | `get_personnel_costs` | - | `list[PersonnelCostPlanResponse]` |
| POST | `/costs/personnel/{version_id}/calculate` | `calculate_personnel_costs` | - | MessageResponse |
| POST | `/costs/personnel/{version_id}` | `create_personnel_cost_entry` | `PersonnelCostPlanCreate` | `PersonnelCostPlanResponse` |
| GET | `/costs/operating/{version_id}` | `get_operating_costs` | - | `list[OperatingCostPlanResponse]` |
| POST | `/costs/operating/{version_id}/calculate` | `calculate_operating_costs` | - | MessageResponse |
| POST | `/costs/operating/{version_id}` | `create_operating_cost_entry` | `OperatingCostPlanCreate` | `OperatingCostPlanResponse` |
| GET | `/costs/{version_id}/summary` | `get_cost_summary` | - | dict |
| GET | `/capex/{version_id}` | `get_capex_plan` | - | `list[CapExPlanResponse]` |
| POST | `/capex/{version_id}` | `create_capex_entry` | `CapExPlanCreate` | `CapExPlanResponse` |
| PUT | `/capex/{version_id}/{capex_id}` | `update_capex_entry` | `CapExPlanUpdate` | `CapExPlanResponse` |
| DELETE | `/capex/{version_id}/{capex_id}` | `delete_capex_entry` | - | 204 No Content |
| POST | `/capex/{capex_id}/depreciation` | `calculate_depreciation` | - | `DepreciationCalculationResponse` |
| GET | `/capex/{capex_id}/depreciation-schedule` | `get_depreciation_schedule` | - | dict |
| GET | `/capex/{version_id}/summary` | `get_capex_summary` | - | dict |
| GET | `/capex/{version_id}/depreciation/{year}` | `get_annual_depreciation` | - | dict |

---

### 2.6 Workforce API (`/api/v1/workforce`)
**File:** `backend/app/api/v1/workforce.py`
**Services:** `EmployeeService`, `AEFEService`

| Method | Endpoint | Handler | Request Schema | Response Schema |
|--------|----------|---------|----------------|-----------------|
| GET | `/employees/{version_id}` | `get_employees` | Query: filters | `EmployeeBulkResponse` |
| GET | `/employees/{version_id}/{employee_id}` | `get_employee` | - | `EmployeeResponse` |
| POST | `/employees` | `create_employee` | `EmployeeCreate` | `EmployeeResponse` |
| PUT | `/employees/{employee_id}` | `update_employee` | `EmployeeUpdate` | `EmployeeResponse` |
| DELETE | `/employees/{employee_id}` | `delete_employee` | - | 204 No Content |
| POST | `/employees/placeholder` | `create_placeholder_employee` | `PlaceholderEmployeeCreate` | `EmployeeResponse` |
| POST | `/employees/{employee_id}/validate` | `validate_placeholder_employee` | `PlaceholderValidationRequest` | `EmployeeResponse` |
| GET | `/employees/{employee_id}/salary` | `get_employee_salary` | - | `EmployeeSalaryResponse` |
| GET | `/employees/{employee_id}/salary/history` | `get_salary_history` | - | `list[EmployeeSalaryResponse]` |
| POST | `/employees/{employee_id}/salary` | `add_employee_salary` | `EmployeeSalaryCreate` | `EmployeeSalaryResponse` |
| POST | `/eos/calculate` | `calculate_eos_preview` | `EOSCalculationRequest` | `EOSCalculationResponse` |
| GET | `/employees/{employee_id}/eos` | `get_eos_provision` | - | `EOSProvisionResponse` |
| POST | `/employees/{employee_id}/eos` | `calculate_employee_eos_provision` | - | `EOSProvisionResponse` |
| POST | `/eos/calculate-all/{version_id}` | `calculate_all_eos` | - | MessageResponse |
| GET | `/eos/summary/{version_id}` | `get_eos_summary` | - | `EOSSummaryResponse` |
| PUT | `/aefe-positions/{version_id}/prrd-rate` | `update_prrd_rate` | body: rate | MessageResponse |
| POST | `/aefe-positions/initialize` | `initialize_aefe_positions` | `InitializeAEFEPositionsRequest` | `list[AEFEPositionResponse]` |
| GET | `/aefe-positions/{version_id}` | `get_aefe_positions` | - | `list[AEFEPositionResponse]` |
| PUT | `/aefe-positions/{position_id}` | `update_aefe_position` | `AEFEPositionUpdate` | `AEFEPositionResponse` |
| POST | `/aefe-positions/{position_id}/assign` | `assign_aefe_position` | body: employee_id | `AEFEPositionResponse` |
| POST | `/aefe-positions/{position_id}/unassign` | `unassign_aefe_position` | - | `AEFEPositionResponse` |
| GET | `/aefe-positions/{version_id}/summary` | `get_aefe_positions_summary` | - | `AEFEPositionSummaryResponse` |
| GET | `/summary/{version_id}` | `get_workforce_summary` | - | `WorkforceSummaryResponse` |

---

### 2.7 Consolidation API (`/api/v1/consolidation`)
**File:** `backend/app/api/v1/consolidation.py`
**Services:** `ConsolidationService`, `FinancialStatementsService`

| Method | Endpoint | Handler | Request Schema | Response Schema |
|--------|----------|---------|----------------|-----------------|
| GET | `/{version_id}/status` | `get_consolidation_status` | - | `ConsolidationStatusResponse` |
| GET | `/{version_id}` | `get_consolidated_budget` | - | `BudgetConsolidationResponse` |
| POST | `/{version_id}/consolidate` | `consolidate_budget` | `ConsolidationRequest` | `BudgetConsolidationResponse` |
| POST | `/{version_id}/submit` | `submit_for_approval` | `SubmitForApprovalRequest` | `WorkflowActionResponse` |
| POST | `/{version_id}/approve` | `approve_budget` | `ApprovebudgetRequest` | `WorkflowActionResponse` |
| GET | `/{version_id}/validation` | `validate_budget_completeness` | - | `ConsolidationValidationResponse` |
| GET | `/{version_id}/summary` | `get_consolidation_summary` | - | `ConsolidationSummary` |
| GET | `/{version_id}/statements/income` | `get_income_statement` | Query: format | `IncomeStatementResponse` |
| GET | `/{version_id}/statements/balance` | `get_balance_sheet` | - | `BalanceSheetResponse` |
| GET | `/{version_id}/statements/periods` | `get_period_totals` | - | `list[FinancialPeriodTotals]` |
| GET | `/{version_id}/statements/periods/{period}` | `get_period_total` | - | `FinancialPeriodTotals` |
| GET | `/{version_id}/statements/{statement_type}` | `get_financial_statement` | Query: format, period | varies |

---

### 2.8 Analysis API (`/api/v1/analysis`)
**File:** `backend/app/api/v1/analysis.py`
**Services:** `KPIService`, `DashboardService`, `BudgetActualService`, `StrategicService`, `MaterializedViewService`

| Method | Endpoint | Handler | Request Schema | Response Schema |
|--------|----------|---------|----------------|-----------------|
| POST | `/kpis/{version_id}/calculate` | `calculate_kpis` | `KPICalculationRequest` | `MessageResponse` |
| GET | `/kpis/{version_id}` | `get_all_kpis` | - | `list[KPIValueResponse]` |
| GET | `/kpis/{version_id}/{kpi_code}` | `get_kpi_by_type` | - | `KPIValueResponse` |
| GET | `/kpis/trends/{kpi_code}` | `get_kpi_trends` | Query: years | `KPITrendResponse` |
| GET | `/kpis/{version_id}/benchmarks` | `get_benchmark_comparison` | - | `dict[str, KPIBenchmarkComparison]` |
| GET | `/dashboard/{version_id}/summary` | `get_dashboard_summary` | - | `DashboardSummaryResponse` |
| GET | `/dashboard/{version_id}/charts/enrollment` | `get_enrollment_chart` | - | `ChartDataResponse` |
| GET | `/dashboard/{version_id}/charts/costs` | `get_cost_breakdown_chart` | - | `ChartDataResponse` |
| GET | `/dashboard/{version_id}/charts/revenue` | `get_revenue_breakdown_chart` | - | `ChartDataResponse` |
| GET | `/dashboard/{version_id}/alerts` | `get_alerts` | - | `list[AlertResponse]` |
| GET | `/dashboard/{version_id}/activity` | `get_recent_activity` | Query: limit | `list[ActivityLogEntry]` |
| GET | `/activity` | `get_recent_activity_no_version` | Query: limit | `list[ActivityLogEntry]` |
| GET | `/dashboard/compare` | `get_comparison_data` | Query: version_ids | `ComparisonResponse` |
| POST | `/actuals/{version_id}/import` | `import_actuals` | File upload | MessageResponse |
| POST | `/actuals/{version_id}/calculate-variance` | `calculate_variance` | - | `MessageResponse` |
| GET | `/actuals/{version_id}/variance` | `get_variance_report` | - | `VarianceReportResponse` |
| POST | `/actuals/{version_id}/forecast` | `create_forecast_revision` | body | `ForecastRevisionResponse` |
| POST | `/strategic-plans` | `create_strategic_plan` | body | `StrategicPlanResponse` |
| GET | `/strategic-plans/{plan_id}` | `get_strategic_plan` | - | `StrategicPlanResponse` |
| GET | `/strategic-plans/{plan_id}/year/{year}` | `get_year_projection` | - | `YearProjectionResponse` |
| PUT | `/strategic-plans/scenarios/{scenario_id}/assumptions` | `update_scenario_assumptions` | body | `MessageResponse` |
| GET | `/strategic-plans/{plan_id}/scenarios` | `compare_scenarios` | - | `ScenarioComparisonResponse` |
| POST | `/strategic-plans/{plan_id}/initiatives` | `add_initiative` | body | `StrategicInitiativeResponse` |
| POST | `/materialized-views/refresh-all` | `refresh_all_materialized_views` | - | MessageResponse |
| POST | `/materialized-views/refresh/{view_name}` | `refresh_specific_materialized_view` | - | MessageResponse |
| GET | `/materialized-views/info/{view_name}` | `get_materialized_view_info` | - | dict |

---

### 2.9 Historical Comparison API (`/api/v1/historical`)
**File:** `backend/app/api/v1/historical.py`
**Service:** `HistoricalComparisonService`

| Method | Endpoint | Handler | Request Schema | Response Schema |
|--------|----------|---------|----------------|-----------------|
| GET | `/enrollment/{version_id}` | `get_enrollment_with_history` | Query: history_years | `EnrollmentWithHistoryResponse` |
| GET | `/classes/{version_id}` | `get_classes_with_history` | Query: history_years | `ClassStructureWithHistoryResponse` |
| GET | `/dhg/{version_id}` | `get_dhg_with_history` | Query: history_years | `DHGWithHistoryResponse` |
| GET | `/revenue/{version_id}` | `get_revenue_with_history` | Query: history_years | `RevenueWithHistoryResponse` |
| GET | `/costs/{version_id}` | `get_costs_with_history` | Query: history_years | `CostsWithHistoryResponse` |
| GET | `/capex/{version_id}` | `get_capex_with_history` | Query: history_years | `CapExWithHistoryResponse` |

---

### 2.10 Writeback API (`/api/v1/writeback`)
**File:** `backend/app/api/v1/writeback.py`
**Service:** `WritebackService`

| Method | Endpoint | Handler | Request Schema | Response Schema |
|--------|----------|---------|----------------|-----------------|
| GET | `/cells/{cell_id}` | `get_cell` | - | `CellResponse` |
| POST | `/cells` | `create_cell` | `CellCreateRequest` | `CellResponse` |
| PUT | `/cells/{cell_id}` | `update_cell` | `CellUpdateRequest` | `CellUpdateResponse` |
| POST | `/cells/batch` | `batch_update_cells` | `BatchUpdateRequest` | `BatchUpdateResponse` |
| GET | `/cells/changes/{version_id}` | `get_change_history` | Query: filters | `list[CellChangeResponse]` |
| POST | `/cells/undo` | `undo_changes` | `UndoRequest` | `UndoResponse` |
| POST | `/cells/{cell_id}/comments` | `add_cell_comment` | `CommentRequest` | `CommentResponse` |
| GET | `/cells/{cell_id}/comments` | `get_cell_comments` | - | `CommentListResponse` |
| POST | `/comments/{comment_id}/resolve` | `resolve_comment` | `ResolveCommentRequest` | `CommentResponse` |
| POST | `/cells/{cell_id}/lock` | `lock_cell` | `LockRequest` | `CellLockResponse` |
| DELETE | `/cells/{cell_id}/lock` | `unlock_cell` | - | `CellLockResponse` |
| GET | `/health` | `health_check` | - | dict |

---

## 3. Services

### Location: `backend/app/services/`

| Service Class | File | Primary Models Used |
|---------------|------|---------------------|
| `BaseService[T]` | `base.py` | Generic (any model) |
| `ConfigurationService` | `configuration_service.py` | `BudgetVersion`, `SystemConfig`, `AcademicCycle`, `AcademicLevel`, `ClassSizeParam`, `Subject`, `SubjectHoursMatrix`, `TeacherCategory`, `TeacherCostParam`, `FeeCategory`, `NationalityType`, `FeeStructure`, `TimetableConstraint` |
| `BudgetVersionService` | `budget_version_service.py` | `BudgetVersion` |
| `EnrollmentService` | `enrollment_service.py` | `EnrollmentPlan`, `NationalityDistribution`, `AcademicLevel` |
| `EnrollmentProjectionService` | `enrollment_projection_service.py` | `EnrollmentProjectionConfig`, `EnrollmentProjection`, `EnrollmentGlobalOverride`, `EnrollmentLevelOverride`, `EnrollmentGradeOverride`, `EnrollmentScenario` |
| `EnrollmentCalibrationService` | `enrollment_calibration_service.py` | `EnrollmentDerivedParameter`, `EnrollmentParameterOverride`, `EnrollmentScenarioMultiplier`, `HistoricalActuals` |
| `ClassStructureService` | `class_structure_service.py` | `ClassStructure`, `EnrollmentPlan`, `ClassSizeParam` |
| `DHGService` | `dhg_service.py` | `DHGSubjectHours`, `DHGTeacherRequirement`, `TeacherAllocation`, `SubjectHoursMatrix`, `ClassStructure` |
| `RevenueService` | `revenue_service.py` | `RevenuePlan`, `FeeStructure`, `EnrollmentPlan` |
| `CostService` | `cost_service.py` | `PersonnelCostPlan`, `OperatingCostPlan`, `Employee`, `DHGTeacherRequirement` |
| `CapExService` | `capex_service.py` | `CapExPlan` |
| `ConsolidationService` | `consolidation_service.py` | `BudgetConsolidation`, `RevenuePlan`, `PersonnelCostPlan`, `OperatingCostPlan`, `CapExPlan`, `BudgetVersion` |
| `FinancialStatementsService` | `financial_statements_service.py` | `FinancialStatement`, `FinancialStatementLine`, `BudgetConsolidation` |
| `EmployeeService` | `employee_service.py` | `Employee`, `EmployeeSalary`, `EOSProvision` |
| `AEFEService` | `aefe_service.py` | `AEFEPosition`, `Employee` |
| `KPIService` | `kpi_service.py` | `KPIDefinition`, `KPIValue`, `BudgetConsolidation` |
| `DashboardService` | `dashboard_service.py` | `DashboardConfig`, `DashboardWidget`, `KPIValue` |
| `BudgetActualService` | `budget_actual_service.py` | `ActualData`, `BudgetVsActual`, `VarianceExplanation` |
| `StrategicService` | `strategic_service.py` | `StrategicPlan`, `StrategicPlanScenario`, `StrategicPlanProjection`, `StrategicInitiative` |
| `WritebackService` | `writeback_service.py` | Cell data (generic), audit logs |
| `HistoricalComparisonService` | `historical_comparison_service.py` | `HistoricalActuals`, `EnrollmentPlan`, `DHGSubjectHours`, `RevenuePlan`, `PersonnelCostPlan`, `OperatingCostPlan`, `CapExPlan` |
| `PlanningProgressService` | `planning_progress_service.py` | All planning models |
| `CascadeService` | `cascade_service.py` | All planning models |
| `ImpactCalculatorService` | `impact_calculator_service.py` | All planning models |
| `MaterializedViewService` | `materialized_view_service.py` | Materialized views |
| `HistoricalImportService` | `historical_import_service.py` | `HistoricalActuals` |
| `ReferenceDataService` | `reference_data_service.py` | Reference tables (`ref_*`) |
| `ClassSizeService` | `class_size_service.py` | `ClassSizeParam` |
| `SubjectHoursService` | `subject_hours_service.py` | `SubjectHoursMatrix`, `Subject` |
| `TeacherCostParametersService` | `teacher_cost_service.py` | `TeacherCostParam`, `TeacherCategory` |
| `FeeStructureService` | `fee_structure_service.py` | `FeeStructure`, `FeeCategory` |
| `TimetableConstraintsService` | `timetable_constraints_service.py` | `TimetableConstraint` |

---

## 4. Calculation Engines

### Location: `backend/app/engine/`

Pure calculation functions with no database access. Each engine follows the pattern:
- **Input Model**: Pydantic `BaseModel` with `frozen=True`
- **Calculator Function**: Pure function `calculate_*(input) -> output`
- **Output Model**: Pydantic `BaseModel` with results

### 4.1 Students Module (`engine/students/` and `engine/enrollment/`)

| Engine | Calculator Functions | Input Data | Output Data |
|--------|---------------------|------------|-------------|
| **Enrollment Projection** | `calculate_enrollment_projection()`, `apply_retention_model()`, `calculate_attrition()`, `calculate_multi_level_total()` | Historical enrollment, retention rates, lateral entry rates | Projected enrollment by grade/year |
| **Fiscal Year Proration** | `calculate_fiscal_proration()` | Enrollment counts, academic calendar | Prorated counts for fiscal year |
| **Calibration** | `calibrate_parameters()` | Historical enrollment data | Derived retention rates, lateral entry rates |
| **Lateral Optimizer** | `optimize_lateral_entry()` | Class capacity, demand | Optimal lateral entry with class structure awareness |

### 4.2 Teachers Module (`engine/teachers/` and `engine/dhg/`, `engine/eos/`, `engine/gosi/`)

| Engine | Calculator Functions | Input Data | Output Data |
|--------|---------------------|------------|-------------|
| **DHG (Workforce)** | `calculate_dhg_hours()`, `calculate_fte_from_hours()`, `calculate_teacher_requirement()`, `calculate_hsa_allocation()`, `calculate_aggregated_dhg_hours()`, `calculate_trmd_gap()` | Class structure, subject hours matrix, teacher categories | Total teaching hours, FTE requirements, HSA hours, gap analysis |
| **EOS (End of Service)** | `calculate_eos()`, `calculate_eos_provision()` | Employee tenure, salary, nationality, termination type | EOS entitlement (0.5 months/year 1-5, 1.0 month/year 6+) |
| **GOSI (Social Insurance)** | `calculate_gosi()`, `calculate_monthly_gosi()`, `get_gosi_rates()` | Employee salary, nationality | GOSI contributions (21.5% Saudi, 2% Expat) |

### 4.3 Finance Module (`engine/finance/` and `engine/revenue/`, `engine/financial_statements/`)

| Engine | Calculator Functions | Input Data | Output Data |
|--------|---------------------|------------|-------------|
| **Revenue** | `calculate_sibling_discount()`, `calculate_tuition_revenue()`, `calculate_trimester_distribution()`, `calculate_total_student_revenue()`, `calculate_aggregate_revenue()`, `calculate_revenue_by_level()`, `calculate_revenue_by_category()` | Fee structure, enrollment, sibling counts | Revenue by category/level, trimester distribution |
| **Financial Statements** | `calculate_operating_result()`, `calculate_period_totals()`, `format_statement_line()`, `generate_income_statement_lines()`, `calculate_income_statement()`, `generate_balance_sheet_lines()`, `calculate_balance_sheet()`, `generate_cash_flow_lines()`, `calculate_cash_flow_statement()` | Consolidated budget data | PCG/IFRS formatted statements |

### 4.4 Insights Module (`engine/insights/` and `engine/kpi/`)

| Engine | Calculator Functions | Input Data | Output Data |
|--------|---------------------|------------|-------------|
| **KPI** | `calculate_student_teacher_ratio()`, `calculate_he_ratio_secondary()`, `calculate_revenue_per_student()`, `calculate_cost_per_student()`, `calculate_margin_percentage()`, `calculate_staff_cost_ratio()`, `calculate_capacity_utilization()`, `calculate_all_kpis()` | Enrollment, staffing, financials | All KPI values with benchmarks |

---

## 5. Database Models

### Location: `backend/app/models/`
### Schema: `efir_budget`

### 5.1 Base Classes (`base.py`)

| Class | Description |
|-------|-------------|
| `AuditMixin` | `created_at`, `updated_at`, `created_by`, `updated_by` |
| `SoftDeleteMixin` | `deleted_at`, `deleted_by`, `is_deleted` |
| `VersionedMixin` | `version_id` FK to BudgetVersion |
| `BaseModel` | Combines `Base` + `AuditMixin` + `SoftDeleteMixin` |
| `ReferenceDataModel` | For reference tables (no version, has `is_active`) |

### 5.2 Configuration Models (`configuration.py`)

| Model | Table Name | Key Columns |
|-------|------------|-------------|
| `SystemConfig` | `settings_system_configs` | `key`, `value`, `category`, `description` |
| `BudgetVersion` | `settings_budget_versions` | `id`, `name`, `fiscal_year`, `academic_year`, `status`, `organization_id`, `parent_version_id` |
| `AcademicCycle` | `ref_academic_cycles` | `id`, `code`, `name_fr`, `name_en`, `display_order` |
| `AcademicLevel` | `ref_academic_levels` | `id`, `code`, `name_fr`, `name_en`, `cycle_id`, `year_in_cycle`, `display_order` |
| `ClassSizeParam` | `settings_class_size_params` | `id`, `version_id`, `level_id`, `cycle_id`, `min_class_size`, `target_class_size`, `max_class_size` |
| `Subject` | `ref_subjects` | `id`, `code`, `name_fr`, `name_en`, `category` |
| `SubjectHoursMatrix` | `settings_subject_hours_matrix` | `id`, `version_id`, `subject_id`, `level_id`, `hours_per_week`, `is_split` |
| `TeacherCategory` | `ref_teacher_categories` | `id`, `code`, `name_fr`, `name_en`, `is_aefe`, `max_teaching_hours` |
| `TeacherCostParam` | `settings_teacher_cost_params` | `id`, `version_id`, `category_id`, `cycle_id`, `prrd_contribution_eur`, `avg_salary_sar`, `social_charges_rate`, `hsa_hourly_rate_sar` |
| `FeeCategory` | `ref_fee_categories` | `id`, `code`, `name_fr`, `name_en`, `is_mandatory` |
| `NationalityType` | `ref_nationality_types` | `id`, `code`, `name_fr`, `name_en` |
| `FeeStructure` | `settings_fee_structures` | `id`, `version_id`, `level_id`, `nationality_type_id`, `fee_category_id`, `amount_sar`, `trimester` |
| `TimetableConstraint` | `settings_timetable_constraints` | `id`, `version_id`, `level_id`, `total_hours_per_week`, `max_hours_per_day`, `days_per_week` |

### 5.3 Planning Models (`planning.py`)

| Model | Table Name | Key Columns |
|-------|------------|-------------|
| `EnrollmentPlan` | `students_enrollment_plans` | `id`, `version_id`, `level_id`, `nationality_type_id`, `student_count` |
| `NationalityDistribution` | `students_nationality_distributions` | `id`, `version_id`, `level_id`, `french_pct`, `saudi_pct`, `other_pct` |
| `ClassStructure` | `students_class_structures` | `id`, `version_id`, `level_id`, `total_students`, `number_of_classes`, `avg_class_size`, `requires_atsem`, `atsem_count` |
| `DHGSubjectHours` | `teachers_dhg_subject_hours` | `id`, `version_id`, `subject_id`, `level_id`, `cycle_id`, `hours_per_class`, `total_hours` |
| `DHGTeacherRequirement` | `teachers_dhg_requirements` | `id`, `version_id`, `subject_id`, `cycle_id`, `total_hours_needed`, `fte_required`, `fte_allocated` |
| `TeacherAllocation` | `teachers_allocations` | `id`, `version_id`, `subject_id`, `cycle_id`, `category_id`, `fte_count` |
| `RevenuePlan` | `finance_revenue_plans` | `id`, `version_id`, `account_code`, `account_name`, `level_id`, `fee_category_id`, `amount_sar`, `trimester` |
| `PersonnelCostPlan` | `finance_personnel_cost_plans` | `id`, `version_id`, `account_code`, `account_name`, `employee_id`, `category_id`, `base_salary_sar`, `gosi_sar`, `eos_sar`, `total_cost_sar` |
| `OperatingCostPlan` | `finance_operating_cost_plans` | `id`, `version_id`, `account_code`, `account_name`, `cost_category`, `amount_sar`, `period` |
| `CapExPlan` | `finance_capex_plans` | `id`, `version_id`, `account_code`, `asset_name`, `acquisition_cost_sar`, `useful_life_years`, `depreciation_method`, `annual_depreciation_sar` |

### 5.4 Personnel Models (`personnel.py`)

| Model | Table Name | Key Columns |
|-------|------------|-------------|
| `Employee` | `teachers_employees` | `id`, `version_id`, `employee_code`, `first_name`, `last_name`, `category` (RESIDENT/EXPAT/AEFE_DETACHED/AEFE_FUNDED), `nationality`, `hire_date`, `is_placeholder` |
| `EmployeeSalary` | `teachers_employee_salaries` | `id`, `version_id`, `employee_id`, `effective_date`, `base_salary_sar`, `housing_allowance_sar`, `transport_allowance_sar` |
| `EOSProvision` | `teachers_eos_provisions` | `id`, `version_id`, `employee_id`, `provision_date`, `years_of_service`, `provision_amount_sar`, `termination_type` |
| `AEFEPosition` | `teachers_aefe_positions` | `id`, `version_id`, `position_code`, `position_type` (DETACHED/FUNDED), `subject_id`, `cycle_id`, `employee_id`, `prrd_contribution_eur` |

### 5.5 Consolidation Models (`consolidation.py`)

| Model | Table Name | Key Columns |
|-------|------------|-------------|
| `BudgetConsolidation` | `finance_budget_consolidations` | `id`, `version_id`, `account_code`, `account_name`, `consolidation_category`, `is_revenue`, `amount_sar`, `source_table` |
| `FinancialStatement` | `finance_financial_statements` | `id`, `version_id`, `statement_type` (INCOME/BALANCE/CASHFLOW), `statement_format` (PCG/IFRS), `fiscal_year`, `total_amount_sar` |
| `FinancialStatementLine` | `finance_financial_statement_lines` | `id`, `statement_id`, `line_code`, `line_name`, `line_type` (HEADER/DETAIL/SUBTOTAL/TOTAL), `amount_sar`, `display_order` |

### 5.6 Analysis Models (`analysis.py`)

| Model | Table Name | Key Columns |
|-------|------------|-------------|
| `KPIDefinition` | `insights_kpi_definitions` | `id`, `kpi_code`, `name_fr`, `name_en`, `category`, `formula`, `benchmark_value`, `unit` |
| `KPIValue` | `insights_kpi_values` | `id`, `version_id`, `kpi_definition_id`, `calculated_value`, `benchmark_comparison` |
| `DashboardConfig` | `insights_dashboard_configs` | `id`, `dashboard_code`, `name`, `role`, `layout_json` |
| `DashboardWidget` | `insights_dashboard_widgets` | `id`, `dashboard_id`, `widget_type`, `config_json`, `position_json` |
| `UserPreferences` | `admin_user_preferences` | `id`, `user_id`, `preferences_json` |
| `ActualData` | `finance_actual_data` | `id`, `organization_id`, `account_code`, `fiscal_year`, `period`, `amount_sar`, `source` (ODOO/MANUAL) |
| `BudgetVsActual` | `finance_budget_vs_actual` | `id`, `version_id`, `account_code`, `budget_amount_sar`, `actual_amount_sar`, `variance_sar`, `variance_pct`, `status` |
| `VarianceExplanation` | `finance_variance_explanations` | `id`, `budget_vs_actual_id`, `explanation`, `action_items` |
| `HistoricalActuals` | `admin_historical_actuals` | `id`, `organization_id`, `module_code`, `dimension_type`, `dimension_id`, `academic_year`, `value`, `data_source` |

### 5.7 Strategic Models (`strategic.py`)

| Model | Table Name | Key Columns |
|-------|------------|-------------|
| `StrategicPlan` | `insights_strategic_plans` | `id`, `name`, `base_version_id`, `start_year`, `end_year`, `description` |
| `StrategicPlanScenario` | `insights_strategic_plan_scenarios` | `id`, `plan_id`, `scenario_type` (BASE/OPTIMISTIC/PESSIMISTIC/CUSTOM), `assumptions_json` |
| `StrategicPlanProjection` | `insights_strategic_plan_projections` | `id`, `scenario_id`, `fiscal_year`, `category`, `projected_value` |
| `StrategicInitiative` | `insights_strategic_initiatives` | `id`, `plan_id`, `name`, `description`, `status`, `start_date`, `end_date`, `budget_impact_sar` |

### 5.8 Enrollment Projection Models (`enrollment_projection.py`)

| Model | Table Name | Key Columns |
|-------|------------|-------------|
| `EnrollmentScenario` | `ref_enrollment_scenarios` | `id`, `code`, `name_fr`, `name_en`, `description`, `multiplier` |
| `EnrollmentLateralEntryDefault` | `ref_enrollment_lateral_defaults` | `id`, `grade_code`, `default_rate`, `is_entry_point` |
| `EnrollmentProjectionConfig` | `students_enrollment_projection_configs` | `id`, `version_id`, `scenario_id`, `base_year`, `projection_years`, `is_validated` |
| `EnrollmentGlobalOverride` | `students_enrollment_global_overrides` | `id`, `config_id`, `new_ms_rate`, `new_gs_rate`, `global_retention_adj` |
| `EnrollmentLevelOverride` | `students_enrollment_level_overrides` | `id`, `config_id`, `cycle_code`, `retention_adj`, `lateral_adj` |
| `EnrollmentGradeOverride` | `students_enrollment_grade_overrides` | `id`, `config_id`, `grade_code`, `fixed_total`, `fixed_lateral`, `retention_override` |
| `EnrollmentProjection` | `students_enrollment_projections` | `id`, `config_id`, `grade_code`, `academic_year`, `retained`, `lateral_entry`, `new_students`, `departures`, `total` |
| `EnrollmentDerivedParameter` | `students_enrollment_derived_params` | `id`, `organization_id`, `grade_code`, `derived_rate`, `confidence`, `sample_size`, `calibrated_at` |
| `EnrollmentParameterOverride` | `students_enrollment_param_overrides` | `id`, `organization_id`, `grade_code`, `override_enabled`, `manual_rate`, `manual_retention` |
| `EnrollmentScenarioMultiplier` | `students_enrollment_scenario_multipliers` | `id`, `organization_id`, `scenario_code`, `multiplier` |

### 5.9 Integration Models (`integrations.py`)

| Model | Table Name | Key Columns |
|-------|------------|-------------|
| `IntegrationLog` | `admin_integration_logs` | `id`, `integration_type`, `operation`, `status`, `records_processed`, `error_message`, `started_at`, `completed_at` |
| `IntegrationSettings` | `admin_integration_settings` | `id`, `organization_id`, `integration_type`, `is_enabled`, `config_json`, `last_sync_at` |

### 5.10 Auth Models (`auth.py`)

| Model | Table Name | Key Columns |
|-------|------------|-------------|
| `User` | `admin_users` | `id`, `email`, `full_name`, `role`, `organization_id`, `is_active` |
| `Organization` | `admin_organizations` | `id`, `name`, `code`, `is_active` |

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Pydantic Schemas** | ~200 classes |
| **API Endpoints** | ~150 routes |
| **Services** | 35 classes |
| **Engine Functions** | 45 functions |
| **Database Models** | 45 models |
| **Database Tables** | 45 tables |

---

*Generated: 2025-12-15*
