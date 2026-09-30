# Production MTProto configuration

This directory contains snapshots from Telegram's production data centers.

## Data centers

- `dc1/`
- `dc2/`
- `dc3/`
- `dc4/`
- `dc5/`

Each DC directory contains the normalized configuration responses collected for that production DC.

## Files in each DC

- `config.json` — `help.getConfig`
- `countries-list.json` — `help.getCountriesList`
- `app-config.json` — `help.getAppConfig`

Production endpoints are discovered dynamically from Telegram's `help.getConfig` response rather than hardcoded in the crawler.
