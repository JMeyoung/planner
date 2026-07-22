(function() {
  // Load saved values from localStorage
  const savedBlur = localStorage.getItem('liquidGlassBlur') || '24';
  const savedOpacity = localStorage.getItem('liquidGlassOpacity') || '0.04';
  
  document.documentElement.style.setProperty('--user-glass-blur', savedBlur + 'px');
  document.documentElement.style.setProperty('--user-glass-opacity', savedOpacity);

  // Create UI on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', () => {
    // Inject Settings Button
    const btn = document.createElement('div');
    btn.innerHTML = '⚙️';
    btn.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.14);
      backdrop-filter: blur(24px) saturate(180%);
      -webkit-backdrop-filter: blur(24px) saturate(180%);
      border: 1px solid rgba(255, 255, 255, 0.32);
      box-shadow: 0 4px 16px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      cursor: pointer;
      z-index: 9999;
      transition: transform 0.2s;
    `;
    btn.onmouseover = () => btn.style.transform = 'scale(1.1)';
    btn.onmouseout = () => btn.style.transform = 'scale(1)';
    document.body.appendChild(btn);

    // Inject Settings Panel
    const panel = document.createElement('div');
    panel.style.cssText = `
      position: fixed;
      bottom: 80px;
      right: 20px;
      width: 280px;
      background: rgba(20, 20, 25, 0.85);
      backdrop-filter: blur(40px) saturate(200%);
      -webkit-backdrop-filter: blur(40px) saturate(200%);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 20px;
      box-shadow: 0 12px 40px rgba(0,0,0,0.5);
      padding: 20px;
      z-index: 9998;
      display: none;
      opacity: 0;
      transform-origin: bottom right;
      transform: translateY(10px) scale(0.95);
      transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), background-color 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), border-color 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
      color: #fff;
      font-family: inherit;
    `;
    
    panel.innerHTML = `
      <div style="font-size: 14px; font-weight: 700; margin-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">
        🫧 Liquid Glass 설정
      </div>
      
      <!-- 1. Blur Slider -->
      <div style="margin-bottom: 16px;">
        <div style="font-size: 12px; font-weight: 600; margin-bottom: 6px; display: flex; justify-content: space-between;">
          <span>블러 강도 (Blur)</span>
          <span id="lg-blur-val" style="color: rgba(255,255,255,0.7); font-variant-numeric: tabular-nums;">${savedBlur}px</span>
        </div>
        <input type="range" id="lg-blur-slider" min="0" max="60" value="${savedBlur}" style="width: 100%; accent-color: #3c6ff0; cursor: pointer;">
      </div>

      <!-- 2. Opacity Slider -->
      <div style="margin-bottom: 8px;">
        <div style="font-size: 12px; font-weight: 600; margin-bottom: 6px; display: flex; justify-content: space-between;">
          <span>배경 불투명도 (Opacity)</span>
          <span id="lg-opacity-val" style="color: rgba(255,255,255,0.7); font-variant-numeric: tabular-nums;">${(parseFloat(savedOpacity) * 100).toFixed(1)}%</span>
        </div>
        <input type="range" id="lg-opacity-slider" min="0" max="40" step="0.1" value="${parseFloat(savedOpacity) * 100}" style="width: 100%; accent-color: #21c48f; cursor: pointer;">
      </div>
    `;
    document.body.appendChild(panel);

    // Toggle logic
    let isOpen = false;
    btn.addEventListener('click', () => {
      isOpen = !isOpen;
      if (isOpen) {
        panel.style.display = 'block';
        setTimeout(() => {
          panel.style.opacity = '1';
          panel.style.transform = 'translateY(0) scale(1)';
        }, 10);
      } else {
        panel.style.opacity = '0';
        panel.style.transform = 'translateY(10px) scale(0.95)';
        setTimeout(() => { panel.style.display = 'none'; }, 200);
      }
    });

    // Blur Slider logic
    const blurSlider = document.getElementById('lg-blur-slider');
    const blurValText = document.getElementById('lg-blur-val');
    
    blurSlider.addEventListener('input', (e) => {
      const v = e.target.value;
      blurValText.textContent = v + 'px';
      document.documentElement.style.setProperty('--user-glass-blur', v + 'px');
      localStorage.setItem('liquidGlassBlur', v);
    });

    // Opacity Slider logic
    const opacitySlider = document.getElementById('lg-opacity-slider');
    const opacityValText = document.getElementById('lg-opacity-val');
    
    opacitySlider.addEventListener('input', (e) => {
      const v = parseFloat(e.target.value);
      const opacityDecimal = (v / 100).toFixed(3);
      opacityValText.textContent = v.toFixed(1) + '%';
      document.documentElement.style.setProperty('--user-glass-opacity', opacityDecimal);
      localStorage.setItem('liquidGlassOpacity', opacityDecimal);
    });

    // injectLiquidGlassBlobs(); // Disabled: clean mint gradient background only
    initLiquidGlassPills();
  });

  // ── Ambient background blobs (DISABLED — clean mint gradient only) ──
  function injectLiquidGlassBlobs() {
    // Blobs removed. Clean mint gradient background via CSS.
    return;
  }

  // ── Draggable glass pills (Style Lab toggle switches) ──
  // Spring-driven, click-vs-drag aware, elastic-boundary pill knob.
  function initLiquidGlassPills() {
    const SPRING_EASING = 'cubic-bezier(0.34, 1.56, 0.64, 1)';
    const DRAG_THRESHOLD = 5; // px before a press counts as a drag
    const ELASTIC_OVERFLOW = 8; // px the knob may travel past the track edges
    const KNOB_SIZE = 18;
    const KNOB_INSET = 3;

    document.querySelectorAll('.switch').forEach((label) => {
      if (label.dataset.lgPillInit) return;
      label.dataset.lgPillInit = '1';

      const input = label.querySelector('input[type="checkbox"]');
      const slider = label.querySelector('.slider');
      if (!input || !slider) return;

      const knob = document.createElement('span');
      knob.className = 'lg-knob';
      knob.innerHTML =
        '<span class="lg-knob-caustics"></span><span class="lg-knob-specular"></span>';
      slider.appendChild(knob);

      let isDragging = false;
      let hasDragged = false;
      let dragX = 0;
      const startXRef = { current: 0 };
      const startPillXRef = { current: 0 };

      const travel = () => slider.clientWidth - KNOB_SIZE - KNOB_INSET * 2;
      const restX = () => (input.checked ? travel() : 0);
      const clampX = (x) => Math.max(-ELASTIC_OVERFLOW, Math.min(travel() + ELASTIC_OVERFLOW, x));

      const setKnobX = (x, durationMs) => {
        knob.style.transition = 'transform ' + durationMs + 'ms ' + SPRING_EASING;
        knob.style.transform = 'translateX(' + x + 'px) scale(' + (isDragging ? 1.08 : 1) + ')';
      };

      const setDragging = (dragging) => {
        isDragging = dragging;
        label.classList.toggle('dragging', dragging);
        knob.style.willChange = dragging ? 'transform' : 'auto';
      };

      const commit = (x) => {
        const next = x > travel() / 2;
        if (input.checked !== next) {
          input.checked = next;
          input.dispatchEvent(new Event('change', { bubbles: true }));
        }
        setKnobX(restX(), 500);
      };

      const onMove = (clientX) => {
        const delta = clientX - startXRef.current;
        if (!hasDragged && Math.abs(delta) >= DRAG_THRESHOLD) hasDragged = true;
        dragX = clampX(startPillXRef.current + delta);
        setKnobX(dragX, 150);
      };

      function onMouseMove(e) {
        onMove(e.clientX);
      }
      function onTouchMove(e) {
        if (e.touches[0]) {
          e.preventDefault();
          onMove(e.touches[0].clientX);
        }
      }
      function onMouseUp() {
        onUp();
      }
      function onTouchEnd() {
        onUp();
      }

      function onUp() {
        setDragging(false);
        if (hasDragged) {
          commit(dragX);
        } else {
          commit(restX() > 0 ? 0 : travel());
        }
        hasDragged = false;
        // registered on drag start, torn down here — mirrors a useEffect cleanup
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        window.removeEventListener('touchmove', onTouchMove);
        window.removeEventListener('touchend', onTouchEnd);
      }

      function startDrag(clientX) {
        startXRef.current = clientX;
        startPillXRef.current = restX();
        dragX = startPillXRef.current;
        hasDragged = false;
        setDragging(true);
        setKnobX(dragX, 0);

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
        window.addEventListener('touchmove', onTouchMove, { passive: false });
        window.addEventListener('touchend', onTouchEnd);
      }

      slider.addEventListener('mousedown', (e) => {
        e.preventDefault();
        startDrag(e.clientX);
      });
      slider.addEventListener(
        'touchstart',
        (e) => {
          e.preventDefault();
          startDrag(e.touches[0].clientX);
        },
        { passive: false }
      );

      // We own toggling entirely through the mousedown/up state machine above;
      // suppress the browser's native label->input click forwarding so it
      // doesn't also flip `checked` and cancel out our own commit().
      label.addEventListener('click', (e) => e.preventDefault());

      // keep the knob synced if `checked` changes programmatically elsewhere
      input.addEventListener('change', () => {
        if (!isDragging) setKnobX(restX(), 500);
      });

      setKnobX(restX(), 0); // initial position, no transition
    });
  }
})();
