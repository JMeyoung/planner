#!/usr/bin/env python3
import pypdf
import re
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "vocab_db.json")

def parse_v101_v201(pdf_path, book_name):
    print(f"[{book_name}] Parsing PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        return []
        
    reader = pypdf.PdfReader(pdf_path)
    pages_text = []
    page_days = []
    current_day = 1
    
    for idx, page in enumerate(reader.pages):
        text = page.extract_text()
        pages_text.append(text)
        
        # Search for Day header (e.g. "DAY 1", "DAY 01")
        day_match = re.search(r'DAY\s*(\d+)', text, re.IGNORECASE)
        if day_match:
            current_day = int(day_match.group(1))
        page_days.append(current_day)
        
    combined_text = ""
    for idx, text in enumerate(pages_text):
        combined_text += f"\n---PAGE_{idx+1}_DAY_{page_days[idx]}---\n" + text
        
    # Split by \n[number]\n
    pattern = r'\n(\d+)\n'
    matches = list(re.finditer(pattern, combined_text))
    
    words = []
    for i in range(len(matches)):
        start_idx = matches[i].end()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(combined_text)
        
        word_num = int(matches[i].group(1))
        block = combined_text[start_idx:end_idx].strip()
        
        # Find Day and Page of this word
        day = 1
        page_num = 1
        prefix = combined_text[:matches[i].start()]
        page_day_matches = list(re.finditer(r'---PAGE_(\d+)_DAY_(\d+)---', prefix))
        if page_day_matches:
            last_match = page_day_matches[-1]
            page_num = int(last_match.group(1))
            day = int(last_match.group(2))
            
        words.append({
            "num": word_num,
            "day": day,
            "page": page_num,
            "raw_block": block
        })
        
    parsed_words = []
    for w in words:
        lines = [line.strip() for line in w["raw_block"].split('\n') if line.strip()]
        lines = [line for line in lines if not line.startswith("---PAGE_")]
        # Remove common PDF headers/footers
        lines = [line for line in lines if not ("LOGIC TREE" in line or "필수 영단어" in line or "단어장" in line or re.match(r'^\d+\s*/\s*/?\d+$', line))]
        
        if len(lines) < 2:
            continue
            
        english = lines[0]
        pronunciation = ""
        tip = ""
        meaning = ""
        
        if lines[1].startswith('[') and lines[1].endswith(']'):
            pronunciation = lines[1]
            remaining = lines[2:]
        else:
            remaining = lines[1:]
            
        if len(remaining) == 1:
            meaning = remaining[0]
        elif len(remaining) >= 2:
            tip = remaining[0]
            meaning = "; ".join(remaining[1:])
            
        parsed_words.append({
            "book": book_name,
            "num": w["num"],
            "day": w["day"],
            "word": english,
            "pron": pronunciation,
            "tip": tip,
            "meaning": meaning
        })
        
    print(f"[{book_name}] Extracted {len(parsed_words)} words successfully.")
    return parsed_words

def parse_v301(pdf_path, book_name="V301"):
    print(f"[{book_name}] Parsing PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        return []
        
    reader = pypdf.PdfReader(pdf_path)
    pages_text = []
    for idx, page in enumerate(reader.pages):
        pages_text.append(page.extract_text())
        
    combined_text = ""
    for idx, text in enumerate(pages_text):
        combined_text += f"\n---PAGE_{idx+1}---\n" + text
        
    # Split by \n[number]\n
    pattern = r'\n(\d+)\n'
    matches = list(re.finditer(pattern, combined_text))
    
    parsed_words = []
    for i in range(len(matches)):
        start_idx = matches[i].end()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(combined_text)
        
        word_num = int(matches[i].group(1))
        block = combined_text[start_idx:end_idx].strip()
        
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        lines = [line for line in lines if not line.startswith("---PAGE_") and not "V301 어휘" in line and not re.match(r'^\d+\s*/\s*/?\d+$', line)]
        
        if len(lines) < 2:
            continue
            
        # V301 structure: theme/category, word, meaning
        # Block #1: ['C1 [01. 유쾌/불쾌] 매혹시키다', 'attract', '마음을 끌다']
        # If len(lines) == 2, then we have word, meaning
        if len(lines) == 2:
            theme = "V301 필수 어휘"
            english = lines[0]
            meaning = lines[1]
        else:
            theme = lines[0]
            english = lines[1]
            meaning = "; ".join(lines[2:])
            
        # V301 has no pronunciation, so set empty. We use theme as the hint tip.
        # Assign simulated Day: 100 words per Day
        simulated_day = (word_num - 1) // 100 + 1
        
        parsed_words.append({
            "book": book_name,
            "num": word_num,
            "day": simulated_day,
            "word": english,
            "pron": "",
            "tip": theme,
            "meaning": meaning
        })
        
    print(f"[{book_name}] Extracted {len(parsed_words)} words successfully.")
    return parsed_words

def main():
    v101_path = "/Users/jaeyoung/Desktop/영단어장/어휘 V101.pdf"
    v201_path = "/Users/jaeyoung/Desktop/영단어장/V201/V201_FULL.pdf"
    v301_path = "/Users/jaeyoung/Desktop/V301 단어장 최종본.pdf"
    
    all_words = []
    all_words.extend(parse_v101_v201(v101_path, "V101"))
    all_words.extend(parse_v101_v201(v201_path, "V201"))
    all_words.extend(parse_v301(v301_path, "V301"))
    
    print(f"Total compiled words: {len(all_words)}")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_words, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
