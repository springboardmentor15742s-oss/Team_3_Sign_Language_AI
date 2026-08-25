import React, { useState } from 'react';
import { HandLandmarkPoint } from '../types/practice';

// MediaPipe's standard 21-point hand skeleton (wrist=0, then each finger's
// joints out to the tip), as [from, to] index pairs.
const HAND_CONNECTIONS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4], // thumb
  [0, 5], [5, 6], [6, 7], [7, 8], // index
  [5, 9], [9, 10], [10, 11], [11, 12], // middle
  [9, 13], [13, 14], [14, 15], [15, 16], // ring
  [13, 17], [17, 18], [18, 19], [19, 20], // pinky
  [0, 17], // palm base
];

// Padding around the raw landmark bounding box, as a fraction of the box's
// own width/height (with a floor so a tightly-bunched hand still gets some
// breathing room rather than an almost-zero-size crop).
const CROP_PADDING_FRACTION = 0.2;
const CROP_PADDING_FLOOR = 0.04;

// Landmarks are normalized 0-1 against the captured (unmirrored) frame. The
// image is cropped to a padded box around them and the SVG viewBox is
// shifted to match, so the skeleton stays aligned without separate pixel
// math for the dots/lines. Cropping itself needs the image's real pixel
// dimensions (read once on load) so the crop isn't stretched relative to
// the source frame's actual aspect ratio; until that's known — or if the
// landmark box is degenerate — this renders the full, uncropped frame.
//
// Shared by Practice.tsx (alphabet classifier results) and
// CommonSigns.tsx (rule-based common-signs results) — same overlay logic,
// only the source of `landmarks` differs.
export function HandLandmarkOverlay({
  imageUrl,
  landmarks,
  variant,
}: {
  imageUrl: string;
  landmarks: HandLandmarkPoint[];
  variant: 'pass' | 'fail';
}) {
  const [naturalSize, setNaturalSize] = useState<{ width: number; height: number } | null>(null);

  const xs = landmarks.map((point) => point.x);
  const ys = landmarks.map((point) => point.y);
  const rawMinX = Math.min(...xs);
  const rawMaxX = Math.max(...xs);
  const rawMinY = Math.min(...ys);
  const rawMaxY = Math.max(...ys);

  const padX = Math.max((rawMaxX - rawMinX) * CROP_PADDING_FRACTION, CROP_PADDING_FLOOR);
  const padY = Math.max((rawMaxY - rawMinY) * CROP_PADDING_FRACTION, CROP_PADDING_FLOOR);

  const minX = Math.max(0, rawMinX - padX);
  const maxX = Math.min(1, rawMaxX + padX);
  const minY = Math.max(0, rawMinY - padY);
  const maxY = Math.min(1, rawMaxY + padY);
  const cropWidth = maxX - minX;
  const cropHeight = maxY - minY;

  let wrapperStyle: React.CSSProperties | undefined;
  let imageStyle: React.CSSProperties | undefined;
  let viewBox = '0 0 1 1';

  if (naturalSize && cropWidth > 0 && cropHeight > 0) {
    wrapperStyle = { aspectRatio: `${cropWidth * naturalSize.width} / ${cropHeight * naturalSize.height}` };
    imageStyle = {
      position: 'absolute',
      maxWidth: 'none',
      width: `${(100 / cropWidth).toFixed(4)}%`,
      height: `${(100 / cropHeight).toFixed(4)}%`,
      left: `${(-(minX / cropWidth) * 100).toFixed(4)}%`,
      top: `${(-(minY / cropHeight) * 100).toFixed(4)}%`,
    };
    viewBox = `${minX} ${minY} ${cropWidth} ${cropHeight}`;
  }

  return (
    <div className="landmark-overlay" style={wrapperStyle}>
      <img
        src={imageUrl}
        alt="Captured hand position"
        className="landmark-overlay__image"
        style={imageStyle}
        onLoad={(event) => {
          const target = event.currentTarget;
          setNaturalSize({ width: target.naturalWidth, height: target.naturalHeight });
        }}
      />
      <svg className="landmark-overlay__svg" viewBox={viewBox} preserveAspectRatio="none" aria-hidden="true">
        {HAND_CONNECTIONS.map(([a, b], index) => {
          const from = landmarks[a];
          const to = landmarks[b];
          if (!from || !to) return null;
          return (
            <line
              key={index}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              className={`landmark-overlay__line landmark-overlay__line--${variant}`}
            />
          );
        })}
        {landmarks.map((point, index) => (
          <circle
            key={index}
            cx={point.x}
            cy={point.y}
            r={0.012}
            className={`landmark-overlay__dot landmark-overlay__dot--${variant}`}
          />
        ))}
      </svg>
    </div>
  );
}
