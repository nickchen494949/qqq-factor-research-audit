"""Restore the audited handoff without network access or third-party packages."""
from pathlib import Path, PurePosixPath
import argparse,hashlib,json,lzma,tarfile,tempfile,shutil
R=Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def safe(base,name):
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe path: '+name)
    dst=(base/Path(*p.parts)).resolve()
    if not dst.is_relative_to(base.resolve()):raise ValueError('Path outside output')
    return dst
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='workspace');ap.add_argument('--include-archives',action='store_true');ap.add_argument('--verify-only',action='store_true');args=ap.parse_args()
    manifest=json.loads((R/'FILE_MANIFEST.json').read_text());pack=json.loads((R/'PACK.json').read_text())
    with tempfile.TemporaryDirectory(prefix='eps-handoff-') as tmp:
        t=Path(tmp);archive=t/'corpus.tar.xz';h=hashlib.sha256()
        with archive.open('wb') as out:
            for e in pack['parts']:
                p=safe(R,e['path'])
                if p.stat().st_size!=e['bytes'] or sha(p)!=e['sha256']:raise ValueError('Invalid part '+e['path'])
                b=p.read_bytes();out.write(b);h.update(b)
        if h.hexdigest()!=pack['sha256']:raise ValueError('Invalid complete archive')
        objects=t/'objects';objects.mkdir()
        with tarfile.open(archive,'r:xz') as z:
            for m in z:
                if not m.isfile() or not m.name.startswith('objects/'):raise ValueError('Unexpected archive entry')
                dst=safe(t,m.name);dst.parent.mkdir(parents=True,exist_ok=True)
                with z.extractfile(m) as src,dst.open('wb') as out:shutil.copyfileobj(src,out)
                if sha(dst)!=dst.name:raise ValueError('Object checksum mismatch')
        dest=Path(args.output).resolve();count=0
        for e in manifest['files']:
            if e['kind']=='archive_member' and not args.include_archives:continue
            src=objects/e['sha256']
            if not src.is_file() or src.stat().st_size!=e['bytes']:raise ValueError('Missing object '+e['path'])
            if not args.verify_only:
                dst=safe(dest,e['path']);dst.parent.mkdir(parents=True,exist_ok=True)
                if dst.exists() and sha(dst)!=e['sha256']:raise FileExistsError('Refusing overwrite: '+str(dst))
                if not dst.exists():shutil.copyfile(src,dst)
            count+=1
        print('Verified',count,'file paths;', 'no files written' if args.verify_only else 'restored to '+str(dest))
if __name__=='__main__':main()
