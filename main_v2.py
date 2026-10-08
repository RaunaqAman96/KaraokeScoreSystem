import matplotlib.pyplot as plt
import numpy as np
import audiofile
import glob
import argparse
import librosa
import sys
import json
import csv

parser = argparse.ArgumentParser()
parser.add_argument(
    '-i', '--input', metavar='INPUT',
    help = 'audio file to be compared')
args= parser.parse_args()

header_results = "track_id, phrase_number, status, phrase_score, label, reason"
header_ranking = "track_id, score, rank"

results_to_csv = []
ranking_to_csv = []

def audio_load(filename):
    """
    Function to load the target track
    """
    d, sr = audiofile.read(filename)
    print("Input Audio loaded")
    d = librosa.to_mono(d)
    return d, sr

def ref_load():
    """
    Function to load the reference track
    """
    d_ref, sr_ref = audiofile.read("assets/reference/vocals_clipped2.wav")
    d_ref = librosa.to_mono(d_ref)
    return d_ref,sr_ref
    
def phrase_split():
    """
    Function to load the phrase structure 
    """
    phrase_number = []
    start_time = []
    end_time = []
    try:
        with open('assets/reference/struct.json', 'r') as file:
            datas = json.load(file)
        
    except FileNotFoundError:
        print("Error: The file 'data.json' was not found.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from the file (invalid JSON format).")
    
    for data in datas['phrases']:
        phrase_number.append(data['phrase_number'])
        start_time.append(data['start_time_ms'])
        end_time.append(data['end_time_ms'])
        
    return phrase_number, start_time, end_time
    
def pitch_measurement(data, sr, data_ref, sr_ref,track_id):
    """
    Function to calculate the pitch of the reference and the target
    """
    score_cumulative = 0
    nG_cumulative = 0
    skip_flag = 0
    phrase_number, start_time, end_time = phrase_split()
    for i,v in enumerate(phrase_number):
        d_ref = data_ref[np.floor(sr_ref*(start_time[i]/1000)).astype(int):np.floor(sr_ref*(end_time[i]/1000)).astype(int)]
        pitch_ref = pitch_calculator(d=d_ref, sr=sr_ref)
        print("Reference pitch calculated for phrase: ", phrase_number[i])
        d = data[np.floor(sr*(start_time[i]/1000)).astype(int):np.floor(sr*(end_time[i]/1000)).astype(int)]
        if 20*np.log10(np.mean(librosa.feature.rms(y=d))) < -35:
            skip_flag = 1
            status = "skipped"
            label = "skipped"
            reason = "Low RMS"
            results_to_csv.append([track_id]+[str(phrase_number[i])]+[status]+["null"]+[label]+[reason])
            continue
        pitch = pitch_calculator(d=d, sr=sr)
        print("Target pitch calculated")
        if len(pitch) == 0:
            skip_flag = 1
            status = "skipped"
            label = "skipped"
            reason = "Failed pitch extraction"
            results_to_csv.append([track_id]+[str(phrase_number[i])]+[status]+["null"]+[label]+[reason])
            continue
        if np.count_nonzero(pitch) < 0.3 * np.count_nonzero(pitch_ref):
            skip_flag = 1
            status = "skipped"
            label = "skipped"
            reason = "Too-short voiced segments"
            results_to_csv.append([track_id]+[str(phrase_number[i])]+[status]+["null"]+[label]+[reason])
            continue
        p_val,p_val_ref,score, nG = score_calculation(p=pitch, p_ref=pitch_ref)
        status = "scored"
        results_to_csv.append([track_id]+[str(phrase_number[i])]+[status]+[str(score)]+["N/A"]+["N/A"])
        score_cumulative = score_cumulative + (score*nG)
        nG_cumulative = nG_cumulative + nG
    with open('results.csv', 'w', newline='') as csvfile_results:
        writer = csv.writer(csvfile_results)
        writer.writerow(header_results.split(','))
        writer.writerows(results_to_csv)
    return score_cumulative, nG_cumulative, skip_flag

    
def silence_trim(p,p_ref):
    """
    Removes the leading silent parts of the tracks
    """
    if any(map(len, np.where(p[1] == True))) is False:
        p_val = p[0]
    else:
        p_val = p[0][(np.where(p[1] == True)[0][0]):]
    p_val_ref = p_ref[0][(np.where(p_ref[1] == True)[0][0]):]
    return p_val,p_val_ref

def score_calculation(p, p_ref):
    """
    Calculate the score of the target track in comparison to the reference phrase
    """
    nG = np.count_nonzero(p_ref[0])
    nE = np.count_nonzero(p[0])
    nC = 0
    score = 0
    p_val, p_val_ref = silence_trim(p,p_ref)
    if len(p_val)>len(p_val_ref):
        pitch_len = len(p_val_ref)
    else:
        pitch_len = len(p_val)
    for i in range(pitch_len):
        if p_val[i]> 0 and p_val_ref[i] > 0:
            if (abs((p_val[i]/p_val_ref[i])-1)<0.06):
                nC = nC + 1
                score = score + 1
            else:
                score = score + min(max(2-(np.emath.logn(10,abs((p_val[i]/p_val_ref[i])-1)*100)),0),1)
    score = score/nG
    accuracy = nC/(nG + nE - nC)
    #precision = nC/nE
    #recall = nC/nG
    #xcr = np.corrcoef(p_val[:pitch_len],p_val_ref[:pitch_len])[0,1]
    return p_val,p_val_ref, score, nG

def pitch_calculator(d, sr):
    """
    Call the f0 function from the Librosa library
    """
    pitch = librosa.pyin(y=d, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr, fill_na = 0)
    return pitch

def rank_songs(score_list):
    """
    Function to sort the scores to rank the target tracks 
    """
    score_list.sort(key=keyFun,reverse=True)
    for i,v in enumerate(score_list):
        ranking_to_csv.append([score_list[i]['track_id']]+[str(score_list[i]['score'])]+[str(i+1)])
    return

def keyFun(e):
    return e['score']

def main():
    score_list=[]
    data_ref, sr_ref = ref_load()
    print("Reference track loaded")
    for name in glob.glob(args.input+"*"):
        print("Calculating pitch for", name)
        data, sr = audio_load(name)
        score_cumulative,nG_cumulative,skip_flag = pitch_measurement(data=data, sr=sr,data_ref=data_ref,sr_ref=sr_ref,track_id=name)
        if skip_flag:
            score_list.append({'track_id':name,'score':0})
            continue
        score_track = score_cumulative/nG_cumulative
        score_list.append({'track_id':name,'score':score_track})
    rank_songs(score_list)
    with open('ranking.csv', 'w', newline='') as csvfile_ranking:
        writer = csv.writer(csvfile_ranking)
        writer.writerow(header_ranking.split(','))
        writer.writerows(ranking_to_csv)
    
if __name__ == '__main__':
	sys.exit(main())