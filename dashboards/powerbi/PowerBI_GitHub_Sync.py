"""Dashboard-only, data-free Power BI project sync to the DataNexus GitHub repo."""
import argparse,hashlib,json,os,re,shutil,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

URL='https://github.com/shah-hussain-bangash/DataNexus-AI-Enterprise.git'
PREFIX='dashboards/powerbi'
NAME='DataNexus_EndToEnd'
REPO_ID='shah-hussain-bangash/DataNexus-AI-Enterprise'
IGNORED={'.pbi','.git','node_modules','__pycache__'}
README='''# DataNexus Power BI overview

Six-page editable Power BI project: platform overview, sources and telemetry,
pipeline assurance, taxi executive view, daily performance, and taxi quality.

Open `DataNexus_EndToEnd.pbip` in Power BI Desktop. Set the `DataNexusRoot` and
`PowerBIDataRoot` Power Query parameters to your local folders, then refresh.
DataNexusRoot defaults to `C:\\DataNexus-AI-Enterprise`. PowerBIDataRoot defaults
to `C:\\DataNexus-PowerBI-Local`. Neither folder nor any imported data is uploaded.

The taxi queries use the repository's local January 2024 reporting snapshot.
Run `Update_DataNexus_Overview.py --repo <local-repository> --output
<PowerBIDataRoot>/DataNexus_Overview_Data.json` before refreshing platform evidence.
Existing validated taxi artifacts are prerequisites. The exporter is read-only.

## Save-to-GitHub on the authoring computer

Save changes in the `.pbip` project, not the separate `.pbix` snapshot.
`PowerBI_GitHub_Sync.py --source <authoring-folder> --state <local-state-folder>
--watch` waits for a stable save, copies only allowlisted project definitions,
replaces computer-specific data paths with parameters, then commits and pushes
this folder through an isolated checkout using existing Git credentials.

The watcher never stages other DataNexus changes, uploads credentials or data,
or force-pushes. Authentication/network/conflict failures retain pending changes
and are recorded in the local sync status. Start it again after resolving errors.
Automatic uploads require the authoring computer to be running and online.

## Deliberately local

PBIX/PBIT files, `.pbi` caches, local settings, JSON evidence snapshots, CSV,
SQLite and Parquet data, credentials and logs are excluded. This source project
can open without its data cache; refresh requires your local datasets.

Stored MTA observations and the aviation sample are historical evidence.
Planned sources and unverified runtime services are labelled. Reporting integrity
does not imply production approval. No live provider collection or cloud Power BI
publication is configured by this folder.
'''
IGNORE='''**/.pbi/
*.pbix
*.pbit
*.abf
*.pbipcache
*.sqlite*
*.parquet
*.csv
*.env
*.log
DataNexus_Overview_Data.json
reporting_preview.json
sync-status.json
'''

