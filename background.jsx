import React, { useEffect, useRef } from 'react';
import './bg.css';

const Bg = () => {
  const containerRef = useRef(null);
  const particlesRef = useRef([]);
  const animationRef = useRef(null);
  const lastTimeRef = useRef(Date.now());

  useEffect(() => {
    const count = 100;
    const container = containerRef.current;

    // Create DOM particles once
    for (let i = 0; i < count; i++) {
      const div = document.createElement("div");
      div.className = "particle";
      const size = Math.random() * 20 + 1;
      div.style.width = `${size}px`;
      div.style.height = `${size}px`;
      div.style.position = "absolute";
      div.style.background = "white";
      div.style.borderRadius = "50%";
      div.style.opacity = (Math.random() * 0.8 + 0.2).toString();

      container.appendChild(div);

      particlesRef.current.push({
        el: div,
        x: Math.random() * 100,
        y: Math.random() * 100,
        speed: Math.random() * 10 + 5,
      });
    }

    const animate = () => {
      const now = Date.now();
      const delta = (now - lastTimeRef.current) / 1000;
      lastTimeRef.current = now;

      for (let p of particlesRef.current) {
        p.y -= p.speed * delta;
        if (p.y < -5) {
          p.y = 105;
          p.x = Math.random() * 100;
        }
        p.el.style.top = `${p.y}%`;
        p.el.style.left = `${p.x}%`;
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);
    return () => {
      cancelAnimationFrame(animationRef.current);
      // Cleanup particles
      particlesRef.current.forEach(p => container.removeChild(p.el));
    };
  }, []);

  return <div className="floating-background" ref={containerRef}>
  </div>;
};

export default Bg;
