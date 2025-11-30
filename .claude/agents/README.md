# EFIR Budget Planning Application - Multi-Agent System

This directory contains the specialized agents for the EFIR Budget Planning Application. The multi-agent architecture ensures clear separation of concerns, domain expertise, and efficient collaboration.

## Agent Structure Overview

### Orchestrator
- **efir_master_agent** - Top-level orchestrator that routes tasks to specialized agents

### Architecture & Requirements Agents
- **product_architect_agent** - Guardian of PRD, FRS, and business rules
- **system_architect_agent** - Owns global architecture and design patterns
- **documentation_training_agent** - Creates all documentation and training materials

### Backend Agents
- **database_supabase_agent** - PostgreSQL schema, RLS policies, migrations
- **backend_engine_agent** - Calculation engines (Enrollment, DHG, Revenue, etc.)
- **backend_api_agent** - FastAPI endpoints and API logic

### Frontend Agents
- **frontend_ui_agent** - React UI, components, and all 17 modules

### Cross-Cutting Agents
- **governance_versioning_agent** - Lifecycle management and audit trails
- **reporting_statements_agent** - PCG/IFRS statements and Board reports
- **security_rls_agent** - Authentication, MFA, and security policies
- **data_migration_agent** - ETL and data import from legacy systems
- **performance_agent** - Profiling, optimization, and load testing
- **qa_validation_agent** - Test coverage and quality assurance

## How to Use the Agents

### Starting a Task

When you start a new task, the **efir_master_agent** will:
1. Analyze your request
2. Determine which specialized agent(s) should handle it
3. Delegate to the appropriate agent(s)
4. Ensure alignment with PRD/FRS
5. Coordinate multi-agent workflows if needed

### Agent Collaboration Flow

```
User Request
    ↓
efir_master_agent (orchestrator)
    ↓
├─→ product_architect_agent (validates requirements)
├─→ system_architect_agent (defines architecture)
├─→ database_supabase_agent (implements database)
├─→ backend_engine_agent (implements calculations)
├─→ backend_api_agent (exposes APIs)
├─→ frontend_ui_agent (builds UI)
├─→ security_rls_agent (secures system)
└─→ qa_validation_agent (validates quality)
```

### Typical Workflows

#### Adding a New Feature
1. **product_architect_agent** - Validates alignment with PRD/FRS
2. **system_architect_agent** - Designs architecture approach
3. **database_supabase_agent** - Creates database schema
4. **backend_engine_agent** - Implements calculation logic
5. **backend_api_agent** - Exposes API endpoints
6. **frontend_ui_agent** - Builds user interface
7. **qa_validation_agent** - Creates and runs tests

#### Fixing a Bug
1. **efir_master_agent** - Routes to appropriate agent
2. Relevant agent investigates and fixes
3. **qa_validation_agent** - Adds regression test

#### Creating a Report
1. **product_architect_agent** - Validates reporting requirements
2. **backend_engine_agent** - Provides calculation data
3. **reporting_statements_agent** - Generates report
4. **qa_validation_agent** - Validates accuracy

#### Importing Data
1. **product_architect_agent** - Validates business rules
2. **data_migration_agent** - Implements ETL logic
3. **database_supabase_agent** - Validates schema compatibility
4. **qa_validation_agent** - Tests import process

## Agent Dependencies

### No Dependencies
- **product_architect_agent** (source of requirements)

### Depends on Product Architect
- **system_architect_agent**
- **documentation_training_agent**

### Depends on System Architect
- **database_supabase_agent**
- **backend_engine_agent**
- **backend_api_agent**
- **frontend_ui_agent**
- **security_rls_agent**

### Depends on Backend Engine
- **backend_api_agent**
- **reporting_statements_agent**
- **performance_agent**

### Depends on Multiple Agents
- **qa_validation_agent** (validates all agents' outputs)
- **efir_master_agent** (coordinates all agents)

## Agent Capabilities Matrix

| Agent | Edit Code | Edit Docs | Write SQL | Create APIs | Define Requirements |
|-------|-----------|-----------|-----------|-------------|---------------------|
| efir_master_agent | ❌ | ✅ | ❌ | ❌ | ❌ |
| product_architect_agent | ❌ | ✅ | ❌ | ❌ | ✅ |
| system_architect_agent | ✅ | ✅ | ❌ | ❌ | ❌ |
| database_supabase_agent | ✅ | ✅ | ✅ | ❌ | ❌ |
| backend_engine_agent | ✅ | ❌ | ❌ | ❌ | ❌ |
| backend_api_agent | ✅ | ❌ | ❌ | ✅ | ❌ |
| frontend_ui_agent | ✅ | ❌ | ❌ | ❌ | ❌ |
| governance_versioning_agent | ✅ | ❌ | ❌ | ❌ | ❌ |
| reporting_statements_agent | ✅ | ❌ | ❌ | ❌ | ❌ |
| security_rls_agent | ✅ | ✅ | ✅ | ❌ | ❌ |
| data_migration_agent | ✅ | ❌ | ❌ | ❌ | ❌ |
| performance_agent | ✅ | ❌ | ❌ | ❌ | ❌ |
| documentation_training_agent | ❌ | ✅ | ❌ | ❌ | ❌ |
| qa_validation_agent | ✅ | ❌ | ❌ | ❌ | ❌ |

## Key Principles

### 1. Single Responsibility
Each agent has a clear, focused domain of expertise.

### 2. Clear Boundaries
Agents respect module boundaries and don't cross into other agents' domains.

### 3. Requirements First
All implementation agents consult **product_architect_agent** for business rules.

### 4. Architecture Consistency
All implementation agents follow patterns from **system_architect_agent**.

### 5. Quality Gates
**qa_validation_agent** validates all changes before deployment.

### 6. Security by Design
**security_rls_agent** ensures security at all layers.

## Getting Started

To invoke a specific agent, you can use the Claude Code agent invocation system. The **efir_master_agent** will automatically route your requests to the appropriate specialized agent based on the task.

## Agent Communication

Agents communicate through:
- **Shared documentation** (PRD, FRS, Technical Specs)
- **Well-defined interfaces** (API contracts, database schemas)
- **Coordination through orchestrator** (efir_master_agent)
- **Validation checkpoints** (qa_validation_agent)

## Version Information

- **Version**: 1.0.0
- **Created**: 2024-11-30
- **Model**: Claude Sonnet 4.5
- **Total Agents**: 14

## Support

For questions about the agent structure, consult:
- CLAUDE.md in the project root
- Individual agent files for specific capabilities
- EFIR_Budget_App_PRD_v1_2.md for business requirements
- EFIR_Module_Technical_Specification.md for technical details
