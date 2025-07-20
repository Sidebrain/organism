# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a React TypeScript frontend built with Vite, part of the Organism project. The backend is a FastAPI application located in `../backend/` that provides transcription API functionality.

## Tech Stack

- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 7
- **Package Manager**: Bun
- **Styling**: Tailwind CSS v4 with shadcn/ui components
- **UI Components**: Radix UI primitives with shadcn/ui styling
- **Linting**: ESLint with TypeScript support

## Development Commands

```bash
# Install dependencies
bun install

# Start development server
bun dev

# Build for production
bun run build

# Lint code
bun run lint

# Preview production build
bun run preview
```

## Project Structure

- `src/components/ui/` - shadcn/ui components (Button, etc.)
- `src/lib/utils.ts` - Utility functions including `cn()` for class merging
- `src/App.tsx` - Main application component
- `@/` - Alias for `src/` directory (configured in vite.config.ts)

## shadcn/ui Configuration

The project uses shadcn/ui with the "new-york" style variant. Configuration is in `components.json`:
- Style: new-york
- Base color: zinc
- CSS variables enabled
- Icons: Lucide React

## Key Patterns

- Import paths use `@/` alias for src directory
- UI components follow shadcn/ui patterns with variant props
- Styling uses Tailwind CSS classes with CSS variables for theming
- TypeScript strict mode enabled with separate configs for app and node
- **Flexible component design** - Build components that can adapt to changing requirements
- **Simple state management** - Use React's built-in state before reaching for external libraries
- **Readable over clever** - Write code that's easy to understand and modify
- **Minimal viable implementations** - Start with the simplest solution that works

## Architecture Notes

This frontend is designed to work with a FastAPI backend that handles transcription functionality. The backend is located in the parent directory at `../backend/`.

## Coding Philosophy

Follow these core principles when working on this codebase:

- **Premature optimization is the root of all evil** - Focus on working solutions first
- **Code should be flexible** - Write adaptable, maintainable code
- **Three-phase development**: Make it work → Make it good → Make it fast
- **Current phase**: **Make it work** - Prioritize functionality over perfection
- **Brevity is the wit of the soul** - Keep code concise and clear
- **Clean minimal design** - Both UI and code should be simple and elegant

## Current Phase: Make It Work

We are currently in the "make it work" phase of development:

- **Functionality first** - Get features working before optimizing
- **Simple implementations** - Use the most straightforward approach that works
- **Iterate quickly** - Build, test, refine in short cycles
- **Avoid over-engineering** - Resist the urge to build complex abstractions too early

