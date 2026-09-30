# Global MTProto configuration data

This directory contains MTProto datasets that are collected at global scope rather than stored separately under each data center.

## Files

### cdn-config.json

Source: `help.getCdnConfig`.

Contains the Telegram CDN configuration returned to the crawler's bot-authorized MTProto session.

### available-reactions.json

Source: `messages.getAvailableReactions`.

This dataset is user-only and is written when `TG_USER_SESSION` is configured.

### premium-promo.json

Source: `help.getPremiumPromo`.

This dataset is user-only and is written when `TG_USER_SESSION` is configured. Personal/volatile response fields are normalized before publication.

## Authentication

Global datasets do not all share the same access level:

- CDN config: bot authorization.
- Available reactions: user authorization.
- Premium promo: user authorization.

No Telegram session credentials are stored in this directory.
