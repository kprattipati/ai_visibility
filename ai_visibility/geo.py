from __future__ import annotations

from dataclasses import dataclass

from ai_visibility.data import City


@dataclass(frozen=True)
class GeoScope:
    kind: str
    label: str
    query_text: str


CITY_GEO = "city"
NEIGHBORHOOD_GEO = "neighborhood"
ZIP_GEO = "zip"
SAMPLE_GEO = "sample"


REPRESENTATIVE_AREAS: dict[str, tuple[GeoScope, ...]] = {
    "New York": (
        GeoScope(NEIGHBORHOOD_GEO, "Manhattan", "Manhattan, New York, NY"),
        GeoScope(NEIGHBORHOOD_GEO, "Brooklyn", "Brooklyn, New York, NY"),
        GeoScope(NEIGHBORHOOD_GEO, "Queens", "Queens, New York, NY"),
        GeoScope(ZIP_GEO, "10001", "near ZIP code 10001 in New York, NY"),
        GeoScope(ZIP_GEO, "11201", "near ZIP code 11201 in Brooklyn, NY"),
    ),
    "Los Angeles": (
        GeoScope(NEIGHBORHOOD_GEO, "Downtown LA", "Downtown Los Angeles, CA"),
        GeoScope(NEIGHBORHOOD_GEO, "Koreatown", "Koreatown, Los Angeles, CA"),
        GeoScope(NEIGHBORHOOD_GEO, "West LA", "West Los Angeles, CA"),
        GeoScope(ZIP_GEO, "90012", "near ZIP code 90012 in Los Angeles, CA"),
        GeoScope(ZIP_GEO, "90024", "near ZIP code 90024 in Los Angeles, CA"),
    ),
    "Chicago": (
        GeoScope(NEIGHBORHOOD_GEO, "Loop", "the Loop in Chicago, IL"),
        GeoScope(NEIGHBORHOOD_GEO, "Lincoln Park", "Lincoln Park, Chicago, IL"),
        GeoScope(NEIGHBORHOOD_GEO, "West Loop", "West Loop, Chicago, IL"),
        GeoScope(ZIP_GEO, "60601", "near ZIP code 60601 in Chicago, IL"),
        GeoScope(ZIP_GEO, "60614", "near ZIP code 60614 in Chicago, IL"),
    ),
    "Houston": (
        GeoScope(NEIGHBORHOOD_GEO, "Downtown Houston", "Downtown Houston, TX"),
        GeoScope(NEIGHBORHOOD_GEO, "The Heights", "the Heights in Houston, TX"),
        GeoScope(NEIGHBORHOOD_GEO, "Galleria/Uptown", "the Galleria/Uptown area of Houston, TX"),
        GeoScope(ZIP_GEO, "77002", "ZIP code 77002 in Houston, TX"),
        GeoScope(ZIP_GEO, "77007", "ZIP code 77007 in Houston, TX"),
    ),
    "Phoenix": (
        GeoScope(NEIGHBORHOOD_GEO, "Downtown Phoenix", "Downtown Phoenix, AZ"),
        GeoScope(NEIGHBORHOOD_GEO, "Arcadia", "Arcadia, Phoenix, AZ"),
        GeoScope(NEIGHBORHOOD_GEO, "Ahwatukee", "Ahwatukee, Phoenix, AZ"),
        GeoScope(ZIP_GEO, "85004", "near ZIP code 85004 in Phoenix, AZ"),
        GeoScope(ZIP_GEO, "85018", "near ZIP code 85018 in Phoenix, AZ"),
    ),
}


def city_scope(city: City) -> GeoScope:
    return GeoScope(CITY_GEO, f"{city.name}, {city.state}", f"{city.name}, {city.state}")


def neighborhood_scope(city: City, neighborhood: str) -> GeoScope:
    return GeoScope(
        NEIGHBORHOOD_GEO,
        neighborhood,
        f"{neighborhood}, {city.name}, {city.state}",
    )


def zip_scope(city: City, zip_code: str) -> GeoScope:
    return GeoScope(
        ZIP_GEO,
        zip_code,
        f"ZIP code {zip_code} in {city.name}, {city.state}",
    )


def scopes_for(
    city: City,
    geo_scope: str,
    neighborhoods: list[str] | None = None,
    zip_codes: list[str] | None = None,
) -> list[GeoScope]:
    if geo_scope == CITY_GEO:
        return [city_scope(city)]
    if geo_scope == SAMPLE_GEO:
        return [city_scope(city), *REPRESENTATIVE_AREAS.get(city.name, ())]
    if geo_scope == NEIGHBORHOOD_GEO:
        if not neighborhoods:
            raise ValueError("--neighborhood is required when --geo-scope neighborhood")
        return [neighborhood_scope(city, value) for value in neighborhoods]
    if geo_scope == ZIP_GEO:
        if not zip_codes:
            raise ValueError("--zip-code is required when --geo-scope zip")
        return [zip_scope(city, value) for value in zip_codes]
    raise ValueError("Unknown geo scope. Use city, sample, neighborhood, or zip.")
