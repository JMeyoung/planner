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

# Remove scripts from body
daily['body'] = re.sub(r'<script>.*?</script>', '', daily['body'], flags=re.DOTALL)
monthly['body'] = re.sub(r'<script>.*?</script>', '', monthly['body'], flags=re.DOTALL)

# Strip duplicate Style Lab and Gooey Menu elements from monthly body to prevent duplicate ID conflicts in planner.html
monthly['body'] = re.sub(r'<!-- Style Lab Drawer & UI -->.*?<\/svg>', '', monthly['body'], flags=re.DOTALL)

# Combine
combined_style = daily['style'] + "\n/* MONTHLY STYLES */\n" + monthly['style']
# we should remove duplicated root variables if possible, but browsers handle overrides gracefully.

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

<div id="view-daily" class="view-container active">
{daily['body']}
</div>

<div id="view-monthly" class="view-container">
{monthly['body']}
</div>

{nav_html}

<script>
{daily['script']}

// ---------------------------------
// MONTHLY SCRIPT
// ---------------------------------
// Some functions (like safeApiCall, extractContent, todayFmt) might be duplicated.
// We will let the browser overwrite them since they are functionally identical in both files.

{monthly['script']}

{nav_js}
</script>
</body>
</html>
"""

with open("planner.html", "w") as f:
    f.write(combined_html)

print("Merged planner.html created.")
