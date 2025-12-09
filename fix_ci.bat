@echo off
echo Adding .github/workflows/ci.yml to staging...
git add .github/workflows/ci.yml

echo Committing changes...
git commit -m "chore: install system dependencies for PyQt6 in CI"

echo Pushing changes...
git push

echo Done.
