#!/bin/bash
set -e

echo "🔍 Starting comprehensive code quality checks..."
echo ""

# Backend checks
echo "🐍 === BACKEND CHECKS ==="
echo "📋 Linting with ruff..."
source .venv/bin/activate && ruff check .

echo "🎨 Formatting with ruff..."
source .venv/bin/activate && ruff format .

echo "🎨 Formatting with Black..."
source .venv/bin/activate && black .

echo "🔍 Type checking with mypy..."
source .venv/bin/activate && mypy .

echo ""

# Frontend checks
echo "⚛️  === FRONTEND CHECKS ==="
cd frontend

echo "📋 Linting with ESLint..."
npm run lint

echo "🎨 Formatting with Prettier..."
npm run format

echo "🔍 Type checking with TypeScript..."
npm run type-check

echo "🏗️  Building for production..."
npm run build

cd ..

echo ""
echo "✅ All checks passed! Code is ready for production."