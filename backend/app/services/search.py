"""Search service layer with fuzzy matching and personalization."""
import re
from difflib import SequenceMatcher
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.core.elasticsearch import search_institutions as es_search
from app.core.redis import cache_get, cache_set, generate_cache_key
from app.models.institution import Institution
from app.models.location import Division, District, Upazila
from app.models.analytics import SearchEvent, PageView
from app.models.user import User


class FuzzyMatcher:
    """Fuzzy string matching for search typo tolerance."""
    
    @staticmethod
    def similarity(a: str, b: str) -> float:
        """Calculate similarity between two strings (0-1)."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    @staticmethod
    def token_sort_ratio(a: str, b: str) -> float:
        """Calculate similarity ignoring word order."""
        a_tokens = sorted(a.lower().split())
        b_tokens = sorted(b.lower().split())
        return SequenceMatcher(None, a_tokens, b_tokens).ratio()
    
    @staticmethod
    def partial_ratio(a: str, b: str) -> float:
        """Calculate best matching substring similarity."""
        if len(a) > len(b):
            a, b = b, a
        
        best = 0
        for i in range(len(b) - len(a) + 1):
            sub = b[i:i + len(a)]
            ratio = SequenceMatcher(None, a.lower(), sub.lower()).ratio()
            best = max(best, ratio)
        
        return best
    
    @staticmethod
    def weighted_ratio(query: str, target: str) -> float:
        """Combined weighted similarity score."""
        scores = [
            FuzzyMatcher.similarity(query, target) * 0.3,
            FuzzyMatcher.token_sort_ratio(query, target) * 0.3,
            FuzzyMatcher.partial_ratio(query, target) * 0.4
        ]
        return sum(scores)
    
    @staticmethod
    def find_matches(
        query: str,
        candidates: List[str],
        threshold: float = 0.6,
        limit: int = 5
    ) -> List[Tuple[str, float]]:
        """Find fuzzy matches above threshold."""
        matches = []
        for candidate in candidates:
            score = FuzzyMatcher.weighted_ratio(query, candidate)
            if score >= threshold:
                matches.append((candidate, score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]


class PersonalizationEngine:
    """Search personalization based on user behavior."""
    
    @staticmethod
    def get_user_preferences(
        db: Session,
        user_id: Optional[int],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze user search history and page views to build preferences.
        
        Returns:
            Dictionary with preferred institution types, locations, keywords
        """
        if not user_id and not session_id:
            return {}
        
        preferences = {
            'institution_types': {},
            'locations': {},
            'keywords': {},
            'recently_viewed': [],
        }
        
        # Build query based on user_id or session_id
        if user_id:
            # Get user's search history
            searches = db.query(SearchEvent).filter(
                SearchEvent.user_id == user_id
            ).order_by(SearchEvent.created_at.desc()).limit(50).all()
            
            # Get user's page views
            views = db.query(PageView).filter(
                PageView.user_id == user_id,
                PageView.institution_id != None
            ).order_by(PageView.created_at.desc()).limit(20).all()
        else:
            # Use session-based tracking for anonymous users
            searches = db.query(SearchEvent).filter(
                SearchEvent.session_id == session_id
            ).order_by(SearchEvent.created_at.desc()).limit(50).all()
            
            views = db.query(PageView).filter(
                PageView.session_id == session_id,
                PageView.institution_id != None
            ).order_by(PageView.created_at.desc()).limit(20).all()
        
        # Analyze search queries for keywords
        from collections import Counter
        all_queries = ' '.join([s.query for s in searches if s.query])
        words = re.findall(r'\b\w{3,}\b', all_queries.lower())
        common_words = Counter(words).most_common(10)
        preferences['keywords'] = {word: count for word, count in common_words}
        
        # Track recently viewed institutions
        preferences['recently_viewed'] = [
            {
                'institution_id': v.institution_id,
                'institution_name': v.institution_name,
                'viewed_at': v.created_at.isoformat() if v.created_at else None
            }
            for v in views[:5]
        ]
        
        return preferences
    
    @staticmethod
    def apply_personalization_boost(
        results: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        boost_factor: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        Apply personalization boost to search results.
        
        Increases relevance score for institutions matching user preferences.
        """
        if not preferences:
            return results
        
        keywords = preferences.get('keywords', {})
        recently_viewed_ids = {
            v['institution_id'] for v in preferences.get('recently_viewed', [])
        }
        
        for item in results:
            boost = 0.0
            
            # Boost for recently viewed institutions
            if item.get('id') in recently_viewed_ids:
                boost += boost_factor * 0.5  # Smaller boost for "seen before"
            
            # Boost for keyword matches
            name = item.get('name_en', '').lower()
            for keyword, weight in keywords.items():
                if keyword in name:
                    boost += boost_factor * (weight / 10)  # Normalize weight
            
            # Apply boost to existing score or add as personalization_score
            if 'relevance_score' in item:
                item['relevance_score'] = item['relevance_score'] * (1 + boost)
            else:
                item['personalization_boost'] = boost
        
        # Re-sort by boosted score
        results.sort(
            key=lambda x: x.get('relevance_score', 0) + x.get('personalization_boost', 0),
            reverse=True
        )
        
        return results
    
    @staticmethod
    def get_suggested_institutions(
        db: Session,
        user_id: Optional[int],
        session_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get institution suggestions based on user behavior.
        
        Returns institutions similar to what user has been viewing.
        """
        preferences = PersonalizationEngine.get_user_preferences(db, user_id, session_id)
        recently_viewed = preferences.get('recently_viewed', [])
        
        if not recently_viewed:
            # Return featured/popular institutions
            popular = db.query(Institution).filter(
                Institution.is_featured == True,
                Institution.is_active == True
            ).limit(limit).all()
            return [inst.to_dict() for inst in popular]
        
        # Get institution IDs to exclude (already viewed)
        exclude_ids = {v['institution_id'] for v in recently_viewed}
        
        # Get keywords from recent searches
        keywords = list(preferences.get('keywords', {}).keys())
        
        if keywords:
            # Find similar institutions based on keywords
            query = db.query(Institution).filter(
                Institution.is_active == True,
                ~Institution.id.in_(exclude_ids)
            )
            
            # Build OR filter for keywords
            keyword_filters = []
            for keyword in keywords[:3]:  # Use top 3 keywords
                keyword_filters.append(Institution.name_en.ilike(f'%{keyword}%'))
            
            if keyword_filters:
                query = query.filter(or_(*keyword_filters))
            
            results = query.limit(limit).all()
            return [inst.to_dict() for inst in results]
        
        # Fallback: return featured institutions
        popular = db.query(Institution).filter(
            Institution.is_featured == True,
            Institution.is_active == True,
            ~Institution.id.in_(exclude_ids)
        ).limit(limit).all()
        
        return [inst.to_dict() for inst in popular]


class SearchService:
    """Service layer for search operations."""
    
    @staticmethod
    def advanced_search(
        db: Session,
        query: str,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Advanced search with Elasticsearch fallback.
        
        Args:
            db: Database session
            query: Search query string
            page: Page number
            page_size: Results per page
            filters: Optional filters (type_id, division_id, etc.)
        
        Returns:
            Search results with items, total count, pagination info
        """
        cache_key = generate_cache_key(
            "search",
            query,
            page,
            page_size,
            **(filters or {})
        )
        
        # Try cache
        cached = cache_get(cache_key)
        if cached:
            return cached
        
        # Try Elasticsearch first
        try:
            es_results = es_search(
                query=query,
                filters=filters or {},
                page=page,
                page_size=page_size
            )
            
            if es_results and es_results.get('items'):
                # Cache results
                cache_set(cache_key, es_results, ttl=300)
                return es_results
        except Exception:
            # Fall back to database search
            pass
        
        # Database fallback search
        db_query = db.query(Institution)
        
        # Apply text search
        if query:
            search_pattern = f"%{query}%"
            db_query = db_query.filter(
                Institution.name_en.ilike(search_pattern) |
                Institution.name_bn.ilike(search_pattern) |
                Institution.short_name.ilike(search_pattern) |
                Institution.description.ilike(search_pattern)
            )
        
        # Apply filters
        if filters:
            if filters.get('type_id'):
                db_query = db_query.filter(
                    Institution.type_id == filters['type_id']
                )
            if filters.get('division_id'):
                db_query = db_query.join(Upazila).join(District).filter(
                    District.division_id == filters['division_id']
                )
            if filters.get('is_featured'):
                db_query = db_query.filter(Institution.is_featured == True)
        
        # Get results
        total = db_query.count()
        items = db_query.offset((page - 1) * page_size).limit(page_size).all()
        
        results = {
            "query": query,
            "items": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
        
        # Cache results
        cache_set(cache_key, results, ttl=300)
        
        return results
    
    @staticmethod
    def autocomplete(
        db: Session,
        query: str,
        limit: int = 10
    ) -> List[str]:
        """
        Get autocomplete suggestions.
        
        Args:
            db: Database session
            query: Partial query string
            limit: Max suggestions
        
        Returns:
            List of suggestion strings
        """
        cache_key = generate_cache_key("autocomplete", query, limit)
        
        # Try cache
        cached = cache_get(cache_key)
        if cached:
            return cached
        
        # Search institutions
        search_pattern = f"%{query}%"
        institutions = db.query(Institution).filter(
            Institution.name_en.ilike(search_pattern)
        ).limit(limit).all()
        
        suggestions = [inst.name_en for inst in institutions]
        
        # Cache for 1 hour
        cache_set(cache_key, suggestions, ttl=3600)
        
        return suggestions
    
    @staticmethod
    def get_popular_searches(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular search queries."""
        # This would typically come from analytics DB
        # For now, return placeholder data
        return [
            {"query": "Dhaka University", "count": 1543},
            {"query": "Medical College", "count": 1234},
            {"query": "BUET", "count": 987},
            {"query": "Private University", "count": 876},
            {"query": "Rajshahi University", "count": 654},
        ][:limit]
    
    @staticmethod
    def fuzzy_search(
        db: Session,
        query: str,
        threshold: float = 0.6,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fuzzy search for typo-tolerant matching.
        
        Args:
            db: Database session
            query: Search query (may contain typos)
            threshold: Minimum similarity score (0-1)
            limit: Max results to return
            
        Returns:
            List of institutions with fuzzy match scores
        """
        if not query or len(query) < 2:
            return []
        
        # Get all active institutions for fuzzy matching
        institutions = db.query(Institution).filter(
            Institution.is_active == True
        ).all()
        
        # Build candidates list
        candidates = []
        for inst in institutions:
            candidates.append((inst, inst.name_en))
            if inst.name_bn:
                candidates.append((inst, inst.name_bn))
            if inst.short_name:
                candidates.append((inst, inst.short_name))
        
        # Find fuzzy matches
        matches = []
        seen_ids = set()
        
        for inst, name in candidates:
            if inst.id in seen_ids:
                continue
                
            score = FuzzyMatcher.weighted_ratio(query, name)
            if score >= threshold:
                matches.append((inst, score))
                seen_ids.add(inst.id)
        
        # Sort by score and return top results
        matches.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for inst, score in matches[:limit]:
            inst_dict = inst.to_dict()
            inst_dict['fuzzy_score'] = round(score, 3)
            inst_dict['match_type'] = 'fuzzy'
            results.append(inst_dict)
        
        return results
    
    @staticmethod
    def did_you_mean(
        db: Session,
        query: str,
        limit: int = 3
    ) -> List[str]:
        """
        Spell correction suggestions using fuzzy matching.
        
        Args:
            db: Database session
            query: The search query that may have typos
            limit: Number of suggestions to return
            
        Returns:
            List of suggested corrections
        """
        if not query or len(query) < 3:
            return []
        
        # Get all institution names for comparison
        institutions = db.query(Institution).filter(
            Institution.is_active == True
        ).all()
        
        candidates = []
        for inst in institutions:
            candidates.append(inst.name_en)
            if inst.name_bn:
                candidates.append(inst.name_bn)
        
        # Find similar names
        suggestions = FuzzyMatcher.find_matches(
            query, candidates, threshold=0.5, limit=limit
        )
        
        return [s[0] for s in suggestions]
    
    @staticmethod
    def personalized_search(
        db: Session,
        query: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search with personalization based on user behavior.
        
        Args:
            db: Database session
            query: Search query
            user_id: Optional user ID for personalization
            session_id: Optional session ID for anonymous personalization
            page: Page number
            page_size: Results per page
            filters: Optional filters
            
        Returns:
            Search results with personalization applied
        """
        # Get base search results
        base_results = SearchService.advanced_search(
            db, query, page, page_size * 2, filters  # Get more results for re-ranking
        )
        
        # Get user preferences
        preferences = PersonalizationEngine.get_user_preferences(
            db, user_id, session_id
        )
        
        # Apply personalization boost
        boosted_results = PersonalizationEngine.apply_personalization_boost(
            base_results['items'], preferences
        )
        
        # Paginate after re-ranking
        total = len(boosted_results)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_results = boosted_results[start:end]
        
        return {
            "query": query,
            "items": paginated_results,
            "total": base_results['total'],
            "page": page,
            "page_size": page_size,
            "pages": (base_results['total'] + page_size - 1) // page_size,
            "personalized": user_id is not None or session_id is not None,
            "suggestions": SearchService.did_you_mean(db, query) if not query else []
        }
    
    @staticmethod
    def get_suggestions_for_user(
        db: Session,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get personalized institution suggestions.
        
        Returns institutions the user might be interested in based on their history.
        """
        return PersonalizationEngine.get_suggested_institutions(
            db, user_id, session_id, limit
        )


# Export service functions
advanced_search = SearchService.advanced_search
autocomplete = SearchService.autocomplete
get_popular_searches = SearchService.get_popular_searches
fuzzy_search = SearchService.fuzzy_search
did_you_mean = SearchService.did_you_mean
personalized_search = SearchService.personalized_search
get_suggestions_for_user = SearchService.get_suggestions_for_user
