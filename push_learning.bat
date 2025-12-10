@echo off
echo Adding files to staging...
git add .github/workflows/learning.yml

echo Committing changes...
git commit -m "feat(workflow): update learning schedule to 5min and fix deps"

echo Pushing changes...
git push

echo Done.
