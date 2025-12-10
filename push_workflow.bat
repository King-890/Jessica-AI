@echo off
echo Adding files to staging...
git add src/core/brain.py
git add .agent/workflows/jessica_workflow.md
git add start_training.bat

echo Committing changes...
git commit -m "feat(workflow): integrate search in brain and add isolated training launcher"

echo Pushing changes...
git push

echo Done.
