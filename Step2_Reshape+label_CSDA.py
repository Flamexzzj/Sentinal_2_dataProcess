# -*- coding: utf-8 -*-
# Author: Zhijie (JJ) Zhangimport os
import sys
from glob import glob
from optparse import Values

import numpy as np
from osgeo import gdal, ogr, osr, gdal_array
from tqdm import tqdm

orig_scene_folder = "E:\\Tellman_Lab\\THP_project\\CSDA_Label_orig_data\\usa\\out_tc"
tar_scene_folder = "E:\\Tellman_Lab\\THP_project\\CSDA_Label_orig_data\\usa\\out_usa_resize"
if not os.path.exists(tar_scene_folder): os.makedirs(tar_scene_folder)

orig_label_folder = "E:\\Tellman_Lab\\THP_project\\CSDA_S2\\Labeled_Chips\\USA"
tar_label_folder = "E:\\Tellman_Lab\\THP_project\\CSDA_S2\\Labeled_Chips\\USA_resize"
if not os.path.exists(tar_label_folder): os.makedirs(tar_label_folder)

stacked_save_path = "E:\\Tellman_Lab\\THP_project\\CSDA_S2\\CSDA_S2_stacked_with_label\\usa"
if not os.path.exists(stacked_save_path): os.makedirs(stacked_save_path)

geojson_file = "E:\\Tellman_Lab\\THP_project\\CSDA_S2\\S1F11_updatedFootprints_060822.geojson"


def readRasterData(rasterFileName):
	print(rasterFileName)
	ds = gdal.Open(rasterFileName)
	data = ds.ReadAsArray()
	data = np.array(data, np.int16)

	return data

def read_geojson(geojson_file):
	labels = []
	scenes = []
	driver = ogr.GetDriverByName('GeoJSON')
	data_source = driver.Open(geojson_file, 0)
	layer = data_source.GetLayer(0)
	for feature in layer:
		# 要素字段名集合
		keys = feature.keys()
		# for key in keys:
		# 要素字段值
		label_value = feature.GetField('location')
		label_name = label_value.split("/")[-1]
		scene_value = feature.GetField('id')
		labels.append(label_name)
		scenes.append(scene_value)
	
	return labels, scenes


############################################
def reproj_resamp(orig_scene_folder, tar_scene_folder):
	image_file_list = glob(orig_scene_folder+"/*.tif")
	for image in image_file_list:
		image_name = image.split("\\")[-1]
		print(image_name)
		ds = gdal.Open(orig_scene_folder + '/' + image_name)
		save_path = tar_scene_folder + '/' + image_name
		new_ds = gdal.Warp(save_path, ds, width = 1024, height = 1024, resampleAlg = "lanczos")


def stack_label(tar_scene_folder,geojson_file, stacked_save_path):
	scene_list = glob(tar_scene_folder+"/*.tif")
	for scene in scene_list:
		scene_name = scene.split("\\")[-1]
		scene_id = int(scene_name.split("_")[0])
		labels, k = read_geojson(geojson_file)
		label = tar_label_folder + '\\' + labels[scene_id]
		print (label)
		print (scene)
		print ("\n")
		label_array = readRasterData(label)
		scene_array = readRasterData(scene)
		# scene_array[scene_array==-9999]= 0
		label_array = np.reshape(label_array, (1,1024,1024))
		stacked = np.append(scene_array, label_array, axis = 0)
		save_stacked_img_name = labels[scene_id].split(".")[0] + "_fused_allBandLabel_S2.tif"
		save_path = stacked_save_path + '\\' + save_stacked_img_name
		# gdal_array.SaveArray(stacked, save_path, "GTiff")
		rows, cols, geoTrans, srs, noDataValue = readRasterMeta(scene)
		writeRaster(save_path,rows,cols,stacked,geoTrans,srs,noDataValue,gdal.GDT_Int16)

#####
def writeRaster(filename, nRows, nCols, data, geoTransform, srs, noDataValue, gdalType):
	format = 'GTiff'
	driver = gdal.GetDriverByName(format)
	ds = driver.Create(filename, nCols, nRows, data.shape[0], gdalType)
	ds.SetGeoTransform(geoTransform)
	ds.SetProjection(srs)
	# ds.GetRasterBand(1).SetNoDataValue(noDataValue)
	# ds.GetRasterBand(1).WriteArray(data)
	for i in range(data.shape[0]):
		outBand = ds.GetRasterBand(i + 1)
		outBand.SetNoDataValue(noDataValue)
		outBand.WriteArray(data[i])

	ds = None
	del ds, outBand
	return True


def readRasterMeta(rasterFileName):
	ds = gdal.Open(rasterFileName)
	band = ds.GetRasterBand(1)
	# data = band.ReadAsArray()
	cols = band.XSize
	rows = band.YSize
	noDataValue = band.GetNoDataValue()
	geoTrans = ds.GetGeoTransform()
	srs = ds.GetProjection()
	if noDataValue is None:
		noDataValue = 0

	return rows, cols, geoTrans, srs, noDataValue



if __name__ == "__main__":
	print("Start!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
	reproj_resamp(orig_scene_folder, tar_scene_folder)
	reproj_resamp(orig_label_folder, tar_label_folder)
	stack_label(tar_scene_folder,geojson_file, stacked_save_path)
	print("\nFinish!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

