"""
Test metadata generator with platform-specific content
"""
import sys
import io

# Fix Windows console encoding for emojis
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import metadata_generator as mg

print('=' * 70)
print('  METADATA GENERATOR TEST - Platform-Specific Content')
print('=' * 70)

# Test data
theme = 'FOOTBALL'
rival1 = 'Barcelona'
rival2 = 'Real Madrid'
champion = 'Barcelona'
scores = {'Barcelona': 3, 'Real Madrid': 2}
duration = 75.5

print('\nGenerating metadata for BOTH platforms...\n')

metadata = mg.generate(theme, rival1, rival2, champion, scores, duration)

print('\n' + '=' * 70)
print('YOUTUBE SHORTS METADATA')
print('=' * 70)
yt = metadata['youtube']
print(f'Title ({len(yt["title"])} chars):')
print(f'  {yt["title"]}\n')

desc_preview = yt['description'][:300] + '...' if len(yt['description']) > 300 else yt['description']
print(f'Description ({len(yt["description"])} chars):')
print(f'  {desc_preview}\n')

print(f'Tags ({len(yt["tags"])} items):')
print(f'  {", ".join(yt["tags"][:10])}...\n')

print('=' * 70)
print('TIKTOK METADATA')
print('=' * 70)
tt = metadata['tiktok']
print(f'Caption ({len(tt["caption"])} chars):')
print(f'  {tt["caption"]}\n')

print(f'Hashtags ({len(tt["hashtags"])} items):')
print(f'  {" ".join(tt["hashtags"])}\n')

print('=' * 70)
print('VALIDATION')
print('=' * 70)

# Check limits
yt_title_ok = len(yt['title']) <= 100
yt_desc_ok = len(yt['description']) <= 5000
yt_tags_ok = len(yt['tags']) >= 10 and len(yt['tags']) <= 18

tt_caption_ok = len(tt['caption']) <= 2200
tt_hashtags_ok = len(tt['hashtags']) >= 3 and len(tt['hashtags']) <= 5

status_ok = '[OK]'
status_fail = '[FAIL]'

print(f'YouTube Title <= 100 chars: {status_ok if yt_title_ok else status_fail} ({len(yt["title"])}/100)')
print(f'YouTube Description <= 5000 chars: {status_ok if yt_desc_ok else status_fail} ({len(yt["description"])}/5000)')
print(f'YouTube Tags 10-18 items: {status_ok if yt_tags_ok else status_fail} ({len(yt["tags"])} tags)')
print(f'TikTok Caption <= 2200 chars: {status_ok if tt_caption_ok else status_fail} ({len(tt["caption"])}/2200)')
print(f'TikTok Hashtags 3-5 items: {status_ok if tt_hashtags_ok else status_fail} ({len(tt["hashtags"])} hashtags)')

all_ok = all([yt_title_ok, yt_desc_ok, yt_tags_ok, tt_caption_ok, tt_hashtags_ok])
print('\n' + '=' * 70)
if all_ok:
    print('  ALL TESTS PASSED')
else:
    print('  SOME TESTS FAILED')
print('=' * 70)
