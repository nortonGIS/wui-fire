#-------------------------------------------------------------------------------
# Name:        importFromFlamMap Tool
# Purpose:     Takes outputs (.ascii) from FlamMap and joins the zonal maximum
#              to the classified layer.
#
#             Steps:
#               - Segment heights into unique objects using SMS
#               - Calculate and join mean height to objects with Zonal Stastics
#               - Separate ground and nonground features and mask naip
# Author:      Peter Norton
#
# Created:     05/25/2017
# Updated:     09/18/2017
# Copyright:   (c) Peter Norton and Matt Ashenfarb 2017
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# USER INPUT PARAMETERS
location_name = "Tahoe_West"
projection = "UTMZ10"  #["UTMZ10", "UTMZ11", "SPIII", "SPIV"]
input_bnd = "classified.shp"
input_naip = "naip.tif"

#-----------------------------------------------
#-----------------------------------------------
# Processing - DO NOT MODIFY BELOW
#-----------------------------------------------
#-----------------------------------------------

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
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

risk_fc = os.path.join(inputs, input_classified)
naip = os.path.join(inputs, input_naip)
burn_metrics = ["fire_line_intensity", "flame_length", "rate_of_spread"]

#-----------------------------------------------
# Alert 
count = 1
def generateMessage(text):
  global count
  arcpy.AddMessage("Step " + str(count) + ": " +text), 
  count += 1
arcpy.AddMessage("Site: "+location_name)
arcpy.AddMessage("Projection: "+projection)
arcpy.AddMessage("Resolution: "+coarsening_size + "m")
arcpy.AddMessage("Fuel Model: "+model)
arcpy.AddMessage("-----------------------------")
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Processing
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
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Set Cell Size
arcpy.env.snapRaster = naip
cell_size = str(arcpy.GetRasterProperties_management(naip, "CELLSIZEX", ""))
naip_cell_size = cell_size +" " +cell_size
#-----------------------------------------------
#-----------------------------------------------

for metric in burn_metrics:

	#-----------------------------------------------
	#-----------------------------------------------
	text = "Calculating and joining max " + metric + " to each object."
	generateMessage(text)
	#-----------------------------------------------
	#Set variables
	in_ascii_file = os.path.join(inputs, metric + ".asc")
	burn = os.path.join(scratchgdb, metric)
	raw_raster = os.path.join(outputs, metric  + "_raw.tif")
	shift = os.path.join(outputs, metric+".tif")
	outTable = os.path.join(scratchgdb, "zonal_"+metric)
	
	#-----------------------------------------------
	#-----------------------------------------------
	# Convert ascii output to raster and align cells
	arcpy.ASCIIToRaster_conversion(in_ascii_file, raw_raster, "INTEGER")
	arcpy.DefineProjection_management(raw_raster, projection)
	arcpy.Resample_management(raw_raster, "INTEGER", naip_cell_size, "")
	arcpy.Shift_management(burn, shift, -(int(cell_size)), 0, naip)
	#-----------------------------------------------
	#-----------------------------------------------
	
	#-----------------------------------------------
	#-----------------------------------------------
	# Calculate zonal max and join to each object
	arcpy.CalculateField_management(risk_fc, "JOIN", "[FID]")
	z_table = ZonalStatisticsAsTable(risk_fc, "JOIN", shift, outTable, "NODATA", "MAXIMUM")
	if metric == "fire_line_intensity":
		metric = "fli"
	elif metric == "rate_of_spread":
		metric = "ros"
	elif metric == "flame_length":
		metric = "fl"
	arcpy.AddField_management(outTable, metric, "INTEGER")
	arcpy.CalculateField_management(outTable, metric, "int([MAX])")
	one_to_one_join(risk_fc, outTable, metric, "INTEGER")
	#-----------------------------------------------
	#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
text = "All burn severity joins are complete."
generateMessage(text)
#-----------------------------------------------