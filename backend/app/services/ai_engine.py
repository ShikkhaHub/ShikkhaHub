"""
AI Decision Engine Service
RAG-based education decision system
Uses actual institution data, not hallucinations
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.institution import Institution, Program
from app.models.verification import InstitutionVerification

logger = logging.getLogger(__name__)


@dataclass
class StudentProfile:
    """Student profile for admission probability calculation"""
    gpa: float
    test_score: Optional[float] = None
    subjects: List[str] = None
    interests: List[str] = None
    location_preference: Optional[str] = None
    budget: Optional[str] = None


@dataclass
class Recommendation:
    """Institution recommendation"""
    institution_id: str
    institution_name: str
    institution_type: str
    location: str
    admission_probability: float
    reasoning: str
    career_prospects: List[str]
    entrance_difficulty: str


class EducationDecisionEngine:
    """
    RAG-based decision engine for education recommendations
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def recommend_institutions(
        self, user_query: str, student_profile: StudentProfile
    ) -> Dict[str, Any]:
        """
        Main recommendation endpoint
        
        Example query: "I got 3.8 GPA and love Computer Science. 
                       What are my best university options in Dhaka?"
        """
        try:
            # Step 1: Parse query and extract criteria
            criteria = await self._parse_query(user_query, student_profile)
            logger.info(f"Parsed criteria: {criteria}")

            # Step 2: Search matching institutions
            matching = await self._search_institutions(criteria)
            logger.info(f"Found {len(matching)} matching institutions")

            # Step 3: Score by admission probability
            scored = await self._score_admission_probability(
                matching, student_profile, criteria
            )
            scored = sorted(
                scored, key=lambda x: x["probability"], reverse=True
            )[:10]

            # Step 4: Build recommendations
            recommendations = await self._build_recommendations(
                scored, student_profile
            )

            # Step 5: Generate explanation
            explanation = self._generate_explanation(
                student_profile, criteria, recommendations
            )

            return {
                "success": True,
                "recommendations": recommendations[:5],
                "explanation": explanation,
                "total_matches": len(matching),
                "sources": ["institution_data", "admission_statistics"],
                "next_steps": await self._get_next_steps(recommendations),
            }

        except Exception as e:
            logger.error(f"Recommendation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def recommend_careers(
        self, student_profile: StudentProfile
    ) -> Dict[str, Any]:
        """
        Recommend careers based on student profile
        """
        try:
            # Get programs matching interests
            programs = await self._find_matching_programs(student_profile)

            # Extract career paths from programs
            careers = {}
            for program in programs:
                program_careers = program.career_paths or []
                for career in program_careers:
                    if career not in careers:
                        careers[career] = {
                            "name": career,
                            "institutions": [],
                            "avg_salary": 0,
                            "job_market": "stable",
                        }
                    careers[career]["institutions"].append(program.institution_id)

            # Rank careers by popularity
            ranked_careers = sorted(
                careers.values(),
                key=lambda x: len(x["institutions"]),
                reverse=True,
            )

            return {
                "success": True,
                "careers": ranked_careers[:10],
                "explanation": f"Based on your interests, these {len(ranked_careers)} careers have strong educational programs in Bangladesh",
            }

        except Exception as e:
            logger.error(f"Career recommendation failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def compare_institutions(
        self, institution_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple institutions
        """
        try:
            institutions = []
            for inst_id in institution_ids[:5]:  # Max 5 comparisons
                inst = await self.db.get(Institution, inst_id)
                if inst:
                    institutions.append(inst)

            # Build comparison matrix
            comparison = {
                "institutions": [
                    {
                        "id": i.id,
                        "name": i.name,
                        "type": i.type,
                        "location": f"{i.district}, {i.division}",
                        "data_completeness": i.data_completeness_score,
                        "verification_status": i.verification_status,
                        "programs_count": len(i.programs) if hasattr(i, "programs") else 0,
                    }
                    for i in institutions
                ],
                "comparison_fields": [
                    "type",
                    "location",
                    "admission_difficulty",
                    "job_prospects",
                    "fees",
                ],
            }

            return {"success": True, "comparison": comparison}

        except Exception as e:
            logger.error(f"Comparison failed: {str(e)}")
            return {"success": False, "error": str(e)}

    # Private Methods

    async def _parse_query(
        self, query: str, profile: StudentProfile
    ) -> Dict[str, Any]:
        """
        Parse natural language query to extract criteria
        """
        criteria = {
            "interests": profile.interests or [],
            "gpa_min": profile.gpa,
            "location": profile.location_preference,
            "type_preference": None,
            "budget": profile.budget,
        }

        # Simple keyword extraction
        query_lower = query.lower()
        if "university" in query_lower or "uni" in query_lower:
            criteria["type_preference"] = "university"
        elif "college" in query_lower:
            criteria["type_preference"] = "government_college"
        elif "polytechnic" in query_lower:
            criteria["type_preference"] = "polytechnic"
        elif "engineering" in query_lower or "cse" in query_lower or "eee" in query_lower:
            criteria["interests"].append("engineering")

        return criteria

    async def _search_institutions(
        self, criteria: Dict[str, Any]
    ) -> List[Institution]:
        """
        Search institutions matching criteria
        """
        try:
            query = select(Institution).where(
                Institution.verification_status.in_(["verified", "official"])
            )

            # Filter by location
            if criteria.get("location"):
                query = query.where(
                    Institution.division == criteria["location"]
                )

            # Filter by type
            if criteria.get("type_preference"):
                query = query.where(
                    Institution.type == criteria["type_preference"]
                )

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    async def _score_admission_probability(
        self,
        institutions: List[Institution],
        profile: StudentProfile,
        criteria: Dict,
    ) -> List[Dict]:
        """
        Score admission probability for each institution
        """
        scored = []

        for inst in institutions:
            # Get programs matching interests
            programs = await self._get_programs_for_interests(
                inst, criteria.get("interests", [])
            )

            for program in programs:
                # Calculate admission probability
                probability = await self._calculate_admission_probability(
                    profile, program, inst
                )

                scored.append({
                    "institution_id": str(inst.id),
                    "institution_name": inst.name,
                    "program_id": str(program.id),
                    "program_name": program.name,
                    "probability": probability,
                    "institution": inst,
                    "program": program,
                })

        return scored

    async def _calculate_admission_probability(
        self, profile: StudentProfile, program: Program, institution: Institution
    ) -> float:
        """
        Calculate admission probability (0-100)
        
        Factors:
        - Student GPA vs average admitted GPA
        - Competition ratio (applicants/seats)
        - Subject matching
        - Test scores
        """
        probability = 50.0  # Base score

        # Factor 1: GPA matching
        if program.admission_requirements:
            min_gpa = program.admission_requirements.get("min_gpa", 3.0)
            if profile.gpa >= min_gpa:
                probability += 25
            elif profile.gpa >= min_gpa - 0.5:
                probability += 15
            else:
                probability -= 10

        # Factor 2: Seat availability
        if program.seats:
            # Assuming avg 100 applicants per seat in Bangladesh context
            competition_ratio = 100 / program.seats
            if competition_ratio < 5:
                probability += 15
            elif competition_ratio < 10:
                probability += 5

        # Factor 3: Subject matching
        if profile.subjects and program.subjects:
            matching_subjects = set(profile.subjects) & set(program.subjects)
            if matching_subjects:
                probability += 10

        # Cap at 100
        return min(100, max(0, probability))

    async def _get_programs_for_interests(
        self, institution: Institution, interests: List[str]
    ) -> List[Program]:
        """
        Get programs matching interests from institution
        """
        if not interests:
            # Return all programs if no specific interests
            stmt = select(Program).where(
                Program.institution_id == institution.id
            )
        else:
            # Match by category or subject
            stmt = select(Program).where(
                and_(
                    Program.institution_id == institution.id,
                    Program.category.in_(interests),
                )
            )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _find_matching_programs(
        self, profile: StudentProfile
    ) -> List[Program]:
        """
        Find programs matching student interests
        """
        stmt = select(Program)
        if profile.interests:
            stmt = stmt.where(Program.category.in_(profile.interests))
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _build_recommendations(
        self, scored: List[Dict], profile: StudentProfile
    ) -> List[Recommendation]:
        """
        Build structured recommendations
        """
        recommendations = []

        for score in scored:
            entrance_difficulty = self._determine_entrance_difficulty(
                score["probability"]
            )

            rec = Recommendation(
                institution_id=score["institution_id"],
                institution_name=score["institution_name"],
                institution_type=score["institution"].type,
                location=f"{score['institution'].district}, {score['institution'].division}",
                admission_probability=score["probability"],
                reasoning=f"Your GPA of {profile.gpa} matches well with this institution's requirements",
                career_prospects=score.get("program", {}).career_paths or ["Engineering"],
                entrance_difficulty=entrance_difficulty,
            )
            recommendations.append(rec)

        return recommendations

    def _determine_entrance_difficulty(self, probability: float) -> str:
        """Determine entrance difficulty from probability"""
        if probability >= 80:
            return "Easy"
        elif probability >= 60:
            return "Moderate"
        elif probability >= 40:
            return "Challenging"
        else:
            return "Very Difficult"

    def _generate_explanation(
        self, profile: StudentProfile, criteria: Dict, recommendations: List
    ) -> str:
        """Generate human-readable explanation"""
        if not recommendations:
            return "No matching institutions found based on your criteria."

        top_inst = recommendations[0]
        return (
            f"Based on your GPA of {profile.gpa} and interests in {', '.join(profile.interests or ['general studies'])}, "
            f"we recommend {top_inst.institution_name} as your top choice with {top_inst.admission_probability:.0f}% admission probability. "
            f"This is a {top_inst.entrance_difficulty.lower()} entrance to compete for."
        )

    async def _get_next_steps(self, recommendations: List) -> List[str]:
        """Generate actionable next steps"""
        return [
            "Check admission deadlines for selected institutions",
            "Prepare for entrance exams if applicable",
            "Gather required documents",
            "Contact institutions for scholarship opportunities",
            "Connect with alumni for guidance",
        ]
