# ShikkhaHub — National Education Platform Architecture
# Strategic System Design (৳10,000,000 | 6-Month Roadmap)

## 0. Architecture Philosophy
**PRIORITY: Data > Product > AI > Scale**

This is NOT a website. It's:
- A national education data system
- A trust & verification layer
- A decision engine for students
- A distribution network

---

## 1. Core Database Architecture

### 1.1 Institution Entity (Core)
```sql
CREATE TABLE institutions (
  id UUID PRIMARY KEY,
  
  -- Basic Info
  name VARCHAR(255) NOT NULL,
  name_bengali VARCHAR(255),
  type ENUM('government_college', 'private_college', 'university', 'polytechnic', 'institute', 'madrasah'),
  
  -- Location Hierarchy (Critical for search)
  division VARCHAR(100) NOT NULL,  -- e.g., "Dhaka", "Chittagong"
  district VARCHAR(100) NOT NULL,  -- e.g., "Dhaka Sadar"
  upazila VARCHAR(100),
  address TEXT,
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  
  -- Authority & Verification
  affiliation_authority VARCHAR(255),  -- "UGC", "Dhaka Board", "BTEB"
  affiliation_id VARCHAR(100),  -- govt registration number
  establishment_year INT,
  website_url VARCHAR(500),
  
  -- Contact
  phone_numbers JSONB,  -- ["0123456789", "0987654321"]
  email VARCHAR(255),
  admission_contact JSONB,
  
  -- Data Quality
  verification_status ENUM('unverified', 'pending', 'verified', 'official'),
  verification_source JSONB,  -- {source: 'ugc_official', verified_date, verified_by}
  data_completeness_score INT,  -- 0-100
  last_updated TIMESTAMP,
  last_verified TIMESTAMP,
  
  -- Internal
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX (division, district, type),
  INDEX (verification_status),
  INDEX (type)
);
```

### 1.2 Programs/Courses Entity
```sql
CREATE TABLE programs (
  id UUID PRIMARY KEY,
  institution_id UUID REFERENCES institutions(id) ON DELETE CASCADE,
  
  -- Program Info
  name VARCHAR(255) NOT NULL,
  name_bengali VARCHAR(255),
  level ENUM('diploma', 'bachelor', 'master', 'phd'),
  category ENUM('engineering', 'science', 'arts', 'commerce', 'medical', 'law'),
  duration_years INT,
  
  -- Admission
  admission_requirements JSONB,  -- {min_gpa: 3.5, subjects: [...], tests: [...]}
  seats INT,
  admission_process ENUM('merit', 'entrance', 'mixed'),
  
  -- Course Structure
  subjects JSONB,  -- Array of subject names
  career_paths JSONB,  -- Linked careers
  
  verification_status ENUM('unverified', 'pending', 'verified'),
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  
  INDEX (institution_id, level, category)
);
```

### 1.3 Verification & Trust Layer
```sql
CREATE TABLE institution_verification (
  id UUID PRIMARY KEY,
  institution_id UUID REFERENCES institutions(id),
  
  verification_type ENUM('official_source', 'alumni_verified', 'admin_checked', 'crowd_verified'),
  verified_by VARCHAR(255),  -- Source authority
  verified_date TIMESTAMP,
  
  fields_verified JSONB,  -- {name: true, courses: true, contact: false, ...}
  notes TEXT,
  
  created_at TIMESTAMP
);

-- Authority Mappings (Trust System)
CREATE TABLE authorities (
  id UUID PRIMARY KEY,
  name VARCHAR(255) UNIQUE,  -- "UGC", "Dhaka Board", "BTEB"
  authority_type ENUM('government', 'regulatory'),
  api_endpoint VARCHAR(500),
  credentials JSONB ENCRYPTED,
  
  verification_weight FLOAT,  -- 1.0 = highest trust
  created_at TIMESTAMP
);
```

### 1.4 Data Source Tracking
```sql
CREATE TABLE data_sources (
  id UUID PRIMARY KEY,
  institution_id UUID REFERENCES institutions(id),
  
  source_type ENUM('official_website', 'ugc_directory', 'manual_entry', 'scrape', 'api', 'alumni_report'),
  source_url VARCHAR(500),
  data_collected JSONB,  -- What was collected
  
  collection_date TIMESTAMP,
  collection_method VARCHAR(255),
  confidence_score FLOAT,  -- 0-1
  
  INDEX (institution_id, source_type)
);
```

---

## 2. Data Collection Pipeline

### 2.1 Three-Tier Data Strategy
```
TIER 1: Official Sources (highest priority)
├─ UGC API (Universities)
├─ Board Portals (Colleges)
└─ BTEB System (Polytechnics)

TIER 2: Hybrid Data
├─ Web scraping (institution websites)
├─ Government directories
└─ Media sources

TIER 3: Community Verification
├─ Alumni reports
├─ Student feedback
└─ Crowdsourced corrections
```

