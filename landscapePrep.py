#-------------------------------------------------------------------------------
# Name:			landscapePrep.py
# 
# Description:	This script takes a landscape.shp and DEM.tif and creates the 
#				7 necessary inputs into FARSITE.
#
# Inputs:		landscape.shp, dem.tiff
#	
# Outputs:		fuel.asc, canopy.asc, standheights.asc, baseheights.asc, 
#				aspect.asc, elevation.asc, slope.asc
#
# Usage:		no user specified parameters required
#
# Author:		Peter Norton
# Created:		04/05/2017
# Copyright:	(c) PeterNorton 2017
# ---------------------------------------------------------------------------

import arcpy
from arcpy.sa import *
import os
import sys
from arcpy import env

# Set workspace and paths
scratchws = env.scratchWorkspace
scriptpath = sys.path[0]
toolpath = os.path.dirname(scriptpath)
if not env.scratchWorkspace:
	scratchws = os.path.join(toolpath, "Scratch")
scratchgdb = os.path.join(scratchws, "Scratch.gdb")
landscape = os.path.join(scratchgdb, "landscape")
dem = os.path.join(scratchgdb, "dem")
temp_raster = os.path.join(scratchgdb, "temp_raster")
farsite_input = os.path.join(toolpath, "input")
mask = os.path.join(scratchgdb, "dem")

# Local variables
landscape_lst = ["fuel", "canopy"] #add 'standheights' and 'baseheights'
elevation_lst = ["elevation", "aspect", "slope"]

for layer in elevation_lst:
	temp = os.path.join(scratchgdb, layer)
	if layer == "slope":
		arcpy.Slope_3d(dem, temp, "DEGREE", 1)
	elif layer == "aspect":
		arcpy.Aspect_3d(dem, temp)
	elif layer == "elevation":
		temp = dem
	temp_raster = os.path.join(toolpath, "temp_raster")
	arcpy.CopyRaster_management(temp, temp_raster, "", "", 0, "", "", "32_BIT_SIGNED")
	ready = ExtractByMask(temp_raster, mask)
	ascii_output = os.path.join(farsite_input, layer + ".asc")
	arcpy.RasterToASCII_conversion(ready, ascii_output)
	arcpy.AddMessage("The {0} file was created.".format(layer))

for layer in landscape_lst:
 	ascii_output = os.path.join(farsite_input, layer + ".asc")
 	where_clause = layer +" <> 9999"
 	temp = os.path.join(scratchgdb, layer)
 	arcpy.Select_analysis(landscape, temp, where_clause)
 	arcpy.PolygonToRaster_conversion(temp, layer, temp_raster, "CELL_CENTER", "", dem)
	ExtractByMask(temp_raster, mask)
 	arcpy.RasterToASCII_conversion(mask, ascii_output)
 	arcpy.AddMessage("The {0} file was created.".format(layer))