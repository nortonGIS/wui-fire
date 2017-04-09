#-------------------------------------------------------------------------------
# Name:        Classifying Tool
# Purpose:     SMS, Create sms_poly, join zonal attributes of image enhancements
#
# Author:      Peter Norton
#
# Created:     03/04/2017
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

# Set Paths
scratchgdb  =os.path.join(scratchws, "Scratch.gdb")
outputspath = os.path.join(toolpath, "output")
naip = os.path.join(toolpath, "naip")
iepath = os.path.join(toolpath, "IE\IE.gdb")
naip_b1 = os.path.join(naip, "naipc1")
naip_b2 = os.path.join(naip, "naipc2")
naip_b3 = os.path.join(naip, "naipc3")
naip_b4 = os.path.join(naip, "naipc4")
height = os.path.join(toolpath, "height") #height layer

# Execute SMS Process
spectral_detail = 10
spatial_detail = 20
min_seg_size = 4
band_inputs = "1,2,3,4"

seg_naip = SegmentMeanShift(naip, spectral_detail, spatial_detail, min_seg_size, band_inputs)

# Execute SMS Raster to Polygon
sms = os.path.join(outputspath, "sms.shp")
arcpy.RasterToPolygon_conversion(seg_naip, sms, "NO_SIMPLIFY", "VALUE")
arcpy.AddMessage("SMS is created.")

zonal_tables = []

# Principle Component Analysis
pca = os.path.join(iepath, "pca")
pca2 = os.path.join(pca, "Band_2")
pca3 = os.path.join(pca, "Band_3")
pc_list = [pca2, pca3]
inZoneData = sms
zoneField = "ID"
numComponents = 4
inValueRaster = PrincipalComponents([naip_b1,naip_b2, naip_b3, naip_b4],numComponents)
inValueRaster.save(pca)
for pc in pc_list:
	pc_num = pc[-1]
	if pc_num == "2":
		field = "pc2"
	else:
		field = "pc3"
	outTable = os.path.join(scratchgdb, "zonal_pc" + pc[-1])
	z_pca = ZonalStatisticsAsTable(inZoneData, zoneField, pc, outTable, "NODATA", "MEAN")
	arcpy.AddField_management(outTable, field, "FLOAT")
	arcpy.CalculateField_management(outTable, field, "[MEAN]")
	zonal_tables.append((outTable, field))
	arcpy.AddMessage("PC" + pc[-1] + " is created.")
	


# NDVI
field = "ndvi"
ndvi = os.path.join(iepath, "ndvi")
inZoneData = sms
zoneField = "ID"
outTable = os.path.join(scratchgdb, "zonal_ndvi")
inValueRaster = (Float(naip_b4)-Float(naip_b1))/(Float(naip_b4)+Float(naip_b1))
inValueRaster.save(ndvi)
z_ndvi = ZonalStatisticsAsTable(inZoneData, zoneField, inValueRaster, outTable, "NODATA", "MEAN")
arcpy.AddField_management(outTable, "ndvi", "FLOAT")
arcpy.CalculateField_management(outTable, field, "[MEAN]")
zonal_tables.append((outTable, field))
arcpy.AddMessage("NDVI is created.")

# GRVI
field = "grvi"
grvi = os.path.join(iepath, "grvi")
inZoneData = sms
zoneField = "ID"
outTable = os.path.join(scratchgdb, "zonal_grvi")
inValueRaster = Float(naip_b4)/Float(naip_b2)
inValueRaster.save(grvi)
z_grvi = ZonalStatisticsAsTable(inZoneData, zoneField, inValueRaster, outTable, "NODATA", "MEAN")
arcpy.AddField_management(outTable, field, "FLOAT")
arcpy.CalculateField_management(outTable, field, "[MEAN]")
zonal_tables.append((outTable, field))
arcpy.AddMessage("GRVI is created.")


