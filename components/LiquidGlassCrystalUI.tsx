import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';

/**
 * Apple WWDC25 "Liquid Glass" — Crystal Clear theme.
 * Ocean-toned, tone-on-tone glass: one background hue, white-only accents.
 */

const SPRING_EASING = 'cubic-bezier(0.34, 1.56, 0.64, 1)';
const DRAG_THRESHOLD = 5; // px of movement before a press counts as a drag
const ELASTIC_OVERFLOW = 8; // px the pill may travel past the track edges

interface Blob {
  color: string;
  opacity: number;
  top: string;
  left: string;
  size: number;
  duration: number;
  delay: number;
}

const BLOBS: Blob[] = [
  { color: '#eaf8f8', opacity: 0.7, top: '10%', left: '8%', size: 340, duration: 22, delay: 0 },
  { color: '#7fb2b4', opacity: 0.6, top: '58%', left: '72%', size: 400, duration: 27, delay: 2 },
  { color: '#d9eeef', opacity: 0.55, top: '72%', left: '18%', size: 260, duration: 19, delay: 4 },
  { color: '#568789', opacity: 0.45, top: '14%', left: '64%', size: 300, duration: 24, delay: 1 },
];

export interface LiquidGlassCrystalUIProps {
  /** Initial pill state when uncontrolled. */
  defaultValue?: boolean;
  /** Controlled pill state. */
  value?: boolean;
  /** Fired when the pill settles on a new state (click or drag release). */
  onChange?: (value: boolean) => void;
  /** Label rendered next to the pill track. */
  label?: string;
  className?: string;
  trackWidth?: number;
  trackHeight?: number;
}

