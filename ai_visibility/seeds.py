from __future__ import annotations

from ai_visibility.models import Business


SAMPLE_COMPETITORS: dict[tuple[str, str], list[Business]] = {
    ("Houston", "personal injury"): [
        Business("The Ammons Law Firm, LLP", "https://www.ammonslaw.com/"),
        Business("Bankston & Associates", "https://www.bankstonlaw.net/"),
        Business("Blizzard Law, PLLC", "https://www.blizzardlaw.com/"),
        Business("The Lanier Law Firm", "https://www.lanierlawfirm.com/"),
        Business("Arnold & Itkin LLP", "https://www.arnolditkin.com/"),
        Business("The Krist Law Firm, P.C.", "https://www.houstoninjurylawyer.com/"),
        Business("The Sher Law Firm, PLLC", "https://sher-law.com/"),
        Business("Sorey & Hoover, LLP", "https://soreylaw.com/"),
        Business("Sorrels Law", "https://www.sorrelslaw.com/"),
        Business("Baumgartner Law Firm", "https://baumgartnerlawyers.com/"),
        Business("Stephen Boutros, LTD.", "https://www.boutroslaw.com/"),
        Business("HURTINTEXAS.COM Law Firm", "https://www.hurtintexas.com/"),
        Business("Leo & Oginni Personal Injury Lawyers, PLLC", "https://www.helpishere.law/"),
        Business("Shariff Injury Lawyers", "https://www.shariffinjurylawyers.com/"),
        Business("Simon & O'Rourke Car Accident & Personal Injury Lawyers", "https://solawpc.com/"),
    ],
    ("New York", "personal injury"): [
        Business("Example Injury Law"),
        Business("Manhattan Accident Counsel"),
        Business("Five Borough Injury Group"),
        Business("Empire Trial Attorneys"),
        Business("NYC Injury Partners"),
        Business("Broadway Personal Injury Law"),
        Business("Metro Accident Advocates"),
        Business("Hudson Legal Group"),
    ],
}


def sample_businesses(city: str, practice_area: str, target_business: str) -> list[Business]:
    businesses = list(SAMPLE_COMPETITORS.get((city, practice_area), []))
    if not businesses:
        businesses = [
            Business(target_business),
            Business(f"{city} Legal Advocates"),
            Business(f"{city} Trial Group"),
            Business(f"{city} Justice Partners"),
            Business(f"{city} Counsel Group"),
            Business(f"Downtown {city} Attorneys"),
            Business(f"Metro {city} Law"),
            Business(f"{city} Client First Law"),
        ]
    if all(business.name != target_business for business in businesses):
        businesses.insert(0, Business(target_business))
    return businesses
