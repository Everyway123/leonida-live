import datetime as dt
import json
import pathlib
from urllib.parse import urlsplit

data=pathlib.Path(__file__).resolve().parents[1]/'public/data'
seen=set()
pins=json.loads((data/'verified-pins.json').read_text())
assert isinstance(pins,list)
for pin in pins:
    assert pin['id'] and pin['id'] not in seen
    seen.add(pin['id'])
    assert pin['category'] in {'safehouse','safe','cash','package','treasure','robbery','vehicle'}
    assert pin['verified'] is True and pin['name'].strip()
    assert pin['reviewer'].strip() and pin['coordinate_evidence'].strip()
    assert pin['coordinate_system']=='gta6map-32768'
    assert all(type(pin[k]) in (float,int) and abs(pin[k])<=16384 for k in ('x','y'))
    url=urlsplit(pin['evidence_url'])
    assert url.scheme=='https' and url.hostname and not url.username and not url.password
    assert dt.datetime.fromisoformat(pin['checked_at']).utcoffset() is not None
print(f'{len(pins)} verified pins')
