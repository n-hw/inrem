# InRem Coding Conventions

## 1. Introduction
This document defines the coding standards for the InRem project. All developers (human and AI) must adhere to these rules to maintain code quality and consistency.

## 2. Tech Stack
- **Frontend**: React Native, TypeScript
- **Backend**: FastAPI, Python 3.12+
- **Database**: PostgreSQL
- **Infrastructure**: Docker, Google Cloud Platform (GCP)

## 3. General Principles
- **DRY (Don't Repeat Yourself)**: Extract common logic into functions/hooks/dependencies.
- **KISS (Keep It Simple, Stupid)**: Avoid over-engineering.
- **Clean Code**: Meaningful variable_names, small functions.

## 4. Frontend Guidelines (React Native)
---
### 4.1. Architecture: Feature-Based + MVVM
We follow a simplified **Feature-Based** architecture combined with **MVVM** principles using Hooks.
- **Structure**:
    - `src/features/{featureName}/`
        - `components/`: Pure UI components (View).
        - `hooks/`: Business logic and State (ViewModel).
        - `api/`: API calls and Data definitions (Model).
- **State**: Server state via React Query; global app state via Context/Zustand.

### 4.2. TypeScript
- Strict typing is enforced.
- Avoid `any`; use `unknown` if necessary and narrow types.
- Define interfaces for all Props and State.

### 4.3. Components
- Use Functional Components.
- File name matches component name (e.g., `MyComponent.tsx`).
- Logic separated from UI where possible (Custom Hooks).

### 4.3. Styling
- Use `StyleSheet.create`.
- No inline styles for complex objects.
- Use the shared theme object for colors, fonts, and spacing.

## 5. Backend Guidelines (FastAPI)
### 5.1. Python Style
- Follow PEP 8 (black formatter recommended).
- Imports sorted (isort).

### 5.2. Architecture: Service-Repository Pattern
We use a **Layered Architecture** to separate concerns:
- **Routers** (`routers/`): Handle HTTP requests, parsing, and response formatting.
- **Services** (`services/`): Contain pure business logic.
- **Repositories** (`repositories/`): abstrac database access (CRUD).
- **Schemas** (`schemas/`): Pydantic models for data transfer (DTO).

### 5.3. API Structure
- Resource-based URLs (`/users`, `/users/{id}`).
- Proper HTTP verbs (GET, POST, PUT, DELETE, PATCH).
- Consistent error responses structure.

### 5.3. Database
- Async drivers (`asyncpg`).
- Connection pooling managed properly.
- No direct SQL injection vulnerabilities (use parameters).

## 6. Git Workflow
- Feature branches: `feature/brief-description`
- Commit messages: "feat: add user login endpoint" (Conventional Commits).
