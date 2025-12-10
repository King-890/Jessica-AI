@echo off
echo Adding src/backend/routes/auth.py to staging...
git add src/backend/routes/auth.py
git add src/backend/cloud/__init__.py

echo Committing changes...
git commit -m "fix(backend): correct relative import in auth.py and add init to cloud package"

echo Pushing changes...
git push

echo Done.
