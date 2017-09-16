#-------------------------------------------------------------------------------
# Name:        generateTraining Tool
# Purpose:     Takes raw naip and lidar data, uses thresholds to classify data
#              and generates training samples by identifying tight thresholds.
#
#             Steps:
#               - Segment heights into unique objects using SMS
#               - Calculate and join mean height to objects with Zonal Stastics
#               - Separate ground and nonground features and mask naip
# Author:      Peter Norton
#
# Created:     05/25/2017
# Updated:     06/03/2017
# Copyright:   (c) Peter Norton and Matt Ashenfarb 2017
#-------------------------------------------------------------------------------
# ---------------------------------------------------------------------------

# Import modules
import arcpy
import os
import sys
from arcpy import env
from arcpy.sa import *
arcpy.env.overwriteOutput = True
from tableJoin import one_to_one_join

#-----------------------------------------------
# Set scratch workspace and environment settings

scriptpath = sys.path[0]
toolpath = os.path.dirname(scriptpath)
scratchws = os.path.join(toolpath, "Scratch")
scratchgdb = os.path.join(scratchws, "Scratch.gdb")


#-----------------------------------------------
# Set I/O Paths
outputs = os.path.join(toolpath, "Outputs")
inputs = os.path.join(toolpath, "Inputs")


#-----------------------------------------------
# Inputs
#-----------------------------------------------

risk_fc = os.path.join(inputs, "classified.shp")
naip = os.path.join(inputs, "naip.tif")

projection = "UTMZ10"

#-----------------------------------------------
# Outputs


#-----------------------------------------------
# Alert 
count = 1
def generateMessage(text):
  global count
  arcpy.AddMessage("Step " + str(count) + ": " +text), 
  count += 1

#-----------------------------------------------
#-----------------------------------------------
# Processing
#-----------------------------------------------
#-----------------------------------------------

fields = ["fire_line_intensity"]#, "flame_len", "rate_of_spread"]



if projection == "UTMZ10":
  scale_height = 0.3048
  projection = "PROJCS['NAD_1983_UTM_Zone_10N',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-123.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"
elif projection == "UTMZ11":
  scale_height = 0.3048
  projection = "PROJCS['NAD_1983_UTM_Zone_11N',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-117.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"
elif projection == "SPIII":
  scale_height = 1
  projection = "PROJCS['NAD_1983_StatePlane_California_III_FIPS_0403_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',6561666.666666666],PARAMETER['False_Northing',1640416.666666667],PARAMETER['Central_Meridian',-120.5],PARAMETER['Standard_Parallel_1',37.06666666666667],PARAMETER['Standard_Parallel_2',38.43333333333333],PARAMETER['Latitude_Of_Origin',36.5],UNIT['Foot_US',0.3048006096012192]]"
elif projection == "SPIV":
  scale_height = 1
  projection = "PROJCS['NAD_1983_StatePlane_California_VI_FIPS_0406_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',6561666.666666666],PARAMETER['False_Northing',1640416.666666667],PARAMETER['Central_Meridian',-116.25],PARAMETER['Standard_Parallel_1',32.78333333333333],PARAMETER['Standard_Parallel_2',33.88333333333333],PARAMETER['Latitude_Of_Origin',32.16666666666666],UNIT['Foot_US',0.3048006096012192]]"

arcpy.env.snapRaster = naip

cell_size = str(arcpy.GetRasterProperties_management(naip, "CELLSIZEX", ""))
naip_cell_size = cell_size +" " +cell_size
for field in fields:

	#------------------------------
	#-----------------------------------------------
	text = "Calculating and joining max " + field + " to each object."
	generateMessage(text)
	#-----------------------------------------------
	in_ascii_file = os.path.join(inputs, field + ".asc")
	data_type = "INTEGER"
	inValueRaster = os.path.join(scratchgdb, field)
	raw_raster = os.path.join(outputs, field  + "_raw.tif")
	shift = os.path.join(outputs, field+".tif")
	arcpy.ASCIIToRaster_conversion(in_ascii_file, raw_raster, data_type)
	arcpy.DefineProjection_management(raw_raster, projection)
	
	arcpy.Resample_management(raw_raster, inValueRaster, naip_cell_size, "")
	arcpy.Shift_management(inValueRaster, shift, -(int(cell_size)), 0, naip)

	zoneField = "JOIN"
	outTable = os.path.join(scratchgdb, "zonal_"+field)
	arcpy.CalculateField_management(risk_fc, zoneField, "[FID]")
	z_table = ZonalStatisticsAsTable(risk_fc, zoneField, shift, outTable, "NODATA", "MAXIMUM")
	if field == "fire_line_intensity":
		field = "fli"
	elif field == "rate_of_spread":
		field = "ros"
	elif field == "flame_len":
		field = "fl"
	#-----------------

	arcpy.AddField_management(outTable, field, "INTEGER")
	arcpy.CalculateField_management(outTable, field, "int([MAX])")
	one_to_one_join(risk_fc, outTable, field, "INTEGER")

