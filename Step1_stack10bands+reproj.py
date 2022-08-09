# -*- coding: utf-8 -*-
# Author: Zhijie (JJ) Zhang
#aaaaaaaaa   branch1
import os
import sys
from glob import glob
from optparse import Values

import numpy as np
from osgeo import gdal, ogr, osr
from tqdm import tqdm


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


def readRasterData(rasterFileName):
	ds = gdal.Open(rasterFileName)
	band = ds.GetRasterBand(1)
	# band = ds.GetRasterBand()
	data = band.ReadAsArray()

	return data


def get_filename(file_name):
	file_name = os.path.basename(file_name)
	file_name = file_name.split('.')[0]
	return file_name


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


def s2res(outputpath, tmp_path, filename, bands, shp_filenames):

	ids = []
	extents = []

	driver = ogr.GetDriverByName('GeoJSON')
	data_source = driver.Open(shp_filenames, 0)
	# if data_source is None:
	#     print("文件【%s】无法打开", file_name)
	#     sys.exit(-1)

	layer = data_source.GetLayer(0)
	for feature in layer:
		# 要素字段名集合
		keys = feature.keys()
		# for key in keys:
		# 要素字段值
		value = feature.GetField('id')

		# 图形字段
		geometry = feature.geometry()
		# print(geometry)
		extent = geometry.GetEnvelope()
		ids.append(value)
		extents.append(extent)

	del data_source

	ref_rows, ref_cols, geoTrans, srs, noDataValue = readRasterMeta(
		filename+"B02.jp2")
	# ref_rows, ref_cols, geoTrans, srs, noDataValue = readRasterMeta(
	# 	filename+"B02.tif")

	prosrs = osr.SpatialReference()

	prosrs.ImportFromWkt(srs)

	geosrs = prosrs.CloneGeogCS()

	col = ref_cols   #

	row = ref_rows

	px = geoTrans[0] + col * geoTrans[1] + row * geoTrans[2]  # 299980.0
	py = geoTrans[3] + col * geoTrans[4] + row * geoTrans[5]  # 4090220.

	px0 = geoTrans[0] + 0 * geoTrans[1] + 0 * geoTrans[2]  # 299980.0

	py0 = geoTrans[3] + 0 * geoTrans[4] + 0 * geoTrans[5]

	ct = osr.CoordinateTransformation(prosrs, geosrs)    #

	coords = ct.TransformPoint(px, py)
	coords0 = ct.TransformPoint(px0, py0)

	img_x_min, img_x_max, img_y_min, img_y_max = coords0[1], coords[1], coords[0], coords0[0]

	for s in tqdm(ids):
		print("\n{}-->{}".format("id", s))
		extent = extents[int(s)]
		x_min, x_max, y_min, y_max = extent

		if x_min > img_x_min and x_max < img_x_max and y_min > img_y_min and y_max < img_y_max:

			img_patch = []
			for b in range(bands.__len__()):
				# if bands[b] not in ['B02','B03','B04','B08']:
				filename_ = filename+bands[b]+".jp2"
				# filename_ = filename+bands[b]+".tif"
				dataset = gdal.Open(filename_)

				gdal.Warp(os.path.join(tmp_path, get_filename(filename_)+'_'+s+'.tif'),
						  dataset,
						  dstSRS = "EPSG:4326",
						  # reproject = True,
						  xRes=0.0001054125427409154152,
						  yRes=0.0001054125427409154152,
						  cutlineDSName=shp_filenames,
						  cutlineWhere="id ="+"'"+s+"'",
						  cropToCutline=True)
						  # dstSRS = "EPSG:4326")
				# cutlineDSName = "shp/03_Houston_HTX.geojson",
				# cropToCutline = True)
				tmp_data = readRasterData(os.path.join(
					tmp_path, get_filename(filename_)+'_'+s+'.tif'))
				ref_rows1, ref_cols1, geoTrans1, srs1, noDataValue1 = readRasterMeta(
					os.path.join(tmp_path, get_filename(filename_)+'_'+s+'.tif'))
				img_patch.append(tmp_data)
			# noDataValue1 = np.nan
			img_patch_ = np.array(img_patch, np.int16)
			img_patch_[img_patch_==0]= noDataValue
			file_name1 = s+'_'+get_filename(filename)+'fused'+'.tif'
			print(file_name1)
			writeRaster(os.path.join(outputpath, file_name1), ref_rows1,
						ref_cols1, img_patch_, geoTrans1, srs1, noDataValue1, gdal.GDT_Int16)


if __name__ == "__main__":
	print("Start")
	tiles = glob("E:\\Tellman_Lab\\THP_project\\CSDA_Label_orig_data\\usa\\S2B_MSIL1C_20190522T165859_N0207_R069_T15TUE_20190522T202833.SAFE\\GRANULE\\L1C_T15TUE_A011535_20190522T170556\\IMG_DATA\\*.jp2")

	# print(tiles)
	# tiles = glob("E:\\Tellman_Lab\\THP_project\\THP_Label_orig_data\\CMO\\post_flood\\reprojected\\*.tif")
	print("tiles!!!!!!!!!!!!!!!")
	print(tiles)
	tiles_ = [t[:-7] for t in tiles]

	tiles_ = list(set(tiles_))
	print("tiles_!!!!!!!!!!!!!!!")
	print(tiles_)

	bands = ['B02', 'B03', 'B04', 'B05', 'B06',
			 'B07', 'B08', 'B8A', 'B11', 'B12']
	# bands = ['02', '03', '04', '05', '06',
	#          '07', '08', '8A', '11', '12']

	outpath = "E:\\Tellman_Lab\\THP_project\\CSDA_Label_orig_data\\usa\\out_ue"
	if not os.path.exists(outpath): os.makedirs(outpath)
	tmp_path = "E:\\Tellman_Lab\\THP_project\\CSDA_Label_orig_data\\usa\\tmp_ue"
	if not os.path.exists(tmp_path): os.makedirs(tmp_path)

	shp_filenames = 'E:\\Tellman_Lab\\THP_project\\CSDA_S2\\S1F11_updatedFootprints_060822.geojson'

	for tt in tiles_:
		# tt = tt.split('B')[0]
		print(tt)
		s2res(outpath, tmp_path, tt, bands, shp_filenames)

	print("end")
