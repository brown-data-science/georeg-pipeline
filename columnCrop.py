import glob, os, re
import numpy as np
from numpy import ndarray
import cv2
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import math
import sklearn
from sklearn.cluster import MeanShift
from multiprocessing import Pool

#Chops the pages into columns

def naturalSort(String_):
	return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', String_)]

def getAvg(img, x, y):
	height, width = img.shape[:2]
	avg = [range(x,y)]
	for i in range(height):
		for j in range(x,y):
				avg += img[i, j]
	return avg/height

def imgAvg(img):
	height, width = img.shape[:2]
	avg = 0
	for i in range(width):
		for j in range(height):
			avg += img[j, i]
	return avg/(height * width)


def cleanImage(image):
    inv = cv2.bitwise_not(image)
    #kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,2000))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,1))
    closing = cv2.morphologyEx(inv, cv2.MORPH_CLOSE, kernel)
    opening = cv2.morphologyEx(closing, cv2.MORPH_OPEN, kernel)
    #dilate = cv2.dilate(inv, kernel)
    return cv2.bitwise_not(opening)
    #return opening


def cropImage(image, file):
	croppedImages = []
	img = image.copy()
	height, width = img.shape[:2]
	sf = float(height)/11675.0
	sfw = float(width)/7820.0
	histogram  = pd.Series([height - cv2.countNonZero(img[:,i]) for i in list(range(width))]).rolling(5).mean()
	do_plots = True
	if do_plots:
		fig = plt.figure()
		ax = histogram.plot()
		ax.set_ylim([0,200])
		fig.savefig(file.partition('.jp2')[0] + '.histogram.pdf', bbox_inches='tight')
		plt.close(fig)
		fig = plt.figure()
		ax = histogram.rolling(50,center=True).mean().rolling(10,center=True).mean().plot()
		ax.set_ylim([0,200])
		fig.savefig(file.partition('.jp2')[0] + '.histogram.smooth.pdf', bbox_inches='tight')
		plt.close(fig)
	dip_df = histogram[histogram < sf*150].to_frame().rename(columns = {0:'count'})
	dip_df.loc[dip_df['count']<sf*50,'count'] = 0
	histogram.iloc[0] = 0
	indices = np.array(dip_df.index.tolist()).reshape(-1,1)
	ms = MeanShift()
	ms.fit(indices)
	dip_group = ms.predict(indices)
	dip_df = dip_df.assign(group = dip_group)
	cut_points = [0] + sorted(dip_df.groupby('group').apply(lambda x: max(x[x['count']==0].index - int(sfw*35.0))).tolist())[1:-1] + [width]
	for i in list(range(len(cut_points)-1)):
		croppedImages.append(img[0:height, cut_points[i]:cut_points[i+1]])
	return croppedImages

def crop_file(file):
	nDirectory = 'cropped'
	print(file)
	img = cv2.imread(file, 0)
	#clean = cv2.fastNlMeansDenoising(img, None, 60, 7, 21)
	crop = cropImage(img, file)
	name = file[:-4]
	ext = file[-4:]
	i = 1
	for image in crop:
		cv2.imwrite(os.path.join(nDirectory, name + " ("+ str(i) + ")" + ext), image)
		i += 1
	#cv2.imwrite(os.path.join(nDirectory, file), clean)
	print file + '-cropped to columns'
	return

def doCrop(folder):
	croppedImages = []
	scans = folder
	nDirectory = 'cropped'
	os.chdir(scans)
	if not os.path.exists(nDirectory):
		os.mkdir(nDirectory)
	do_multiprocessing = False
	if do_multiprocessing:
		pool = Pool(4)
		pool.map(crop_file, sorted(glob.glob("*.jp2"), key=naturalSort))
	for file in sorted(glob.glob("*.jp2"), key=naturalSort):
		crop_file(file)
	
	




