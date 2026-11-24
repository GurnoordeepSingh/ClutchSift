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

## Review and release

The public repository is [GurnoordeepSingh/ClutchSift](https://github.com/GurnoordeepSingh/ClutchSift). Review the [recovered baseline](https://github.com/GurnoordeepSingh/ClutchSift/pull/1) first. The [export and desktop changes](https://github.com/GurnoordeepSingh/ClutchSift/pull/2) are stacked on that baseline. After the baseline lands, target the follow-up at main and check CI on the new base.

For a tagged release, check a fresh Windows installation and publish a demo using footage cleared for distribution.

## First creator outreach message

> Hey! I'm testing a free local gaming clipper that scans long recordings for candidate moments and exports YouTube Shorts. It's an early prototype, so the detection isn't perfect. Would you be open to trying it with one of your own recordings and telling me what wastes your time? No uploads or sign-up required.

Avoid promises like “automatically finds viral kills” until gameplay-aware detection is validated.

## Current validation

- [x] Recovered archive passed all 14 original tests on Windows.
- [x] Updated suite passed 19 tests on the RTX 5060 laptop, including desktop scan, trim, export and subtitle burn-in.
- [x] Verified actual hardware encoding and decoding of the resulting MP4.
- [x] Published the source and follow-up as review branches.
- [ ] Check large-v3-turbo transcription and multimodal frame review on a creator recording.
- [ ] Measure accepted distinct candidates and editing time on five creators' own recordings.
