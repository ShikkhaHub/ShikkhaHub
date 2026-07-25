"""AI Service with RAG (Retrieval Augmented Generation) for education assistant."""
import json
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import openai
from app.core.config import settings
from app.core.elasticsearch import search_institutions

# OpenAI configuration
openai.api_key = getattr(settings, 'OPENAI_API_KEY', None)

class SimpleVectorStore:
    """Simple in-memory vector store using TF-IDF for document similarity."""
    
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        self.vectors = None
        self.is_fitted = False
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the vector store."""
        self.documents.extend(documents)
        self._update_vectors()
    
    def _update_vectors(self):
        """Update TF-IDF vectors for all documents."""
        if not self.documents:
            return
        
        texts = [self._extract_text(doc) for doc in self.documents]
        if len(texts) > 0:
            self.vectors = self.vectorizer.fit_transform(texts)
            self.is_fitted = True
    
    def _extract_text(self, doc: Dict[str, Any]) -> str:
        """Extract searchable text from document."""
        text_parts = []
        
        # Institution fields
        if 'name_en' in doc:
            text_parts.append(doc.get('name_en', ''))
        if 'name_bn' in doc:
            text_parts.append(doc.get('name_bn', ''))
        if 'short_name' in doc:
            text_parts.append(doc.get('short_name', ''))
        if 'description' in doc:
            text_parts.append(doc.get('description', ''))
        if 'address' in doc:
            text_parts.append(doc.get('address', ''))
        if 'type_name' in doc:
            text_parts.append(doc.get('type_name', ''))
        if 'division_name' in doc:
            text_parts.append(doc.get('division_name', ''))
        if 'district_name' in doc:
            text_parts.append(doc.get('district_name', ''))
        
        # Course/subject fields
        if 'course_name' in doc:
            text_parts.append(doc.get('course_name', ''))
        if 'subject_name' in doc:
            text_parts.append(doc.get('subject_name', ''))
        
        return ' '.join(text_parts)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if not self.is_fitted or not self.documents:
            return []
        
        # Vectorize query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.vectors).flatten()
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                doc = self.documents[idx].copy()
                doc['_score'] = float(similarities[idx])
                results.append(doc)
        
        return results


# Global vector store instance
_vector_store: Optional[SimpleVectorStore] = None


def get_vector_store() -> SimpleVectorStore:
    """Get or create the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = SimpleVectorStore()
    return _vector_store


