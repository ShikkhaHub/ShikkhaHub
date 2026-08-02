from app.models.location import Division, District, Upazila
from app.models.institution import (
    Institution,
    InstitutionType,
    InstitutionContact,
    InstitutionRequirement,
)
from app.models.course import Course, CourseType
from app.models.subject import Subject
from app.models.affiliation import (
    Affiliation,
    EducationBoard,
    UniversityGrantCommission,
)
from app.models.analytics import (
    SearchEvent,
    PageView,
    ClickEvent,
    PopularSearch,
    NoResultSearch,
    DailyAnalytics,
)
from app.models.student_analytics import (
    StudentProfile,
    AnalyticsEvent,
    StudySession,
    ConsentRecord,
)
from app.models.user import User, UserRole
from app.models.review import InstitutionReview, ReviewHelpfulVote, ReviewReport
from app.models.qa import Question, Answer, QuestionVote, AnswerVote
from app.models.comment import Comment, CommentLike
from app.models.chat import ChatSession, ChatMessage
from app.models.institution_detail import (
    Campus,
    FacilityType,
    InstitutionFacility,
    GalleryImage,
    InstitutionRanking,
    Accreditation,
)
from app.models.announcement import Admission, Notice, Scholarship
from app.models.education_graph import InstitutionCourse, SavedInstitution

__all__ = [
    "Division",
    "District",
    "Upazila",
    "Institution",
    "InstitutionType",
    "InstitutionContact",
    "InstitutionRequirement",
    "Course",
    "CourseType",
    "Subject",
    "Affiliation",
    "EducationBoard",
    "UniversityGrantCommission",
    "SearchEvent",
    "PageView",
    "ClickEvent",
    "PopularSearch",
    "NoResultSearch",
    "DailyAnalytics",
    "StudentProfile",
    "AnalyticsEvent",
    "StudySession",
    "ConsentRecord",
    "User",
    "UserRole",
    "InstitutionReview",
    "ReviewHelpfulVote",
    "ReviewReport",
    "Question",
    "Answer",
    "QuestionVote",
    "AnswerVote",
    "Comment",
    "CommentLike",
    "ChatSession",
    "ChatMessage",
    "Campus",
    "FacilityType",
    "InstitutionFacility",
    "GalleryImage",
    "InstitutionRanking",
    "Accreditation",
    "Admission",
    "Notice",
    "Scholarship",
    "InstitutionCourse",
    "SavedInstitution",
]
