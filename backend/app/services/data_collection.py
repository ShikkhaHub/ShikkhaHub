"""
Data Collection Service
Handles multi-source institution data collection with verification
Priority: Official > Verified > Community
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import httpx
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.institution import Institution, DataSource
from app.models.verification import InstitutionVerification, Authority

logger = logging.getLogger(__name__)


class SourceType(str, Enum):
    OFFICIAL_WEBSITE = "official_website"
    UGC_DIRECTORY = "ugc_directory"
    BOARD_PORTAL = "board_portal"
    MANUAL_ENTRY = "manual_entry"
    WEB_SCRAPE = "web_scrape"
    ALUMNI_REPORT = "alumni_report"
    API = "api"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    OFFICIAL = "official"


class InstitutionDataCollector:
    """Multi-source institution data collection pipeline"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.client = httpx.AsyncClient(timeout=30.0)

    async def collect_all(self) -> Dict[str, Any]:
        """Execute full data collection cycle"""
        results = {
            "ugc_collected": 0,
            "boards_collected": 0,
            "websites_scraped": 0,
            "total_processed": 0,
            "errors": [],
        }

        try:
            # Tier 1: Official sources
            logger.info("Starting Tier 1: Official sources collection")
            results["ugc_collected"] = await self.collect_from_ugc()
            results["boards_collected"] = await self.collect_from_boards()

            # Tier 2: Web scraping
            logger.info("Starting Tier 2: Web scraping")
            results["websites_scraped"] = await self.collect_from_websites()

            # Merge and verify
            logger.info("Merging and verifying data")
            results["total_processed"] = await self.merge_and_verify()

            logger.info(f"Collection cycle complete: {results}")
            return results

        except Exception as e:
            logger.error(f"Collection error: {str(e)}")
            results["errors"].append(str(e))
            return results

    async def collect_from_ugc(self) -> int:
        """
        Collect from UGC (University Grants Commission) API
        Trust score: 0.95+
        """
        try:
            # Get UGC authority config
            ugc_auth = await self._get_authority("UGC")
            if not ugc_auth:
                logger.warning("UGC authority not configured")
                return 0

            # Fetch universities from UGC API
            universities = await self._fetch_ugc_universities(ugc_auth)

            collected = 0
            for uni_data in universities:
                institution = await self._create_or_update_institution(
                    data=uni_data,
                    source_type=SourceType.UGC_DIRECTORY,
                    verification_status=VerificationStatus.OFFICIAL,
                    confidence_score=0.95,
                )
                if institution:
                    collected += 1

            logger.info(f"Collected {collected} universities from UGC")
            return collected

        except Exception as e:
            logger.error(f"UGC collection failed: {str(e)}")
            return 0

    async def collect_from_boards(self) -> int:
        """
        Collect from government education boards
        Trust score: 0.9+
        Boards: Dhaka, Chittagong, Rajshahi, Khulna, Barisal, Sylhet, Mymensingh
        """
        try:
            boards = [
                "Dhaka Education Board",
                "Chittagong Education Board",
                "Rajshahi Education Board",
                "Khulna Education Board",
                "Barisal Education Board",
                "Sylhet Education Board",
                "Mymensingh Education Board",
            ]

            collected = 0
            for board_name in boards:
                board_auth = await self._get_authority(board_name)
                if not board_auth:
                    continue

                colleges = await self._fetch_board_colleges(board_auth)
                for college_data in colleges:
                    institution = await self._create_or_update_institution(
                        data=college_data,
                        source_type=SourceType.BOARD_PORTAL,
                        verification_status=VerificationStatus.OFFICIAL,
                        confidence_score=0.90,
                    )
                    if institution:
                        collected += 1

            logger.info(f"Collected {collected} colleges from boards")
            return collected

        except Exception as e:
            logger.error(f"Board collection failed: {str(e)}")
            return 0

    async def collect_from_websites(self) -> int:
        """
        Web scraping institution websites
        Trust score: 0.7-0.8
        Only for institutions with confidence_score < 0.85
        """
        try:
            # Get institutions needing data
            stmt = select(Institution).where(
                Institution.data_completeness_score < 85
            )
            result = await self.db.execute(stmt)
            institutions = result.scalars().all()

            scraped = 0
            for institution in institutions[:500]:  # Rate limit
                data = await self._scrape_institution_website(institution)
                if data:
                    await self._merge_data(
                        institution,
                        data,
                        source_type=SourceType.WEB_SCRAPE,
                        confidence_score=0.75,
                    )
                    scraped += 1

            logger.info(f"Scraped {scraped} institution websites")
            return scraped

        except Exception as e:
            logger.error(f"Website scraping failed: {str(e)}")
            return 0

    async def collect_from_alumni(
        self, institution_id: str, data: Dict[str, Any]
    ) -> bool:
        """
        Accept alumni verification reports
        Trust score: 0.6 per report, 0.8+ with 5+ reports
        """
        try:
            # Create verification record
            verification = InstitutionVerification(
                institution_id=institution_id,
                verification_type="alumni_verified",
                verified_by="alumni_report",
                fields_verified=data.get("fields_verified", {}),
                notes=data.get("notes", ""),
            )
            self.db.add(verification)

            # Update institution confidence if 5+ reports
            stmt = select(InstitutionVerification).where(
                InstitutionVerification.institution_id == institution_id,
                InstitutionVerification.verification_type == "alumni_verified",
            )
            result = await self.db.execute(stmt)
            alumni_reports = result.scalars().all()

            if len(alumni_reports) >= 5:
                institution = await self.db.get(Institution, institution_id)
                if institution:
                    institution.verification_status = VerificationStatus.VERIFIED
                    institution.last_verified = datetime.utcnow()

            await self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Alumni collection failed: {str(e)}")
            await self.db.rollback()
            return False

    async def merge_and_verify(self) -> int:
        """
        Merge data from multiple sources
        Priority: Official > Multiple Verified > Single Source
        """
        try:
            processed = 0

            # Get all institutions with multiple sources
            stmt = select(Institution).order_by(Institution.updated_at.desc())
            result = await self.db.execute(stmt)
            institutions = result.scalars().all()

            for institution in institutions:
                # Get all data sources
                sources_stmt = select(DataSource).where(
                    DataSource.institution_id == institution.id
                )
                sources_result = await self.db.execute(sources_stmt)
                sources = sources_result.scalars().all()

                if len(sources) > 1:
                    # Merge conflicting data
                    merged_data = await self._merge_sources(sources)
                    institution.data_completeness_score = (
                        self._calculate_completeness(merged_data)
                    )

                    # Auto-verify if multiple official sources
                    official_sources = [
                        s for s in sources if s.source_type in [
                            SourceType.UGC_DIRECTORY,
                            SourceType.BOARD_PORTAL,
                        ]
                    ]
                    if len(official_sources) >= 1:
                        institution.verification_status = VerificationStatus.OFFICIAL

                processed += 1

            await self.db.commit()
            logger.info(f"Processed {processed} institutions for merge/verify")
            return processed

        except Exception as e:
            logger.error(f"Merge/verify failed: {str(e)}")
            await self.db.rollback()
            return 0

    # Helper Methods

    async def _get_authority(self, authority_name: str) -> Optional[Authority]:
        """Get authority config from database"""
        stmt = select(Authority).where(Authority.name == authority_name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _fetch_ugc_universities(self, auth: Authority) -> List[Dict]:
        """Fetch from UGC API"""
        # Implementation would call actual UGC API
        # For now, return empty list
        return []

    async def _fetch_board_colleges(self, auth: Authority) -> List[Dict]:
        """Fetch from Board portal"""
        # Implementation would scrape/call board portal
        return []

    async def _scrape_institution_website(
        self, institution: Institution
    ) -> Optional[Dict]:
        """Scrape institution website for data"""
        if not institution.website_url:
            return None

        try:
            response = await self.client.get(
                institution.website_url, follow_redirects=True, timeout=10.0
            )
            # Parse and extract data (simplified)
            return {"scraped": True, "url": institution.website_url}
        except Exception as e:
            logger.error(f"Scrape failed for {institution.name}: {str(e)}")
            return None

    async def _create_or_update_institution(
        self,
        data: Dict[str, Any],
        source_type: SourceType,
        verification_status: VerificationStatus,
        confidence_score: float,
    ) -> Optional[Institution]:
        """Create or update institution record"""
        try:
            # Check if exists
            stmt = select(Institution).where(
                Institution.name == data.get("name")
            )
            result = await self.db.execute(stmt)
            institution = result.scalar_one_or_none()

            if not institution:
                institution = Institution(
                    name=data.get("name"),
                    type=data.get("type"),
                    division=data.get("division"),
                    district=data.get("district"),
                    verification_status=verification_status,
                )
                self.db.add(institution)

            # Create data source record
            source = DataSource(
                institution_id=institution.id,
                source_type=source_type,
                source_url=data.get("source_url"),
                confidence_score=confidence_score,
                collection_date=datetime.utcnow(),
            )
            self.db.add(source)

            await self.db.commit()
            return institution

        except Exception as e:
            logger.error(f"Create/update failed: {str(e)}")
            await self.db.rollback()
            return None

    async def _merge_sources(self, sources: List[DataSource]) -> Dict:
        """Merge data from multiple sources"""
        # Priority: Official > Verified > Web scrape
        merged = {}
        for source in sorted(
            sources, key=lambda s: s.confidence_score, reverse=True
        ):
            merged.update(source.data_collected or {})
        return merged

    def _calculate_completeness(self, data: Dict) -> int:
        """Calculate data completeness score (0-100)"""
        required_fields = [
            "name",
            "type",
            "division",
            "district",
            "phone_numbers",
            "website_url",
        ]
        present = sum(1 for f in required_fields if data.get(f))
        return int((present / len(required_fields)) * 100)

    async def _merge_data(
        self,
        institution: Institution,
        new_data: Dict,
        source_type: SourceType,
        confidence_score: float,
    ):
        """Merge new data into existing institution"""
        source = DataSource(
            institution_id=institution.id,
            source_type=source_type,
            data_collected=new_data,
            confidence_score=confidence_score,
            collection_date=datetime.utcnow(),
        )
        self.db.add(source)
        await self.db.commit()
