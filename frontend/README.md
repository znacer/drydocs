# DryDocs Frontend

> **SvelteKit-based Document Management UI**

---

## Overview

The DryDocs frontend is a SvelteKit application that provides a modern, responsive UI for managing documents. It communicates with the DryDocs backend API to perform all document operations.

### Data Flow

```mermaid
flowchart TB
    subgraph Frontend
        UI[UI Components]
        APIClient[API Client]
        Auth[Auth Service]
        i18n[i18n Service]
    end
    
    subgraph Backend
        FastAPI[FastAPI Backend]
    end
    
    subgraph External
        MinIO[(MinIO Storage)]
        DB[(PostgreSQL)]
    end
    
    UI --> APIClient
    UI --> Auth
    UI --> i18n
    APIClient --> FastAPI
    Auth --> FastAPI
    FastAPI --> MinIO
    FastAPI --> DB
```

### Features

- **Document Management**: Upload, view, and manage documents
- **Version History**: View and navigate document versions
- **Markdown Preview**: View converted Markdown content
- **Validation Workflow**: Mark documents as validated
- **Authentication**: Email/password login with better-auth
- **Internationalization**: Multi-language support (English, French) via Paraglide-js
- **Responsive Design**: Mobile-friendly UI with Tailwind CSS v4 + daisyUI

### Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Framework** | SvelteKit | Latest |
| **Svelte** | Svelte 5 (Runes) | Latest |
| **Language** | TypeScript | Latest |
| **Styling** | Tailwind CSS | v4 |
| **UI Library** | daisyUI | Latest |
| **Package Manager** | Bun | Latest |
| **Auth** | better-auth | Latest |
| **ORM** | Drizzle ORM | Latest |
| **i18n** | Paraglide-js | Latest |
| **Markdown** | mdsvex | Latest |

---

## Quick Start

### Prerequisites

