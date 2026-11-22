"""Read-only helpers for validating a checked-out Stepik course export."""
import html
import json
import re
from functools import lru_cache
from pathlib import Path

WORK = Path(__file__).resolve().parent


def _find_root():
    for start in (WORK, Path.cwd().resolve()):
        for candidate in (start, *start.parents):
            if (candidate / 'courses/86957/course.json').is_file():
                return candidate
    raise RuntimeError(
        'Place the validator inside the course repository or run it from the '
        'repository root containing courses/86957/course.json.'
    )


ROOT = _find_root()
PATHS = {
    int(path.name.split('_')[1]): path
    for path in (ROOT / 'courses/86957/steps').glob('*/*.step')
}


@lru_cache(maxsize=None)
def block(step_id):
    return json.loads(PATHS[step_id].read_text(encoding='utf-8'))['block']


def codes(step_id):
    return [
        html.unescape(code)
        for code in re.findall(
            r'<pre><code[^>]*>(.*?)</code></pre>', block(step_id)['text'], re.S
        )
    ]
