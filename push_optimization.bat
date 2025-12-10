@echo off
echo Adding files to staging...
git add src/backend/continuous_learning.py
git add .github/workflows/learning.yml

echo Committing changes...
git commit -m "fix(cloud): switch to long-running 6h learning job"

echo Pushing changes...
git push

echo Done.