class EducationAssistant:
    """AI Education Assistant with RAG capabilities."""
    
    SYSTEM_PROMPT = """You are ShikkhaBot, an AI education assistant for Bangladesh. 
Your role is to help students and parents with:
- Finding suitable institutions (universities, colleges, schools)
- Understanding admission requirements
- Comparing institutions
- Course and career guidance
- Education board information

Guidelines:
1. Always base your answers on the provided context data
2. If you're unsure, say so and suggest how to find the information
3. Be friendly and encouraging
4. Use simple language suitable for students
5. Include specific names and details when available
6. For admissions, mention important dates and requirements
7. When comparing, highlight key differences objectively

Context data will be provided with each query. Use it to give accurate, specific answers."""
    
    def __init__(self):
        self.vector_store = get_vector_store()
    
    async def chat(self, message: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Process a chat message and return AI response."""
        
        # 1. Retrieve relevant context from vector store
        context_docs = self.vector_store.search(message, top_k=5)
        
        # 2. Also search Elasticsearch for institutions
        es_results = search_institutions(message, page_size=5)
        
        # 3. Build context from retrieved data
        context = self._build_context(context_docs, es_results.get('items', []))
        
        # 4. Prepare messages for LLM
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT + "\n\nContext:\n" + context}
        ]
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                messages.append(msg)
        
        messages.append({"role": "user", "content": message})
        
        # 5. Call LLM
        try:
            if openai.api_key:
                response = await self._call_openai(messages)
            else:
                # Fallback to rule-based response if no API key
                response = self._generate_fallback_response(message, context_docs)
            
            return {
                "response": response,
                "context_used": len(context_docs) + len(es_results.get('items', [])),
                "sources": self._extract_sources(context_docs, es_results.get('items', []))
            }
        except Exception as e:
            return {
                "response": f"I apologize, but I'm having trouble processing your request. Error: {str(e)}",
                "context_used": 0,
                "sources": []
            }
    
    def _build_context(self, vector_docs: List[Dict], es_docs: List[Dict]) -> str:
        """Build context string from retrieved documents."""
        context_parts = []
        
        # Add vector store results
        for i, doc in enumerate(vector_docs, 1):
            ctx = f"[{i}] Institution: {doc.get('name_en', 'N/A')}"
            if doc.get('type_name'):
                ctx += f" (Type: {doc['type_name']})"
            if doc.get('description'):
                ctx += f" - {doc['description'][:200]}"
            if doc.get('address'):
                ctx += f" - Address: {doc['address']}"
            if doc.get('established_year'):
                ctx += f" - Established: {doc['established_year']}"
            context_parts.append(ctx)
        
        # Add Elasticsearch results
        for i, doc in enumerate(es_docs, len(vector_docs) + 1):
            ctx = f"[{i}] Institution: {doc.get('name_en', doc.get('name', 'N/A'))}"
            if doc.get('type_name'):
                ctx += f" (Type: {doc['type_name']})"
            if doc.get('division_name'):
                ctx += f" - Location: {doc.get('division_name')}"
            if doc.get('district_name'):
                ctx += f", {doc.get('district_name')}"
            context_parts.append(ctx)
        
        return "\n\n".join(context_parts) if context_parts else "No specific institution data found."
    
    def _extract_sources(self, vector_docs: List[Dict], es_docs: List[Dict]) -> List[Dict]:
        """Extract source information for citations."""
        sources = []
        
        for doc in vector_docs + es_docs:
            sources.append({
                "name": doc.get('name_en') or doc.get('name', 'Unknown'),
                "type": doc.get('type_name', 'Institution'),
                "slug": doc.get('slug'),
                "relevance_score": doc.get('_score', 0)
            })
        
        return sources[:5]  # Top 5 sources
    
    async def _call_openai(self, messages: List[Dict[str, str]]) -> str:
        """Call OpenAI API."""
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",  # Or gpt-4 if available
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error calling AI service: {str(e)}"
    
    def _generate_fallback_response(self, message: str, context_docs: List[Dict]) -> str:
        """Generate a simple response when LLM is not available."""
        message_lower = message.lower()
        
        # Simple keyword matching for common queries
        if 'medical college' in message_lower or 'mbbs' in message_lower:
            return """For medical colleges in Bangladesh, you have several options:
1. Dhaka Medical College - One of the oldest and most prestigious
2. Sir Salimullah Medical College - Also in Dhaka
3. Mymensingh Medical College - Located in Mymensingh
4. Chittagong Medical College - For Chittagong region
5. Rajshahi Medical College - For Rajshahi region

Admission is based on HSC results and a medical admission test. Would you like details about a specific medical college?"""
        
        if 'university' in message_lower and ('best' in message_lower or 'top' in message_lower):
            return """Top universities in Bangladesh include:
1. University of Dhaka (DU) - The oldest and largest
2. BUET - Best for engineering
3. North South University - Top private university
4. BRAC University - Another excellent private option
5. Jahangirnagar University - Known for its beautiful campus

Would you like more details about any specific university?"""
        
        if context_docs:
            names = [doc.get('name_en', 'Unknown') for doc in context_docs[:3]]
            return f"Based on your query, I found these relevant institutions: {', '.join(names)}. Could you be more specific about what you're looking for?"
        
        return """I'm here to help you with education-related questions! I can assist with:
- Finding institutions (universities, colleges, schools)
- Admission requirements and deadlines
- Course information
- Comparing different institutions
- Career guidance

What would you like to know about?"""


# Global assistant instance
_assistant: Optional[EducationAssistant] = None


def get_education_assistant() -> EducationAssistant:
    """Get or create the global education assistant instance."""
    global _assistant
    if _assistant is None:
        _assistant = EducationAssistant()
    return _assistant


async def index_institutions_for_rag(institutions: List[Dict[str, Any]]):
    """Index institutions for RAG system."""
    vector_store = get_vector_store()
    vector_store.add_documents(institutions)
    print(f"Indexed {len(institutions)} institutions for AI search")