# NDWI
field = "ndwi"
ndwi = os.path.join(iepath, "ndwi")
inZoneData = sms
zoneField = "ID"
outTable = os.path.join(scratchgdb, "zonal_ndwi")
inValueRaster = (Float(naip_b2)-Float(naip_b4))/(Float(naip_b2)+Float(naip_b4))
inValueRaster.save(ndwi)
z_ndwi = ZonalStatisticsAsTable(inZoneData, zoneField, inValueRaster, outTable, "NODATA", "MEAN")
arcpy.AddField_management(outTable, field, "FLOAT")
arcpy.CalculateField_management(outTable, field, "[MEAN]")
zonal_tables.append((outTable, field))
arcpy.AddMessage("NDWI is created.")


# Heights
field = "height"
inZoneData = sms
zoneField = "ID"
outTable = os.path.join(scratchgdb, "zonal_height")
inValueRaster = height
z_height = ZonalStatisticsAsTable(inZoneData, zoneField, inValueRaster, outTable, "NODATA", "MEAN")
arcpy.AddField_management(outTable, field, "FLOAT")
arcpy.CalculateField_management(outTable, field, "[MEAN]")
zonal_tables.append((outTable, field))
arcpy.AddMessage("Height is created.")


# join zonal tables with SMS
sms_fc = os.path.join(scratchgdb, "sms_fc")	#sms feature class
arcpy.FeatureClassToFeatureClass_conversion(sms, scratchgdb, "sms_fc")
num_tables = len(zonal_tables)
for i in range(num_tables):
	table = zonal_tables[i][0]	#table file
	field = zonal_tables[i][1]	#join field
	arcpy.AddMessage("Joining: " + field)
	arcpy.JoinField_management(sms_fc,"ID", table, "ID", field)
	arcpy.AddMessage("Table {0} of {1} was joined.".format(i+1, num_tables))
arcpy.AddMessage("Tables joined to SMS.")

#-----Classifier----------------
def classify(x, stage):
	if stage == "1":
		if x == "c_grvi":
			return ("def landcover(x):\\n  if x < 0.21:\\n    return \"water\"\\n  elif x < 0.5:\\n    return \"impervious\"\\n  return \"vegetation\"")
		elif x == "c_ndwi":
			return ("def landcover(x):\\n  if x < 0.05:\\n    return \"vegetation\"\\n  elif x < 0.66:\\n    return \"impervious\"\\n  return \"water\"")
		elif x == "c_pc2":
			return("def landcover(x):\\n  if x < 100:\\n    return \"water\"\\n  elif x < 150:\\n    return \"impervious\"\\n  return \"vegetation\"")
		elif x == "c_pc3":
			return("def landcover(x):\\n  if x < 160:\\n    return \"vegetation\"\\n  return \"impervious\"")
		elif x == "stage1":
			return("def landcover(a,b,c,d):\\n    \\n  tot = [a,b,c,d]\\n    \\n  V,I,W = 0,0,0\\n    \\n  for i in tot:\\n        \\n    if i == \"vegetation\":\\n            \\n      V += 1\\n\\n    elif i == \"impervious\":\\n\\n       I += 1\\n \\n    else:\\n            \\n      W += 1\\n\\n  if V > I:\\n\\n    if V > W:\\n      return \"vegetation\"\\n\\n    return \"VW confusion\"\\n\\n  elif I > W:\\n\\n      if I == W:\\n\\n        return \"IW confusion\"\\n\\n      elif I == V:\\n\\n        return \"VI confusion\"\\n\\n      return \"impervious\"\\n\\n  elif W == I:\\n\\n      return \"IW confusion\"\\n\\n  else:\\n\\n      return \"water\"\\n")
	elif stage == "vegetation":
		if x == "c2_heig":
			return("def landcover(x):\\n  if x < 0:\\n    return \"Confusion\"\\n  if x < 3:\\n    return \"Grass\"\\n  elif x < 6:\\n    return \"Shrub\"\\n  elif x < 500:\\n    return \"Tree\"\\n  return \"Confusion\"")
		elif x == "c2_grvi":
			return("def landcover(x):\\n  if x < 1.3:\\n    return \"Senescent\"\\n  return \"Healthy\"")
		elif x == "c2_ndwi":
			return("def landcover(x):\\n  if x < 0:\\n    return \"Senescent\"\\n  return \"Healthy\"")
		elif x == "c2_GRID":
			return("def landcover(x):\\n  if x < 150:\\n    return \"Tree/Shrub/Grass\"\\n  return \"Grass\"")
		elif x == "stage2":
			return("def landcover(a,b,c,d):\\n  if a in d:\\n    if b == c:\\n      return b + \" \" + a\\n    return \"Mature \" + a\\n  return \"Confusion\"")
	elif stage == "impervious":
		if x == "c2_heig":
			return("def landcover(x):\\n  if x < 0:\\n    return \"Confusion\"\\n  elif x < 5:\\n    return \"pavement\"\\n  elif x < 50:\\n    return \"building\"\\n  return \"Confusion\"")
		elif x == "stage2":
			return("def landcover(x):\\n  return \"x\"")
	elif stage == "water":
		if x == "stage2":
			return("def landcover(x):\\n  return \"x\"")
