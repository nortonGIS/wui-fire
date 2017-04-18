#-------------------------------------------------------------------------------
# Name:        Classifying Tool
# Purpose:     SMS, Create sms_poly, join zonal attributes of image enhancements, 
#				generate training and testing samples				
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
scratchgdb = os.path.join(scratchws, "Scratch.gdb")
outputspath = os.path.join(toolpath, "output")
naip = os.path.join(toolpath, "naip.tif")
iepath = os.path.join(toolpath, "IE\IE.gdb")
naip_b1 = os.path.join(naip, "Band_1")
naip_b2 = os.path.join(naip, "Band_2")
naip_b3 = os.path.join(naip, "Band_3")
naip_b4 = os.path.join(naip, "Band_4")
height = os.path.join(toolpath, "heights.tif") #height layer

# # Execute SMS Process
# spectral_detail = 10
# spatial_detail = 20
# min_seg_size = 4
# band_inputs = "1,2,3,4"

# sms_raster = os.path.join(scratchgdb, "sms_raster")
# seg_naip = SegmentMeanShift(naip, spectral_detail, spatial_detail, min_seg_size, band_inputs)
# seg_naip.save(sms_raster)

# # Execute SMS Raster to Polygon
# sms = os.path.join(outputspath, "sms.shp")
# arcpy.RasterToPolygon_conversion(seg_naip, sms, "NO_SIMPLIFY", "VALUE")
# arcpy.AddMessage("SMS is created.")

# zonal_tables = []

# # Principle Component Analysis
# pca = os.path.join(iepath, "pca")
# pca2 = os.path.join(pca, "Band_2")
# pca3 = os.path.join(pca, "Band_3")
# pc_list = [pca2, pca3]
# inZoneData = sms
# zoneField = "ID"
# numComponents = 4
# inValueRaster = PrincipalComponents([naip_b1,naip_b2, naip_b3, naip_b4],numComponents)
# inValueRaster.save(pca)
# for pc in pc_list:
# 	pc_num = pc[-1]
# 	if pc_num == "2":
# 		field = "pc2"
# 	else:
# 		field = "pc3"
# 	outTable = os.path.join(scratchgdb, "zonal_pc" + pc[-1])
# 	z_pca = ZonalStatisticsAsTable(inZoneData, zoneField, pc, outTable, "NODATA", "MEAN")
# 	arcpy.AddField_management(outTable, field, "FLOAT")
# 	arcpy.CalculateField_management(outTable, field, "[MEAN]")
# 	zonal_tables.append((outTable, field))
# 	arcpy.AddMessage("PC" + pc[-1] + " is created.")
	


# # NDVI
# field = "ndvi"
# ndvi = os.path.join(iepath, "ndvi")
# inZoneData = sms
# zoneField = "ID"
# outTable = os.path.join(scratchgdb, "zonal_ndvi")
# inValueRaster = (Float(naip_b4)-Float(naip_b1))/(Float(naip_b4)+Float(naip_b1))
# inValueRaster.save(ndvi)
# z_ndvi = ZonalStatisticsAsTable(inZoneData, zoneField, inValueRaster, outTable, "NODATA", "MEAN")
# arcpy.AddField_management(outTable, "ndvi", "FLOAT")
# arcpy.CalculateField_management(outTable, field, "[MEAN]")
# zonal_tables.append((outTable, field))
# arcpy.AddMessage("NDVI is created.")

# # GRVI
# field = "grvi"
# grvi = os.path.join(iepath, "grvi")
# inZoneData = sms
# zoneField = "ID"
# outTable = os.path.join(scratchgdb, "zonal_grvi")
# inValueRaster = Float(naip_b4)/Float(naip_b2)
# inValueRaster.save(grvi)
# z_grvi = ZonalStatisticsAsTable(inZoneData, zoneField, inValueRaster, outTable, "NODATA", "MEAN")
# arcpy.AddField_management(outTable, field, "FLOAT")
# arcpy.CalculateField_management(outTable, field, "[MEAN]")
# zonal_tables.append((outTable, field))
# arcpy.AddMessage("GRVI is created.")

# # NDWI
# field = "ndwi"
# ndwi = os.path.join(iepath, "ndwi")
# inZoneData = sms
# zoneField = "ID"
# outTable = os.path.join(scratchgdb, "zonal_ndwi")
# inValueRaster = (Float(naip_b2)-Float(naip_b4))/(Float(naip_b2)+Float(naip_b4))
# inValueRaster.save(ndwi)
# z_ndwi = ZonalStatisticsAsTable(inZoneData, zoneField, inValueRaster, outTable, "NODATA", "MEAN")
# arcpy.AddField_management(outTable, field, "FLOAT")
# arcpy.CalculateField_management(outTable, field, "[MEAN]")
# zonal_tables.append((outTable, field))
# arcpy.AddMessage("NDWI is created.")