export default function LiquidGlassCrystalUI({
  defaultValue = false,
  value,
  onChange,
  label = 'Liquid Glass',
  className = '',
  trackWidth = 96,
  trackHeight = 48,
}: LiquidGlassCrystalUIProps) {
  const isControlled = value !== undefined;
  const [internalValue, setInternalValue] = useState(defaultValue);
  const settled = isControlled ? value : internalValue;

  const [isDragging, setIsDragging] = useState(false);
  const [hasDragged, setHasDragged] = useState(false);
  const [dragX, setDragX] = useState(0);

  const startXRef = useRef(0);
  const startPillXRef = useRef(0);

  const inset = 4;
  const pillSize = trackHeight - inset * 2;
  const travel = trackWidth - pillSize - inset * 2;
  const restX = settled ? travel : 0;

  const clamp = useCallback(
    (x: number) => Math.max(-ELASTIC_OVERFLOW, Math.min(travel + ELASTIC_OVERFLOW, x)),
    [travel]
  );

  const commit = useCallback(
    (x: number) => {
      const next = x > travel / 2;
      if (!isControlled) setInternalValue(next);
      onChange?.(next);
    },
    [travel, isControlled, onChange]
  );

  const handleMove = useCallback(
    (clientX: number) => {
      const delta = clientX - startXRef.current;
      if (!hasDragged && Math.abs(delta) >= DRAG_THRESHOLD) {
        setHasDragged(true);
      }
      setDragX(clamp(startPillXRef.current + delta));
    },
    [clamp, hasDragged]
  );

  const handleUp = useCallback(() => {
    setIsDragging(false);
    if (hasDragged) {
      commit(dragX);
    } else {
      // plain click/tap — toggle regardless of where the pointer landed
      commit(restX > 0 ? 0 : travel);
    }
    setHasDragged(false);
  }, [hasDragged, dragX, commit, restX, travel]);

  useEffect(() => {
    if (!isDragging) return;

    const onMouseMove = (e: MouseEvent) => handleMove(e.clientX);
    const onMouseUp = () => handleUp();
    const onTouchMove = (e: TouchEvent) => {
      const touch = e.touches[0];
      if (touch) handleMove(touch.clientX);
    };
    const onTouchEnd = () => handleUp();

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('touchmove', onTouchMove, { passive: false });
    window.addEventListener('touchend', onTouchEnd);

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('touchmove', onTouchMove);
      window.removeEventListener('touchend', onTouchEnd);
    };
  }, [isDragging, handleMove, handleUp]);

  const startDrag = (clientX: number) => {
    startXRef.current = clientX;
    startPillXRef.current = restX;
    setDragX(restX);
    setHasDragged(false);
    setIsDragging(true);
  };

  const pillX = isDragging ? dragX : restX;
  const lightRotation = isDragging ? 35 : settled ? 15 : -15;
  const transitionMs = isDragging ? 150 : 500;

  return (
    <div className={`relative min-h-screen w-full overflow-hidden ${className}`} style={{ color: '#1e293b' }}>
      <style>{`
        @keyframes lg-float {
          0%, 100% { transform: translate3d(0, 0, 0); }
          50% { transform: translate3d(0, -18px, 0); }
        }
      `}</style>

      {/* 1. Background — single ocean tone, no added hues */}
      <div
        className="absolute inset-0"
        style={{ background: 'linear-gradient(160deg, #d2ebec 0%, #9fccce 45%, #659799 100%)' }}
      />
      {BLOBS.map((blob, i) => (
        <div
          key={i}
          className="absolute rounded-full blur-3xl"
          style={{
            top: blob.top,
            left: blob.left,
            width: blob.size,
            height: blob.size,
            backgroundColor: blob.color,
            opacity: blob.opacity,
            animation: `lg-float ${blob.duration}s ease-in-out ${blob.delay}s infinite`,
            willChange: 'transform',
          }}
        />
      ))}

      {/* Glass card */}
      <div className="relative z-10 flex min-h-screen items-center justify-center p-6">
        <GlassSurface rotation={lightRotation} className="rounded-[28px] px-8 py-7">
          <div className="flex items-center gap-5">
            <span className="text-sm font-semibold tracking-wide">{label}</span>

            {/* 3. Draggable pill track (static layer — safe to backdrop-blur if desired) */}
            <div
              className="relative shrink-0 rounded-full"
              style={{
                width: trackWidth,
                height: trackHeight,
                background: 'rgba(255,255,255,0.14)',
                boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.18)',
              }}
              onMouseDown={(e) => startDrag(e.clientX)}
              onTouchStart={(e) => startDrag(e.touches[0].clientX)}
            >
              {/* Moving pill lives in its own z-10 layer, isolated from the static
                  blurred layers above — keeps backdrop-blur off the animated element. */}
              <div
                className="absolute z-10 overflow-hidden rounded-full"
                style={{
                  top: inset,
                  left: inset,
                  width: pillSize,
                  height: pillSize,
                  transform: `translateX(${pillX}px) scale(${isDragging ? 1.08 : 1})`,
                  transition: `transform ${transitionMs}ms ${SPRING_EASING}`,
                  willChange: isDragging ? 'transform' : 'auto',
                  background: isDragging
                    ? 'rgba(255,255,255,0.22)'
                    : 'linear-gradient(to bottom, #fff, #eef1f6)',
                  backdropFilter: isDragging ? 'blur(10px) saturate(2) brightness(1.15)' : undefined,
                  WebkitBackdropFilter: isDragging ? 'blur(10px) saturate(2) brightness(1.15)' : undefined,
                  boxShadow:
                    'inset 0 1.5px 1px rgba(255,255,255,0.55), inset 0 -2px 2px rgba(0,0,0,0.16), 0 6px 14px rgba(0,0,0,0.22)',
                }}
              >
                {/* caustics — only while dragging */}
                <div
                  className="absolute inset-0"
                  style={{
                    background:
                      'radial-gradient(ellipse at 30% 20%, rgba(255,255,255,0.75) 0%, transparent 45%), radial-gradient(ellipse at 70% 80%, rgba(255,255,255,0.55) 0%, transparent 45%)',
                    mixBlendMode: 'screen',
                    opacity: isDragging ? 1 : 0,
                    transition: `opacity ${transitionMs}ms ${SPRING_EASING}`,
                  }}
                />
                {/* specular top sheet */}
                <div
                  className="absolute inset-x-0 top-0 h-1/2"
                  style={{
                    background: 'linear-gradient(to bottom, rgba(255,255,255,0.7), transparent)',
                    opacity: isDragging ? 0.5 : 0.9,
                    transition: `opacity ${transitionMs}ms ${SPRING_EASING}`,
                  }}
                />
              </div>
            </div>
          </div>
        </GlassSurface>
      </div>
    </div>
  );
}

/** Shared 4-layer glass surface used by every card/button in the theme. */
function GlassSurface({
  children,
  className = '',
  rotation = 0,
}: {
  children: ReactNode;
  className?: string;
  rotation?: number;
}) {
  return (
    <div
      className={`relative overflow-hidden border border-white/[0.28] bg-white/[0.05] backdrop-blur-[16px] backdrop-saturate-[2] backdrop-brightness-[1.12] ${className}`}
      style={{
        boxShadow:
          'inset 0 1.5px 1px rgba(255,255,255,0.55), inset 0 -2px 2px rgba(0,0,0,0.16), 0 20px 40px rgba(0,0,0,0.28)',
      }}
    >
      {/* layer 2 — fresnel gradient, brighter at top */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-white/[0.22] to-transparent" />
      {/* layer 4 — dynamic light, 200% size, rotates with interaction state */}
      <div
        className="pointer-events-none absolute"
        style={{
          top: '-50%',
          left: '-50%',
          width: '200%',
          height: '200%',
          background: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.28) 0%, transparent 45%)',
          transform: `rotate(${rotation}deg)`,
          transition: `transform 500ms ${SPRING_EASING}`,
        }}
      />
      <div className="relative">{children}</div>
    </div>
  );
}
