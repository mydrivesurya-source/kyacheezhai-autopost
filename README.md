# Kya Cheez Hai autopost
Daily Instagram publishing for @kyacheezhai.in. Claude drops posts into `queue/` (files named `YYYY-MM-DD-slot.json`, IST date) with media in `media/`; GitHub Actions publishes them at 11:45 AM and 7:45 PM IST. Token lives in the `IG_TOKEN` repo secret.

## Tara host clips (media/hosts)
6 looks, 8 s each, generic Hinglish line that names no product: rooftop (black satin), party (coral), gym (mint), goa (cream linen), cafe (blazer) — no bindi — plus garden_bindi (original teal kurta look). Stills in media/looks. Reels rotate hosts by date when `"host": "auto"`.

## Specs
Drop a spec in `specs/` (see scripts/build.py docstring). A push builds the media into `media/` and the post into `queue/`; the 11:45 AM / 7:45 PM IST runs publish anything due.

## Daily schedule (IST)
10:15 story · 11:45 reel · 13:15 story · 15:15 carousel · 17:15 story · 19:45 reel · 21:15 story.
Spec stems: YYYY-MM-DD-HHMM-<slug>. Story spec: {"kind":"story","style":"find|question|reminder|deal","images":[url],"title":"..","text":"..","cta":"Link in bio"} or {"kind":"story","video":"media/<reel stem>.mp4"} to reshare a reel.
