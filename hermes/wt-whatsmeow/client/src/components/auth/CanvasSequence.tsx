import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export const CanvasSequence = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;

    const frameCount = 192;
    const currentFrame = { index: 0 };
    const images: HTMLImageElement[] = [];

    // Preload Images
    for (let i = 1; i <= frameCount; i++) {
      const img = new Image();
      const frameNumber = i.toString().padStart(4, "0");
      img.src = `/video_frames/frame_${frameNumber}.jpg`;
      images.push(img);
    }

    const render = () => {
      const frameIndex = Math.floor(currentFrame.index);
      const img = images[frameIndex];
      if (img && img.complete) {
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(img, 0, 0, canvas.width, canvas.height);
      }
    };

    if (images[0]) {
      images[0].onload = render;
    }

    // GSAP Scroll Animation
    const trigger = ScrollTrigger.create({
      trigger: document.body,
      start: "top top",
      end: "bottom bottom",
      scrub: 0,
      animation: gsap.to(currentFrame, {
        index: frameCount - 1,
        ease: "none",
        onUpdate: () => requestAnimationFrame(render),
      }),
    });

    return () => {
      trigger.kill();
    };
  }, []);

  return (
    <div ref={containerRef} className="absolute inset-0 z-0 flex items-center justify-center bg-black/40">
      <canvas
        ref={canvasRef}
        width={1280}
        height={720}
        className="w-full h-full object-cover relative z-10"
      />
      <div className="absolute inset-0 bg-gradient-to-r from-transparent to-background z-20" />
    </div>
  );
};