- [Node.js](https://nodejs.org/) 20+
- [Bun](https://bun.sh/) (recommended) or npm/pnpm
- DryDocs backend running on http://localhost:8000
- PostgreSQL for Drizzle ORM (optional, for frontend-specific data)

### 1. Install Dependencies

```bash
bun install
```

Or with npm:
```bash
npm install
```

### 2. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```bash
# Backend API URL
VITE_API_URL=http://localhost:8000

# Database (for Drizzle ORM - optional)
DATABASE_URL=postgresql://postgres:password@localhost:5432/docmanager

# Auth
AUTH_SECRET=your-auth-secret-here
AUTH_URL=http://localhost:3000

# i18n (Paraglide-js)
PARAGLIDE_WRITE_KEY=your-write-key
```

### 3. Run Development Server

```bash
bun run dev --port 3000
```

Or with auto-open:
```bash
bun run dev --port 3000 --open
```

The application will be available at: http://localhost:3000

---

## Project Structure

### Component Hierarchy

```mermaid
flowchart TB
    Layout["+layout.svelte"] --> Navbar
    Layout --> Main
    
    Main --> Home["+page.svelte\nHome"]
    Main --> DocsList["documents/+page.svelte\nDocument List"]
    Main --> DocDetail["documents/[id]/+page.svelte\nDocument Detail"]
    Main --> Login["login/+page.svelte\nLogin"]
    
    DocsList --> DocumentCard
    DocsList --> UploadModal
    DocsList --> Pagination
    
    DocDetail --> MarkdownViewer
    DocDetail --> VersionHistory
    DocDetail --> ValidateButton
    
    DocumentCard --> Button
    DocumentCard --> Badge
    
    UploadModal --> Input
    UploadModal --> Button
    
    style Layout fill:#f9f,stroke:#333
    style Home fill:#9f9,stroke:#333
    style DocsList fill:#9f9,stroke:#333
    style DocDetail fill:#9f9,stroke:#333
```

### Project Structure

```
frontend/
├── src/
│   ├── lib/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── DocumentCard.svelte
│   │   │   ├── DocumentList.svelte
│   │   │   ├── UploadModal.svelte
│   │   │   ├── MarkdownViewer.svelte
│   │   │   ├── VersionHistory.svelte
│   │   │   ├── Navbar.svelte
│   │   │   └── ...
│   │   │
│   │   ├── server/             # Server-only logic
│   │   │   ├── auth.ts         # Authentication configuration
│   │   │   ├── db.ts           # Drizzle ORM client
│   │   │   └── api.ts          # API client utilities
│   │   │
│   │   └── utils/              # Shared utilities
│   │       ├── api.ts          # Centralized API client
│   │       ├── constants.ts    # Application constants
│   │       └── helpers.ts      # Helper functions
│   │
│   ├── routes/                 # Application routes
│   │   ├── +layout.svelte      # Root layout
│   │   ├── +page.svelte        # Home page
│   │   ├── documents/
│   │   │   ├── +page.svelte    # Document list
│   │   │   └── [id]/
│   │   │       ├── +page.svelte # Document detail
│   │   │       └── +page.ts    # Load function
│   │   ├── login/
│   │   │   └── +page.svelte    # Login page
│   │   └── api/                # Frontend API endpoints
│   │       └── auth/
│   │           └── [...path]/
│   │               └── +server.ts
│   │
│   ├── app.html                # HTML template
│   ├── app.d.ts                # Type declarations
│   ├── hooks.server.ts         # Server hooks
│   └── hooks.ts                # Universal hooks
│
├── messages/                   # i18n message files
│   ├── en.json
│   └── fr.json
│
├── drizzle/                    # Drizzle ORM migrations
│   └── *.sql
│
├── static/                     # Static assets
│   └── favicon.png
│
├── auth-schema.ts              # better-auth schema
├── package.json
├── tsconfig.json
├── svelte.config.js
├── vite.config.ts
├── tailwind.config.js
├── .env.example
└── README.md
```

---

## Development Commands

| Command | Description |
|---------|-------------|
| `bun run dev` | Start development server |
| `bun run build` | Build for production |
| `bun run preview` | Preview production build |
| `bun run check` | Type check with TypeScript |
| `bun run lint` | Lint code with ESLint |
| `bun run lint:fix` | Auto-fix lint issues |
| `bun run format` | Format code with Prettier |
| `bun run db:push` | Push database schema (Drizzle) |
| `bun run db:studio` | Open Drizzle Studio |
| `bun run auth:schema` | Generate auth schema |
| `bun run i18n:extract` | Extract i18n messages |
| `bun run i18n:sync` | Sync i18n messages |

---

## API Client

All backend API communication should be centralized in `src/lib/utils/api.ts` with functions for uploading documents, retrieving document lists, getting individual documents, validation, and downloading Markdown/documents.

---

## Authentication

Authentication is handled by [better-auth](https://better-auth.com/) with Email/Password strategy. Configuration is in `src/lib/server/auth.ts` using Drizzle ORM adapter.

Route protection is implemented in `src/hooks.server.ts` to require authentication for protected routes.

---

## Database (Drizzle ORM)

Drizzle ORM is used for any frontend-specific database needs (e.g., user preferences, UI state). Configuration is in `src/lib/server/db.ts`.

### Running Migrations

1. Update schema in `src/lib/server/schema.ts`
2. Generate migration:
   ```bash
   bun run db:push
   ```
3. Migrations are stored in `/drizzle`

---

## Internationalization (Paraglide-js)

Multi-language support using Paraglide-js with English and French.

### Extracting Messages

After adding new messages to components:

```bash
bun run i18n:extract
bun run i18n:sync
```

---

## Component Library

### Common Components

| Component | File | Description |
|-----------|------|-------------|
| `DocumentCard` | `src/lib/components/DocumentCard.svelte` | Card displaying document info |
| `DocumentList` | `src/lib/components/DocumentList.svelte` | List of documents with pagination |
| `UploadModal` | `src/lib/components/UploadModal.svelte` | Modal for uploading documents |
| `MarkdownViewer` | `src/lib/components/MarkdownViewer.svelte` | Render Markdown content |
| `VersionHistory` | `src/lib/components/VersionHistory.svelte` | Show version history |
| `Navbar` | `src/lib/components/Navbar.svelte` | Navigation bar |
| `Button` | `src/lib/components/Button.svelte` | Styled button |
| `Input` | `src/lib/components/Input.svelte` | Styled input field |
| `Modal` | `src/lib/components/Modal.svelte` | Modal dialog |
| `Table` | `src/lib/components/Table.svelte` | Data table |

---

## Routing

### File-based Routing

| File | Route |
|------|-------|
| `src/routes/+page.svelte` | `/` |
| `src/routes/documents/+page.svelte` | `/documents` |
| `src/routes/documents/[id]/+page.svelte` | `/documents/:id` |
| `src/routes/login/+page.svelte` | `/login` |
| `src/routes/settings/+page.svelte` | `/settings` |

### Load Functions

Load functions in `+page.ts` files fetch data before page rendering. For example, `src/routes/documents/[id]/+page.ts` fetches a document by ID.

### Actions

Actions in `+page.server.ts` files handle form submissions. For example, `src/routes/documents/[id]/+page.server.ts` handles document validation with authentication checks.

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_URL` | Backend API URL | Yes |
| `DATABASE_URL` | PostgreSQL connection URL (for Drizzle) | No |
| `AUTH_SECRET` | better-auth secret key | Yes |
| `AUTH_URL` | Application URL for auth | Yes |
| `PARAGLIDE_WRITE_KEY` | Paraglide-js write key | No |

---

## Troubleshooting

### CORS Issues

Ensure the backend has CORS configured to allow requests from `http://localhost:3000`.

### TypeScript Errors

Run type checking:
```bash
bun run check
```

Common fixes:
- Ensure all props are properly typed
- Add type annotations for variables
- Check import paths are correct

### Linting Errors

Run linting:
```bash
bun run lint
```

Auto-fix:
```bash
bun run lint:fix
```

### Build Errors

If build fails:
1. Delete `node_modules` and reinstall: `rm -rf node_modules && bun install`
2. Clear SvelteKit cache: `rm -rf .svelte-kit`
3. Try building again: `bun run build`

### API Connection Issues

Verify:
1. Backend is running: `curl http://localhost:8000`
2. `VITE_API_URL` is correctly set in `.env`
3. CORS is configured on the backend
4. No network/firewall blocking the connection
