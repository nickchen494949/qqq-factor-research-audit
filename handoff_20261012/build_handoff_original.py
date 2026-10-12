from pathlib import Path
import hashlib,json,zipfile,tarfile,lzma,io,collections,shutil,re
B=Path(__file__).resolve().parent;R=B/'github_handoff_20261012';O=B/'handoff_objects';O.mkdir(exist_ok=True)
roots=['economic_pool','qqq_smh_top1','green5_test','relative_green','monthly_consistency','absolute_momentum','absolute_all','top135','top135_absolute','earnings_trial','quality_trial','combined_quality','eps_growth']
files=[];archives=[];objects={}
def add(path,b,kind,origin):
    h=hashlib.sha256(b).hexdigest();p=O/h
    if h not in objects:p.write_bytes(b);objects[h]=len(b)
    files.append(dict(path=path,sha256=h,bytes=len(b),kind=kind,origin=origin))
for root in roots:
    for p in sorted((B/root).rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':add(p.relative_to(B).as_posix(),p.read_bytes(),'workspace',root)
for p in sorted(B.glob('*.html')):add(p.name,p.read_bytes(),'workspace','root_report')
for p in sorted(list(B.glob('*.zip'))+list((B/'restore').glob('*.zip'))):
    meta=dict(path=p.relative_to(B).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    if zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z:
            members=[i for i in z.infolist() if not i.is_dir()];meta.update(valid_zip=True,members=len(members))
            for i in members:
                add('historical_archives/'+p.stem+'/'+i.filename,z.read(i),'archive_member',meta['path'])
    else:
        meta.update(valid_zip=False,issue='ZIP central directory unreadable; original bytes retained; use expanded workspace')
        add('quarantine/'+p.name,p.read_bytes(),'invalid_archive',meta['path'])
    archives.append(meta)
manifest=dict(format='sha256-content-store-v1',roots=roots,files=files,original_archives=archives)
(R/'FILE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
integrity=dict(file_paths=len(files),unique_objects=len(objects),logical_bytes=sum(x['bytes'] for x in files),unique_bytes=sum(objects.values()),archive_count=len(archives),invalid_archives=[a for a in archives if not a['valid_zip']],scope='Research workspace plus all valid archive member contents and invalid archive bytes; excludes transport helpers and transient duplicate check folders',checks={'credential_scan':'No credential patterns confirmed. Two SEC plain-text URLs containing the word risk matched an overly broad sk- pattern and were manually classified as false positives.','eps_frozen_replay':'Monthly EPS coverage reproduced from frozen events; NOT an EPS return backtest.','data_truth':'No claim of complete PIT data or independent market data verification.'})
(R/'INTEGRITY.json').write_text(json.dumps(integrity,ensure_ascii=False,indent=2))
print('Objects prepared',integrity['file_paths'],integrity['unique_objects'],flush=True)
archive=B/'handoff_corpus.tar.xz'
with lzma.open(archive,'wb',preset=6) as out:
    with tarfile.open(fileobj=out,mode='w|') as z:
        for h in sorted(objects):
            b=(O/h).read_bytes();info=tarfile.TarInfo('objects/'+h);info.size=len(b);info.mode=0o644;info.mtime=0;z.addfile(info,io.BytesIO(b))
parts=R/'parts';parts.mkdir(exist_ok=True);entries=[]
with archive.open('rb') as f:
    n=0
    while b:=f.read(512*1024):
        name=f'parts/corpus.part{n:04d}';(R/name).write_bytes(b);entries.append(dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),git_blob_sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()));n+=1
(R/'PACK.json').write_text(json.dumps(dict(bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),parts=entries),indent=2))
print('Pack finished',archive.stat().st_size,'bytes',len(entries),'parts',flush=True)
