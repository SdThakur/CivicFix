"""Location model definition with GeoAlchemy2 PostGIS support."""

from typing import TYPE_CHECKING, List, Optional
from geoalchemy2 import Geometry
from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.report import Report
    from app.models.issue import Issue


class Location(Base, UUIDMixin, TimestampMixin):
    """Location database model for geospatial tracking using PostGIS."""

    __tablename__ = "locations"

    address: Mapped[Optional[str]] = mapped_column(String(550), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    formatted_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)

    # PostGIS Spatial Geometry Column (Point geometry in WGS84 - EPSG:4326)
    location = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    # Relationships
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="location")
    issues: Mapped[List["Issue"]] = relationship("Issue", back_populates="location")
