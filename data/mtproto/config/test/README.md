# Test MTProto configuration

This directory contains optional snapshots from Telegram's MTProto test network.

## Data centers

- `dc1/`
- `dc2/`
- `dc3/`

Test collection requires the optional test API credentials and an explicit `TDC_TEST_DC_ENDPOINTS` mapping.

The test network is kept separate from production so that changes in test configuration do not get mixed with production snapshots.

Each DC directory follows the same file layout as production:

- `config.json`
- `countries-list.json`
- `app-config.json`
