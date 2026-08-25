// Mirrors backend/app/schemas/common_signs.py

import { HandLandmarkPoint } from './practice';

export interface SupportedSigns {
  signs: string[];
}

export interface CommonSignResult {
  // False when no hand was found at all — distinct from a hand being
  // present but not matching a supported sign (sign=null, detected_hand=true).
  detected_hand: boolean;
  sign: string | null;
  landmarks: HandLandmarkPoint[] | null;
}