### 2.2 Data Collection Architecture
```python
# backend/services/data_collection.py

class InstitutionDataCollector:
    """
    Multi-source institution data collection pipeline
    Priority: Official > Verified > Community
    """
    
    async def collect_from_ugc(self):
        """Fetch from UGC official API"""
        # UGC provides: University list, program details, contacts
        # Highest trust score: 0.95+
        
    async def collect_from_boards(self):
        """Fetch college data from Board portals"""
        # Dhaka Board, Chittagong Board, etc.
        # Trust score: 0.9+
        
    async def collect_from_websites(self):
        """Web scraping institution websites"""
        # Extract: Courses, admission, contact
        # Trust score: 0.7-0.8
        
    async def collect_from_alumni(self, institution_id):
        """Community verification reports"""
        # Alumni submit updates
        # Trust score: 0.6-0.75 (avg of 5+ reports = 0.8+)
        
    async def merge_and_verify(self):
        """
        Merge multiple sources
        If data conflicts:
        - Official source wins
        - Multiple verified sources create flag for review
        """
```

### 2.3 Batch Collection Jobs
```python
# backend/jobs/data_collection_jobs.py

class DataCollectionJobs:
    
    @schedule(cron='0 2 * * 0')  # Weekly Sunday 2 AM
    async def weekly_data_refresh():
        """Full refresh from all sources"""
        
    @schedule(cron='0 * * * *')  # Hourly
    async def hourly_verification_check():
        """Check pending verifications"""
        
    @schedule(cron='0 3 1 * *')  # Monthly
    async def monthly_completeness_audit():
        """Audit data completeness scores"""
```

---

## 3. Search Engine Architecture

### 3.1 Search Index Schema
```
INDEX: institutions_search_v1

Document:
{
  id: "inst_123",
  name: "Dhaka University",
  name_bengali: "ঢাকা বিশ্ববিদ্যালয়",
  
  -- Searchable Fields
  type: "university",
  division: "Dhaka",
  district: "Dhaka Sadar",
  courses: ["Computer Science", "Engineering", "Medicine"],
  
  -- Ranking Signals
  verification_status: "verified",  -- boost
  data_completeness: 98,  -- boost if > 90
  popularity_score: 850,  -- based on views
  student_ratings: 4.5,  -- based on reviews
  
  -- Location
  location: {lat, lng},
  
  -- Text
  combined_text: "Dhaka University ... all searchable content"
}
```

### 3.2 Search Endpoints
```python
# backend/api/search.py

@app.get("/api/v1/search")
async def search(
    query: str,
    filters: SearchFilters,  # type, division, category, etc.
    limit: int = 20
):
    """
    Fast search with:
    - Full-text search
    - Faceted filters
    - Geo-location
    - Sorting by relevance + verification
    
    Response time target: <200ms
    """

# Faceted Search Response
{
    "results": [
        {
            "id": "inst_123",
            "name": "Dhaka University",
            "type": "university",
            "location": "Dhaka",
            "relevance_score": 98,
            "verification_status": "verified",
            "courses_count": 45,
            "student_count": 32000
        }
    ],
    "facets": {
        "type": {
            "university": 234,
            "college": 1200,
            "polytechnic": 450
        },
        "division": {
            "Dhaka": 2100,
            "Chittagong": 890,
            ...
        },
        "verification_status": {
            "verified": 1950,
            "pending": 340
        }
    },
    "total_count": 3400
}
```

---

## 4. AI Decision Engine Architecture

### 4.1 RAG System (NOT Chatbot)
```python
# backend/services/ai_engine.py

class EducationDecisionEngine:
    """
    RAG-based decision engine
    Uses actual institution data, not hallucinations
    """
    
    async def query(self, user_question: str):
        """
        Example: "I got 3.8 GPA. What are my best options for CSE?"
        
        Process:
        1. Parse question → extract criteria
        2. Search institutions matching criteria
        3. Rank by admission probability
        4. Generate explanation with sources
        5. Return actionable recommendations
        """
        
        # Step 1: Parse Query
        criteria = await self.parse_query(user_question)
        # {gpa: 3.8, interest: "CSE", budget: "any", ...}
        
        # Step 2: Search
        matching = await self.search_institutions(criteria)
        # Returns: [top 10 institutions]
        
        # Step 3: Rank & Score
        ranked = await self.rank_by_admission_probability(matching, criteria)
        # {institution, admission_probability, reasoning}
        
        # Step 4: Format Response
        return {
            "recommendations": ranked[:5],
            "explanation": "Based on your GPA and interests...",
            "sources": ["institution_data", "alumni_feedback"],
            "next_steps": ["Check admission deadlines", "Prepare for entrance"]
        }
```

