import os
import re
import json
import time
import urllib.request
import urllib.parse

PO_PATH = 'locale/ar/LC_MESSAGES/django.po'
CACHE_PATH = 'locale/ar/LC_MESSAGES/translation_cache.json'

def load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def translate_text(text, sl='en', tl='ar'):
    if not text.strip():
        return text

    # Protect placeholders
    # 1. Python curly braces {user.username}
    # 2. Django / Python old-style formatting %(name)s, %s, %d
    # 3. Double percent %%
    placeholders = []
    
    # We will find matches for:
    # - {anything without braces}
    # - %\([^)]+\)[s|d]
    # - %[s|d]
    # - %%
    pattern = re.compile(r'(\{[^{}]+\}|%\([^)]+\)[s|d]|%[s|d]|%%)')
    
    parts = pattern.split(text)
    protected_parts = []
    for part in parts:
        if pattern.match(part):
            placeholder_id = f"__P{len(placeholders)}__"
            placeholders.append((placeholder_id, part))
            protected_parts.append(placeholder_id)
        else:
            protected_parts.append(part)
            
    protected_text = "".join(protected_parts)
    
    # Call Google Translate API
    url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=' + sl + '&tl=' + tl + '&dt=t&q=' + urllib.parse.quote(protected_text)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    translated_text = ""
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res = json.loads(response.read().decode('utf-8'))
                # Google Translate returns a list of segments
                translated_segments = []
                for segment in res[0]:
                    if segment[0]:
                        translated_segments.append(segment[0])
                translated_text = "".join(translated_segments)
                break
        except Exception as e:
            print(f"Error translating '{text}' (attempt {attempt+1}): {e}")
            time.sleep(2)
    else:
        # If all attempts fail, return original
        return ""

    # Restore placeholders
    # Google Translate sometimes inserts spaces around our placeholders (e.g. " __P0__ " or " __ P0 __ ")
    # Let's normalize the placeholder occurrences before replacing them.
    for placeholder_id, original in placeholders:
        # Match placeholder even if spaces were inserted inside it, e.g. __ P0 __
        # but usually it's just __P0__ with outer spaces.
        # Let's replace any variant of __P{i}__ with the original placeholder.
        # We need a regex that matches the placeholder with optional spaces before/after/inside it.
        num = placeholder_id.strip('_P')
        regex_pattern = re.compile(rf'\s*__\s*P\s*{num}\s*__\s*')
        translated_text = regex_pattern.sub(original, translated_text)
        
    return translated_text

def parse_po(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    entries = []
    current_entry = {
        'comments': [],
        'msgid_lines': [],
        'msgstr_lines': [],
        'state': None,
        'line_no': 0
    }
    
    for idx, line in enumerate(lines):
        line_strip = line.strip()
        if line.startswith('#'):
            if current_entry['state'] == 'msgstr':
                entries.append(current_entry)
                current_entry = {'comments': [], 'msgid_lines': [], 'msgstr_lines': [], 'state': None, 'line_no': idx}
            current_entry['comments'].append(line)
        elif line.startswith('msgid '):
            if current_entry['state'] == 'msgstr':
                entries.append(current_entry)
                current_entry = {'comments': [], 'msgid_lines': [], 'msgstr_lines': [], 'state': None, 'line_no': idx}
            current_entry['state'] = 'msgid'
            val = line[6:].strip()
            if val.startswith('\"') and val.endswith('\"'):
                val = val[1:-1]
            current_entry['msgid_lines'].append(val)
        elif line.startswith('msgstr '):
            current_entry['state'] = 'msgstr'
            val = line[7:].strip()
            if val.startswith('\"') and val.endswith('\"'):
                val = val[1:-1]
            current_entry['msgstr_lines'].append(val)
        elif line_strip.startswith('\"') and line_strip.endswith('\"'):
            val = line_strip[1:-1]
            if current_entry['state'] == 'msgid':
                current_entry['msgid_lines'].append(val)
            elif current_entry['state'] == 'msgstr':
                current_entry['msgstr_lines'].append(val)
        elif not line_strip:
            if current_entry['state'] == 'msgstr':
                entries.append(current_entry)
                current_entry = {'comments': [], 'msgid_lines': [], 'msgstr_lines': [], 'state': None, 'line_no': idx}
            else:
                # empty line outside msgstr state (could be headers, trailing newlines)
                pass
                
    if current_entry['state'] == 'msgstr':
        entries.append(current_entry)
        
    return entries

def write_po(path, entries):
    with open(path, 'w', encoding='utf-8') as f:
        # Check if there are any comments at the very beginning before any entry
        # Typically entries contain everything.
        for idx, entry in enumerate(entries):
            for comment in entry['comments']:
                f.write(comment)
            
            # Write msgid
            if len(entry['msgid_lines']) == 1:
                f.write(f'msgid "{entry["msgid_lines"][0]}"\n')
            else:
                f.write('msgid ""\n')
                for line in entry['msgid_lines']:
                    f.write(f'"{line}"\n')
                    
            # Write msgstr
            if len(entry['msgstr_lines']) == 1:
                f.write(f'msgstr "{entry["msgstr_lines"][0]}"\n')
            else:
                f.write('msgstr ""\n')
                for line in entry['msgstr_lines']:
                    f.write(f'"{line}"\n')
            f.write('\n')

def main():
    entries = parse_po(PO_PATH)
    cache = load_cache()
    
    translated_count = 0
    skipped_count = 0
    new_translations = 0
    
    # First entry is usually the header msgid "" / msgstr ""
    # We should skip it
    for entry in entries:
        msgid = "".join(entry['msgid_lines'])
        msgstr = "".join(entry['msgstr_lines'])
        
        if not msgid:
            # Header
            continue
            
        if msgstr.strip():
            # Already has a translation in the PO file itself
            skipped_count += 1
            continue
            
        if msgid in cache:
            # Found in translation cache
            entry['msgstr_lines'] = [cache[msgid]]
            translated_count += 1
            continue
            
        # Needs translation
        print(f"Translating: {repr(msgid)}")
        ar_trans = translate_text(msgid)
        if ar_trans:
            # Unescape some chars if needed or keep raw
            entry['msgstr_lines'] = [ar_trans]
            cache[msgid] = ar_trans
            new_translations += 1
            translated_count += 1
            
            # Save cache every 10 new translations
            if new_translations % 10 == 0:
                save_cache(cache)
                
            time.sleep(0.15) # rate limit prevention
        else:
            print(f"Warning: Failed to translate '{msgid}'")
            
    save_cache(cache)
    write_po(PO_PATH, entries)
    print(f"Done! Translated {translated_count} messages (new: {new_translations}), skipped {skipped_count}.")

if __name__ == '__main__':
    main()
