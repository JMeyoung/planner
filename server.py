#!/usr/bin/env python3
"""
스터디 플래너 로컬 서버
============================
사용법:
  1. 이 파일과 planner_standalone.html을 같은 폴더에 저장
  2. 터미널에서: python server.py
  3. Chrome에서: http://localhost:3000 접속
  4. 첫 실행 시 Notion 통합 토큰 입력 (secret_xxx 또는 ntn_xxx)

종료: Ctrl+C
"""
import http.server
import json
import os
import re
import urllib.request
import urllib.parse
from urllib.error import HTTPError

PORT = int(os.environ.get('PORT', 3005))  # Railway는 PORT 환경변수 사용
HOST = '0.0.0.0'  # 클라우드에서는 모든 인터페이스에서 수신
NOTION_API = 'https://api.notion.com/v1'
NOTION_VERSION = '2022-06-28'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MONTHLY_HTML = os.path.join(BASE_DIR, 'monthly.html')
DAILY_HTML   = os.path.join(BASE_DIR, 'daily.html')
PLANNER_HTML = os.path.join(BASE_DIR, 'planner.html')
KNOWLEDGE_HTML = os.path.join(BASE_DIR, 'knowledge.html')
TIMER_HTML   = os.path.join(BASE_DIR, 'timer.html')
KNOWLEDGE_JSON = os.path.join(BASE_DIR, 'knowledge_db.json')
TOKEN_FILE   = os.path.join(BASE_DIR, '.notion_token')


