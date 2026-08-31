from typing import Optional

from pydantic import BaseModel

from app.schemas.practice import HandLandmarkPoint


class SupportedSignsResponse(BaseModel):
    signs: list[str]


class CommonSignResponse(BaseModel):
    # False when no hand was found in frame at all — distinct from a hand
    # being present but not matching a supported sign (sign=None, detected_hand=True)
    detected_hand: bool
    # Null when no hand was found, OR when a hand was found but didn't
    # match any of the supported static handshapes — never a guess.
    sign: Optional[str] = None
    landmarks: Optional[list[HandLandmarkPoint]] = None
