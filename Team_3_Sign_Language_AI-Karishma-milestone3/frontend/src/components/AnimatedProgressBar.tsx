import React, { useEffect, useState } from 'react';

interface AnimatedProgressBarProps {
  percent: number;
  className?: string;
  dimension?: 'width' | 'height';
}

// Renders at 0 for one frame, then transitions to the real value — the
// CSS `transition: width/height` on the fill class does the actual
// animating. A one-time reveal per mount/value change, not a loop.
export function AnimatedProgressBar({ percent, className, dimension = 'width' }: AnimatedProgressBarProps) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    const frame = requestAnimationFrame(() => setValue(percent));
    return () => cancelAnimationFrame(frame);
  }, [percent]);

  return <div className={className} style={{ [dimension]: `${value}%` }} />;
}
