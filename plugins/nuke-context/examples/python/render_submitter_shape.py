# render_submitter_shape — nuke-context example (original code).
# category: pipeline tool | teaches: the architecture of a render submitter - introspect, build a job, confirm, emit
# verified: API-checked against python_index (nuke-17.0)
"""The shape of a render-farm submitter, with the farm itself stubbed out.

Every real submitter (Deadline, AWS Deadline Cloud, a studio's in-house one)
has the same four stages, and this example is that skeleton with the
farm-specific last step replaced by writing a JSON job file next to the
script:

  1. INTROSPECT   walk the script for Write nodes, frame ranges, file paths
  2. BUILD        assemble a plain-data job description (a dict - testable
                  without Nuke; this is the pure core)
  3. CONFIRM      show the artist what will be submitted; let them opt out
  4. EMIT         hand the job to the farm (here: a .json file)

Swapping stage 4 for a real farm API call is the only farm-specific work.
Difficulty: intermediate.
"""
import json
import pathlib

from PySide6 import QtWidgets

import nuke


def collect_jobs():
    """Stage 1+2: one job dict per enabled Write node. Pure data out."""
    jobs = []
    first = int(nuke.root()["first_frame"].value())
    last = int(nuke.root()["last_frame"].value())
    for write in nuke.allNodes("Write"):
        if write["disable"].value():
            continue
        jobs.append({
            "node": write.name(),
            "output": write["file"].value(),
            "frames": f"{first}-{last}",
            "script": nuke.root().name(),
        })
    return jobs


def confirm(jobs):
    """Stage 3: a summary dialog. Returns True to proceed."""
    lines = "\n".join(f"  {j['node']}  ->  {j['output']}  [{j['frames']}]"
                      for j in jobs)
    answer = QtWidgets.QMessageBox.question(
        None, "Submit renders?",
        f"About to submit {len(jobs)} job(s):\n\n{lines}")
    return answer == QtWidgets.QMessageBox.StandardButton.Yes


def emit(jobs):
    """Stage 4: the farm boundary. Here: a JSON file next to the script."""
    script = pathlib.Path(nuke.root().name())
    out = script.with_suffix(".jobs.json")
    out.write_text(json.dumps(jobs, indent=2))
    nuke.message(f"Wrote {len(jobs)} job(s) to {out.name}")


def submit():
    jobs = collect_jobs()
    if not jobs:
        nuke.message("No enabled Write nodes to submit.")
        return
    if confirm(jobs):
        emit(jobs)


# menu.py hook:  nuke.menu("Nuke").addCommand("Render/Submit (example)", submit)
