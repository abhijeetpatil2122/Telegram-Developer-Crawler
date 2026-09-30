# Global MTProto configuration data

This directory contains MTProto datasets that are collected at global scope rather than stored separately under each data center.

## Files

- `cdn-config.json` — `help.getCdnConfig`, collected with bot authorization.
- `available-reactions.json` — `messages.getAvailableReactions`, collected with user authorization.
- `premium-promo.json` — `help.getPremiumPromo`, collected with user authorization.

User-only files are produced only when `TG_USER_SESSION` is configured. Personal and volatile fields are normalized before publication.

No Telegram session credentials are stored in this directory.
