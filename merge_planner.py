import re

def extract_sections(html):
    style = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
    body = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
    script = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
    
    return {
        'style': style.group(1) if style else '',
        'body': body.group(1) if body else '',
        'script': script.group(1) if script else ''
    }

with open("daily.html", "r") as f:
    daily = extract_sections(f.read())

with open("monthly.html", "r") as f:
    monthly = extract_sections(f.read())

# Extract global elements from daily.html body before cleaning
theme_toggle_match = re.search(r'<button class="theme-toggle".*?</button>', daily['body'], flags=re.DOTALL)
theme_toggle = theme_toggle_match.group(0) if theme_toggle_match else ''

open_btn_match = re.search(r'<button class="open-window-btn".*?</button>', daily['body'], flags=re.DOTALL)
open_btn = open_btn_match.group(0) if open_btn_match else ''

token_setup_match = re.search(r'<!-- Notion 토큰 설정 모달 -->.*?</div>\s*</div>\s*</div>', daily['body'], flags=re.DOTALL)
token_setup = token_setup_match.group(0) if token_setup_match else ''

style_lab_match = re.search(r'<!-- Style Lab Drawer & UI -->.*?<\/svg>', daily['body'], flags=re.DOTALL)
style_lab = style_lab_match.group(0) if style_lab_match else ''

celebrate_block = '<div class="celebrate-wrap" id="celebrate"></div>'
toast_block = '<div id="toast" class="toast"></div>'

# Clean duplicate global elements from both daily and monthly bodies
def clean_body(body_html):
    # Remove script tags from body
    body_html = re.sub(r'<script>.*?</script>', '', body_html, flags=re.DOTALL)
    # Strip themeToggle button
    body_html = re.sub(r'<button class="theme-toggle"[^>]*>.*?</button>', '', body_html, flags=re.DOTALL)
    # Strip open-window-btn (token setup button)
    body_html = re.sub(r'<button class="open-window-btn"[^>]*>.*?</button>', '', body_html, flags=re.DOTALL)
    # Strip tokenSetup modal
    body_html = re.sub(r'<!-- Notion 토큰 설정 모달 -->.*?</div>\s*</div>\s*</div>', '', body_html, flags=re.DOTALL)
    # Strip Style Lab & Gooey Menu
    body_html = re.sub(r'<!-- Style Lab Drawer & UI -->.*?<\/svg>', '', body_html, flags=re.DOTALL)
    # Strip celebrate-wrap
    body_html = re.sub(r'<div class="celebrate-wrap"[^>]*></div>', '', body_html, flags=re.DOTALL)
    # Strip toast container
    body_html = re.sub(r'<div id="toast"[^>]*></div>', '', body_html, flags=re.DOTALL)
    return body_html

cleaned_daily_body = clean_body(daily['body'])
cleaned_monthly_body = clean_body(monthly['body'])

# Combine style
combined_style = daily['style'] + "\n/* MONTHLY STYLES */\n" + monthly['style']

nav_html = """
<style>
/* Bottom Nav */
.bottom-nav {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  height: 65px;
  background: rgba(30,30,40,0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid rgba(255,255,255,0.1);
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 1000;
  padding-bottom: env(safe-area-inset-bottom);
}
.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.3s ease;
  width: 50%;
  height: 100%;
  cursor: pointer;
}
.nav-item.active {
  color: var(--accent-math);
}
.nav-icon {
  font-size: 1.4rem;
  margin-bottom: 3px;
}
.view-container {
  display: none;
  animation: fadeIn 0.3s ease;
  padding-bottom: 80px; /* space for nav */
}
.view-container.active {
  display: block;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>

<div class="bottom-nav">
  <div class="nav-item active" onclick="switchTab('daily')">
    <span class="nav-icon">📝</span>
    <span>일간 플래너</span>
  </div>
  <div class="nav-item" onclick="switchTab('monthly')">
    <span class="nav-icon">📅</span>
    <span>월간 플래너</span>
  </div>
</div>
"""

nav_js = """
// 탭 전환 로직
function switchTab(tab) {
  document.querySelectorAll('.view-container').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  
  if(tab === 'daily') {
    document.getElementById('view-daily').classList.add('active');
    document.querySelectorAll('.nav-item')[0].classList.add('active');
  } else {
    document.getElementById('view-monthly').classList.add('active');
    document.querySelectorAll('.nav-item')[1].classList.add('active');
  }
}

// Intercept all clicks on "/daily?date=YYYY-MM-DD" links to load date in single page!
document.addEventListener('click', function(e) {
  const target = e.target.closest('a');
  if (target && target.getAttribute('href') && target.getAttribute('href').startsWith('/daily?date=')) {
    e.preventDefault();
    const url = new URL(target.href, window.location.href);
    const dateStr = url.searchParams.get('date');
    if (dateStr) {
      switchTab('daily');
      if (window.loadDailyDate) {
        window.loadDailyDate(dateStr);
      }
    }
  }
});
"""

combined_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<title>2027 스터디 통합 플래너</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📅</text></svg>">
<style>
{combined_style}
</style>
</head>
<body class="dark-theme">

<!-- Global UI Elements -->
{theme_toggle}
{open_btn}
{token_setup}
{style_lab}
{celebrate_block}

<div id="view-daily" class="view-container active">
{cleaned_daily_body}
</div>

<div id="view-monthly" class="view-container">
{cleaned_monthly_body}
</div>

{toast_block}
{nav_html}

<script>
{daily['script']}

// ---------------------------------
// MONTHLY SCRIPT
// ---------------------------------
{monthly['script']}

{nav_js}
</script>
</body>
</html>
"""

with open("planner.html", "w") as f:
    f.write(combined_html)

print("Merged planner.html created.")
