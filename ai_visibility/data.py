from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    name: str
    state: str
    population_2025: int


@dataclass(frozen=True)
class PracticeArea:
    slug: str
    label: str
    customer_language: tuple[str, ...]
    evidence_signals: tuple[str, ...]


TOP_CITIES: tuple[City, ...] = (
    City("New York", "NY", 8_584_629),
    City("Los Angeles", "CA", 3_869_089),
    City("Chicago", "IL", 2_731_585),
    City("Houston", "TX", 2_397_315),
    City("Phoenix", "AZ", 1_665_481),
    City("Las Vegas", "NV", 671_705),
    City("Orlando", "FL", 320_742),
    City("San Francisco", "CA", 815_201),
    City("Miami", "FL", 470_914),
    City("Washington", "DC", 689_545),
    City("New Orleans", "LA", 364_136),
    City("Nashville", "TN", 715_884),
)


PRACTICE_AREAS: tuple[PracticeArea, ...] = (
    PracticeArea(
        slug="personal injury",
        label="Personal Injury Attorney",
        customer_language=(
            "car accident",
            "truck accident",
            "slip and fall",
            "serious injury",
            "free consultation",
            "contingency fee",
        ),
        evidence_signals=(
            "case results",
            "settlement examples",
            "Avvo profile",
            "Super Lawyers listing",
            "Google reviews mentioning accident cases",
            "practice-area landing pages",
            "attorney bios with trial experience",
        ),
    ),
    PracticeArea(
        slug="divorce",
        label="Divorce / Family Law Attorney",
        customer_language=(
            "divorce",
            "child custody",
            "high-conflict divorce",
            "spousal support",
            "mediation",
            "complex assets",
        ),
        evidence_signals=(
            "family-law directory profiles",
            "reviews mentioning custody or divorce",
            "clear consultation process",
            "attorney bios with family court experience",
            "content about local court process",
            "pages for custody, support, and mediation",
        ),
    ),
    PracticeArea(
        slug="immigration",
        label="Immigration Attorney",
        customer_language=(
            "green card",
            "visa",
            "deportation defense",
            "asylum",
            "citizenship",
            "family immigration",
        ),
        evidence_signals=(
            "multilingual content",
            "AILA membership or equivalent credentials",
            "reviews mentioning immigration case types",
            "pages for visa, green card, asylum, and citizenship",
            "attorney bios with immigration specialization",
            "clear appointment and document-prep guidance",
        ),
    ),
    PracticeArea(
        slug="itinerary",
        label="Travel Attractions & Itinerary",
        customer_language=(
            "things to do",
            "day trip",
            "must-see",
            "weekend visit",
            "tourist spots",
            "hidden gems",
        ),
        evidence_signals=(
            "Google Maps listing with photos and reviews",
            "TripAdvisor or Yelp profile",
            "official website with hours and admission",
            "featured in travel guides or listicles",
            "strong volume of visitor photos and ratings",
            "accessible location and transit information",
        ),
    ),
)


def get_city(name: str) -> City:
    normalized = name.strip().lower()
    for city in TOP_CITIES:
        if city.name.lower() == normalized:
            return city
    raise ValueError(f"Unknown city: {name}")


def get_practice_area(slug: str) -> PracticeArea:
    normalized = slug.strip().lower()
    for area in PRACTICE_AREAS:
        if area.slug == normalized or area.label.lower() == normalized:
            return area
    raise ValueError(f"Unknown practice area: {slug}")
