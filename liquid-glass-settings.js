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
      transform: translateY(10px);
      transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
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
          <span id="lg-opacity-val" style="color: rgba(255,255,255,0.7); font-variant-numeric: tabular-nums;">${Math.round(savedOpacity * 100)}%</span>
        </div>
        <input type="range" id="lg-opacity-slider" min="0" max="40" value="${Math.round(savedOpacity * 100)}" style="width: 100%; accent-color: #21c48f; cursor: pointer;">
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
          panel.style.transform = 'translateY(0)';
        }, 10);
      } else {
        panel.style.opacity = '0';
        panel.style.transform = 'translateY(10px)';
        setTimeout(() => { panel.style.display = 'none'; }, 300);
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
      const v = e.target.value;
      const opacityDecimal = (v / 100).toFixed(2);
      opacityValText.textContent = v + '%';
      document.documentElement.style.setProperty('--user-glass-opacity', opacityDecimal);
      localStorage.setItem('liquidGlassOpacity', opacityDecimal);
    });
  });
})();
