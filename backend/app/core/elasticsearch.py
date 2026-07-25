"""Elasticsearch integration for ShikkhaHub."""
from typing import Optional, List, Dict, Any
from elasticsearch import Elasticsearch, exceptions
from app.core.config import settings

# Elasticsearch client
es_client: Optional[Elasticsearch] = None

def get_elasticsearch_client() -> Optional[Elasticsearch]:
    """Get or create Elasticsearch client."""
    global es_client
    if es_client is None:
        try:
            es_host = getattr(settings, 'ELASTICSEARCH_HOST', 'localhost')
            es_port = getattr(settings, 'ELASTICSEARCH_PORT', 9200)
            
            es_client = Elasticsearch(
                hosts=[{'host': es_host, 'port': es_port, 'scheme': 'http'}],
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Test connection
            if not es_client.ping():
                print("Elasticsearch connection failed")
                es_client = None
            else:
                print(f"Connected to Elasticsearch at {es_host}:{es_port}")
                
                # Ensure index exists
                ensure_index_exists()
                
        except Exception as e:
            print(f"Elasticsearch client error: {e}")
            es_client = None
    
    return es_client

def ensure_index_exists():
    """Create institutions index if it doesn't exist."""
    client = get_elasticsearch_client()
    if client is None:
        return
    
    index_name = "institutions"
    
    if not client.indices.exists(index=index_name):
        # Define mapping for institutions
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "name_en": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "suggest": {
                                "type": "completion"
                            }
                        }
                    },
                    "name_bn": {"type": "text"},
                    "short_name": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "slug": {"type": "keyword"},
                    "type_id": {"type": "integer"},
                    "type_name": {
                        "type": "keyword",
                        "fields": {
                            "text": {"type": "text"}
                        }
                    },
                    "established_year": {"type": "integer"},
                    "address": {"type": "text"},
                    "division_name": {"type": "keyword"},
                    "district_name": {"type": "keyword"},
                    "upazila_name": {"type": "keyword"},
                    "description": {"type": "text"},
                    "education_level": {"type": "keyword"},
                    "verification_status": {"type": "keyword"},
                    "is_featured": {"type": "boolean"},
                    "search_suggest": {
                        "type": "completion"
                    }
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "institution_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "asciifolding",
                                "word_delimiter"
                            ]
                        }
                    }
                }
            }
        }
        
        try:
            client.indices.create(index=index_name, body=mapping)
            print(f"Created Elasticsearch index: {index_name}")
        except Exception as e:
            print(f"Error creating index: {e}")

def index_institution(institution_data: Dict[str, Any]) -> bool:
    """Index a single institution."""
    client = get_elasticsearch_client()
    if client is None:
        return False
    
    try:
        # Add search suggestions
        suggestions = []
        if institution_data.get('name_en'):
            suggestions.append(institution_data['name_en'])
        if institution_data.get('short_name'):
            suggestions.append(institution_data['short_name'])
        
        institution_data['search_suggest'] = suggestions
        
        client.index(
            index="institutions",
            id=institution_data['id'],
            body=institution_data
        )
        return True
    except Exception as e:
        print(f"Error indexing institution: {e}")
        return False

def bulk_index_institutions(institutions: List[Dict[str, Any]]) -> bool:
    """Bulk index multiple institutions."""
    client = get_elasticsearch_client()
    if client is None or not institutions:
        return False
    
    try:
        from elasticsearch.helpers import bulk
        
        actions = []
        for inst in institutions:
            # Add search suggestions
            suggestions = []
            if inst.get('name_en'):
                suggestions.append(inst['name_en'])
            if inst.get('short_name'):
                suggestions.append(inst['short_name'])
            
            inst['search_suggest'] = suggestions
            
            actions.append({
                "_index": "institutions",
                "_id": inst['id'],
                "_source": inst
            })
        
        success, errors = bulk(client, actions, raise_on_error=False)
        print(f"Indexed {success} institutions, {len(errors)} errors")
        return success > 0
        
    except Exception as e:
        print(f"Error bulk indexing: {e}")
        return False

def search_institutions(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """Search institutions with full-text search and filters."""
    client = get_elasticsearch_client()
    if client is None:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}
    
    try:
        # Build query
        must_clauses = []
        
        if query and query.strip():
            # Multi-match query for full-text search
            must_clauses.append({
                "multi_match": {
                    "query": query,
                    "fields": [
                        "name_en^3",
                        "name_en.keyword^2",
                        "short_name^2",
                        "address",
                        "description",
                        "type_name"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                    "prefix_length": 2
                }
            })
        
        # Add filters
        filter_clauses = []
        if filters:
            if filters.get('type_id'):
                filter_clauses.append({"term": {"type_id": filters['type_id']}})
            if filters.get('type_name'):
                filter_clauses.append({"term": {"type_name": filters['type_name']}})
            if filters.get('division_name'):
                filter_clauses.append({"term": {"division_name": filters['division_name']}})
            if filters.get('district_name'):
                filter_clauses.append({"term": {"district_name": filters['district_name']}})
            if filters.get('verification_status'):
                filter_clauses.append({"term": {"verification_status": filters['verification_status']}})
            if filters.get('is_featured') is not None:
                filter_clauses.append({"term": {"is_featured": filters['is_featured']}})
        
        # Build final query
        es_query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}],
                "filter": filter_clauses
            }
        }
        
        # Execute search
        response = client.search(
            index="institutions",
            body={
                "query": es_query,
                "from": (page - 1) * page_size,
                "size": page_size,
                "sort": [
                    {"is_featured": {"order": "desc"}},
                    {"_score": {"order": "desc"}},
                    {"name_en.keyword": {"order": "asc"}}
                ],
                "highlight": {
                    "fields": {
                        "name_en": {},
                        "description": {}
                    }
                }
            }
        )
        
        # Parse results
        hits = response['hits']['hits']
        total = response['hits']['total']['value']
        
        items = []
        for hit in hits:
            source = hit['_source']
            source['_score'] = hit['_score']
            source['_highlight'] = hit.get('highlight', {})
            items.append(source)
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        print(f"Search error: {e}")
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

def get_search_suggestions(query: str, size: int = 10) -> List[str]:
    """Get autocomplete suggestions."""
    client = get_elasticsearch_client()
    if client is None or not query:
        return []
    
    try:
        response = client.search(
            index="institutions",
            body={
                "suggest": {
                    "institution-suggest": {
                        "prefix": query,
                        "completion": {
                            "field": "search_suggest",
                            "size": size,
                            "fuzzy": {
                                "fuzziness": "AUTO"
                            }
                        }
                    }
                }
            }
        )
        
        suggestions = []
        for option in response['suggest']['institution-suggest'][0]['options']:
            suggestions.append(option['text'])
        
        return suggestions
        
    except Exception as e:
        print(f"Suggestions error: {e}")
        return []

def delete_institution_index(institution_id: int) -> bool:
    """Remove institution from index."""
    client = get_elasticsearch_client()
    if client is None:
        return False
    
    try:
        client.delete(index="institutions", id=institution_id)
        return True
    except exceptions.NotFoundError:
        return True  # Already deleted
    except Exception as e:
        print(f"Error deleting institution: {e}")
        return False
