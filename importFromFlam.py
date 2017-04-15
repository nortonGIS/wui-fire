#-------------------------------------------------------------------------------
# Name:        importFromFlam Tool
# Purpose:     Retrieves burn rasters from FlamMap, creates zonal statistics,
#				and joins to original SMS_fc
#
# Author:      Peter Norton
#
# Created:     04/12/2017
# Copyright:   (c) Peter Norton 2017
#-------------------------------------------------------------------------------

import os
import sys
import arcpy
from arcpy import env
from arcpy.sa import *

# Set Scratch Workspace
scratchws = env.scratchWorkspace
scriptpath = sys.path[0]    
toolpath = os.path.dirname(scriptpath)

# Set environment settings
if not env.scratchWorkspace:
	scratchws = os.path.join(toolpath, "Scratch")
scratchgdb = os.path.join(scratchws, "Scratch.gdb")

# Set Local Variables
FlamMap_output = os.path.join(toolpath, "FlamMap")
prj = os.path.join(scratchgdb, "cc_bnd")
##
# Execute SMS Process
spectral_detail = 10
spatial_detail = 20
min_seg_size = 4
band_inputs = "1,2,3,4"

naip = os.path.join(scratchws, "cc_naip")
sms_raster = os.path.join(scratchws, "cc_sms_raster")
seg_naip = SegmentMeanShift(naip, spectral_detail, spatial_detail, min_seg_size, band_inputs)
seg_naip.save(sms_raster)

# Execute SMS Raster to Polygon
sms_fc = os.path.join(scratchgdb, "cc_sms_fc")
arcpy.RasterToPolygon_conversion(seg_naip, sms_fc, "NO_SIMPLIFY", "VALUE")
arcpy.DefineProjection_management(sms_fc, "PROJCS['NAD_1983_StatePlane_California_III_FIPS_0403_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',6561666.666666666],PARAMETER['False_Northing',1640416.666666667],PARAMETER['Central_Meridian',-120.5],PARAMETER['Standard_Parallel_1',37.06666666666667],PARAMETER['Standard_Parallel_2',38.43333333333333],PARAMETER['Latitude_Of_Origin',36.5],UNIT['Foot_US',0.3048006096012192]]")
arcpy.AddMessage("SMS is created.")

zonal_tables = []

# FOR CC ONLY
field = "fuel"
cc = os.path.join(toolpath, "cc_"+field+ ".shp")
inValueRaster = os.path.join(scratchgdb, "cc_fuel")
arcpy.PolygonToRaster_conversion(cc, field, inValueRaster)
outTable = os.path.join(scratchgdb, "zonal_"+field)
z_table = ZonalStatisticsAsTable(sms_fc, "ID", inValueRaster, outTable, "NODATA", "MAXIMUM")
arcpy.AddField_management(outTable, field, "FLOAT")
arcpy.CalculateField_management(outTable, field, "[MAX]")
arcpy.JoinField_management(sms_fc, "ID", outTable, "ID", field)
arcpy.AddMessage("Fuel is joined.")

# FLAMMAP OUTPUT

fields = ["fli", "ros", "flame_len"]
for field in fields:

	in_ascii_file = os.path.join(FlamMap_output, field + ".asc")
	data_type = "INTEGER"
	inValueRaster = os.path.join(scratchgdb, field)
	arcpy.ASCIIToRaster_conversion(in_ascii_file, inValueRaster, data_type)
	arcpy.DefineProjection_management(inValueRaster, "PROJCS['NAD_1983_StatePlane_California_III_FIPS_0403_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',6561666.666666666],PARAMETER['False_Northing',1640416.666666667],PARAMETER['Central_Meridian',-120.5],PARAMETER['Standard_Parallel_1',37.06666666666667],PARAMETER['Standard_Parallel_2',38.43333333333333],PARAMETER['Latitude_Of_Origin',36.5],UNIT['Foot_US',0.3048006096012192]]")
	inZoneData = sms_fc
	zoneField = "ID"
	outTable = os.path.join(scratchgdb, "zonal_"+field)
	z_table = ZonalStatisticsAsTable(inZoneData, zoneField, inValueRaster, outTable, "NODATA", "MAXIMUM")
	arcpy.AddField_management(outTable, field, "FLOAT")
	arcpy.CalculateField_management(outTable, field, "[MAX]")
	zonal_tables.append((outTable, field))
	arcpy.AddMessage("{0} is created.".format(field))

# join zonal tables with SMS
num_tables = len(zonal_tables)
for i in range(num_tables):
	table = zonal_tables[i][0]	#table file
	field = zonal_tables[i][1]	#join field
	arcpy.AddMessage("Joining: " + field)
	arcpy.JoinField_management(sms_fc,"ID", table, "ID", field)
	arcpy.AddMessage("Table {0} of {1} was joined.".format(i+1, num_tables))
arcpy.AddMessage("Tables joined to SMS.")
