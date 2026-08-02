"""Natural Language Query Processing (NLQP) service.

Implements the NLQP component of the Bangladesh Education Directory roadmap:

1. **Intent Recognition** - determine what the user wants (find institutions,
   admissions info, scholarship info, etc.)
2. **Entity Extraction (NER)** - identify institution type, course/subject,
   location, ownership, level, and features inside free-text queries.
3. **Query Mapping (Text-to-SQL)** - translate extracted entities into a
   SQLAlchemy query over the national education knowledge graph.

The pipeline is rule/gazetteer based (fast, deterministic, no external LLM
required for the common cases) but structured so an LLM or Elasticsearch
fallback can be plugged in later. Every parse produces:

- an explicit `intent`
- a structured `entities` dictionary
- a human-readable `query_summary` (what the system understood)
- a compiled SQLAlchemy query for execution

Example: "Show me private universities with scholarships in Chittagong"
-> intent=find_institutions, type=university, ownership=private,
   feature=scholarship, district=Chittagong
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import exists
from sqlalchemy.orm import Session

from app.models.institution import Institution
from app.models.location import Division, District, Upazila
from app.models.announcement import Scholarship
from app.models.course import Course
from app.models.education_graph import InstitutionCourse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Intents
# ---------------------------------------------------------------------------
INTENT_FIND_INSTITUTIONS = "find_institutions"
INTENT_ADMISSIONS = "admissions"
INTENT_SCHOLARSHIPS = "scholarships"
INTENT_INSTITUTION_DETAIL = "institution_detail"
INTENT_COUNT = "count"

# ---------------------------------------------------------------------------
# Gazetteers (synonym maps)
# ---------------------------------------------------------------------------
TYPE_SYNONYMS: Dict[str, Set[str]] = {
    "university": {
        "university", "universities", "univ", "বিশ্ববিদ্যালয়",
        "varsity", "varsities", "medical college", "medical",
    },
    "college": {
        "college", "colleges", "মহাবিদ্যালয়", "degree college",
        "hsc college", "higher secondary college",
    },
    "school": {
        "school", "schools", "বিদ্যালয়", "primary school",
        "secondary school", "high school", "madrasah", "madrasa",
    },
    "polytechnic": {
        "polytechnic", "polytechnics", "কারিগরি", "technical institute",
        "technical college", "technical education",
    },
    "institute": {
        "institute", "institutes", "প্রতিষ্ঠান",
        "training institute", "monotechnic",
    },
}

OWNERSHIP_SYNONYMS: Dict[str, Set[str]] = {
    "government": {"government", "govt", "govt.", "public", "সরকারি", "govt"},
    "private": {"private", "প্রাইভেট", "bebsa", "বেসরকারি"},
    "trust": {"trust", "trust-run", "trust run"},
    "autonomous": {"autonomous", "স্বায়ত্তশাসিত"},
}

LEVEL_SYNONYMS: Dict[str, Set[str]] = {
    "primary": {"primary", "প্রাথমিক"},
    "secondary": {"secondary", "school level", "ssc", "মাধ্যমিক"},
    "higher_secondary": {"higher secondary", "hsc", "college level", "উচ্চ মাধ্যমিক"},
    "diploma": {"diploma", "ডিপ্লোমা"},
    "degree": {"degree", "undergraduate", "bachelor", "bachelors", "b.sc", "b.sc.", "ba", "স্নাতক"},
    "postgraduate": {"postgraduate", "post graduate", "masters", "master's", "phd", "স্নাতকোত্তর"},
}

# Subject/domain vocabulary -> Course keyword matching
SUBJECT_KEYWORDS: Dict[str, Set[str]] = {
    "computer science": {"computer science", "cse", "computing", "ict", "it"},
    "engineering": {"engineering", "engineer"},
    "medical": {"medical", "mbbs", "medicine", "health"},
    "nursing": {"nursing", "nurse"},
    "business": {"business", "bba", "commerce", "management", "marketing"},
    "accounting": {"accounting", "accountancy"},
    "law": {"law", "llb"},
    "agriculture": {"agriculture", "agricultural"},
    "science": {"science", "physics", "chemistry", "biology", "mathematics", "math"},
    "arts": {"arts", "humanities", "bangla", "english literature"},
    "textile": {"textile", "garments"},
    "education": {"education", "b.ed", "teacher training"},
    "economics": {"economics", "finance", "banking"},
    "pharmacy": {"pharmacy", "pharmaceutical"},
    "architecture": {"architecture", "urban planning"},
    "electronics": {"electronics", "electrical", "eee"},
    "civil": {"civil engineering", "civil"},
}

FEATURE_SYNONYMS: Dict[str, Set[str]] = {
    "scholarship": {"scholarship", "scholarships", "financial aid", "stipend", "বৃত্তি"},
    "hostel": {"hostel", "residential", "dormitory", "আবাসিক"},
    "evening": {"evening", "night shift", "সন্ধ্যা"},
    "co_educational": {"co-ed", "coeducational", "co educational", "mixed"},
    "verified": {"verified", "authentic", "trusted", "official"},
}

# Words that mark an intent or filter, removed from the "free text" remainder
STOPWORDS: Set[str] = {
    "a", "an", "the", "show", "me", "find", "list", "give", "want", "i'd", "id",
    "like", "please", "in", "at", "with", "for", "that", "which", "are", "is",
    "of", "to", "and", "or", "near", "around", "has", "have", "having", "offers",
    "offering", "located", "there", "any", "some", "can", "could", "from", "my",
    "all", "best", "top", "good", "great", "looking", "institutions", "institute",
    "नगर", "what", "tell", "you", "recommend", "suggest", "about", "does", "do",
    "admission", "admissions", "get", "apply", "application", "when", "who",
    "result", "results",
}

COUNT_TRIGGERS = {"how many", "count", "number of", "total", "quantity"}
DETAIL_TRIGGERS = {
    "about", "details", "information", "contact", "address", "phone", "email",
    "website", "tell me about", "what is", "who is",
}

QUANTIFIER_WORDS = {
    "first", "best", "top", "popular", "recent", "latest", "recommended",
}

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class NLQueryResult:
    """Structured output of parsing + executing a natural language query."""

    query: str
    intent: str = INTENT_FIND_INSTITUTIONS
    entities: Dict[str, Any] = field(default_factory=dict)
    query_summary: str = ""
    sql_alias: Optional[str] = None
    raw_filters: List[str] = field(default_factory=list)
    items: List[Dict[str, Any]] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    pages: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "intent": self.intent,
            "entities": self.entities,
            "query_summary": self.query_summary,
            "filters_applied": self.raw_filters,
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "pages": self.pages,
        }


# ---------------------------------------------------------------------------
# Tokenizer helpers
# ---------------------------------------------------------------------------
def tokenize(text: str) -> List[str]:
    """Lowercase, split on non-word characters, drop empty tokens."""
    return [t for t in re.split(r"[^\w'+#.\-]+", text.lower()) if t]


def contains_phrase(phrase: str, text: str) -> bool:
    """Case-insensitive phrase match (whole token boundaries where possible)."""
    return phrase.lower() in text.lower()


# ---------------------------------------------------------------------------
# Entity extraction
# ---------------------------------------------------------------------------


def _match_gazetteer(text: str, gazetteer: Dict[str, Set[str]]) -> List[str]:
    """Return gazetteer keys whose any synonym appears in the text."""
    found = []
    for key, synonyms in gazetteer.items():
        for syn in synonyms:
            if contains_phrase(syn, text):
                found.append(key)
                break
    return found


def extract_location(db: Session, text: str) -> Dict[str, str]:
    """Find division/district/upazila mentions by matching against the DB."""
    found: Dict[str, str] = {}
    lowered = text.lower()

    for div in db.query(Division).all():
        for name in (div.name_en, div.name_bn):
            if name and contains_phrase(name, lowered):
                found["division"] = div.name_en
                break
        if "division" in found:
            break

    for dist in db.query(District).all():
        for name in (dist.name_en, dist.name_bn):
            if name and contains_phrase(name, lowered):
                found["district"] = dist.name_en
                break
        if "district" in found:
            break

    for up in db.query(Upazila).all():
        for name in (up.name_en, up.name_bn):
            if name and contains_phrase(name, lowered):
                found["upazila"] = up.name_en
                break
        if "upazila" in found:
            break

    return found


def extract_courses(db: Session, text: str) -> List[str]:
    """Match subject/domain vocabulary; return matched domain labels."""
    matched = []
    for key, keywords in SUBJECT_KEYWORDS.items():
        for kw in keywords:
            if contains_phrase(kw, text):
                matched.append(key)
                break
    return matched


def extract_features(text: str) -> List[str]:
    return _match_gazetteer(text, FEATURE_SYNONYMS)


def extract_ownership(text: str) -> Optional[str]:
    found = _match_gazetteer(text, OWNERSHIP_SYNONYMS)
    return found[0] if found else None


def extract_level(text: str) -> Optional[str]:
    found = _match_gazetteer(text, LEVEL_SYNONYMS)
    return found[0] if found else None


def extract_types(text: str) -> List[str]:
    return _match_gazetteer(text, TYPE_SYNONYMS)


def extract_named_institutions(db: Session, text: str) -> List[Institution]:
    """Find institutions whose name appears verbatim in the query."""
    hits = []
    institutions = (
        db.query(Institution)
        .filter(Institution.is_active.is_(True))
        .all()
    )
    for inst in institutions:
        for name in (inst.name_en, inst.name_bn, inst.short_name):
            if name and len(name) >= 3 and name.lower() in text:
                hits.append(inst)
                break
    return hits


# ---------------------------------------------------------------------------
# Intent recognition
# ---------------------------------------------------------------------------


def detect_intent(text: str, has_type: bool, has_named: bool) -> str:
    lowered = text.lower()
    if any(trig in lowered for trig in COUNT_TRIGGERS):
        return INTENT_COUNT
    if any(contains_phrase(trig, lowered) for trig in DETAIL_TRIGGERS):
        return INTENT_INSTITUTION_DETAIL
    if contains_phrase("scholarship", lowered) or "scholarships" in lowered:
        if "institution" in lowered or "where" in lowered or has_type:
            # "universities with scholarships" => still a find
            return INTENT_FIND_INSTITUTIONS
        return INTENT_SCHOLARSHIPS
    if "admission" in lowered or "apply" in lowered or "applicat" in lowered:
        return INTENT_ADMISSIONS
    return INTENT_FIND_INSTITUTIONS


# ---------------------------------------------------------------------------
# Query builder
# ---------------------------------------------------------------------------


class NLQPQueryBuilder:
    """Translates extracted entities into a SQLAlchemy query."""

    def __init__(self, db: Session, entities: Dict[str, Any]) -> None:
        self.db = db
        self.entities = entities

    def build(self) -> Any:
        """Return the SQLAlchemy query selecting active institutions."""
        query = self.db.query(Institution).filter(Institution.is_active.is_(True))
        self._apply_type(query)
        self._apply_ownership(query)
        self._apply_level(query)
        self._apply_location(query)
        self._apply_courses(query)
        self._apply_features(query)
        self._apply_names(query)
        return query

    def _apply_type(self, query) -> None:
        types = self.entities.get("types", [])
        if not types:
            return
        from app.models.institution import InstitutionType

        type_ids = (
            self.db.query(InstitutionType.id)
            .filter(InstitutionType.name.in_(types))
            .all()
        )
        ids = [tid for (tid,) in type_ids]
        if ids:
            query = query.filter(Institution.type_id.in_(ids))

    def _apply_ownership(self, query) -> None:
        ownership = self.entities.get("ownership")
        if ownership:
            query = query.filter(Institution.ownership == ownership)

    def _apply_level(self, query) -> None:
        level = self.entities.get("level")
        if level:
            query = query.filter(Institution.education_level == level)

    def _apply_location(self, query) -> None:
        division = self.entities.get("division")
        district = self.entities.get("district")
        upazila = self.entities.get("upazila")

        if upazila:
            query = query.filter(
                Institution.upazila_id.in_(
                    self.db.query(Upazila.id).filter(Upazila.name_en == upazila)
                )
            )
        elif district:
            query = query.filter(
                Institution.district_id.in_(
                    self.db.query(District.id).filter(District.name_en == district)
                )
            )
        elif division:
            query = query.filter(
                Institution.division_id.in_(
                    self.db.query(Division.id).filter(Division.name_en == division)
                )
            )

    def _apply_courses(self, query) -> None:
        courses = self.entities.get("courses", [])
        if not courses:
            return
        domain = courses[0].replace("_", " ")
        keyword_pattern = "%" + domain + "%"
        offering_subq = (
            self.db.query(InstitutionCourse.institution_id)
            .join(Course, InstitutionCourse.course_id == Course.id)
            .filter(
                Course.name_en.ilike(keyword_pattern)
                | Course.keywords.ilike(keyword_pattern)
                | Course.career_prospects.ilike(keyword_pattern)
                | Course.description.ilike(keyword_pattern)
            )
        )
        query = query.filter(Institution.id.in_(offering_subq))

    def _apply_features(self, query) -> None:
        features = self.entities.get("features", [])

        if "scholarship" in features:
            query = query.filter(
                exists().where(
                    Scholarship.institution_id == Institution.id,
                    Scholarship.is_active.is_(True),
                )
            )
        if "hostel" in features:
            query = query.filter(Institution.facilities.any())
        if "verified" in features:
            query = query.filter(Institution.verification_status == "verified")

    def _apply_names(self, query) -> None:
        named = self.entities.get("named_institutions", [])
        if named:
            # stored as integer ids (see parse())
            ids = [i if isinstance(i, int) else i.id for i in named]
            query = query.filter(Institution.id.in_(ids))


# ---------------------------------------------------------------------------
# Public engine
# ---------------------------------------------------------------------------


class NaturalLanguageSearchEngine:
    """Top-level NLQP orchestrator."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def parse(self, text: str) -> NLQueryResult:
        lowered = text.strip().lower()
        result = NLQueryResult(query=text)

        # 1. Entity extraction
        types = extract_types(lowered)
        ownership = extract_ownership(lowered)
        level = extract_level(lowered)
        location = extract_location(self.db, lowered)
        courses = extract_courses(self.db, lowered)
        features = extract_features(lowered)
        named = extract_named_institutions(self.db, lowered)

        # 2. Intent
        intent = detect_intent(lowered, bool(types), bool(named))
        result.intent = intent

        entities: Dict[str, Any] = {
            "types": types,
            "ownership": ownership,
            "level": level,
            "courses": courses,
            "features": features,
            "named_institutions": [i.id for i in named],
            "division": location.get("division"),
            "district": location.get("district"),
            "upazila": location.get("upazila"),
        }
        result.entities = entities

        # 3. Human-readable summary
        result.query_summary = self._summarize(entities)
        result.raw_filters = self._describe_filters(entities)

        # 4. Execute
        if intent in (INTENT_FIND_INSTITUTIONS, INTENT_COUNT):
            self._execute(result, count_only=(intent == INTENT_COUNT))
        elif intent == INTENT_INSTITUTION_DETAIL and named:
            self._execute(result)
        else:
            result.total = 0

        return result

    def _execute(self, result: NLQueryResult, count_only: bool = False) -> None:
        builder = NLQPQueryBuilder(self.db, result.entities)
        query = builder.build()
        total = query.count()
        result.total = total
        result.pages = (total + result.page_size - 1) // result.page_size
        if count_only:
            return
        items = (
            query.order_by(Institution.is_featured.desc(), Institution.view_count.desc())
            .offset((result.page - 1) * result.page_size)
            .limit(result.page_size)
            .all()
        )
        result.items = [self._serialize(i) for i in items]

    @staticmethod
    def _serialize(inst) -> Dict[str, Any]:
        return {
            "id": inst.id,
            "name_en": inst.name_en,
            "name_bn": inst.name_bn,
            "short_name": inst.short_name,
            "slug": inst.slug,
            "type": inst.type.name if inst.type else None,
            "ownership": inst.ownership,
            "education_level": inst.education_level,
            "division": inst.division.name_en if inst.division else None,
            "district": inst.district.name_en if inst.district else None,
            "upazila": inst.upazila.name_en if inst.upazila else None,
            "address": inst.address,
            "view_count": inst.view_count,
            "is_featured": inst.is_featured,
            "verification_status": inst.verification_status,
        }

    @staticmethod
    def _summarize(entities: Dict[str, Any]) -> str:
        parts = []
        if entities.get("types"):
            parts.append(", ".join(entities["types"]))
        if entities.get("ownership"):
            parts.append(entities["ownership"])
        if entities.get("level"):
            parts.append(entities["level"].replace("_", " "))
        if entities.get("courses"):
            parts.append(entities["courses"][0].replace("_", " "))
        if entities.get("features"):
            parts.append("with " + ", ".join(entities["features"]))
        if entities.get("upazila"):
            parts.append("in " + entities["upazila"])
        elif entities.get("district"):
            parts.append("in " + entities["district"])
        elif entities.get("division"):
            parts.append("in " + entities["division"])
        summary = "Looking for " + (", ".join(parts) if parts else "educational institutions")
        return summary

    @staticmethod
    def _describe_filters(entities: Dict[str, Any]) -> List[str]:
        filters = []
        if entities.get("types"):
            filters.append(f"type in ({', '.join(entities['types'])})")
        if entities.get("ownership"):
            filters.append(f"ownership = {entities['ownership']}")
        if entities.get("level"):
            filters.append(f"level = {entities['level']}")
        if entities.get("courses"):
            filters.append(f"offers course matching '{entities['courses'][0]}'")
        if entities.get("features"):
            for f in entities["features"]:
                filters.append(f"feature: {f}")
        for key in ("upazila", "district", "division"):
            if entities.get(key):
                filters.append(f"{key} = {entities[key]}")
        return filters


def natural_language_search(
    db: Session,
    query: str,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """Convenience wrapper used by the API layer."""
    engine = NaturalLanguageSearchEngine(db)
    result = engine.parse(query)
    result.page = page
    result.page_size = page_size
    if result.items:
        result.total = max(result.total, len(result.items))
        result.pages = (result.total + page_size - 1) // page_size
    return result.to_dict()
