import os
import sys
import cv2
import json
import glob
import numpy

def distance (i, j):
    return abs(i - j)

def ordinal_hash (frame):
    brightness = [
        numpy.sum(frame[0:12,0:12,2:3]),
        numpy.sum(frame[0:12,12:24,2:3]),
        numpy.sum(frame[0:12,24:36,2:3]),
        numpy.sum(frame[0:12,36:48,2:3]),
        numpy.sum(frame[12:24,0:12,2:3]),
        numpy.sum(frame[12:24,12:24,2:3]),
        numpy.sum(frame[12:24,24:36,2:3]),
        numpy.sum(frame[12:24,36:48,2:3]),
        numpy.sum(frame[24:36,0:12,2:3]),
        numpy.sum(frame[24:36,12:24,2:3]),
        numpy.sum(frame[24:36,24:36,2:3]),
        numpy.sum(frame[24:36,36:48,2:3]),
        numpy.sum(frame[36:48,0:12,2:3]),
        numpy.sum(frame[36:48,12:24,2:3]),
        numpy.sum(frame[36:48,24:36,2:3]),
        numpy.sum(frame[36:48,36:48,2:3])
    ]
    brightness = [(brightness[i], i) for i in range(len(brightness))]
    brightness = [arr[1] for arr in sorted(brightness)]
    result = [0]*len(brightness)
    for i in range(len(brightness)):
        result[brightness[i]] = i
    return result

def extract_frames (video_file):
    frames = []
    video = cv2.VideoCapture(video_file)
    stride = int(video.get(cv2.CAP_PROP_FPS))
    more, frame = video.read()
    while more:
        frames += [cv2.cvtColor(cv2.resize(frame, (48, 48)), cv2.COLOR_BGR2HSV)]
        for i in range(stride):
            more = video.grab()
        more, frame = video.read()
    video.release()
    return frames

def vectorize (video_file, output_file=False):
    vector = [ordinal_hash(frame) for frame in extract_frames(video_file)]
    if output_file:
        numpy.save(open(output_file, 'wb'), vector)
    return vector

"""
python dejavu.py vectorize media/tidal.mp4 media/tidal.djv
python dejavu.py recognize capture/0.fs7 media/

python dejavu.py recognize2 record/dco1.mp4 media/
"""
if __name__ == "__main__":
    if sys.argv[1] == "vectorize":
        vectorize(sys.argv[2], sys.argv[3])
    if sys.argv[1] == "recognize":
        result = {}
        mystery = [ordinal_hash(cv2.cvtColor(cv2.resize(cv2.imread(file), (48, 48)), cv2.COLOR_BGR2HSV)) for file in sorted(glob.glob(sys.argv[2] + "*"))]
        vectors = [(f, numpy.load(f)) for f in glob.glob(sys.argv[3] + "/*.djv")]
        for vector in vectors:
            max_diff = 1e10
            f, vector = vector
            for i in range(len(vector) - len(mystery) + 1):
                diff = 0
                for j in range(len(mystery)):
                    for k in range(len(mystery[j])):
                        diff += distance(vector[i+j][k], mystery[j][k])
                if diff < max_diff:
                    max_diff = diff
            max_diff /= len(mystery)
            result[f] = max_diff
        result = [(result[name], name) for name in result.keys()]
        result = [pair[::-1] for pair in sorted(result)]
        print(json.dumps(result))
    if sys.argv[1] == "recognize2":
        result = {}
        mystery = vectorize(sys.argv[2])
        vectors = [(f, numpy.load(f)) for f in glob.glob(sys.argv[3] + "/*.djv")]
        for vector in vectors:
            max_diff = 1e10
            f, vector = vector
            for i in range(len(vector) - len(mystery) + 1):
                diff = 0
                for j in range(len(mystery)):
                    for k in range(len(mystery[j])):
                        diff += distance(vector[i+j][k], mystery[j][k])
                if diff < max_diff:
                    max_diff = diff
            max_diff /= len(mystery)
            result[f] = max_diff
        result = [(result[name], name) for name in result.keys()]
        result = [pair[::-1] for pair in sorted(result)]
        print(json.dumps(result))