### 4.2 Admission Probability Calculator
```python
class AdmissionProbabilityCalculator:
    """
    Learns from historical admission data
    """
    
    def calculate(self, student_profile, program):
        """
        Factors:
        - Student GPA vs avg admitted GPA
        - Competition ratio (applicants/seats)
        - Subject matching
        - Test scores if required
        - Quota system (if applicable)
        
        Returns: 0-100 probability
        """
```

### 4.3 Career Recommendation Engine
```python
class CareerRecommendationEngine:
    """
    Maps: Student Profile → Program → Career
    """
    
    async def recommend_careers(self, student_profile):
        """
        Input: interests, skills, location
        Output: [
            {career, institutions offering, success_rate, salary_range}
        ]
        """
```

---

## 5. Trust & Verification System

### 5.1 Verification Workflow
```
UNVERIFIED (Initial state)
    ↓ (collected from web/scrape)
PENDING (awaiting verification)
    ↓ (official source OR 5+ verified alumni reports)
VERIFIED (data quality > 85%)
    ↓ (official authority confirms)
OFFICIAL (UGC/Board certified)
```

### 5.2 Verification Badges
```python
# Types of verification badges users see

OFFICIAL = {
    icon: "shield-check",
    label: "Official Data",
    meaning: "Verified by government authority",
    trust_score: 1.0
}

VERIFIED = {
    icon: "check-circle",
    label: "Community Verified",
    meaning: "Verified by 5+ alumni + manual check",
    trust_score: 0.9
}

PENDING = {
    icon: "clock",
    label: "Data Pending Verification",
    meaning: "Collected but awaiting confirmation",
    trust_score: 0.7
}
```

### 5.3 Update Timestamps
```
Every institution shows:
"Last updated: 2 days ago"
"Last verified: 1 week ago"
"Data quality: 94% complete"
```

---

## 6. API Structure (Production-Grade)

### 6.1 Core Endpoints
```
GET /api/v1/institutions
  - List, filter, paginate
  
GET /api/v1/institutions/{id}
  - Full details with verification status
  
GET /api/v1/search
  - Full-text search with facets
  
GET /api/v1/programs/{institution_id}
  - List programs for institution
  
GET /api/v1/ai/recommend
  - AI decision engine
  
POST /api/v1/verify/report
  - Student verification reports (with auth)
```

### 6.2 Response Format (Consistent)
```json
{
  "success": true,
  "data": {...},
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "verification_status": "verified",
    "data_age_hours": 48
  }
}
```

---

## 7. Frontend Architecture

### 7.1 Key Pages
```
/ - Homepage (stats: "10,000+ institutions")
/search - Search engine with filters
/institution/:id - Institution detail + verification badges
/compare - Compare institutions
/ai/recommend - AI decision engine
/admin - Data verification dashboard
```

### 7.2 Key Components
```
SearchFilter (division, type, category)
InstitutionCard (name, location, verified badge, rating)
VerificationBadge (status + last update)
AIRecommendationPanel
DataQualityMeter
LocationMap
```

---

## 8. Month-by-Month Data Targets

### Month 1: Foundation
- 2,000 institutions (top universities + colleges in major cities)
- 100% government institutions
- Complete verification system

### Month 2: MVP Expansion
- 5,000 institutions (add Tier-2 cities)
- 95%+ verification rate
- Working search engine

### Month 3: National Scale
- 10,000+ institutions (all colleges)
- 85%+ verification rate (targeting 90%+)
- Full location hierarchy
- Course-level data for 70%+

### Month 4: AI + Community
- 10,000+ institutions (maintained)
- 90%+ verification rate
- AI recommendation engine live
- Alumni verification system active

### Month 5: Trust Building
- 10,000+ institutions (maintained)
- 92%+ verification rate
- Community Q&A live
- Mentorship features

### Month 6: Dominance
- 10,000+ institutions (maintained)
- 95%+ verification rate
- "If it's not on ShikkhaHub, it doesn't exist"
- Institutional partnerships

---

## 9. Success Metrics

### Data Quality KPIs
- Data completeness: 85%+ by M3, 90%+ by M6
- Verification rate: 90%+ of critical fields
- Update frequency: 95% of data refreshed weekly
- Accuracy: 99%+ (based on official sources)

### User KPIs
- Monthly active users: 100K by M3, 1M by M6
- Search success rate: 95%+ (found what looking for)
- Average session: 5+ minutes
- Returning users: 30%+ weekly

### Performance KPIs
- Search response: <200ms p99
- Page load: <2 sec
- API availability: 99.9%

---

## 10. Why This Wins Bangladesh

If ShikkhaHub becomes:
✓ **Most complete** - 10,000+ institutions
✓ **Most trusted** - Official verification
✓ **Fastest search** - <200ms response
✓ **Best decision engine** - Personalized recommendations
✓ **Most distributed** - Everywhere students are

Then: "If it's not on ShikkhaHub, it doesn't exist"

This becomes the default education reference for Bangladesh.
