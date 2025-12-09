@echo off
echo Adding src/tools/test_ui_theme.py to staging...
git add src/tools/test_ui_theme.py

echo Committing changes...
git commit -m "chore: configure Qt for headless CI"

echo Pushing changes...
git push

echo Done.
