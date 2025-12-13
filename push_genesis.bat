@echo off
echo Pushing Project Genesis files to GitHub...
git add src/model/transformer.py
git add src/training/train.py
git add src/training/data_miner.py
git add README_CLOUD_ARCH.md
git add SOVEREIGN_AI_ROADMAP.md
git commit -m "feat: Implement Sovereign AI (Transformer, Trainer, Miner)"
git push
echo Done.
pause
