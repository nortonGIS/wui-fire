#-------------------------------------------------------------------------------
# Name:			unpackFire.py
# 
# Description:	This script (1) unpacks the output shapefile from FARSITE, 
#				(2) re-stacks the shapefiles, and (3) creates the image stack 
#				needed to create a movie (.GIF) of the burn simulation.
#
# Inputs:		burn.shp, bnd.shp, bnd_template.lyr, fire_template.lyr
#	
# Outputs:		(shapefiles separated by minutes) burn_#.shp, burn_#.png, 
#				burn_union.shp
#
# Usage:		no user specified parameters required
#
# Author:		Peter Norton
# Created:		04/05/2017
# Copyright:	(c) PeterNorton 2017
# ---------------------------------------------------------------------------

# Import system modules
import arcpy
import os
import sys
from arcpy import env
scratchws = env.scratchWorkspace
scriptpath = sys.path[0]
toolpath = os.path.dirname(scriptpath)
mxd_path = os.path.join(toolpath,"temp_mxd.mxd")
# Set environment settings
if not env.scratchWorkspace:
	scratchws = os.path.join(toolpath, "Scratch")
scratchgdb = os.path.join(scratchws, "Scratch.gdb")
# Set paths
bndpath = os.path.join(toolpath, "OD_bnd.shp")
symbology_bnd = os.path.join(toolpath, "bnd_template.lyr")
symbology_layer = os.path.join(toolpath, "fire_template.lyr")
datapath = os.path.join(toolpath, "burn.shp")
outpath = os.path.join(toolpath, "output")
burn_gdb = os.path.join(outpath, "burn.gdb")
gifpath = os.path.join(toolpath, "fire_gif")
gif = os.path.join(gifpath, "fire_sim.gif")
scratchgdb = os.path.join(scratchws, "Scratch.gdb")
sms_fc = os.path.join(scratchgdb, "sms_fc")
# Local variables
attributes = []
name = "burn_"

# Set projection

#arcpy.DefineProjection_management(datapath,"PROJCS['NAD_1983_StatePlane_California_III_FIPS_0403_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',6561666.666666666],PARAMETER['False_Northing',1640416.666666667],PARAMETER['Central_Meridian',-120.5],PARAMETER['Standard_Parallel_1',37.06666666666667],PARAMETER['Standard_Parallel_2',38.43333333333333],PARAMETER['Latitude_Of_Origin',36.5],UNIT['Foot_US',0.3048006096012192]]")

# Repair geometry for multi-part features with negative area
#arcpy.RepairGeometry_management(datapath, "DELETE_NULL")

# Process: Iterate Feature Selection
#-------------------------------------------------------------
# This step iterates through the overlayed, multi-part feature
# by the user selected field and outputs a new feature class.

# Create a layer from the shapefile and add it to the map
name = "burn_"
cursor = arcpy.da.SearchCursor(datapath, ["Elapsed Mi"], "", "")
for row in cursor:
	attr = str(row)[1:-4]
	if attr not in attributes:
		attributes.append(attr)
arcpy.AddMessage("Attributes used: {0}".format(attributes))
attr_length = len(attributes)
count = 0
frames = []
burn_list = []
union_fields = ["stack#", "tot"]

temp_attributes = []
i = 0
while i < 10:
	temp_attributes.append(attributes[i])
	i += 1
for attr in temp_attributes:
	out_name = attr
	where_clause = "\"Elapsed Mi\"=" + attr
	
	temp_fire = os.path.join(outpath, "temp_fire.shp")
	output_burn = os.path.join(outpath, out_name + ".shp")

	#arcpy.Select_analysis(datapath, temp_fire, where_clause)
	#arcpy.Clip_analysis(temp_fire, bndpath, output_burn)
	
	# Add fields and calculate
	toa = os.path.join(burn_gdb, "T" + out_name)
	#arcpy.FeatureClassToGeodatabase_conversion(output_burn, burn_gdb)
	#arcpy.AddField_management(toa, "stack", "SHORT")
	#arcpy.CalculateField_management(toa, "stack", 1)
	burn_fields = [f.name for f in arcpy.ListFields(toa)]
	delete_fields = ["Month", "Day", "Hour", "Elapsed_Mi", "Fire_Type"]
	arcpy.DeleteField_management(toa, delete_fields)
	burn_list.append(toa)
	del temp_fire
	del output_burn

	count += 1
	# png_name = out_name + ".png"
	# output_png = os.path.join(gifpath, png_name)
	# mxd = arcpy.mapping.MapDocument(mxd_path)
	# df = arcpy.mapping.ListDataFrames(mxd)[0]
	# bnd = arcpy.mapping.Layer(bndpath)
	# layer = arcpy.mapping.Layer(output_burn)
	# arcpy.ApplySymbologyFromLayer_management(layer,symbology_layer)
	# arcpy.mapping.AddLayer(df, layer)
	# arcpy.ApplySymbologyFromLayer_management(bnd,symbology_bnd)
	# arcpy.mapping.AddLayer(df, bnd)
	# df.extent = bnd.getExtent()
	# arcpy.RefreshActiveView()
	# arcpy.RefreshTOC()
	# arcpy.mapping.ExportToPNG(mxd, output_png)
	# #frames.append(imageio.imread(image))
	# del layer
	# del df
	# del mxd
	arcpy.AddMessage("{0} of {1}".format(count, attr_length))

# Create a list of feature classes in the current workspace


# Add fields and calculate
arcpy.AddMessage(burn_list)
burn_union = os.path.join(burn_gdb, "burn_union")
arcpy.Union_analysis(burn_list, burn_union, "NO_FID")
arcpy.AddMessage("Union Complete")
stack_fields = []
union_stack_fields = [f.name for f in arcpy.ListFields(burn_union)]
for field in union_stack_fields:
	if field[:5] == "stack":
		stack_fields.append(field)
arcpy.AddMessage("{0} fields will be unioned".format(len(stack_fields)))
expression = ""
for field in stack_fields:
	expression += "[" + field + "] + "
expression = expression[:-2]
arcpy.AddMessage(expression)
arcpy.AddField_management(burn_union, "tot", "SHORT")
arcpy.CalculateField_management(burn_union, "tot", expression)
arcpy.DeleteField_management(burn_union, stack_fields)