# # Heights
# field = "height"
# inZoneData = sms
# zoneField = "ID"
# outTable = os.path.join(scratchgdb, "zonal_height")
# inValueRaster = height
# z_height = ZonalStatisticsAsTable(inZoneData, zoneField, inValueRaster, outTable, "NODATA", "MEAN")
# arcpy.AddField_management(outTable, field, "FLOAT")
# arcpy.CalculateField_management(outTable, field, "[MEAN]")
# zonal_tables.append((outTable, field))
# arcpy.AddMessage("Height is created.")

# # join zonal tables with SMS
sms_fc = os.path.join(scratchgdb, "sms_fc")	#sms feature class
# arcpy.FeatureClassToFeatureClass_conversion(sms, scratchgdb, "sms_fc", "NO_SIMPLIFY")
# num_tables = len(zonal_tables)
# for i in range(num_tables):
# 	table = zonal_tables[i][0]	#table file
# 	field = zonal_tables[i][1]	#join field
# 	arcpy.AddMessage("Joining: " + field)
# 	arcpy.JoinField_management(sms_fc,"ID", table, "ID", field)
# 	arcpy.AddMessage("Table {0} of {1} was joined.".format(i+1, num_tables))
# arcpy.AddMessage("Tables joined to SMS.")

# # #-----Classifier----------------
# def classify(x, stage):
# 	if stage == "1":
#  		if x == "c_grvi":
#  			return ("def landcover(x):\\n  if x < 0.21:\\n    return \"water\"\\n  elif x < 0.6:\\n    return \"impervious\"\\n  return \"vegetation\"")
#  		elif x == "c_ndwi":
#  			return ("def landcover(x):\\n  if x < 0.085:\\n    return \"vegetation\"\\n  elif x < 0.66:\\n    return \"impervious\"\\n  return \"water\"")
#  		elif x == "c_pc2":
#  			return("def landcover(x):\\n  if x < 100:\\n    return \"water\"\\n  elif x < 190:\\n    return \"impervious\"\\n  return \"vegetation\"")
#  		elif x == "c_pc3":
#  			return("def landcover(x):\\n  if x < 100:\\n    return \"impervious\"\\n  elif x < 150:\\n    return \"vegetation\"\\n  return \"impervious\"")
#  		elif x == "stage1":
#  			return("def landcover(a,b,c,d):\\n    \\n  tot = [a,b,c,d]\\n    \\n  V,I,W = 0,0,0\\n    \\n  for i in tot:\\n        \\n    if i == \"vegetation\":\\n            \\n      V += 1\\n\\n    elif i == \"impervious\":\\n\\n       I += 1\\n \\n    else:\\n            \\n      W += 1\\n\\n  if V > I:\\n\\n    if V > W:\\n      return \"vegetation\"\\n\\n    return \"VW confusion\"\\n\\n  elif I > W:\\n\\n      if I == W:\\n\\n        return \"IW confusion\"\\n\\n      elif I == V:\\n\\n        return \"VI confusion\"\\n\\n      return \"impervious\"\\n\\n  elif W == I:\\n\\n      return \"IW confusion\"\\n\\n  else:\\n\\n      return \"water\"\\n")
#  	elif stage == "vegetation":
#  		if x == "c2_heig":
#  			return("def landcover(x):\\n  if x < 0:\\n    return \"confusion\"\\n  if x < 3:\\n    return \"G\"\\n  elif x < 6:\\n    return \"S\"\\n  elif x < 500:\\n    return \"T\"\\n  return \"confusion\"")
#  		elif x == "c2_grvi":
#  			return("def landcover(x):\\n  if x < 1.3:\\n    return \"S\"\\n  return \"H\"")
#  		elif x == "c2_GRID":
#  			return("def landcover(x):\\n  if x < 150:\\n    return \"Tree/Shrub/Grass\"\\n  return \"Grass\"")
#  		elif x == "stage2":
#  			return("def landcover(a,b,c):\\n  if a in c:\\n    return b + a\\n    return \"confusion\"")
#  	elif stage == "impervious":
#  		if x == "c2_heig":
#  			return("def landcover(x):\\n  if x < 0:\\n    return \"confusion\"\\n  elif x < 5:\\n    return \"P\"\\n  elif x < 50:\\n    return \"B\"\\n  return \"confusion\"")
#  		elif x == "stage2":
#  			return("def landcover(x):\\n  return x")
#  	elif stage == "water":
#  		if x == "c2_heig":
#  			return("def landcover(x):\\n  if x > 5:\\n    return \"confusion\"\\n  return \"W\"")
#  		if x == "stage2":
#  			return("def landcover(x):\\n  return x")


