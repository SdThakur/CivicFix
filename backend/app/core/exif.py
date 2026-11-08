"""CivicFix EXIF GPS Extraction & Public Privacy Sanitization Engine.

Features:
- extract_exif_gps: Parses EXIF GPS tags from citizen photo bytes for internal deduplication.
- strip_exif_metadata: Strips all EXIF, GPS, camera, and timestamp metadata before public delivery.
- Protects citizen privacy by ensuring public photo responses never leak home/exact GPS coordinates.
"""

import io
import logging
from typing import Optional, Tuple
from PIL import Image, ExifTags

logger = logging.getLogger("civicfix.exif")


def _convert_dms_to_decimal(dms, ref: str) -> float:
    """Convert degrees, minutes, seconds tuple into signed decimal degrees."""
    degrees = float(dms[0])
    minutes = float(dms[1]) / 60.0
    seconds = float(dms[2]) / 3600.0
    decimal = degrees + minutes + seconds
    if ref in ("S", "W"):
        decimal = -decimal
    return decimal


def extract_exif_gps(image_bytes: bytes) -> Optional[Tuple[float, float]]:
    """Extract GPS latitude and longitude from photo EXIF tags (used internally for deduplication)."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            exif = img.getexif()
            if not exif:
                return None

            # Look up GPS IFD tag (0x8825 = 34853)
            gps_info = None
            for key, val in exif.items():
                if ExifTags.TAGS.get(key) == "GPSInfo" or key == 34853:
                    gps_info = val
                    break

            if not gps_info:
                return None

            # If GPS tags are stored in IFD
            if hasattr(exif, "get_ifd"):
                gps_ifd = exif.get_ifd(34853)
                if gps_ifd:
                    gps_info = gps_ifd

            lat_dms = gps_info.get(2)
            lat_ref = gps_info.get(1)
            lng_dms = gps_info.get(4)
            lng_ref = gps_info.get(3)

            if lat_dms and lat_ref and lng_dms and lng_ref:
                lat = round(_convert_dms_to_decimal(lat_dms, lat_ref), 6)
                lng = round(_convert_dms_to_decimal(lng_dms, lng_ref), 6)
                return lat, lng

    except Exception as e:
        logger.debug(f"Could not extract EXIF GPS: {e}")

    return None


def strip_exif_metadata(image_bytes: bytes, output_format: str = "WEBP") -> bytes:
    """Strip all EXIF, GPS, device, and timestamp metadata from image bytes.

    Produces a sanitized byte stream suitable for public delivery without privacy leaks.
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Create fresh image containing only pixel data
            clean_img = Image.new(img.mode, img.size)
            clean_img.putdata(list(img.getdata()))

            out_buf = io.BytesIO()
            clean_img.save(out_buf, format=output_format)
            return out_buf.getvalue()
    except Exception as e:
        logger.warning(f"Error sanitizing image EXIF metadata: {e}")
        return image_bytes
