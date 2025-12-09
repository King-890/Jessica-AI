@echo off
echo Adding src/tools/test_ui_theme.py to staging...
git add src/tools/test_ui_theme.py

echo Committing changes...
git commit -m "chore: auto-close UI test to prevent CI hang"

echo Pushing changes...
git push

echo Done.