def prepare(source):
    files={}
    entry=source/(NAME+'.pbip')
    if not entry.is_file():raise ValueError('Save the DataNexus_EndToEnd PBIP project first')
    candidates=[entry]
    for suffix in ('.Report','.SemanticModel'):
        folder=source/(NAME+suffix)
        candidates += [p for p in folder.rglob('*') if p.is_file() and not any(x in IGNORED for x in p.relative_to(source).parts) and (p.suffix in ('.json','.tmdl','.pbir','.pbism') or p.name=='.platform')]
    root_strings=[str(Path.home()/'DataNexus-AI-Enterprise'),str(source)]
    for p in candidates:
        if p.stat().st_size>2_000_000:raise ValueError('Unexpected large project definition: '+p.name)
        text=p.read_text(encoding='utf-8-sig')
        if not text.strip():raise ValueError('Incomplete save: '+p.name)
        if p.suffix in ('.json','.pbip','.pbir','.pbism') or p.name=='.platform':json.loads(text)
        if p.suffix=='.tmdl':
            # Use shared query parameters in the public source, keeping the author's
            # local project unchanged. Never publish personal Windows paths.
            for s,param in zip(root_strings,('DataNexusRoot','PowerBIDataRoot')):
                text=text.replace('File.Contents("'+s+'\\','File.Contents('+param+' & "\\')
            if re.search(r'C:\\Users\\',text,re.I):raise ValueError('Unparameterized personal path in '+p.name)
        if p.suffix=='.json' and p.name=='visual.json':
            d=json.loads(text)
            # Replace snapshot-specific prose with reusable pipeline descriptions.
            def clean(v):
                if isinstance(v,str):
                    v=re.sub(r'\b[\d,]+ distinct rows quarantined\b','Rejected rows retained separately',v)
                    v=re.sub(r'\b\d+ in-month dates; \d+ outside month\b','Pickup dates retain their original month boundaries',v)
                elif isinstance(v,list):v=[clean(x) for x in v]
                elif isinstance(v,dict):v={k:clean(x) for k,x in v.items()}
                return v
            text=json.dumps(clean(d),indent=2,ensure_ascii=True)+'\n'
        if re.search(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{30,})',text):raise ValueError('Potential credential in '+p.name)
        files[p.relative_to(source).as_posix()]=text
    files[NAME+'.SemanticModel/definition/expressions.tmdl']='''expression DataNexusRoot = "C:\\DataNexus-AI-Enterprise" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
    lineageTag: d87c79b5-c4b5-4f1a-b1ca-41e02fd82ba8

expression PowerBIDataRoot = "C:\\DataNexus-PowerBI-Local" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
    lineageTag: 3c8f0985-af67-459b-a2dc-3ab10f1b78da
'''.replace('    lineageTag:','\tlineageTag:')
    model=NAME+'.SemanticModel/definition/model.tmdl'
    files[model]+='\nref expression DataNexusRoot\nref expression PowerBIDataRoot\n'
    files['README.md']=README;files['.gitignore']=IGNORE
    files['Update_DataNexus_Overview.py']=(source/'Update_DataNexus_Overview.py').read_text(encoding='utf-8')
    files['PowerBI_GitHub_Sync.py']=Path(__file__).read_text(encoding='utf-8')
    return files

def digest(files):
    h=hashlib.sha256()
    for p,t in sorted(files.items()):h.update(p.encode());h.update(b'\0');h.update(t.encode());h.update(b'\0')
    return h.hexdigest()

