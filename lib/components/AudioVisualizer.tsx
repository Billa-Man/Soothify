'use client';

import { useEffect, useRef, useState } from 'react';
import lottie, { AnimationItem } from 'lottie-web';

interface AudioVisualizerProps {
  analyser: AnalyserNode | null;
  className?: string;
  width?: number;
  height?: number;
}

export function AudioVisualizer({
  analyser,
  className = '',
  width = 200,
  height = 200
}: AudioVisualizerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const animationRef = useRef<AnimationItem | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const loadAnimation = async () => {
      try {
        const response = await fetch('/media/siri_wave.json');
        const animationData = await response.json();

        if (cancelled || !containerRef.current) return;

        animationRef.current = lottie.loadAnimation({
          container: containerRef.current,
          renderer: 'svg',
          loop: true,
          autoplay: true,
          animationData,
        });

        animationRef.current.setSpeed(0.8);
        setIsAnimating(true);
      } catch (error) {
        console.error('Failed to load Lottie animation:', error);
      }
    };

    loadAnimation();

    return () => {
      cancelled = true;
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (animationRef.current) {
        animationRef.current.destroy();
        animationRef.current = null;
      }
      setIsAnimating(false);
    };
  }, []);

  useEffect(() => {
    if (!analyser || !animationRef.current) return;

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const animate = () => {
      if (!analyser || !animationRef.current) return;

      analyser.getByteFrequencyData(dataArray);

      // Calculate average amplitude (0-1)
      const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length / 255;

      // Adjust animation speed based on audio amplitude
      const speed = Math.max(0.6, 0.6 + avg * 2.0);
      animationRef.current.setSpeed(speed);

      // Adjust scale based on amplitude for visual feedback
      if (containerRef.current) {
        const scale = Math.max(0.8, 1 + Math.min(0.35, avg * 0.8));
        containerRef.current.style.transform = `scale(${scale})`;
      }

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    };
  }, [analyser]);

  return (
    <div className={`flex justify-center ${className}`}>
      <div
        ref={containerRef}
        style={{
          width,
          height,
          opacity: isAnimating ? 1 : 0.5,
          transition: 'opacity 0.3s ease',
        }}
      />
    </div>
  );
}
