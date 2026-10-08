import pyaudio
import matplotlib.pyplot as plt
import scipy
import numpy as np
import audiofile
import audresample
import glob
import argparse
import sqlite3
import librosa
import sys
from shapesimilarity import shape_similarity
from swift_f0 import *

detector = SwiftF0(fmin=46.875, fmax=2093.75, confidence_threshold=0.9)

np.set_printoptions(threshold=sys.maxsize)

parser = argparse.ArgumentParser()
parser.add_argument(
    '-i', '--input', metavar='INPUT',
    help = 'audio file to be compared')
args= parser.parse_args()


def audio_load(filename):
    d, sr = audiofile.read(filename)
    print("Input Audio loaded")
    d = librosa.to_mono(d)
    return d, sr

def ref_load():
    d_ref, sr_ref = audiofile.read("vocals_clipped2.wav")
    d_ref = librosa.to_mono(d_ref)
    return d_ref,sr_ref
    
def pitch_measurement(data, sr):
    similarity = 0
    d_ref, sr_ref = ref_load()
    print("Reference track loaded")
    #fig, ax = plt.subplots(nrows=2, sharex=True, sharey=True)
    chroma_cq1 = librosa.feature.chroma_cqt(y=data, sr=sr)
    #img1 = librosa.display.specshow(chroma_cq1, y_axis='chroma', x_axis='time',ax = ax[0])
    chroma_cq2 = librosa.feature.chroma_cqt(y=d_ref, sr=sr_ref)
    #img2 = librosa.display.specshow(chroma_cq2, y_axis='chroma', x_axis='time',ax=ax[1])
    for i in range(12):
        if len(chroma_cq1[i])>len(chroma_cq2[i]):
            temp1 = chroma_cq1[i][:len(chroma_cq2[i])]
            temp2 = chroma_cq2[i]
        else:
            temp2 = chroma_cq2[i][:len(chroma_cq1[i])]
            temp1 = chroma_cq1[i]
        similarity = similarity + cosine_similarity_numpy(temp1,temp2)
    print(similarity)
    pitch_ref = pitch_calculator(d_ref, sr_ref)
    print("Reference pitch calculated")
    pitch = pitch_calculator(data, sr)
    print("Target pitch calculated")
    p_val,p_val_ref,p_i,p_i_ref = score_calculation(p=pitch, p_ref=pitch_ref)
    score_calculation_notes(p=pitch, p_ref=pitch_ref)
    
    if (len(p_val)>=len(p_val_ref)):
        p_val = p_val[:len(p_val_ref)]
    else:
        p_val = np.pad(p_val,(0,len(p_val_ref)-len(p_val)))
        
    times = range(len(p_val))
    times_ref = range(len(p_val_ref))
    
    shape = np.column_stack((times_ref,p_val))
    shape_ref = np.column_stack((times_ref,p_val_ref))
    similarity = shape_similarity(shape,shape_ref, checkRotation = False)
    print(similarity)
    plt.figure(figsize=(10,4))
    times = librosa.times_like(p_val,sr=sr)
    times_ref = librosa.times_like(p_val_ref,sr=sr_ref)
    if (len(times_ref)>len(times)):
        plt.figure(1)
        plt.plot(times,p_val)
        plt.figure(2)
        plt.plot(times,p_val_ref[:len(times)])
        #plt.plot(times,p_i)
        #plt.plot(times,p_i_ref[:len(times)])
    else:
        plt.figure(1)
        plt.plot(times_ref,p_val[:len(times_ref)])
        plt.figure(2)
        plt.plot(times_ref,p_val_ref)
        #plt.plot(times_ref,p_i[:len(times_ref)])
        #plt.plot(times_ref,p_i_ref)
    #plt.plot(times,pitch)
    plt.show()
    return
    
def cosine_similarity_numpy(vec1, vec2):
    """
    Calculates the cosine similarity between two 1D vectors using NumPy.
    """
    dot_product = np.dot(vec1, vec2)
    magnitude_vec1 = np.linalg.norm(vec1)
    magnitude_vec2 = np.linalg.norm(vec2)
    
    # Handle division by zero for zero-magnitude vectors
    if magnitude_vec1 == 0 or magnitude_vec2 == 0:
        return 0.0
        
    similarity = dot_product / (magnitude_vec1 * magnitude_vec2)
    return similarity
    
