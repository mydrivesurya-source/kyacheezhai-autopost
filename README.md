# Kya Cheez Hai autopost
Daily Instagram publishing for @kyacheezhai.in. Claude drops posts into `queue/` (files named `YYYY-MM-DD-slot.json`, IST date) with media in `media/`; GitHub Actions publishes them at 11:45 AM and 7:45 PM IST. Token lives in the `IG_TOKEN` repo secret.

## Tara host clips (media/hosts)
5 looks, no bindi, 8 s each, generic Hinglish line that names no product: rooftop (black satin), party (coral), gym (mint), goa (cream linen), cafe (blazer). Stills in media/looks. Reels rotate hosts by date when `"host": "auto"`.

## Specs
Drop a spec in `specs/` (see scripts/build.py docstring). A push builds the media into `media/` and the post into `queue/`; the 11:45 AM / 7:45 PM IST runs publish anything due.
