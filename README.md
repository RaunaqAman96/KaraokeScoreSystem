# Pitch Scoring Assignment

## Goal
Build a system that scores candidate vocal tracks against a reference performance at the **phrase level**.

You should compare each candidate phrase to the matching reference phrase, then determine relative quality (better/worse) based on your own methodology.

## Dataset

- Reference audio: `assets/reference/vocals.mp3`
- Optional phrase timing metadata: `assets/reference/struct.json`
- Candidate tracks: `assets/tracks/*.wav`

## Your Task

1. Create an analysis pipeline to compare each candidate track to the reference.
2. Produce a **score per phrase** for each track (your scale/definition is up to you).
3. Produce an overall **ranking/order** of tracks from best to worst relative to the reference.
4. Explain how phrase scores are combined (or otherwise used) to create the final track ranking.

You may use any language, framework, and audio tooling you prefer.

- Example pitch library (optional): [`swift-f0`](https://github.com/lars76/swift-f0)

## Handling Difficult/Noisy Tracks

Some tracks or individual phrases may be too noisy or otherwise unsuitable for a reliable score.

You can programmatically skip tracks or specific phrases, but each skipped item must include:

- A `label` indicating it was skipped
- A `reason` explaining why (for example: low SNR, clipped audio, failed pitch extraction, too-short voiced segments, any relevant classes of errors)

## Deliverables

Please submit:

1. Source code for your solution.
2. A short write-up (`SCORE.md`) describing:
   - Your pipeline
   - Your scoring definition
   - How ranking is produced
   - Tradeoffs/limitations
3. A machine-readable results file (`results.csv` or `results.json`) containing phrase-level records.
4. A machine-readable track ranking summary (`ranking.csv` or `ranking.json`), or include equivalent track-level ranking fields in the same results file.

Recommended result fields:

- `track_id` (filename)
- `phrase_number` (`1-4` from `assets/reference/struct.json`)
- `status` (`scored` or `skipped`)
- `phrase_score` (null if skipped)
- `label` (required if skipped)
- `reason` (required if skipped)

Recommended track-level ranking fields:

- `track_id` (filename)
- `aggregate_score` (how you combine phrase-level evidence)
- `rank` (1 = best match to reference)

## Evaluation Focus

The evaluation will run against a larger holdout dataset of tracks, so similar tracks would ideally end up in similar buckets with your code.

## Notes

- There is no single "correct" scoring formula.
- Prioritize a method you can explain and defend when scoring relative to the reference track.
- Working/dealing with noisy tracks is completely optional
- Consider finding recordings on Youtube or testing against recordings of yourself
