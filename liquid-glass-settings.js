(function() {
  // Load saved blur value from localStorage
  const savedBlur = localStorage.getItem('liquidGlassBlur');
  if (savedBlur) {
    document.documentElement.style.setProperty('--user-glass-blur', savedBlur + 'px');
  }

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
      background: rgba(255, 255, 255, 0.14);
      backdrop-filter: blur(40px) saturate(200%);
      -webkit-backdrop-filter: blur(40px) saturate(200%);
      border: 1px solid rgba(255, 255, 255, 0.32);
      border-radius: 16px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.4);
      padding: 16px;
      z-index: 9998;
      display: none;
      opacity: 0;
      transform: translateY(10px);
      transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
      color: #fff;
      font-family: inherit;
    `;
    
    panel.innerHTML = `
      <div style="font-size: 13px; font-weight: 700; margin-bottom: 12px; display: flex; justify-content: space-between;">
        <span>Liquid Glass 투명도 설정</span>
        <span id="lg-blur-val" style="color: rgba(255,255,255,0.7); font-variant-numeric: tabular-nums;">${savedBlur || 24}px</span>
      </div>
      <input type="range" id="lg-blur-slider" min="0" max="60" value="${savedBlur || 24}" style="width: 100%; accent-color: #3c6ff0; cursor: pointer;">
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

    // Slider logic
    const slider = document.getElementById('lg-blur-slider');
    const valText = document.getElementById('lg-blur-val');
    
    slider.addEventListener('input', (e) => {
      const v = e.target.value;
      valText.textContent = v + 'px';
      document.documentElement.style.setProperty('--user-glass-blur', v + 'px');
      localStorage.setItem('liquidGlassBlur', v);
    });
  });
})();
