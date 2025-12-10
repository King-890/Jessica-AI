@echo off
echo Adding files to staging...
git add src/core/brain.py
git add src/tools/test_ui_theme.py

echo Committing changes...
git commit -m "fix(core): improve untrained AI response and fix UI test compatibility"

echo Pushing changes...
git push

echo Done.