def load_saved_token():
    """환경변수 우선, 없으면 파일에서 토큰 읽기"""
    env_token = os.environ.get('NOTION_TOKEN', '').strip()
    if env_token:
        return env_token
    try:
        with open(TOKEN_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return ''


def save_token(token):
    """토큰을 파일에 저장"""
    try:
        with open(TOKEN_FILE, 'w') as f:
            f.write(token)
    except Exception:
        pass  # 클라우드 읽기전용 환경에서는 무시


# ───────────────────────────────────────────────
# Notion API helpers
# ───────────────────────────────────────────────

def notion_request(path, method='GET', body=None, token=''):
    url = NOTION_API + path
    headers = {
        'Authorization': f'Bearer {token}',
        'Notion-Version': NOTION_VERSION,
        'Content-Type': 'application/json',
    }
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except HTTPError as e:
        msg = e.read().decode('utf-8')
        raise Exception(f'Notion API {e.code}: {msg}')


def get_rich_text(rich_text_arr):
    return ''.join(rt.get('plain_text', '') for rt in (rich_text_arr or []))

def blocks_to_markdown(blocks):
    lines = []
    for block in blocks:
        btype = block.get('type', '')
        content = block.get(btype, {})

        if btype == 'heading_1':
            lines.append('# ' + get_rich_text(content.get('rich_text', [])))
        elif btype == 'heading_2':
            lines.append('## ' + get_rich_text(content.get('rich_text', [])))
        elif btype == 'heading_3':
            lines.append('### ' + get_rich_text(content.get('rich_text', [])))
        elif btype == 'paragraph':
            t = get_rich_text(content.get('rich_text', []))
            lines.append(t)
        elif btype == 'to_do':
            t = get_rich_text(content.get('rich_text', []))
            mark = '[x]' if content.get('checked') else '[ ]'
            lines.append(f'- {mark} {t}')
        elif btype == 'bulleted_list_item':
            lines.append('- ' + get_rich_text(content.get('rich_text', [])))
        elif btype == 'numbered_list_item':
            lines.append('1. ' + get_rich_text(content.get('rich_text', [])))
        elif btype == 'child_page':
            title = content.get('title', '')
            bid = block.get('id', '').replace('-', '')
            url = f'https://www.notion.so/p/{bid}'
            lines.append(f'<page url="{url}">{title}</page>')
        elif btype == 'divider':
            lines.append('---')
        elif btype == 'toggle':
            t = get_rich_text(content.get('rich_text', []))
            lines.append(t)
        elif btype == 'callout':
            t = get_rich_text(content.get('rich_text', []))
            lines.append(f'> {t}')
        # else: skip unsupported

    return '\n'.join(lines)


def fetch_all_blocks(block_id, token):
    all_blocks = []
    cursor = None
    while True:
        path = f'/blocks/{block_id}/children?page_size=100'
        if cursor:
            path += f'&start_cursor={urllib.parse.quote(cursor)}'
        data = notion_request(path, token=token)
        all_blocks.extend(data.get('results', []))
        if not data.get('has_more'):
            break
        cursor = data.get('next_cursor')
    return all_blocks


def get_page_title(page_id, token):
    """Retrieve Notion page to get its title"""
    try:
        data = notion_request(f'/pages/{page_id}', token=token)
        properties = data.get('properties', {})
        for prop in properties.values():
            if prop.get('type') == 'title':
                return get_rich_text(prop.get('title', []))
    except Exception:
        pass
    return ''


def fetch_page_as_text(page_id, token):
    """Fetch Notion page blocks → markdown text wrapped in <content> tags"""
    # Clean up page_id (remove dashes if present)
    pid = page_id.replace('-', '')
    # Format as UUID
    if len(pid) == 32:
        pid = f'{pid[:8]}-{pid[8:12]}-{pid[12:16]}-{pid[16:20]}-{pid[20:]}'
    
    title = get_page_title(pid, token)
    blocks = fetch_all_blocks(pid, token)
    md = blocks_to_markdown(blocks)
    if title:
        return f"# {title}\n\n{md}"
    return md


def find_todo_block_by_text(page_id, target_text, token):
    """Find a to_do block matching target_text; returns (block_id, checked) or (None, None)"""
    blocks = fetch_all_blocks(page_id, token)
    target = target_text.strip()
    for block in blocks:
        if block.get('type') == 'to_do':
            c = block.get('to_do', {})
            text = get_rich_text(c.get('rich_text', [])).strip()
            if text == target:
                return block['id'], c.get('checked', False)
    return None, None


def update_todo_checked(block_id, checked, token):
    body = {'to_do': {'checked': checked}}
    return notion_request(f'/blocks/{block_id}', method='PATCH', body=body, token=token)


def insert_todo_after_block(page_id, after_block_id, text, token):
    """Append a new to_do block after a given block"""
    body = {
        'children': [{
            'object': 'block',
            'type': 'to_do',
            'to_do': {
                'rich_text': [{'type': 'text', 'text': {'content': text}}],
                'checked': False,
                'color': 'default'
            }
        }]
    }
    if after_block_id and after_block_id != page_id:
        body['after'] = after_block_id
    
    # Notion API: append children to parent page
    return notion_request(f'/blocks/{page_id}/children', method='PATCH', body=body, token=token)

def append_retro_to_page(page_id, daily_memo, weekly_memo, ai_retro, token):
    """Append the user's memos and AI retrospective to the bottom of the page"""
    from datetime import datetime
    import pytz
    KST = pytz.timezone('Asia/Seoul')
    today_str = datetime.now(KST).strftime("%Y-%m-%d")
    
    children = [
        {
            'object': 'block',
            'type': 'heading_2',
            'heading_2': {
                'rich_text': [{'type': 'text', 'text': {'content': f"📝 회고록 ({today_str})"}}]
            }
        }
    ]
    
    if daily_memo:
        children.append({
            'object': 'block',
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{'type': 'text', 'text': {'content': "오늘의 회고:\n" + daily_memo}}]
            }
        })
        
    if weekly_memo:
        children.append({
            'object': 'block',
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{'type': 'text', 'text': {'content': "이번 주 회고:\n" + weekly_memo}}]
            }
        })
        
    if ai_retro:
        children.append({
            'object': 'block',
            'type': 'callout',
            'callout': {
                'rich_text': [{'type': 'text', 'text': {'content': ai_retro}}],
                'icon': {'type': 'emoji', 'emoji': '✨'},
                'color': 'gray_background'
            }
        })
        
    return notion_request(f'/blocks/{page_id}/children', method='PATCH', body={'children': children}, token=token)


