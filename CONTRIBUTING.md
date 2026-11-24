# Contributing to ClutchSift

Thanks for contributing. Please open an issue explaining the problem and attach **only footage you own or are explicitly permitted to distribute**. Avoid sharing personal data, private streams, confidential recordings, game account credentials, and copyrighted audio you cannot distribute.

1. Fork the repo; create one feature branch per change.
2. Use Python 3.11+; run `python -m unittest discover -s tests -v`.
3. Keep core operation available without a paid API or download of massive models.
4. Never advertise a detector as recognizing kills, emotions, jokes or virality unless validated against labeled examples.
5. Don't copy source code from other repositories without appropriate license review/attribution.
6. Write a test for new detectors, output layouts, and file-safety handling.
7. Document model download size, licensing, languages, and peak VRAM for GPU options.

Useful contributions: bug fixes, Windows validation, small synthetic test clips, localization, subtitle design, game-event detection benchmark datasets with permissions, and reproducible speed tests.
