@echo off
echo Adding files to staging...
git add src/backend/continuous_learning.py
git add .github/workflows/learning.yml

echo Committing changes...
git commit -m "fix(workflow): revert to 5-min schedule with 300s loop"

echo Pushing changes...
git push

echo Done.