def apply_content_update(page_id, old_str, new_str, token):
    """
    Replicate MCP notion-update-page update_content behavior.
    Two cases:
      1. Checkbox toggle: one line changed from [ ] ↔ [x]
      2. Insertion: new line added at end (quick-add)
    """
    old_lines = old_str.split('\n')
    new_lines = new_str.split('\n')

    # Case 1: same number of lines, find the changed one
    if len(old_lines) == len(new_lines):
        for ol, nl in zip(old_lines, new_lines):
            if ol != nl:
                om = re.match(r'^- \[([ x])\] (.+)$', ol.strip())
                nm = re.match(r'^- \[([ x])\] (.+)$', nl.strip())
                if om and nm:
                    task_text = om.group(2)
                    new_checked = nm.group(1) == 'x'
                    bid, _ = find_todo_block_by_text(page_id, task_text, token)
                    if bid:
                        update_todo_checked(bid, new_checked, token)
                break
        return

    # Case 2: new_lines has more lines (insertion)
    if len(new_lines) > len(old_lines):
        # The new item is the last line of new_str
        new_item_line = new_lines[-1].strip()
        anchor_line = old_lines[-1].strip()
        m = re.match(r'^- \[[ x]\] (.+)$', new_item_line)
        if m:
            new_text = m.group(1)
            # Find anchor block
            anchor_text = re.sub(r'^- \[[ x]\] ', '', anchor_line)
            blocks = fetch_all_blocks(page_id, token)
            anchor_id = None
            for block in blocks:
                btype = block.get('type', '')
                c = block.get(btype, {})
                txt = get_rich_text(c.get('rich_text', [])).strip()
                if txt == anchor_text.strip():
                    anchor_id = block['id']
                    break
            if anchor_id:
                insert_todo_after_block(page_id, anchor_id, new_text, token)


