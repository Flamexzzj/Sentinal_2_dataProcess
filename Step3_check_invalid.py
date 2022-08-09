# -*- coding: utf-8 -*-
# Author: Zhijie (JJ) Zhang
import os
import sys
from glob import glob
from optparse import Values

import numpy as np
from osgeo import gdal, ogr, osr
from tqdm import tqdm
import tifffile
import shutil


images = glob(r"E:\Tellman_Lab\THP_project\CSDA_S2\CSDA_S2_stacked_with_label\usa\*.tif")
bad_img_path = r"E:\Tellman_Lab\THP_project\CSDA_S2\CSDA_S2_stacked_with_label\usa_bad"
# print(images)

for image in images:
	print(image)
	band1 = tifffile.imread(image)[:,:,0]
	print(band1)
	print(band1.shape)
	band1 = np.array(band1, dtype=int)
	cnt_array = np.where(band1, 0, 1)
	num_zero_pixels = np.sum(cnt_array)
	print(num_zero_pixels)

	if num_zero_pixels >= 5000:
		if not os.path.exists(bad_img_path):os.makedirs(bad_img_path)
		# new_location = bad_img_path + "\\" + image.split('\\')[-1]
		shutil.move(image, bad_img_path)


	print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")