# Founder launch checklist

## Before you publish

- [ ] Run `py -3 -m unittest discover -s tests -v`
- [ ] Try a **real 10–20 minute gameplay recording** on Windows
- [ ] Confirm FFmpeg/FFplay installed and found on PATH
- [ ] Review one exported landscape and one 9:16 clip on a phone
- [ ] Try optional captions; check transcription errors
- [ ] Remove personal video paths, tokens, sample recordings, and private data from commits
- [ ] Pick a final project name; **ClutchSift is just a working name**, not a trademark clearance
- [ ] Create your own demo and screenshots, with permission for any game footage
- [ ] Ask 5 creators to test; record how many suggestions are actually usable

## Publish as a GitHub repository

1. Create a new GitHub repository (e.g. `clutchsift`). Do not initialize with a different license/README because these are already included.
2. From this folder in PowerShell or terminal:

   ```bash
   git init
   git add .
   git commit -m "Initial open-source local gaming clipper MVP"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

3. Replace YOUR_USERNAME and YOUR_REPO with your actual repository. Sign into GitHub using your normal authenticated Git setup or Git Credential Manager. This archive has **not** been pushed for you.
4. Add a short demo recording (with rights), tags, and clear limitations in README.
5. Publish a v0.1.0 release only after verifying it works on a separate Windows install. A ZIP of Python code is not a Windows `.exe` installer.

## First creator outreach message

> Hey! I'm testing a free local gaming clipper that scans long recordings for candidate moments and exports YouTube Shorts. It's an early prototype, so the detection isn't perfect. Would you be open to trying it with one of your own recordings and telling me what wastes your time? No uploads or sign-up required.

Avoid promises like “automatically finds viral kills” until gameplay-aware detection is validated.

## v0.2 publish gate

- [x] 12 automated tests pass on development machine with FFmpeg.
- [x] Reusable research docs, architecture, business hypothesis, CI and contributor/security guides.
- [ ] Run on the actual Windows RTX 5060 laptop, verify Tkinter GUI and NVIDIA NVENC.
- [ ] Validate optional faster-whisper/Ollama download/runtime and styled captions end-to-end on Windows.
- [ ] Get 5 users' own consented recordings and record precision@5 and time saved.
- [ ] Create the *correct* GitHub repository; do not mix with unrelated File-sorter.
- [ ] Push the GitHub-ready source and screenshots/demo only after user-approved repository exists.
