from sqlalchemy import Column, Integer, String, ForeignKey, Table, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

# Association table for Institution <-> EducationBoard
institution_board_association = Table(
    'institution_boards',
    Base.metadata,
    Column('institution_id', Integer, ForeignKey('institutions.id')),
    Column('board_id', Integer, ForeignKey('education_boards.id'))
)

# Association table for Institution <-> UGC
institution_ugc_association = Table(
    'institution_ugc',
    Base.metadata,
    Column('institution_id', Integer, ForeignKey('institutions.id')),
    Column('ugc_id', Integer, ForeignKey('university_grant_commissions.id'))
)


class EducationBoard(Base):
    """Bangladesh Education Boards (e.g., Dhaka Board, Chittagong Board)."""
    __tablename__ = "education_boards"
    
    id = Column(Integer, primary_key=True, index=True)
    name_en = Column(String(200), nullable=False, unique=True)
    name_bn = Column(String(200), nullable=True)
    short_code = Column(String(20), unique=True)  # e.g., "dhaka", "ctg"
    board_type = Column(String(50))  # "general", "madrasa", "technical"
    website = Column(String(255), nullable=True)
    
    # Relationships
    affiliated_institutions = relationship(
        "Institution",
        secondary=institution_board_association,
        back_populates="education_boards"
    )
    
    __table_args__ = (
        Index('idx_board_name', 'name_en'),
        Index('idx_board_type', 'board_type'),
    )
    
    def __repr__(self) -> str:
        return f"<EducationBoard {self.name_en}>"


class UniversityGrantCommission(Base):
    """UGC and other higher education authorities."""
    __tablename__ = "university_grant_commissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name_en = Column(String(200), nullable=False)
    name_bn = Column(String(200), nullable=True)
    short_code = Column(String(20), unique=True)  # e.g., "ugc_bd"
    commission_type = Column(String(50))  # "ugc", "medical", "engineering"
    website = Column(String(255), nullable=True)
    
    # Relationships
    affiliated_institutions = relationship(
        "Institution",
        secondary=institution_ugc_association,
        back_populates="ugc_affiliations"
    )
    
    __table_args__ = (
        Index('idx_ugc_name', 'name_en'),
        Index('idx_ugc_type', 'commission_type'),
    )
    
    def __repr__(self) -> str:
        return f"<UGC {self.name_en}>"


class Affiliation(Base):
    """Direct affiliations (e.g., college affiliated with a university)."""
    __tablename__ = "affiliations"
    
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    parent_institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    affiliation_type = Column(String(50), nullable=False)  # "college", "department", "campus"
    status = Column(String(20), default="active")  # active, inactive, pending
    
    # Relationships
    institution = relationship("Institution", foreign_keys=[institution_id], back_populates="affiliations")
    parent_institution = relationship("Institution", foreign_keys=[parent_institution_id], back_populates="affiliated_members")
    
    __table_args__ = (
        Index('idx_affiliation_institution', 'institution_id'),
        Index('idx_affiliation_parent', 'parent_institution_id'),
    )
    
    def __repr__(self) -> str:
        return f"<Affiliation {self.affiliation_type}>"
