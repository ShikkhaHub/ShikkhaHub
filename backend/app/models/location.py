from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class Division(Base):
    """Bangladesh Divisions (8 total)."""

    __tablename__ = "divisions"

    id = Column(Integer, primary_key=True, index=True)
    name_en = Column(String(100), nullable=False, unique=True)
    name_bn = Column(String(100), nullable=True)
    code = Column(String(10), unique=True)  # ISO code or custom

    # Relationships
    districts = relationship("District", back_populates="division", lazy="dynamic")
    institutions = relationship("Institution", back_populates="division")

    __table_args__ = (Index("idx_division_name", "name_en"),)

    def __repr__(self) -> str:
        return f"<Division {self.name_en}>"


class District(Base):
    """Bangladesh Districts (64 total)."""

    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    name_en = Column(String(100), nullable=False)
    name_bn = Column(String(100), nullable=True)
    code = Column(String(10), unique=True)
    division_id = Column(Integer, ForeignKey("divisions.id"), nullable=False)

    # Relationships
    division = relationship("Division", back_populates="districts")
    upazilas = relationship("Upazila", back_populates="district", lazy="dynamic")
    institutions = relationship("Institution", back_populates="district")

    __table_args__ = (
        Index("idx_district_name", "name_en"),
        Index("idx_district_division", "division_id"),
    )

    def __repr__(self) -> str:
        return f"<District {self.name_en}>"


class Upazila(Base):
    """Bangladesh Upazilas/Thanas (495 total)."""

    __tablename__ = "upazilas"

    id = Column(Integer, primary_key=True, index=True)
    name_en = Column(String(100), nullable=False)
    name_bn = Column(String(100), nullable=True)
    code = Column(String(10), unique=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)

    # Relationships
    district = relationship("District", back_populates="upazilas")
    institutions = relationship("Institution", back_populates="upazila", lazy="dynamic")

    __table_args__ = (
        Index("idx_upazila_name", "name_en"),
        Index("idx_upazila_district", "district_id"),
    )

    def __repr__(self) -> str:
        return f"<Upazila {self.name_en}>"