def generate_sentence_with_gemini(word, meaning, api_key=None):
    if not api_key:
        api_key = os.environ.get('GEMINI_API_KEY', '').strip()
        
    if not api_key:
        return f"[No API Key] '{word}' means '{meaning}'. Please configure GEMINI_API_KEY.", f"예문 생성을 위해 환경 설정에서 API Key를 입력해주시거나 서버 환경변수를 설정해주세요."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = (
        f"Create a simple, clear, and practical English example sentence using the vocabulary word '{word}' "
        f"(meaning: {meaning}) for an English study app. Also provide a natural Korean translation. "
        f"Format the output strictly as a JSON object: {{\"sentence\": \"English sentence here\", \"translation\": \"Korean translation here\"}}."
    )
    
    req_body = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(url, data=json.dumps(req_body).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            text_out = res_data['candidates'][0]['content']['parts'][0]['text']
            parsed = json.loads(text_out)
            return parsed.get('sentence', '').strip(), parsed.get('translation', '').strip()
    except Exception as e:
        print("Gemini API Error:", e)
        return f"Failed to generate example for '{word}' due to API error.", f"API 오류로 예문을 생성하지 못했습니다: {str(e)}"


# ───────────────────────────────────────────────
# HTTP Server
# ───────────────────────────────────────────────

class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f'  {self.address_string()} [{fmt % args}]')

    def send_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Notion-Token')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path in ('/', '/index.html', '/monthly.html', '/planner_standalone.html'):
            # 월별 플래너 (메인)
            self._serve_html(MONTHLY_HTML, 'planner_standalone.html')

        elif path in ('/planner.html',):
            # 통합 플래너
            self._serve_html(PLANNER_HTML, 'planner.html')

        elif path == '/favicon.ico':
            # 파비콘은 HTML <link rel="icon">으로 처리되므로 여기선 204로 조용히 응답
            self.send_response(204)
            self.end_headers()

        elif path in ('/daily', '/daily/', '/daily.html', '/daily_planner_standalone.html'):
            # 일별 플래너 단독 실행
            self._serve_html(DAILY_HTML, 'daily_planner_standalone.html')

        elif path in ('/knowledge', '/knowledge/', '/knowledge.html'):
            # 오늘의 전공 지식 페이지
            self._serve_html(KNOWLEDGE_HTML, 'knowledge.html')

        elif path in ('/timer', '/timer/', '/timer.html'):
            # 문법 타임어택 타이머 페이지
            self._serve_html(TIMER_HTML, 'timer.html')

        elif path in ('/vocab', '/vocab/', '/vocab.html'):
            # 영단어 학습 웹앱 페이지
            self._serve_html(os.path.join(BASE_DIR, 'vocab.html'), 'vocab.html')

        elif path == '/api/vocab':
            # 영단어 목록 반환 API (파라미터: book, day)
            book = qs.get('book', [None])[0]
            day_str = qs.get('day', [None])[0]
            if not book or not day_str:
                return self._json(400, {'error': 'book과 day 파라미터가 필요합니다'})
            try:
                day = int(day_str)
                db_path = os.path.join(BASE_DIR, 'vocab_db.json')
                if not os.path.exists(db_path):
                    return self._json(404, {'error': 'vocab_db.json 파일이 존재하지 않습니다. 전처리를 수행하세요.'})
                with open(db_path, 'r', encoding='utf-8') as f:
                    all_words = json.load(f)
                
                filtered = [w for w in all_words if w.get('book') == book and w.get('day') == day]
                
                sentences_path = os.path.join(BASE_DIR, 'vocab_sentences.json')
                sentences_cache = {}
                if os.path.exists(sentences_path):
                    try:
                        with open(sentences_path, 'r', encoding='utf-8') as sf:
                            sentences_cache = json.load(sf)
                    except Exception:
                        pass
                
                for w in filtered:
                    word_key = w.get('word', '').lower().strip()
                    cache_item = sentences_cache.get(word_key)
                    if cache_item:
                        w['sentence'] = cache_item.get('sentence', '')
                        w['translation'] = cache_item.get('translation', '')
                    else:
                        w['sentence'] = ''
                        w['translation'] = ''
                        
                self._json(200, filtered)
            except Exception as e:
                self._json(500, {'error': str(e)})

        elif path == '/api/knowledge':
            # 오늘의 지식 데이터 반환 API
            try:
                with open(KNOWLEDGE_JSON, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._json(200, data)
            except Exception as e:
                self._json(500, {'error': str(e)})

        elif path == '/api/token':
            # 저장된 토큰 반환 (페이지 로드 시 자동 적용용)
            saved = load_saved_token()
            self._json(200, {'token': saved})

        elif path == '/api/fetch':
            token = self.headers.get('X-Notion-Token', '')
            page_id = qs.get('id', [None])[0]
            if not token or not page_id:
                return self._json(400, {'error': 'token (X-Notion-Token 헤더) 과 id 쿼리스트링이 필요합니다'})
            try:
                text = fetch_page_as_text(page_id, token)
                self._json(200, {'text': text})
            except Exception as e:
                self._json(500, {'error': str(e)})

        elif path.endswith('.css') or path.endswith('.js') or path.endswith('.json'):
            # 정적 파일 서빙 (CSS, JS, JSON)
            filename = os.path.basename(path)
            filepath = os.path.join(BASE_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    body = f.read()
                ext = path.rsplit('.', 1)[-1]
                content_types = {'css': 'text/css', 'js': 'application/javascript', 'json': 'application/json'}
                self.send_response(200)
                self.send_header('Content-Type', content_types.get(ext, 'application/octet-stream') + '; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)
            else:
                self._json(404, {'error': f'{filename} not found'})

        else:
            self._json(404, {'error': 'not found'})

    def do_POST(self):
        body = self._body()
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        token = self.headers.get('X-Notion-Token', '')

        if path == '/api/search':
            if not token:
                return self._json(400, {'error': 'X-Notion-Token 헤더 필요'})
            try:
                query = body.get('query', '')
                page_size = body.get('page_size', 5)
                data = notion_request('/search', method='POST',
                    body={'query': query, 'page_size': page_size}, token=token)
                results = []
                for r in data.get('results', []):
                    if r.get('object') != 'page':
                        continue
                    # Extract title from any property named title/Name
                    title = ''
                    for prop in r.get('properties', {}).values():
                        if prop.get('type') == 'title':
                            title = get_rich_text(prop.get('title', []))
                            break
                    results.append({
                        'id': r.get('id', ''),
                        'type': 'page',
                        'title': title,
                        'timestamp': r.get('last_edited_time', '')
                    })
                self._json(200, {'results': results})
            except Exception as e:
                self._json(500, {'error': str(e)})

        elif path == '/api/token':
            # 토큰 저장 (POST body: {"token": "secret_xxx"})
            new_token = body.get('token', '').strip()
            if not new_token:
                return self._json(400, {'error': '토큰이 비어있습니다'})
            save_token(new_token)
            self._json(200, {'ok': True})

        elif path == '/api/update':
            if not token:
                return self._json(400, {'error': 'X-Notion-Token 헤더 필요'})
            try:
                page_id = body.get('page_id', '')
                command = body.get('command', '')
                if command == 'update_content':
                    for upd in body.get('content_updates', []):
                        apply_content_update(page_id, upd.get('old_str',''), upd.get('new_str',''), token)
                self._json(200, {'ok': True})
            except Exception as e:
                self._json(500, {'error': str(e)})

        elif path == '/api/vocab/sentence':
            word = body.get('word', '').strip()
            meaning = body.get('meaning', '').strip()
            api_key = body.get('apiKey', '').strip()
            
            if not word:
                return self._json(400, {'error': 'word가 누락되었습니다'})
                
            word_key = word.lower().strip()
            sentences_path = os.path.join(BASE_DIR, 'vocab_sentences.json')
            
            sentences_cache = {}
            if os.path.exists(sentences_path):
                try:
                    with open(sentences_path, 'r', encoding='utf-8') as sf:
                        sentences_cache = json.load(sf)
                except Exception:
                    pass
            
            if word_key in sentences_cache:
                return self._json(200, sentences_cache[word_key])
                
            try:
                sentence, translation = generate_sentence_with_gemini(word, meaning, api_key)
                result_data = {
                    "sentence": sentence,
                    "translation": translation
                }
                
                if not sentence.startswith("[No API Key]") and not sentence.startswith("Failed to generate"):
                    sentences_cache[word_key] = result_data
                    with open(sentences_path, 'w', encoding='utf-8') as sf:
                        json.dump(sentences_cache, sf, ensure_ascii=False, indent=2)
                
                self._json(200, result_data)
            except Exception as e:
                self._json(500, {'error': f'서버 예문 생성 중 예외 발생: {str(e)}'})

        else:
            self._json(404, {'error': 'not found'})

    def _serve_html(self, filepath, filename):
        try:
            with open(filepath, 'rb') as f:
                body = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_cors()
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self._json(404, {'error': f'{filename} 파일을 찾을 수 없습니다. server.py와 같은 폴더에 있어야 합니다.'})

    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length) if length else b'{}'
        try:
            return json.loads(raw.decode('utf-8'))
        except Exception:
            return {}

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    print()
    print('┌─────────────────────────────────────────┐')
    print('│  스터디 플래너 로컬 서버                 │')
    print(f'│  월별: http://localhost:{PORT}            │')
    print(f'│  일별: http://localhost:{PORT}/daily      │')
    print('└─────────────────────────────────────────┘')
    print()
    print(f'  월별: {MONTHLY_HTML}')
    print(f'  일별: {DAILY_HTML}')
    print('  종료: Ctrl+C')
    print()

    srv = http.server.HTTPServer((HOST, PORT), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\n서버 종료')
# Force auto-redeploy trigger
