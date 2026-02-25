# OmniRemote Branding Submission

This folder contains the icons and logos to be submitted to the [Home Assistant Brands](https://github.com/home-assistant/brands) repository.

## Why Submit to Brands?

Submitting to the brands repository enables:
- **HACS**: Icon appears in HACS search results and repository listings
- **Integrations List**: Icon appears in Settings → Devices & Services
- **Config Flow**: Icon appears during setup wizard

## Icon Specifications

All icons meet the Home Assistant requirements:

| File | Size | Status |
|------|------|--------|
| `icon.png` | 256×256 | ✅ Ready |
| `icon@2x.png` | 512×512 | ✅ Ready |
| `logo.png` | 256×256 | ✅ Ready |
| `logo@2x.png` | 512×512 | ✅ Ready |

## How to Submit

1. Fork the [home-assistant/brands](https://github.com/home-assistant/brands) repository
2. Copy the `custom_integrations/omniremote` folder to your fork
3. Create a Pull Request with title: `Add OmniRemote custom integration`
4. Wait for review and merge (usually 1-3 days)

### Folder Structure

```
home-assistant/brands/
└── custom_integrations/
    └── omniremote/
        ├── icon.png      # 256×256 square icon
        ├── icon@2x.png   # 512×512 high-DPI icon
        ├── logo.png      # 256×256 logo (uses icon as fallback)
        └── logo@2x.png   # 512×512 high-DPI logo
```

## After Submission

Once merged, icons will be served from:
- `https://brands.home-assistant.io/omniremote/icon.png`
- `https://brands.home-assistant.io/omniremote/logo.png`
- `https://brands.home-assistant.io/_/omniremote/icon.png` (with fallback)

Icons are cached for 7 days, so changes may take time to propagate.

## Design Notes

The OmniRemote icon features:
- Remote control silhouette
- Purple/blue gradient (#667eea → #764ba2)
- Clean, modern design
- Transparent background
- Optimized for both light and dark themes
