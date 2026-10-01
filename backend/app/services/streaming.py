"""Which streaming services users can pick (Phase 2, DESIGN.md §2).

A curated subset of TMDB's ~300 US providers: major subscription services only, no
"Amazon Channel"/"Roku Channel" duplicates, rent/buy stores, or free ad-supported services
(we only store flat-rate providers, so those would never match). Tiers are listed separately,
as TMDB lists them. Rows are seeded by migration 2335c45abee8; keep the two in sync.
"""

SUPPORTED_SERVICE_IDS: frozenset[int] = frozenset(
    {
        8,  # Netflix
        9,  # Amazon Prime Video
        11,  # MUBI
        15,  # Hulu
        34,  # MGM Plus
        43,  # Starz
        99,  # Shudder
        258,  # Criterion Channel
        283,  # Crunchyroll
        337,  # Disney Plus
        350,  # Apple TV (the Apple TV+ subscription)
        386,  # Peacock Premium
        387,  # Peacock Premium Plus
        526,  # AMC+
        1899,  # HBO Max
        2303,  # Paramount Plus Premium
        2616,  # Paramount Plus Essential
    }
)