def git(folder,*args):
    env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never')
    p=subprocess.run(['git','-c','credential.interactive=never','-C',str(folder),*args],capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=90,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if p.returncode:raise RuntimeError('git '+args[0]+': '+(p.stderr or p.stdout).strip())
    return p.stdout.strip()

def status(state_dir,**values):
    state_dir.mkdir(parents=True,exist_ok=True)
    d={'checked_utc':datetime.now(timezone.utc).isoformat(),'process_id':os.getpid(),**values}
    (state_dir/'sync-status.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')

def sync(files,state):
    checkout=state/'checkout'
    if not (checkout/'.git').is_dir():
        state.mkdir(parents=True,exist_ok=True)
        git(state,'clone','--single-branch','--branch','main',URL,str(checkout))
    if git(checkout,'remote','get-url','origin')!=URL:raise ValueError('Unexpected Git remote')
    if git(checkout,'branch','--show-current')!='main':raise ValueError('Unexpected sync branch')
    # Only this helper writes the isolated checkout. Never touch the main user checkout.
    git(checkout,'fetch','origin','main')
    # Retry a previously rejected ordinary push before creating another commit.
    ahead=int(git(checkout,'rev-list','--count','origin/main..HEAD'))
    if ahead:
        behind=int(git(checkout,'rev-list','--count','HEAD..origin/main'))
        if behind:
            try:git(checkout,'rebase','origin/main')
            except Exception:
                try:git(checkout,'rebase','--abort')
                except Exception:pass
                raise RuntimeError('Remote dashboard conflict; pending local commit preserved for review')
        git(checkout,'push','origin','HEAD:main')
    git(checkout,'merge','--ff-only','origin/main')
    target=(checkout/PREFIX).resolve()
    if not target.is_relative_to(checkout.resolve()):raise ValueError('Invalid dashboard destination')
    tracked=git(checkout,'ls-files','--',PREFIX).splitlines()
    expected={PREFIX+'/'+p for p in files}
    for rel in tracked:
        path=(checkout/rel).resolve()
        if rel not in expected:
            if not path.is_relative_to(target):raise ValueError('Deletion outside dashboard scope')
            if path.exists():path.unlink()
    for rel,text in files.items():
        path=(target/rel).resolve()
        if not path.is_relative_to(target):raise ValueError('Invalid project path')
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists() or path.read_text(encoding='utf-8')!=text:path.write_text(text,encoding='utf-8')
    git(checkout,'add','--',PREFIX)
    staged=git(checkout,'diff','--cached','--name-only').splitlines()
    if any(not p.startswith(PREFIX+'/') for p in staged):raise ValueError('Staging scope exceeded')
    if staged:
        # Reuse the user's existing commit identity; do not store credentials.
        git(checkout,'commit','-m','feat(powerbi): sync saved dashboard project')
        git(checkout,'push','origin','HEAD:main')
    sha=git(checkout,'rev-parse','HEAD')
    status(state,state='synced',commit=sha,repository=REPO_ID,scope=PREFIX,files=len(files))
    return sha

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--state',type=Path,default=Path(__file__).resolve().parent.parent/'work/powerbi-github-sync')
    p.add_argument('--prepare',type=Path)
    p.add_argument('--watch',action='store_true')
    p.add_argument('--once',action='store_true')
    p.add_argument('--start',action='store_true')
    p.add_argument('--stop',action='store_true')
    args=p.parse_args();source=args.source.resolve();state=args.state.resolve()
    if args.stop:
        state.mkdir(parents=True,exist_ok=True)
        (state/'stop.request').touch()
        print('Dashboard auto-sync will stop within a few seconds.');return
    if args.start:
        state.mkdir(parents=True,exist_ok=True)
        if (state/'stop.request').exists():(state/'stop.request').unlink()
        runtime=Path(sys.executable).with_name('pythonw.exe')
        if not runtime.exists():runtime=Path(sys.executable)
        subprocess.Popen([str(runtime),str(Path(__file__).resolve()),'--source',str(source),'--state',str(state),'--watch'],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),close_fds=True)
        print('Dashboard-only auto-sync started.');return
    if args.prepare:
        files=prepare(source);args.prepare.mkdir(parents=True,exist_ok=True)
        for path,text in files.items():
            dest=args.prepare/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text,encoding='utf-8')
        print('Prepared',len(files),'data-free project files');return
    if args.once:print(sync(prepare(source),state));return
    if not args.watch:p.error('Choose --prepare, --once, --start, --stop or --watch')
    # Process-level lock prevents duplicate startup/watch workers.
    import msvcrt
    state.mkdir(parents=True,exist_ok=True)
    lock=(state/'watch.lock').open('a+b');lock.seek(0)
    try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    except OSError:return
    seen=None;uploaded=None;quiet=time.monotonic();retry=0
    while not (state/'stop.request').exists():
        try:
            files=prepare(source);current=digest(files)
            if current!=seen:seen=current;quiet=time.monotonic()
            if current!=uploaded and time.monotonic()-quiet>=12 and time.monotonic()>=retry:
                sync(files,state);uploaded=current
        except Exception as exc:
            status(state,state='pending',error=str(exc),scope=PREFIX)
            retry=time.monotonic()+60
        time.sleep(3)
    status(state,state='stopped',scope=PREFIX)

if __name__=='__main__':main()
