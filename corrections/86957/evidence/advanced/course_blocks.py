"""Read exact code blocks from the course snapshot or corrected copies."""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[4]
LESSONS = [770596, 770597, 877082, 877081, 877083, 897987, 877084,
           853532, 853534, 853535, 853536, 853537, 973837, 973842, 977027,
           853539, 853540, 853541, 973829, 973831, 973816, 973825, 973826]


def source_path(step_id):
    found = list((ROOT / 'courses/86957/steps').glob(f'*/*_{step_id}_*.step'))
    assert len(found) == 1, (step_id, found)
    return found[0]


def step(step_id, corrected=False):
    original = source_path(step_id)
    path = ROOT / 'corrections/86957/steps' / original.parent.name / original.name
    if not corrected or not path.exists():
        path = original
    return json.loads(path.read_text())


def blocks(step_id, corrected=False):
    text = step(step_id, corrected)['block']['text']
    return [html.unescape(re.sub(r'<[^>]+>', '', m.group(1)))
            for m in re.finditer(r'<pre[^>]*>(.*?)</pre>', text, re.S)]


def rbt(corrected=False):
    return (blocks(3570303, corrected)[1] + '\n' +
            '\n'.join(blocks(3570304, corrected)) + '\n' +
            '\n'.join(blocks(3570333, corrected)))
