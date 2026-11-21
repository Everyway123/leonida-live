# Leonida Live
Ukrainian fan atlas. Cloudflare Pages settings: production branch main, no framework, build command python3 scripts/validate.py, output directory public.
The published landmarks and overview tile come from the GTA VI Mapping Project (public domain). The overview stays visible beneath higher resolution tiles. Landmarks represent the community reconstruction. Reviewed loot is a separate dataset.

## Reviewing leads
The monitor appends source URLs to review/candidates.json. In a pull request, check the original screenshot or video, verify the game, category and coordinates against the gta6map reconstruction, and check the source permits reuse. If evidence is missing, leave the candidate pending. To approve, set the candidate status to reviewed and add a record to public/data/verified-pins.json. Required fields are id, name, category, x, y, verified (true), evidence_url, coordinate_system (gta6map-32768), coordinate_evidence (how the point was matched), reviewer, and checked_at (ISO timestamp with timezone). Run python3 scripts/validate.py. Accepting the pull request publishes the reviewed record via Pages Git integration once connected.

Actions logs each source check. A source status change or new data updates the committed snapshot. Failed fetches retain the prior map. Timestamps on the website record status changes, while individual checks are visible in Actions. Run python3 scripts/source_watch.py to check locally.
