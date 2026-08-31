# Intermediate and Professional ASL curriculum data

This folder defines two word-level ASL curricula built from the official MS-ASL annotations:

- **Intermediate Conversational Fluency** — conversational vocabulary building blocks.
- **Professional & Workplace Communication** — workplace vocabulary building blocks.

## What is included

`msasl_curriculum_labels.json` contains the hand-selected glosses, source details, licence notice, and citation. `manifests/` is generated locally and holds JSON Lines files, one for each course and MS-ASL split. Each line keeps the source URL, time range, normalized signer bounding box, signer id, and class label required to reproduce a clip preparation step.

Run from `backend/`:

```bash
python scripts/build_msasl_curriculum.py
```

The MS-ASL metadata archive is stored at `data/external/msasl/MS-ASL.zip`; it contains the authoritative C-UDA licence PDF. The generated manifest does **not** download or redistribute any source video. Downloading or publishing video clips needs a separate licence/availability review.

## Important limits

MS-ASL is an isolated, word-level recognition dataset. It is appropriate for a first temporal sign recognizer, but not for claiming sentence translation, conversational fluency assessment, or professional interpretation. The professional vocabulary is also not a substitute for a qualified ASL interpreter.

Before use, review the C-UDA licence packaged in the archive. It restricts this dataset to computational/research use; do not use the material commercially or redistribute clips without appropriate permission. Cite MS-ASL in any research output.
