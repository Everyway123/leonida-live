"""Publish licensed snapshots and queue public leads. Verification is a separate review."""
import datetime as dt
import hashlib
import json
import pathlib
import re
import urllib.request

from urllib.parse import urljoin, urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / 'public/data'
STATUS = DATA / 'source-status.json'
QUEUE = ROOT / 'review/candidates.json'
REPO = 'gta6map/gta6map.github.io'
NEWS = 'https://graph.rockstargames.com/'
REDDIT = 'https://www.reddit.com/r/GTA6/new.json?limit=100'
LOOT = re.compile(r'\b(safehouses?|safes?|money|cash|hidden packages?|treasures?|robber(?:y|ies)|vehicles?|stash(?:es)?)\b', re.I)
GAME = re.compile(r'\b(?:GTA|Grand Theft Auto)\s*(?:VI|6)\b', re.I)


def read(url, limit=4_000_000):
    req = urllib.request.Request(url, headers={'User-Agent': 'LeonidaLive/1.1 (public map source monitor)'})
    with urllib.request.urlopen(req, timeout=15) as response:
        body = response.read(limit + 1)
    if len(body) > limit:
        raise ValueError('response exceeds size limit')
    return body


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


def snapshot():
    rev = json.loads(read(f'https://api.github.com/repos/{REPO}/commits/main'))['sha']
    if not re.fullmatch('[0-9a-f]{40}', rev):
        raise ValueError('invalid revision')
    base = f'https://raw.githubusercontent.com/{REPO}/{rev}'
    license_text = read(base + '/readme.md').decode().lower()
    if not all(s in license_text for s in ('public domain', 'landmark data', 'map tiles')):
        raise ValueError('source license needs review')
    landmarks = read(base + '/data/landmarks.json')
    rows = json.loads(landmarks)
    if not rows or not all(isinstance(r,list) and len(r)>=8 and isinstance(r[2],list) and len(r[2]) in (0,2) and all(type(v) in (float,int) and abs(v)<=16384 for v in r[2]) for r in rows):
        raise ValueError('landmark coordinate schema changed')
    tile = read(base + '/tiles/dupzor,51/0/0,0,0.jpg')
    if not tile.startswith(b'\xff\xd8') or not tile.endswith(b'\xff\xd9'):
        raise ValueError('invalid overview')
    (DATA/'landmarks.json').write_bytes(landmarks)
    (DATA.parent/'assets/overview.jpg').write_bytes(tile)
    return {'revision':rev,'landmarks':sum(bool(r[2]) for r in rows),'landmarks_sha256':hashlib.sha256(landmarks).hexdigest(),'overview_sha256':hashlib.sha256(tile).hexdigest()}, []


def reddit():
    posts=json.loads(read(REDDIT))['data']['children']
    if not isinstance(posts,list):
        raise ValueError('invalid feed')
    leads=[]
    for post in posts:
        p=post['data']
        if p.get('subreddit','').lower()=='gta6' and LOOT.search(p['title']) and re.fullmatch(r'/r/GTA6/comments/[\w/-]+',p['permalink'],re.I):
            leads.append((p['title'],'https://www.reddit.com'+p['permalink']))
    return {}, leads


def news():
    query = 'query { posts(page: 1, locale: "en_us", limit: 50) { results { title url primary_tags { name } secondary_tags { name } } } }'
    req = urllib.request.Request(NEWS, data=json.dumps({'query':query}).encode(),
                                 headers={'Content-Type':'application/json','User-Agent':'LeonidaLive/1.1'})
    with urllib.request.urlopen(req,timeout=15) as response:
        posts=json.load(response)['data']['posts']['results']
    if not posts:
        raise ValueError('empty Newswire response')
    leads=[]
    for post in posts:
        title=post['title']
        tags=' '.join(tag['name'] for key in ('primary_tags','secondary_tags') for tag in (post.get(key) or []))
        url=urljoin('https://www.rockstargames.com',post['url'])
        if GAME.search(title+' '+tags) and LOOT.search(title) and urlsplit(url).hostname=='www.rockstargames.com' and url.startswith('https://'):
            leads.append((title,url))
    return {}, leads


def main():
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    old=json.loads(STATUS.read_text())
    states=dict(old.get('sources',{}))
    queue=json.loads(QUEUE.read_text())
    urls={row['url'] for row in queue}
    for key, action in [('gta6map',snapshot),('rockstar_newswire',news),('reddit_gta6',reddit)]:
        previous=states.get(key,{})
        try:
            details,leads=action()
            row={**previous,**details,'health':'ok'}
            for title,url in leads:
                if url not in urls:
                    queue.append(dict(title=title,url=url,source=key,retrieved_at=now,status='candidate'))
                    urls.add(url)
        except Exception as err:
            print(key,type(err).__name__,str(err)[:120])
            row={**previous,'health':'unavailable'}
        if row!=previous:
            row['changed_at']=now
            if row['health']=='ok':
                row['last_success_at_change']=now
        states[key]=row
        print(now,key,row['health'])
    if states!=old.get('sources'):
        save(STATUS,{'sources':states})
    save(QUEUE,queue)
    return sum(row['health']=='ok' for row in states.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
