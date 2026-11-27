"""Phase 3.9 manual incident review; requires local operator flags."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"apps/api"))
from mta_incident_review import append_review

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--assessment",required=True,help="SHA-256 of existing alert assessment")
    p.add_argument("--action",required=True,choices=("acknowledge","assign","resolve"))
    p.add_argument("--actor",required=True)
    p.add_argument("--note",required=True)
    p.add_argument("--assignee")
    p.add_argument("--evidence-reference",help="Required to record a HUMAN resolution assertion")
    p.add_argument("--data-root",default="data/dev")
    args=p.parse_args()
    result=append_review(args.data_root,args.assessment,args.action,args.actor,args.note,args.assignee,args.evidence_reference)
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("MTA review rejected:",str(exc),file=sys.stderr);sys.exit(1)
