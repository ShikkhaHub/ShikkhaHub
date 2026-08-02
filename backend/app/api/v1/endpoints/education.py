"""API endpoints for the national education knowledge graph entities.

Read endpoints are public; write endpoints require admin; saved-institution
endpoints require an authenticated user.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_admin_user, get_current_user_optional
from app.models import (
    Accreditation,
    Admission,
    Campus,
    Course,
    FacilityType,
    GalleryImage,
    Institution,
    InstitutionCourse,
    InstitutionFacility,
    InstitutionRanking,
    Notice,
    SavedInstitution,
    Scholarship,
    User,
)
from app.models.institution import (
    INSTITUTION_OWNERSHIPS,
    INSTITUTION_EDUCATION_LEVELS,
    INSTITUTION_STATUSES,
)
from app.schemas.education_graph import (
    AccreditationCreate,
    AccreditationResponse,
    AdmissionCreate,
    AdmissionResponse,
    AdmissionUpdate,
    CampusCreate,
    CampusResponse,
    CampusUpdate,
    FacilityTypeResponse,
    GalleryImageCreate,
    GalleryImageResponse,
    InstitutionCourseCreate,
    InstitutionCourseResponse,
    InstitutionCourseUpdate,
    InstitutionFacilityCreate,
    InstitutionFacilityResponse,
    InstitutionRankingCreate,
    InstitutionRankingResponse,
    NoticeCreate,
    NoticeResponse,
    NoticeUpdate,
    SavedInstitutionCreate,
    SavedInstitutionResponse,
    ScholarshipCreate,
    ScholarshipResponse,
    ScholarshipUpdate,
)

router = APIRouter()


def _get_institution_or_404(db: Session, institution_id: int) -> Institution:
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    return inst


# ---------------------------------------------------------------------------
# Campuses
# ---------------------------------------------------------------------------


@router.get(
    "/institutions/{institution_id}/campuses", response_model=list[CampusResponse]
)
def list_campuses(institution_id: int, db: Session = Depends(get_db)):
    _get_institution_or_404(db, institution_id)
    return db.query(Campus).filter(Campus.institution_id == institution_id).all()


@router.get("/campuses/{campus_id}", response_model=CampusResponse)
def get_campus(campus_id: int, db: Session = Depends(get_db)):
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise HTTPException(status_code=404, detail="Campus not found")
    return campus


@router.post(
    "/campuses", response_model=CampusResponse, status_code=status.HTTP_201_CREATED
)
def create_campus(
    payload: CampusCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    _get_institution_or_404(db, payload.institution_id)
    campus = Campus(**payload.model_dump())
    db.add(campus)
    db.commit()
    db.refresh(campus)
    return campus


@router.put("/campuses/{campus_id}", response_model=CampusResponse)
def update_campus(
    campus_id: int,
    payload: CampusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise HTTPException(status_code=404, detail="Campus not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(campus, field, value)
    db.commit()
    db.refresh(campus)
    return campus


@router.delete("/campuses/{campus_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campus(
    campus_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if not campus:
        raise HTTPException(status_code=404, detail="Campus not found")
    db.delete(campus)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Facilities
# ---------------------------------------------------------------------------


@router.get("/facilities/types", response_model=list[FacilityTypeResponse])
def list_facility_types(db: Session = Depends(get_db)):
    return (
        db.query(FacilityType)
        .order_by(FacilityType.display_order, FacilityType.name)
        .all()
    )


@router.get(
    "/institutions/{institution_id}/facilities",
    response_model=list[InstitutionFacilityResponse],
)
def list_institution_facilities(institution_id: int, db: Session = Depends(get_db)):
    _get_institution_or_404(db, institution_id)
    return (
        db.query(InstitutionFacility)
        .filter(InstitutionFacility.institution_id == institution_id)
        .all()
    )


@router.post(
    "/institutions/{institution_id}/facilities",
    response_model=InstitutionFacilityResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_institution_facility(
    institution_id: int,
    payload: InstitutionFacilityCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    _get_institution_or_404(db, institution_id)
    if (
        not db.query(FacilityType)
        .filter(FacilityType.id == payload.facility_type_id)
        .first()
    ):
        raise HTTPException(status_code=400, detail="Facility type not found")
    existing = (
        db.query(InstitutionFacility)
        .filter_by(
            institution_id=institution_id, facility_type_id=payload.facility_type_id
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409, detail="Facility already linked to institution"
        )
    facility = InstitutionFacility(
        institution_id=institution_id, **payload.model_dump()
    )
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return facility


@router.delete(
    "/institutions/{institution_id}/facilities/{facility_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_institution_facility(
    institution_id: int,
    facility_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    facility = (
        db.query(InstitutionFacility)
        .filter(
            InstitutionFacility.id == facility_id,
            InstitutionFacility.institution_id == institution_id,
        )
        .first()
    )
    if not facility:
        raise HTTPException(status_code=404, detail="Facility link not found")
    db.delete(facility)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Gallery
# ---------------------------------------------------------------------------


@router.get(
    "/institutions/{institution_id}/gallery", response_model=list[GalleryImageResponse]
)
def list_gallery(institution_id: int, db: Session = Depends(get_db)):
    _get_institution_or_404(db, institution_id)
    return (
        db.query(GalleryImage)
        .filter(GalleryImage.institution_id == institution_id)
        .order_by(GalleryImage.sort_order, GalleryImage.id)
        .all()
    )


@router.post(
    "/institutions/{institution_id}/gallery",
    response_model=GalleryImageResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_gallery_image(
    institution_id: int,
    payload: GalleryImageCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    _get_institution_or_404(db, institution_id)
    image = GalleryImage(institution_id=institution_id, **payload.model_dump())
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


@router.delete("/gallery/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gallery_image(
    image_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    image = db.query(GalleryImage).filter(GalleryImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Gallery image not found")
    db.delete(image)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Rankings
# ---------------------------------------------------------------------------


@router.get(
    "/institutions/{institution_id}/rankings",
    response_model=list[InstitutionRankingResponse],
)
def list_rankings(institution_id: int, db: Session = Depends(get_db)):
    _get_institution_or_404(db, institution_id)
    return (
        db.query(InstitutionRanking)
        .filter(InstitutionRanking.institution_id == institution_id)
        .order_by(InstitutionRanking.year.desc(), InstitutionRanking.rank)
        .all()
    )


@router.post(
    "/institutions/{institution_id}/rankings",
    response_model=InstitutionRankingResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_ranking(
    institution_id: int,
    payload: InstitutionRankingCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    _get_institution_or_404(db, institution_id)
    ranking = InstitutionRanking(institution_id=institution_id, **payload.model_dump())
    db.add(ranking)
    db.commit()
    db.refresh(ranking)
    return ranking


@router.delete("/rankings/{ranking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ranking(
    ranking_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    ranking = (
        db.query(InstitutionRanking).filter(InstitutionRanking.id == ranking_id).first()
    )
    if not ranking:
        raise HTTPException(status_code=404, detail="Ranking not found")
    db.delete(ranking)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Accreditations
# ---------------------------------------------------------------------------


@router.get(
    "/institutions/{institution_id}/accreditations",
    response_model=list[AccreditationResponse],
)
def list_accreditations(institution_id: int, db: Session = Depends(get_db)):
    _get_institution_or_404(db, institution_id)
    return (
        db.query(Accreditation)
        .filter(Accreditation.institution_id == institution_id)
        .all()
    )


@router.post(
    "/institutions/{institution_id}/accreditations",
    response_model=AccreditationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_accreditation(
    institution_id: int,
    payload: AccreditationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    _get_institution_or_404(db, institution_id)
    accreditation = Accreditation(institution_id=institution_id, **payload.model_dump())
    db.add(accreditation)
    db.commit()
    db.refresh(accreditation)
    return accreditation


@router.delete(
    "/accreditations/{accreditation_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_accreditation(
    accreditation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    accreditation = (
        db.query(Accreditation).filter(Accreditation.id == accreditation_id).first()
    )
    if not accreditation:
        raise HTTPException(status_code=404, detail="Accreditation not found")
    db.delete(accreditation)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Admissions
# ---------------------------------------------------------------------------


@router.get(
    "/institutions/{institution_id}/admissions", response_model=list[AdmissionResponse]
)
def list_admissions(
    institution_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    _get_institution_or_404(db, institution_id)
    query = db.query(Admission).filter(Admission.institution_id == institution_id)
    if status_filter:
        query = query.filter(Admission.status == status_filter)
    return query.order_by(Admission.created_at.desc()).all()


@router.get("/admissions/{admission_id}", response_model=AdmissionResponse)
def get_admission(admission_id: int, db: Session = Depends(get_db)):
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")
    return admission


@router.post(
    "/admissions", response_model=AdmissionResponse, status_code=status.HTTP_201_CREATED
)
def create_admission(
    payload: AdmissionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    _get_institution_or_404(db, payload.institution_id)
    admission = Admission(**payload.model_dump())
    db.add(admission)
    db.commit()
    db.refresh(admission)
    return admission


@router.put("/admissions/{admission_id}", response_model=AdmissionResponse)
def update_admission(
    admission_id: int,
    payload: AdmissionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(admission, field, value)
    db.commit()
    db.refresh(admission)
    return admission


@router.delete("/admissions/{admission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admission(
    admission_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")
    db.delete(admission)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Notices
# ---------------------------------------------------------------------------


@router.get(
    "/institutions/{institution_id}/notices", response_model=list[NoticeResponse]
)
def list_notices(institution_id: int, db: Session = Depends(get_db)):
    _get_institution_or_404(db, institution_id)
    return (
        db.query(Notice)
        .filter(Notice.institution_id == institution_id)
        .order_by(Notice.is_important.desc(), Notice.created_at.desc())
        .all()
    )


@router.post(
    "/notices", response_model=NoticeResponse, status_code=status.HTTP_201_CREATED
)
def create_notice(
    payload: NoticeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    _get_institution_or_404(db, payload.institution_id)
    notice = Notice(**payload.model_dump())
    db.add(notice)
    db.commit()
    db.refresh(notice)
    return notice


@router.put("/notices/{notice_id}", response_model=NoticeResponse)
def update_notice(
    notice_id: int,
    payload: NoticeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(notice, field, value)
    db.commit()
    db.refresh(notice)
    return notice


@router.delete("/notices/{notice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    db.delete(notice)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Scholarships
# ---------------------------------------------------------------------------


@router.get(
    "/institutions/{institution_id}/scholarships",
    response_model=list[ScholarshipResponse],
)
def list_scholarships(institution_id: int, db: Session = Depends(get_db)):
    _get_institution_or_404(db, institution_id)
    return (
        db.query(Scholarship)
        .filter(Scholarship.institution_id == institution_id)
        .order_by(Scholarship.created_at.desc())
        .all()
    )


@router.post(
    "/scholarships",
    response_model=ScholarshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_scholarship(
    payload: ScholarshipCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    _get_institution_or_404(db, payload.institution_id)
    scholarship = Scholarship(**payload.model_dump())
    db.add(scholarship)
    db.commit()
    db.refresh(scholarship)
    return scholarship


@router.put("/scholarships/{scholarship_id}", response_model=ScholarshipResponse)
def update_scholarship(
    scholarship_id: int,
    payload: ScholarshipUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
    if not scholarship:
        raise HTTPException(status_code=404, detail="Scholarship not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(scholarship, field, value)
    db.commit()
    db.refresh(scholarship)
    return scholarship


@router.delete("/scholarships/{scholarship_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scholarship(
    scholarship_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
    if not scholarship:
        raise HTTPException(status_code=404, detail="Scholarship not found")
    db.delete(scholarship)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Course offerings (institution_courses)
# ---------------------------------------------------------------------------


@router.get(
    "/institutions/{institution_id}/courses",
    response_model=list[InstitutionCourseResponse],
)
def list_institution_courses(institution_id: int, db: Session = Depends(get_db)):
    _get_institution_or_404(db, institution_id)
    offerings = (
        db.query(InstitutionCourse)
        .filter(InstitutionCourse.institution_id == institution_id)
        .order_by(InstitutionCourse.status, InstitutionCourse.id)
        .all()
    )
    results = []
    for offering in offerings:
        data = {
            **{
                c.name: getattr(offering, c.name)
                for c in InstitutionCourse.__table__.columns
            }
        }
        data["course_name"] = offering.course.name_en if offering.course else None
        results.append(InstitutionCourseResponse(**data))
    return results


@router.post(
    "/institutions/{institution_id}/courses",
    response_model=InstitutionCourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_institution_course(
    institution_id: int,
    payload: InstitutionCourseCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    _get_institution_or_404(db, institution_id)
    if not db.query(Course).filter(Course.id == payload.course_id).first():
        raise HTTPException(status_code=400, detail="Course not found")
    existing = (
        db.query(InstitutionCourse)
        .filter_by(institution_id=institution_id, course_id=payload.course_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409, detail="Course already offered by institution"
        )
    offering = InstitutionCourse(institution_id=institution_id, **payload.model_dump())
    db.add(offering)
    db.commit()
    db.refresh(offering)
    data = {
        **{
            c.name: getattr(offering, c.name)
            for c in InstitutionCourse.__table__.columns
        }
    }
    data["course_name"] = offering.course.name_en if offering.course else None
    return InstitutionCourseResponse(**data)


@router.put(
    "/institution-courses/{offering_id}", response_model=InstitutionCourseResponse
)
def update_institution_course(
    offering_id: int,
    payload: InstitutionCourseUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    offering = (
        db.query(InstitutionCourse).filter(InstitutionCourse.id == offering_id).first()
    )
    if not offering:
        raise HTTPException(status_code=404, detail="Course offering not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(offering, field, value)
    db.commit()
    db.refresh(offering)
    data = {
        **{
            c.name: getattr(offering, c.name)
            for c in InstitutionCourse.__table__.columns
        }
    }
    data["course_name"] = offering.course.name_en if offering.course else None
    return InstitutionCourseResponse(**data)


@router.delete(
    "/institution-courses/{offering_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_institution_course(
    offering_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    offering = (
        db.query(InstitutionCourse).filter(InstitutionCourse.id == offering_id).first()
    )
    if not offering:
        raise HTTPException(status_code=404, detail="Course offering not found")
    db.delete(offering)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Saved institutions (authenticated users)
# ---------------------------------------------------------------------------


@router.get("/me/saved", response_model=list[SavedInstitutionResponse])
def list_saved_institutions(
    user: User = Depends(get_current_user_optional), db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    saved = (
        db.query(SavedInstitution)
        .filter(SavedInstitution.user_id == user.id)
        .order_by(SavedInstitution.created_at.desc())
        .all()
    )
    results = []
    for item in saved:
        data = {
            **{
                c.name: getattr(item, c.name)
                for c in SavedInstitution.__table__.columns
            }
        }
        if item.institution:
            data["institution_name"] = item.institution.name_en
            data["institution_slug"] = item.institution.slug
        results.append(SavedInstitutionResponse(**data))
    return results


@router.get("/me/saved/{institution_id}", response_model=SavedInstitutionResponse)
def get_saved_institution(
    institution_id: int,
    user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    item = (
        db.query(SavedInstitution)
        .filter(
            SavedInstitution.user_id == user.id,
            SavedInstitution.institution_id == institution_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Institution not saved")
    data = {
        **{c.name: getattr(item, c.name) for c in SavedInstitution.__table__.columns}
    }
    if item.institution:
        data["institution_name"] = item.institution.name_en
        data["institution_slug"] = item.institution.slug
    return SavedInstitutionResponse(**data)


@router.post(
    "/me/saved/{institution_id}",
    response_model=SavedInstitutionResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_institution(
    institution_id: int,
    payload: SavedInstitutionCreate,
    user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    _get_institution_or_404(db, institution_id)
    existing = (
        db.query(SavedInstitution)
        .filter(
            SavedInstitution.user_id == user.id,
            SavedInstitution.institution_id == institution_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Institution already saved")
    item = SavedInstitution(
        user_id=user.id, institution_id=institution_id, note=payload.note
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    data = {
        **{c.name: getattr(item, c.name) for c in SavedInstitution.__table__.columns}
    }
    data["institution_name"] = item.institution.name_en if item.institution else None
    data["institution_slug"] = item.institution.slug if item.institution else None
    return SavedInstitutionResponse(**data)


@router.delete("/me/saved/{institution_id}", status_code=status.HTTP_204_NO_CONTENT)
def unsave_institution(
    institution_id: int,
    user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    item = (
        db.query(SavedInstitution)
        .filter(
            SavedInstitution.user_id == user.id,
            SavedInstitution.institution_id == institution_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Institution not saved")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Graph metadata & taxonomy
# ---------------------------------------------------------------------------


@router.get("/meta/institution-types")
def institution_metadata():
    """Public metadata about the normalized institution taxonomy."""
    return {
        "ownerships": list(INSTITUTION_OWNERSHIPS),
        "education_levels": list(INSTITUTION_EDUCATION_LEVELS),
        "statuses": list(INSTITUTION_STATUSES),
        "verification_levels": list(range(4)),
    }