#-----------------------------------------------
#-----------------------------------------------
text = "All burn severity joins are complete."
generateMessage(text)
#-----------------------------------------------

# # Fire Simulation 
# output_file = os.path.join(toolpath, "output")
# toagdb = os.path.join(FlamMap_output, "toa.gdb")
# toa = os.path.join(scratchgdb, "toa")
# temp = os.path.join(scratchgdb, "temp")
# gifpath = os.path.join(toolpath, "fire_gif")
# mxd_path = os.path.join(toolpath,"temp_mxd.mxd")
# bndpath = os.path.join(scratchgdb, "bnd")
# basemap = os.path.join(scratchgdb, "house_buff_landscape_dis")
# symbology_bnd = os.path.join(toolpath, "bnd_template.lyr")
# symbology_layer = os.path.join(toolpath, "fire_template.lyr")
# symbology_baselayer = os.path.join(toolpath, "house_buff_landscape_dis.lyr")
# spatial_ref = os.path.join(toolpath, "bnd.prj")

# # convert ascii to polygon and add dissolve field
# toa_ascii = os.path.join(outputs, "hb_toa.asc")
# toa_raster = os.path.join(output, "hb_toa_raster.tif")
# arcpy.ASCIIToRaster_conversion(toa_ascii, toa_raster, "INTEGER")
# arcpy.AddMessage("...making raster...")
# arcpy.DefineProjection_management(toa_raster, "PROJCS['NAD_1983_StatePlane_California_III_FIPS_0403_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',6561666.666666666],PARAMETER['False_Northing',1640416.666666667],PARAMETER['Central_Meridian',-120.5],PARAMETER['Standard_Parallel_1',37.06666666666667],PARAMETER['Standard_Parallel_2',38.43333333333333],PARAMETER['Latitude_Of_Origin',36.5],UNIT['Foot_US',0.3048006096012192]]")
# arcpy.AddMessage("...making polygon...")
# arcpy.RasterToPolygon_conversion(toa_raster, toa)
# arcpy.AddField_management(toa, "toa", "INTEGER")
# arcpy.CalculateField_management(toa, "toa", 1)

# cursor = arcpy.da.SearchCursor(toa, "gridcode", "")
# maximum = 0
# for row in cursor:
# 	val = row[0]
# 	if maximum == 0:
# 		maximum = val
# 	elif val > maximum:
# 		maximum = val

# arcpy.AddMessage("...separating toa...")


# #creating backgdrop
# mxd = arcpy.mapping.MapDocument(mxd_path)
# df = arcpy.mapping.ListDataFrames(mxd)[0]
# bnd = arcpy.mapping.Layer(bndpath)
# base_layer = arcpy.mapping.Layer(basemap)
# arcpy.ApplySymbologyFromLayer_management(base_layer,symbology_baselayer)

# range_lst = []
# for i in range(maximum):
# 	if i % 100 == 0:
# 		range_lst.append(i)

# lwr_bnd = range_lst.pop(0)
# range_len = len(range_lst)
# range_len = len(range_lst)
# output_burn = ""
# count = 1
# gif_list = []
# merge = ""
# for i in range_lst:
# 	upr_bnd = i
# 	out_name = str(upr_bnd)
# 	burn = os.path.join(toagdb, "hb_toa_" + out_name)
# 	where_clause = "GRIDCODE > " + str(lwr_bnd) + " AND GRIDCODE <=" + str(upr_bnd)
# 	arcpy.Select_analysis(toa, temp, where_clause)
# 	arcpy.Dissolve_management(temp, burn, "toa", "", "", "")

# #	lwr_bnd = upr_bnd
# #	if merge == "":
# 	output_burn = burn
# #	else:
# #		output_burn = os.path.join(scratchgdb, "b_" + str(count))	
# #		arcpy.Merge_management([burn, merge], output_burn)
# #	merge = output_burn
	
# 	arcpy.AddMessage("...making .PNG...")
	
# 	# Make png
# 	# png_name = "hb_"+out_name + ".png"
# 	# output_png = os.path.join(gifpath, png_name)
# 	# arcpy.mapping.AddLayer(df, base_layer)
# 	# layer = arcpy.mapping.Layer(output_burn)
# 	# arcpy.ApplySymbologyFromLayer_management(layer,symbology_layer)
# 	# arcpy.mapping.AddLayer(df, layer)
# 	# arcpy.ApplySymbologyFromLayer_management(bnd,symbology_bnd)
# 	# arcpy.mapping.AddLayer(df, bnd)
# 	# df.spatialReference = arcpy.SpatialReference(spatial_ref)
# 	# df.extent = bnd.getExtent()
# 	# arcpy.RefreshActiveView()
# 	# arcpy.RefreshTOC()
# 	# arcpy.mapping.ExportToPNG(mxd, output_png)
# 	# if count > 2:
# 	# 	scrap = os.path.join(scratchgdb, "b_" + str(i-1))
# 	# 	arcpy.Delete_management(scrap)
# 	# arcpy.AddMessage("{0} of {1} developed.".format(count, range_len))
# 	# count += 1