def silence_trim(p,p_ref):
    p_val = p[0][(np.where(p[1] == True)[0][0]):]
    #print(p_val)
    p_val_ref = p_ref[0][(np.where(p_ref[1] == True)[0][0]):]
    #print(p_val_ref)
    return p_val,p_val_ref

def score_calculation(p, p_ref):
    #temp = [value for value in p_ref[0] if value!=0]
    #print(temp,librosa.hz_to_note(temp))
    p_i = []
    p_i_ref = []
    nG = np.count_nonzero(p_ref[0])
    nE = np.count_nonzero(p[0])
    nC = 0
    score = 0
    counter = 0
    #print(p[1])
    #print(p_ref[1])
    p_val, p_val_ref = silence_trim(p,p_ref)
    if len(p_val)>len(p_val_ref):
        pitch_len = len(p_val_ref)
    else:
        pitch_len = len(p_val)
    for i in range(pitch_len):
        if p_val[i]> 0 and p_val_ref[i] > 0:
            p_i.append(librosa.note_to_hz(librosa.hz_to_note(p_val[i])))
            p_i_ref.append(librosa.note_to_hz(librosa.hz_to_note(p_val_ref[i])))
            #print(abs((p[i]/p_ref[i])-1))
            if (abs((p_val[i]/p_val_ref[i])-1)<0.06):
                nC = nC + 1
                score = score + 1
            else:
                score = score + min(max(2-(np.emath.logn(10,abs((p_val[i]/p_val_ref[i])-1)*100)),0),1)
            counter = counter + 1
        else:
            p_i.append(0)
            p_i_ref.append(0)
    score = score/nG
    accuracy = nC/(nG + nE - nC)
    precision = nC/nE
    recall = nC/nG
    #xcr = np.corrcoef(p_val[:pitch_len],p_val_ref[:pitch_len])[0,1]
    print(accuracy,score)
    return p_val,p_val_ref,p_i,p_i_ref
    
def score_calculation_notes(p, p_ref):
    #temp = [value for value in p_ref[0] if value!=0]
    #print(temp,librosa.hz_to_note(temp))
    p_i = []
    p_i_ref = []
    nG = np.count_nonzero(p_ref[0])
    nE = np.count_nonzero(p[0])
    nC = 0
    score = 0
    counter = 0
    p_val, p_val_ref = silence_trim(p,p_ref)
    if len(p_val)>len(p_val_ref):
        pitch_len = len(p_val_ref)
    else:
        pitch_len = len(p_val)
    for i in range(pitch_len):
        if p_val[i]> 0 and p_val_ref[i] > 0:
            temp = librosa.note_to_hz(librosa.hz_to_note(p_val[i]))
            temp_ref = librosa.note_to_hz(librosa.hz_to_note(p_val_ref[i]))
            p_i.append(temp)
            p_i_ref.append(temp_ref)
            #print(abs((p[i]/p_ref[i])-1))
            if (abs((temp/temp_ref)-1)<0.06):
                nC = nC + 1
                score = score + 1
            else:
                score = score + min(max(2-(np.emath.logn(10,abs((temp/temp_ref)-1)*100)),0),1)
            counter = counter + 1
        else:
            p_i.append(0)
            p_i_ref.append(0)
    score = score/nG
    accuracy = nC/(nG + nE - nC)
    precision = nC/nE
    recall = nC/nG
    #xcr = np.corrcoef(p_val[:pitch_len],p_val_ref[:pitch_len])[0,1]
    print(accuracy,score)
    return p_val,p_val_ref,p_i,p_i_ref

def score_store(song_name, score, cursor):
    cursor.execute("INSERT INTO stored_scores(Song_name, Song_score) VALUES (?,?)", song_name, str(score)) 
    return

def pitch_calculator(d, sr):
    pitch = librosa.pyin(y=d, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr, fill_na = 0)
    #print(pitch[0],pitch[1])
    #key = librosa.hz_to_note(pitch)
    return pitch

def main():
    #for name in glob.glob(args.filename+"*"):
    data, sr = audio_load(args.input)
    score = pitch_measurement(data, sr)
    result = detector.detect_from_file(args.input)
    plot_pitch(result, show=False, output_path="pitch.jpg")
    #song_name, min_distance = distance_calculation(score,table)
    #print("Closest song", song_name)
    
if __name__ == '__main__':
	sys.exit(main())