"""
Multi-source data fetcher for the Athar AI knowledge base.

Sources:
  1. Wikipedia      — broad encyclopedia coverage
  2. Met Museum API — 400k+ artworks with rich cultural metadata (no key needed)
  3. World History Encyclopedia — scholarly articles (no key needed)
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Literal

import httpx
import wikipedia
import wikipedia.exceptions

logger = logging.getLogger(__name__)

# ── Wikipedia Topics ──────────────────────────────────────────────────────────
# Organized by civilization for automatic metadata tagging

TOPICS_BY_CATEGORY: dict[str, list[str]] = {
    "islamic": [
        "House of Wisdom",
        "Islamic Golden Age",
        "Al-Khwarizmi",
        "Avicenna",
        "Ibn Khaldun",
        "Averroes",
        "Alhazen",
        "Al-Biruni",
        "Alhambra",
        "Islamic architecture",
        "Islamic calligraphy",
        "Islamic geometric patterns",
        "Abbasid Caliphate",
        "Al-Andalus",
        "Ottoman Empire",
        "Mamluk Sultanate",
        "Dome of the Rock",
        "Great Mosque of Cordoba",
        "Arabesque",
    ],
    "ancient_mediterranean": [
        "Ancient Greece",
        "Ancient Rome",
        "Roman Empire",
        "Ancient Egypt",
        "Egyptian pyramids",
        "Acropolis of Athens",
        "Colosseum",
        "Parthenon",
        "Julius Caesar",
        "Cleopatra",
        "Socrates",
        "Aristotle",
        "Plato",
        "Alexander the Great",
        "Hellenistic period",
        "Roman architecture",
        "Greek mythology",
    ],
    "mesopotamia": [
        "Mesopotamia",
        "Babylon",
        "Sumerian civilization",
        "Epic of Gilgamesh",
        "Cuneiform",
        "Akkadian Empire",
        "Persian Empire",
        "Cyrus the Great",
        "Phoenicia",
    ],
    "asia": [
        "Tang dynasty",
        "Ming dynasty",
        "Song dynasty",
        "Confucius",
        "Great Wall of China",
        "Forbidden City",
        "Silk Road",
        "Mughal Empire",
        "Taj Mahal",
        "Buddhism",
        "Hinduism",
        "Japanese art",
        "Samurai",
        "Angkor Wat",
        "Khmer Empire",
        "Maurya Empire",
        "Gupta Empire",
    ],
    "africa": [
        "Ancient Carthage",
        "Mali Empire",
        "Mansa Musa",
        "Great Zimbabwe",
        "Nubian pyramids",
        "Timbuktu",
        "Axum",
        "Songhai Empire",
        "Kingdom of Kush",
    ],
    "europe": [
        "Byzantine Empire",
        "Medieval Europe",
        "Renaissance",
        "Leonardo da Vinci",
        "Michelangelo",
        "Gothic architecture",
        "Romanesque architecture",
        "Magna Carta",
        "Black Death",
        "Crusades",
        "Age of Exploration",
        "Baroque",
        "Impressionism",
        "Ancient Celtic culture",
        "Viking Age",
    ],
    "americas": [
        "Aztec Empire",
        "Maya civilization",
        "Inca Empire",
        "Machu Picchu",
        "Tenochtitlan",
        "Olmec",
        "Ancestral Puebloans",
    ],
    "science_philosophy": [
        "History of mathematics",
        "History of astronomy",
        "History of medicine",
        "Philosophy",
        "Ancient Greek philosophy",
        "Islamic philosophy",
        "Indian philosophy",
        "Chinese philosophy",
        "Scientific revolution",
        "Alchemy",
    ],
    "monuments": [
        "Seven Wonders of the Ancient World",
        "Stonehenge",
        "Petra",
        "Chichen Itza",
        "Moai",
        "Colosseum",
        "UNESCO World Heritage Site",
    ],
}

# Flat list for default ingestion
WIKIPEDIA_TOPICS: list[str] = []
_seen: set[str] = set()
for _cat_topics in TOPICS_BY_CATEGORY.values():
    for _t in _cat_topics:
        if _t not in _seen:
            _seen.add(_t)
            WIKIPEDIA_TOPICS.append(_t)


def _category_for_topic(title: str) -> str:
    """Return the category key for a topic title."""
    for cat, titles in TOPICS_BY_CATEGORY.items():
        if title in titles:
            return cat
    return "general"


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class FetchedArticle:
    title: str
    content: str
    url: str
    summary: str
    source: Literal["wikipedia", "met_museum", "world_history"] = "wikipedia"
    metadata: dict = field(default_factory=dict)


# ── Wikipedia Fetcher ─────────────────────────────────────────────────────────

def fetch_wikipedia_article(title: str, retries: int = 3) -> FetchedArticle | None:
    """Fetch a single Wikipedia article with disambiguation and retry handling."""
    for attempt in range(retries + 1):
        try:
            page = wikipedia.page(title, auto_suggest=False)
            content = _clean_wikipedia_text(page.content)
            if len(content) < 300:
                logger.warning("'%s' too short, skipping.", title)
                return None
            category = _category_for_topic(title)
            return FetchedArticle(
                title=page.title,
                content=content,
                url=page.url,
                summary=page.summary[:500],
                source="wikipedia",
                metadata={
                    "category": category,
                    "source_type": "encyclopedia",
                    "language": "en",
                },
            )
        except wikipedia.exceptions.DisambiguationError as e:
            if e.options:
                logger.info("Disambiguation '%s' -> '%s'", title, e.options[0])
                title = e.options[0]
            else:
                return None
        except wikipedia.exceptions.PageError:
            logger.warning("Page not found: '%s'", title)
            return None
        except Exception as e:
            if attempt < retries:
                wait = (attempt + 1) * 3  # 3s, 6s, 9s
                logger.warning("Fetch error '%s' (attempt %d/%d): %s — retry in %ds",
                               title, attempt + 1, retries, e, wait)
                time.sleep(wait)
            else:
                logger.error("Failed after %d attempts: '%s'", retries, title)
                return None
    return None


def fetch_wikipedia_articles(
    topics: list[str] | None = None,
    max_articles: int = 40,
    delay_seconds: float = 0.5,
) -> list[FetchedArticle]:
    """Fetch multiple Wikipedia articles with rate limiting."""
    topics = (topics or WIKIPEDIA_TOPICS)[:max_articles]
    wikipedia.set_lang("en")

    fetched: list[FetchedArticle] = []
    for i, topic in enumerate(topics, 1):
        logger.info("[%d/%d] Wikipedia: %s", i, len(topics), topic)
        article = fetch_wikipedia_article(topic)
        if article:
            fetched.append(article)
        if i < len(topics):
            time.sleep(delay_seconds)

    logger.info("Wikipedia: %d/%d articles fetched", len(fetched), len(topics))
    return fetched


# ── Met Museum API Fetcher ────────────────────────────────────────────────────
# Public API — no key required
# Docs: https://metmuseum.github.io/

MET_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"

# Departments with the richest cultural content
MET_DEPARTMENTS = {
    6:  "Asian Art",
    10: "Egyptian Art",
    11: "European Paintings",
    14: "Greek and Roman Art",
    16: "Islamic Art",
    17: "Medieval Art",
    19: "Musical Instruments",
    21: "African Art",
    5:  "Arts of Africa, Oceania, and the Americas",
    3:  "Ancient Near Eastern Art",
}


def fetch_met_department(
    department_id: int,
    max_objects: int = 30,
    min_description_length: int = 200,
) -> list[FetchedArticle]:
    """
    Fetch artwork descriptions from one Met Museum department.
    Filters for objects that have a meaningful description.
    """
    department_name = MET_DEPARTMENTS.get(department_id, f"Department {department_id}")
    articles: list[FetchedArticle] = []

    try:
        with httpx.Client(timeout=30) as client:
            # Get object IDs for the department
            resp = client.get(
                f"{MET_BASE}/objects",
                params={"departmentIds": department_id},
            )
            resp.raise_for_status()
            object_ids: list[int] = resp.json().get("objectIDs", [])[:500]

            if not object_ids:
                logger.warning("No objects found in Met department %d", department_id)
                return []

            logger.info("Met Museum '%s': scanning %d objects for %d with descriptions",
                        department_name, len(object_ids), max_objects)

            fetched = 0
            for obj_id in object_ids:
                if fetched >= max_objects:
                    break

                try:
                    obj_resp = client.get(f"{MET_BASE}/objects/{obj_id}")
                    obj_resp.raise_for_status()
                    obj = obj_resp.json()

                    # Build a rich description from available fields
                    description = _build_met_description(obj)
                    if len(description) < min_description_length:
                        continue

                    title = obj.get("title") or f"Object {obj_id}"
                    culture = obj.get("culture", "")
                    period = obj.get("period", "")
                    dynasty = obj.get("dynasty", "")
                    artist = obj.get("artistDisplayName", "")
                    date_str = obj.get("objectDate", "")
                    medium = obj.get("medium", "")
                    url = obj.get("objectURL", "")

                    articles.append(FetchedArticle(
                        title=f"{title} — {department_name}",
                        content=description,
                        url=url,
                        summary=description[:300],
                        source="met_museum",
                        metadata={
                            "category": department_name.lower().replace(" ", "_"),
                            "source_type": "museum_collection",
                            "culture": culture,
                            "period": period,
                            "dynasty": dynasty,
                            "artist": artist,
                            "date": date_str,
                            "medium": medium,
                            "department": department_name,
                            "object_id": str(obj_id),
                        },
                    ))
                    fetched += 1
                    time.sleep(0.1)

                except Exception as e:
                    logger.debug("Met object %d error: %s", obj_id, e)
                    continue

    except Exception as e:
        logger.error("Met Museum department %d fetch error: %s", department_id, e)

    logger.info("Met Museum '%s': got %d objects", department_name, len(articles))
    return articles


def fetch_met_museum(
    department_ids: list[int] | None = None,
    max_per_department: int = 25,
) -> list[FetchedArticle]:
    """Fetch artwork descriptions from multiple Met Museum departments."""
    department_ids = department_ids or list(MET_DEPARTMENTS.keys())
    all_articles: list[FetchedArticle] = []
    for dept_id in department_ids:
        articles = fetch_met_department(dept_id, max_objects=max_per_department)
        all_articles.extend(articles)
        time.sleep(1.0)
    logger.info("Met Museum total: %d artworks fetched", len(all_articles))
    return all_articles


def _build_met_description(obj: dict) -> str:
    """Build a descriptive text from Met Museum object fields."""
    parts: list[str] = []

    title = obj.get("title", "Untitled")
    parts.append(f"Title: {title}")

    if obj.get("artistDisplayName"):
        parts.append(f"Artist: {obj['artistDisplayName']}")
    if obj.get("culture"):
        parts.append(f"Culture: {obj['culture']}")
    if obj.get("period"):
        parts.append(f"Period: {obj['period']}")
    if obj.get("dynasty"):
        parts.append(f"Dynasty: {obj['dynasty']}")
    if obj.get("objectDate"):
        parts.append(f"Date: {obj['objectDate']}")
    if obj.get("medium"):
        parts.append(f"Medium: {obj['medium']}")
    if obj.get("dimensions"):
        parts.append(f"Dimensions: {obj['dimensions']}")
    if obj.get("department"):
        parts.append(f"Department: {obj['department']}")
    if obj.get("objectName"):
        parts.append(f"Object type: {obj['objectName']}")
    if obj.get("classification"):
        parts.append(f"Classification: {obj['classification']}")
    if obj.get("creditLine"):
        parts.append(f"Credit: {obj['creditLine']}")
    if obj.get("geographyType") and obj.get("city"):
        parts.append(f"Geography: {obj.get('geographyType', '')} {obj.get('city', '')} {obj.get('country', '')}")
    if obj.get("excavation"):
        parts.append(f"Excavation: {obj['excavation']}")
    if obj.get("rightsAndReproduction"):
        parts.append(f"Rights: {obj['rightsAndReproduction']}")

    # Tags (extra keywords)
    tags = obj.get("tags", [])
    if tags:
        tag_str = ", ".join(t.get("term", "") for t in tags if t.get("term"))
        if tag_str:
            parts.append(f"Subjects: {tag_str}")

    return "\n".join(parts)


# ── Unified fetch_all_articles ────────────────────────────────────────────────

def fetch_all_articles(
    topics: list[str] | None = None,
    max_articles: int = 40,
    include_met: bool = True,
    met_max_per_dept: int = 20,
) -> list[FetchedArticle]:
    """
    Fetch from all configured sources.

    Args:
        topics: Wikipedia topics (None = all defaults).
        max_articles: Max Wikipedia articles.
        include_met: Whether to include Met Museum objects.
        met_max_per_dept: Max artworks per Met department.
    """
    all_articles: list[FetchedArticle] = []

    # Source 1: Wikipedia
    wiki_articles = fetch_wikipedia_articles(
        topics=topics,
        max_articles=max_articles,
    )
    all_articles.extend(wiki_articles)

    # Source 2: Met Museum (if no custom topics override)
    if include_met and topics is None:
        logger.info("Fetching Met Museum collection data...")
        met_articles = fetch_met_museum(max_per_department=met_max_per_dept)
        all_articles.extend(met_articles)

    logger.info(
        "Total corpus: %d documents (%d Wikipedia, %d Met Museum)",
        len(all_articles),
        len(wiki_articles),
        len(all_articles) - len(wiki_articles),
    )
    return all_articles


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean_wikipedia_text(text: str) -> str:
    """Remove citations, section markers, and normalize whitespace."""
    text = re.sub(r"\[\d+\]|\[note \d+\]|\[citation needed\]|\[edit\]", "", text)
    text = re.sub(r"={2,}[^=]+=+\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