# # # -----stage 1--------
# arcpy.AddMessage("...Executing: Stage 1 Classification...")
# stage = "1"
# s1_indices = ["grvi", "ndwi", "pc2", "pc3"]
# for index in s1_indices:
# 	field = "c_"+index
#  	fxn = "landcover(!"+index+"!)"
#  	arcpy.AddField_management(sms_fc, field, "TEXT")
#  	label_class = classify(field, stage)
#  	arcpy.CalculateField_management(sms_fc, field, fxn, "PYTHON_9.3", label_class)
#  	arcpy.AddMessage("Field: '" + field +"' was classified.")
# field = "stage1"
# fxn = "landcover(!c_grvi!, !c_ndwi!, !c_pc2!, !c_pc3!)"
# label_class = classify(field, stage)
# arcpy.AddField_management(sms_fc, field, "TEXT")
# arcpy.CalculateField_management(sms_fc, field, fxn, "PYTHON_9.3", label_class)
# arcpy.AddMessage("Complete: Stage1 Classification")

# s1_classes = ["vegetation", "water", "impervious"]
# for c in s1_classes:
# 	output = os.path.join(scratchgdb, c)
#  	where_clause = "\""+field+"\" = '" + c + "'"
#  	arcpy.Select_analysis(sms_fc, output, where_clause)

# # # -----stage 2--------

# arcpy.AddMessage("...Executing: Stage 2 Classification...")

# # vegetation
stage = "vegetation"
veg = os.path.join(scratchgdb, stage)
# veg_indices = ["height", "grvi", "GRIDCODE"]
veg_classes = [veg, ["HG", "HS", "HT", "SG", "SS", "ST"]]
# for index in veg_indices:
# 	field = "c2_"+index[:4]
# 	fxn = "landcover(!"+index+"!)"
# 	arcpy.AddField_management(veg, field, "TEXT")
# 	label_class = classify(field, stage)
# 	arcpy.CalculateField_management(veg, field, fxn, "PYTHON_9.3", label_class)
# 	arcpy.AddMessage("Vegetation field: '"+ field + "' was classified.")
# field = "stage2"
# fxn = "landcover(!c2_heig!, !c2_grvi!, !c2_GRID! )"
# label_class = classify(field, stage)
# arcpy.AddField_management(veg, field, "TEXT")
# arcpy.CalculateField_management(veg, field, fxn, "PYTHON_9.3", label_class)
# arcpy.AddMessage("Complete: Stage2 Vegetation Classification")

# # impervious
stage = "impervious"
imp = os.path.join(scratchgdb, stage)
# imp_indices = ["height"]
imp_classes = [imp, ["B", "P"]]
# for index in imp_indices:
# 	field = "c2_"+index[:4]
# 	fxn = "landcover(!"+index+"!)"
# 	arcpy.AddField_management(imp, field, "TEXT")
# 	label_class = classify(field, stage)
# 	arcpy.CalculateField_management(imp, field, fxn, "PYTHON_9.3", label_class)
# 	arcpy.AddMessage("Impervious field: '"+ field + "' was classified.")
# field = "stage2"
# fxn = "landcover(!c2_heig!)"
# label_class = classify(field, stage)
# arcpy.AddField_management(imp, field, "TEXT")
# arcpy.CalculateField_management(imp, field, fxn, "PYTHON_9.3", label_class)
# arcpy.AddMessage("Complete: Stage2 Impervious Classification")
# #
# # water
stage = "water"
wat = os.path.join(scratchgdb, stage)
# wat_indices = ["height"]
wat_classes = [wat, ["W"]]
# for index in wat_indices:
# 	field = "c2_"+index[:4]
# 	fxn = "landcover(!"+index+"!)"
# 	arcpy.AddField_management(wat, field, "TEXT")
# 	label_class = classify(field, stage)
# 	arcpy.CalculateField_management(wat, field, fxn, "PYTHON_9.3", label_class)
# 	arcpy.AddMessage("Water field: '"+ field + "' was classified.")
# field = "stage2"
# fxn = "landcover(!c2_heig!)"
# label_class = classify(field, stage)
# arcpy.AddField_management(wat, field, "TEXT")
# arcpy.CalculateField_management(wat, field, fxn, "PYTHON_9.3", label_class)
# arcpy.AddMessage("Complete: Stage2 Water Classification")

