"""Settings domain services - Configuration, versions, and parameters."""

from app.services.settings.class_size_service import ClassSizeService
from app.services.settings.configuration_service import ConfigurationService
from app.services.settings.fee_structure_service import FeeStructureService
from app.services.settings.reference_data_service import ReferenceDataService
from app.services.settings.subject_hours_service import SubjectHoursService
from app.services.settings.timetable_constraints_service import (
    TimetableConstraintsService,
)
from app.services.settings.version_service import VersionService

__all__ = [
    "ClassSizeService",
    "ConfigurationService",
    "FeeStructureService",
    "ReferenceDataService",
    "SubjectHoursService",
    "TimetableConstraintsService",
    "VersionService",
]
