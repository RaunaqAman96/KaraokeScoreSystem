# Pitch-Based Singing Score System

## 1. Overview
This document describes a system designed to compare input audio tracks to a reference track, calculating a score based on how close they are to the reference track with regard to
the pitch and the melodic structure.

---

## 2. System Pipeline

### 2.1 Input
- **Reference Track**: The target audio file used as the baseline for comparison. In this case, **You Are My Sunshine** by Johnny Cash.
- **Candidate Tracks**: A collection of audio files to be evaluated. For all use cases, several performances of the reference track, as well as some entirely unrelated musical pieces

---

### 2.2 Preprocessing
- Convert all audio to mono. Sampling rate is defined by the audio track itself:
- Loaded the phrase information (stored in a JSON format in this case), and split the reference track and the target track into corresponding phrases
- Performed corresponding feature checks (RMS level, SNR, voice activity) on the target track to ensure that it is suitable for pitch extraction. If not skip pitch extraction and scoring.

---

### 2.3 Pitch Extraction
- Used the probabilistic YIN algorithm via Librosa’s pyin function
- Output:
  - Fundamental frequency (F0) over time
  - Voiced/unvoiced decisions and probabilities

---

### 2.4 Feature Representation
Convert raw pitch data into structured features:

- Pitch contour (continuous F0 values)
- Pitch histograms (distribution of notes)

---

## 3. Scoring System

### 3.1 Preprocessing

- Check whether the pitch extraction process is successful. If not, skip scoring.
- Check whether there are large enough voiced-segments. If not, skip scoring
- Trimmed the leading silence on the tracks so as to minimise the phase difference between the target and reference tracks.
- Check for frames that are voiced for both the reference track and the target track.

### 3.2 Score Definition

**Accuracy** (ratio of correct pitches to the total number of detected pitches) was briefly considered before being discarded due to very harsh penalties provided if it did not match exactly with the reference phrase.

Therefore, a custom scoring system was implemented:

RawScore = 1; if pitch_target is within 6% of pitch_reference
RawScore = 2 - log10(abs(pitch_target/pitch_reference-1)\*100); for pitch target within 6% < pitch_reference < 100%
RawScore = 0; for all other pitch targets

Where:

- **pitch_target**: pitch of target phrase
- **pitch_reference**: pitch of reference phrase

The value of 6% is taken because the frequency ratio between two adjacent semitones in a Western musical system is:

**2^1/12 ≃ 1.06**

Therefore, a full score is given to those pitches that are within a semitone of the target pitch.

After that, a linear penalty scale would have been too forgiving for incorrect notes, so a logarithmic scale was decided so that an appropriate penalty would be applied to the score.

The raw score of all the voiced frames was then divided by the number of voiced frames of the reference phrase. This will give a score between 0 and 1 and would represent how close the target pitch is to the reference pitch.
This gives the normalised score of the phrase.
---

### 3.2 Scoring of full track

To calculate the normalised score of the full track, the raw score of each phrase is added, then weighted with the total number of voiced frames in the reference track and then added.

**Final Score** = w1 * RawScore_phrase1 + w2 * RawScore_phrase2 + …

- w_i are weights

---

### 3.3 Interpretation
- **Score ≈ 1** → Highly similar  
- **Score ≈ 0** → Dissimilar  

---

## 4. Ranking Mechanism

### 4.1 Sorting
- Sort candidate tracks in descending order of similarity score

---

### 4.2 Tie Handling
- As of this moment, no tie-handling mechanism has been implemented

---

### 4.3 Output
Example ranked list:

1. Track A — Score: 0.92  
2. Track B — Score: 0.87  
3. Track C — Score: 0.81  

---

## 5. Trade-offs and Limitations with Possible Solutions

### 5.1 Time Alignment between Tracks
- Despite pre-processing to remove leading silences, there was a possibility of tracks being out of sync due to differences in recording.
tempo differences between the target track and the reference track
- This is especially prominent in the phrase system, since the manually selected phrases of the target track may not align well with the reference track,
causing a mismatch between the phrases
- One solution is **dynamic time warping (DTW)** to align the tracks. This needs to be investigated further.
- In this use case, another possible solution might be using automatic transcription to link the tracks to the lyrics and thus providing a base for alignment.

---

### 5.2 Score System:
- The formula for scoring might be too forgiving, as a couple of tracks had a comparatively high score despite audibly being very different. This is because the pitch of the target track is close enough
to the reference track to keep scoring.
- Melody structure using **chroma features** was extracted; however, upon calculating the various difference features (Euclidean distance, Cosine similarity, etc.), it still did not create any sort of appreciable difference.
- The shape of pitch contours was programmatically compared, again to limited success.
- One possible solution might be using the **note representation** to measure the melody sequence. The pitches need to be stable enough for an appreciable amount of time for the note sequencing to be effective.
---

### 5.3 Noise 
- Since there is only a single mixture without any noise profile available, pre-processing to remove the noise will be very effective.
- Speech enhancement techniques (both programmatically, as well as manually using Audacity) were also used, with basically no change.
- AI speech and voice enhancement may cause embellishment of the audio, causing false scores.

---