stage2classes = [veg_classes, imp_classes, wat_classes]
# arcpy.AddMessage("Complete: Stage2 Classification")

# GENERATE TRAINING AND TESTING SAMPLES
from random import randint

svmpath = os.path.join(toolpath, "SVM") 
samplespath = os.path.join(svmpath, "samples")
training_gdb = os.path.join(samplespath, "training.gdb")
training_samples = os.path.join(training_gdb, "training_fc")
testing_samples = os.path.join(training_gdb, "testing_fc")

arcpy.AddMessage("...Generating Samples...")

# Trees
def gen_samples(classes):
	# returns a list of random rows equal to the desired number of training samples
	def gen_training(num_training, num_samples):
		def rand_samples(count, sample_selection, num_training):
			while count < num_training:
				row_num = randint(1, num_samples)
				if row_num in sample_selection:
					return rand_samples(count, sample_selection, num_training)
				sample_selection.append(row_num)
				count += 1
			return sample_selection
		return rand_samples(0, [], num_training)

	landcover = classes[0]
	labels = classes[1]
	for label in labels:
		samples = os.path.join(training_gdb, label + "_samples")
		training = os.path.join(training_gdb, label + "_training")
		#testing = os.path.join(training_gdb, label + "_testing")
		where_clause = "\"stage2\"= '" + label + "'"
		arcpy.Select_analysis(landcover, samples, where_clause)
		arcpy.CalculateField_management(samples, "ID", "[OBJECTID]")
		
		num_samples = int(str(arcpy.GetCount_management(samples)))
		if num_samples > 0:		
			num_training = 800
			#num_testing = 150
			row_num = gen_training(num_training, num_samples)
			where_clause = "("
			for row in row_num:
				where_clause += str(row) + ", "
			where_clause = where_clause[:-2] + ")"
			arcpy.Select_analysis(samples, training, "ID in " + where_clause)
			#arcpy.Select_analysis(samples, testing, "ID not in " + where_clause)
			arcpy.AddMessage("Created {0} {1} training samples.".format(num_training, label))

			#arcpy.AddMessage("Created {0} {1} testing samples.".format(num_testing, label))
			training_merge.append(training)
			#testing_merge.append(testing)
		else:
			arcpy.AddMessage("Samples for " + label + " cannot be created.")
training_merge = []
testing_merge = []
for classes in stage2classes:
	gen_samples(classes)
arcpy.Merge_management(training_merge, training_samples)
train = os.path.join(training_gdb, "train")
arcpy.Dissolve_management(training_samples, train, "stage2")

#FORMAT TRAINING
#training_fields = ["Classname", "Classvalue", "RED", "GREEN", "BLUE", ]
#arcpy.AddField_management(train, "", "INTEGER")
#arcpy.AddMessage("All training samples created.")
#arcpy.Merge_management(testing_merge, testing_samples)
#arcpy.AddMessage("All testing samples created.")

# Layer stack
stack = os.path.join(toolpath, "Stack")
layers = ["pc2", "grvi", "ndwi"]
additional = ["pc3", "ndvi", "height", "GRIDCODE"]
bands = []
composite = os.path.join(stack, "composite")
for layer in layers:
	out_rasterdataset = os.path.join(stack, layer)
	arcpy.PolygonToRaster_conversion(sms_fc, layer, out_rasterdataset, "", "", 1)
	bands.append(out_rasterdataset)
	arcpy.AddMessage("{0} created as band.".format(layer))
for layer in additional:
	additional_raster = os.path.join(stack, layer)
	arcpy.PolygonToRaster_conversion(sms_fc, layer, additional_raster, "", "", 1)
	arcpy.AddMessage("{0} created as band.".format(layer))
arcpy.CompositeBands_management(bands, composite)
arcpy.DefineProjection_management(composite,"PROJCS['NAD_1983_StatePlane_California_III_FIPS_0403_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',6561666.666666666],PARAMETER['False_Northing',1640416.666666667],PARAMETER['Central_Meridian',-120.5],PARAMETER['Standard_Parallel_1',37.06666666666667],PARAMETER['Standard_Parallel_2',38.43333333333333],PARAMETER['Latitude_Of_Origin',36.5],UNIT['Foot_US',0.3048006096012192]]")
arcpy.AddMessage("Composite created with {0}, {1}, and {2}.".format(layers[0], layers[1], layers[2]))
