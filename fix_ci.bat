@echo off
echo Adding .github/workflows/ci.yml to staging...
git add .github/workflows/ci.yml

echo Committing changes...
git commit -m "chore: fix CI by installing PyQt6"

echo Pushing changes...
git push

echo Done.