#
# -----stage 1--------
#
arcpy.AddMessage("...Executing: Stage 1 Classification...")
stage = "1"
s1_indices = ["grvi", "ndwi", "pc2", "pc3"]
for index in s1_indices:
	field = "c_"+index
	fxn = "landcover(!"+index+"!)"
	arcpy.AddField_management(sms_fc, field, "TEXT")
	label_class = classify(field, stage)
	arcpy.CalculateField_management(sms_fc, field, fxn, "PYTHON_9.3", label_class)
	arcpy.AddMessage("Field: '" + field +"' was classified.")
field = "stage1"
fxn = "landcover(!c_grvi!, !c_ndwi!, !c_pc2!, !c_pc3!)"
label_class = classify(field, stage)
arcpy.AddField_management(sms_fc, field, "TEXT")
arcpy.CalculateField_management(sms_fc, field, fxn, "PYTHON_9.3", label_class)
arcpy.AddMessage("Complete: Stage1 Classification")

s1_classes = ["vegetation", "water", "impervious"]
for c in s1_classes:
	output = os.path.join(scratchgdb, c)
	where_clause = "\""+field+"\" = '" + c + "'"
	arcpy.Select_analysis(sms_fc, output, where_clause)
#
# -----stage 2--------
#
arcpy.AddMessage("...Executing: Stage 2 Classification...")
#
# vegetation
stage = "vegetation"
veg = os.path.join(scratchgdb, stage)
veg_indices = ["height", "grvi", "ndwi", "GRIDCODE"]
for index in veg_indices:
	field = "c2_"+index[:4]
	fxn = "landcover(!"+index+"!)"
	arcpy.AddField_management(veg, field, "TEXT")
	label_class = classify(field, stage)
	arcpy.CalculateField_management(veg, field, fxn, "PYTHON_9.3", label_class)
	arcpy.AddMessage("Vegetation field: '"+ field + "' was classified.")
field = "stage2"
fxn = "landcover(!c2_heig!, !c2_grvi!, !c2_ndwi!, !c2_GRID! )"
label_class = classify(field, stage)
arcpy.AddField_management(veg, field, "TEXT")
arcpy.CalculateField_management(veg, field, fxn, "PYTHON_9.3", label_class)
arcpy.AddMessage("Complete: Stage2 Vegetation Classification")
#
# impervious
stage = "impervious"
imp = os.path.join(scratchgdb, stage)
imp_indices = ["height"]
for index in imp_indices:
	field = "c2_"+index[:4]
	fxn = "landcover(!"+index+"!)"
	arcpy.AddField_management(imp, field, "TEXT")
	label_class = classify(field, stage)
	arcpy.CalculateField_management(imp, field, fxn, "PYTHON_9.3", label_class)
	arcpy.AddMessage("Impervious field: '"+ field + "' was classified.")
field = "stage2"
fxn = "landcover(!c2_heig!)"
label_class = classify(field, stage)
arcpy.AddField_management(imp, field, "TEXT")
arcpy.CalculateField_management(imp, field, fxn, "PYTHON_9.3", label_class)
arcpy.AddMessage("Complete: Stage2 Impervious Classification")
#
# water
stage = "water"
wat = os.path.join(scratchgdb, stage)
field = "stage2"
fxn = "landcover(!stage1!)"
label_class = classify(field, stage)
arcpy.AddField_management(wat, field, "TEXT")
arcpy.CalculateField_management(wat, field, fxn, "PYTHON_9.3", label_class)
arcpy.AddMessage("Complete: Stage2 Water Classification")