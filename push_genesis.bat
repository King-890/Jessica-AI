@echo off
echo Pushing Project Genesis files to GitHub...
git add .
git commit -m "Update Sovereign AI Codebase (Tokenizer)"
git push origin main
echo Done.
