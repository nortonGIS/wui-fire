#-------------------------------------------------------------------------------
# Name:        Generate Fuel Model Tool
# Purpose:     				
#
# Author:      Peter Norton
#
# Created:     04/17/2017
# Copyright:   (c) Peter Norton 2017
#-------------------------------------------------------------------------------

import os
import sys
import arcpy
from arcpy import env
from arcpy.sa import *

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
# Boundary
bnd = os.path.join(inputs,"Gold_Run_test_bnd.shp")

# DEM Inputs
dem = os.path.join(inputs, "dem")
mask = dem

# Heights (DSM - DEM)
heights = os.path.join(inputs, "height")

#sms feature class
sms_fc = os.path.join(inputs, "classified_image.shp")

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

# Set Paths
# stack = os.path.join(toolpath, "Stack")
# composite = os.path.join(stack, "composite")
# height = os.path.join(stack, "height")
# svmpath = os.path.join(toolpath, "SVM")
# training_samples = os.path.join(svmpath, "training_classes.shp")
# outputspath = os.path.join(toolpath, "output")
# sms_fc = os.path.join(scratchgdb, "sms_fc")
# landscape = os.path.join(scratchgdb, "landscape")

# svm_fc = os.path.join(scratchgdb, "svm_fc")

# temp_raster = os.path.join(scratchgdb, "temp_raster")
# farsite_input = os.path.join(toolpath, "input")
# mask = os.path.join(scratchgdb, "dem")
# hex_cents_shp = os.path.join(scratchgdb,"hex_cents")
# bnd_path = os.path.join(scratchgdb,"bnd")
# bnd = arcpy.mapping.Layer(bnd_path)

#SVM
# in_raster = composite
# in_training_features = training_samples
# classifier_definition = os.path.join(svmpath, "svm_class.ecd")
# max_samples = "500"
# additional = height
# attributes = "COLOR;MEAN;STD;COUNT;COMPACTNESS;RECTANGULARITY"
# #arcpy.gp.TrainSupportVectorMachineClassifier(in_raster, in_training_features, classifier_definition, additional, max_samples, attributes)
# arcpy.AddMessage("Classifier definition created.")

# # Classiy Raster
# svm_fuel_model = os.path.join(scratchgdb, "svm_fuel_model")
# #classified = ClassifyRaster(in_raster, classifier_definition, additional)
# #classified.save(svm_fuel_model)
# arcpy.AddMessage("Fuel Model raster generated.")

def classify(x):
	#53 Standard Fuel Models
	#if x == "fuel":
	#	return ("def fuelmodel(x):\\n  if x == \"B\":\\n    return 13\\n  elif x == \"P\": \\n    return 99\\n  elif x == \"W\":\\n    return 98\\n  elif x == \"HG\":\\n    return 105\\n  elif x == \"HS\":\\n    return 143\\n  elif x == \"HT\":\\n    return 9\\n  elif x == \"SG\":\\n    return 122\\n  elif x == \"SS\":\\n    return 145\\n  elif x == \"ST\":\\n    return 165\\n")
	
	# 13 Anderson
	if x == "fuel":
		return ("def fuelmodel(x):\\n  if x == \"B\":\\n    return 13\\n  elif x == \"P\": \\n    return 99\\n  elif x == \"W\":\\n    return 98\\n  elif x == \"G\":\\n    return 1\\n  elif x == \"S\":\\n    return 6\\n  elif x == \"T\":\\n    return 8\\n")
	elif x == "canopy":
		return ("def fuelmodel(x):\\n  if x == \"T\" or x == \"B\":\\n    return 100\\n  return 0")
	elif x == "stand":
		return("def fuelmodel(x):\\n  return x")

#height
mitigation = [[sms_fc, "Gold_Run"]]

for strategy in mitigation:
	landscape = strategy[0]
	mitigation_type = strategy[1]

# 	landscape_fields = [["fuel", "stage2"], ["canopy", "stage2"], ["stand", "height"]]
# 	for field in landscape_fields:
# 		input_field = field[1]
# 		output_field = field[0]
# 		arcpy.AddField_management(landscape, output_field, "INTEGER")
# 		fxn = "fuelmodel(!"+input_field+"!)"
# 		label_class = classify(output_field)
# 		arcpy.CalculateField_management(landscape, output_field, fxn, "PYTHON_9.3", label_class)
# 		arcpy.AddMessage("{0} created.".format(output_field))
# 	arcpy.AddMessage("Landscape created!")

	# FARSITE INPUT VARIABLES
	landscape_lst = ["fuel", "canopy", "stand"]
	elevation_lst = ["slope", "elevation", "aspect"]
	ascii_layers = []



	def convertToAscii(x, y):
		arcpy.AddMessage("...generating asciis ...".format(x))

		for layer in landscape_lst:
		 	ascii_output = os.path.join(outputs, layer + ".asc")
		 	where_clause = layer +" <> 9999"
		 	temp = os.path.join(scratchgdb, "t_"+layer)
		 	temp_raster = os.path.join(scratchgdb, "t_"+layer+"_r")
		 	arcpy.Select_analysis(landscape, temp, where_clause)
		 	arcpy.PolygonToRaster_conversion(temp, layer, temp_raster, "CELL_CENTER", "", dem)
			arcpy.DefineProjection_management(temp_raster,"PROJCS['NAD_1983_UTM_Zone_10N',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-123.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]")
			final = os.path.join(scratchgdb, layer)
			arcpy.CopyRaster_management(temp_raster, final, "", "", "0", "NONE", "NONE", "32_BIT_SIGNED","NONE", "NONE", "GRID", "NONE")
			ready = ExtractByMask(final, mask)
			ready.save(temp_raster)
		 	ascii_layers.append([temp_raster, layer])
		 	arcpy.RasterToASCII_conversion(ready, ascii_output)
		 	arcpy.AddMessage("The {0} file was created.".format(layer))

		for layer in elevation_lst:
			ascii_output = os.path.join(outputs, layer + ".asc")
			temp = os.path.join(scratchgdb, "t_" + layer)
			if layer == "slope":
				arcpy.Slope_3d(dem, temp, "DEGREE")
			elif layer == "aspect":
				arcpy.Aspect_3d(dem, temp)
			elif layer == "elevation":
				temp = dem
			temp_raster = os.path.join(scratchgdb, "t_"+layer+"_r")
			arcpy.CopyRaster_management(temp, temp_raster, "", "", "0", "NONE", "NONE", "32_BIT_SIGNED","NONE", "NONE","GRID", "NONE")
			arcpy.DefineProjection_management(temp_raster,"PROJCS['NAD_1983_UTM_Zone_10N',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-123.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]")
			ready = ExtractByMask(temp_raster, final)
			ready.save(temp_raster)
		 	ascii_layers.append([temp_raster, layer])
			arcpy.RasterToASCII_conversion(ready, ascii_output)
			arcpy.AddMessage("The {0} file was created.".format(layer))

		arcpy.AddMessage("{0} is finished.".format(y))
	convertToAscii(landscape, mitigation_type)
arcpy.AddMessage("All ascii are created.")


#-------------Create Hexagons------------------------------------
#
# num_rings = 2
# i = 1
# def numHexes(num_rings,i):
#    if num_rings == 0:
#        return 1
#    else:
#        return 6*i + numHexes(num_rings-1, i+1)
# num_hexes = numHexes(num_rings,i)

# # Calculate geometry
# extent = bnd.getExtent()
# bnd_xmin = extent.XMin
# bnd_ymin = extent.YMin
# bnd_xmax = extent.XMax
# bnd_ymax = extent.YMax

# deltaX = bnd_xmax - bnd_xmin
# deltaY = bnd_ymax - bnd_ymin

# if deltaX < deltaY:
#     binding = deltaX
# else:
#     binding = deltaY

# a = binding / ((2*(3**.5))+(4*(3**.5)*num_rings))

# meancenter_Y = (bnd_ymax + bnd_ymin) / 2
# meancenter_X = (bnd_xmax + bnd_xmin) / 2
# pts_lst = [[meancenter_X, meancenter_Y]]

# # Create pts_lst

# num_rings += 1
# #Possibly mroe efficient version:
# def create_pts_lst(meancenter_x,meancenter_y,num_rings):
#    if num_rings == 0:
#        return pts_lst
#    def ring_reduce(x,y,num_rings):
#        if num_rings == 0:
#            return
#        else:
#            return create_pts_lst(x,y,num_rings-1)
#    newpts = []
#    p1 = [meancenter_x,meancenter_y+2*(3**.5)*a]
#    if p1 not in pts_lst:
#        pts_lst.append(p1)
#        newpts.append(p1)
#    p2 = [meancenter_x+3*a,meancenter_y+(3**.5)*a]
#    if p2 not in pts_lst:
#        pts_lst.append(p2)
#        newpts.append(p2)
#    p3 = [meancenter_x+3*a,meancenter_y-(3**.5)*a]
#    if p3 not in pts_lst:
#        pts_lst.append(p3)
#        newpts.append(p3)
#    p4 = [meancenter_x,meancenter_y-2*(3**.5)*a]
#    if p4 not in pts_lst:
#        pts_lst.append(p4)
#        newpts.append(p4)
#    p5 = [meancenter_x-3*a,meancenter_y-(3**.5)*a]
#    if p5 not in pts_lst:
#        pts_lst.append(p5)
#        newpts.append(p5)
#    p6 = [meancenter_x-3*a,meancenter_y+(3**.5)*a]
#    if p6 not in pts_lst:
#        pts_lst.append(p6)
#        newpts.append(p6)
#    for point in newpts:
#        ring_reduce(point[0],point[1],num_rings)


# create_pts_lst(meancenter_X,meancenter_Y,num_rings)

# # Hexagon Centroids (hex_pts.shp)
# pt = arcpy.Point()
# geompts_lst = []

# for point in pts_lst:
#     pt.X = point[0]
#     pt.Y = point[1]
#     geompts_lst.append(arcpy.PointGeometry(pt))

# arcpy.CopyFeatures_management(geompts_lst,hex_cents_shp)

# # Thiessen Polygons (thiessen.shp)
# thiessen = os.path.join(scratchgdb,"thiessen")
# arcpy.CreateThiessenPolygons_analysis(hex_cents_shp,thiessen,"ALL")
# arcpy.AddMessage("Thiessen created.")

# # Ignition Hexagons (hex_X.shp in hexes_path(scratch folder)
# arcpy.DefineProjection_management(thiessen, "PROJCS['NAD_1983_StatePlane_California_III_FIPS_0403_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',6561666.666666666],PARAMETER['False_Northing',1640416.666666667],PARAMETER['Central_Meridian',-120.5],PARAMETER['Standard_Parallel_1',37.06666666666667],PARAMETER['Standard_Parallel_2',38.43333333333333],PARAMETER['Latitude_Of_Origin',36.5],UNIT['Foot_US',0.3048006096012192]]")
# arcpy.AddGeometryAttributes_management(thiessen,"AREA")
# hex_area = int(((3*(3**.5))/2)*((2*a)**2))

# fields = ["OBJECTID","SHAPE@AREA"]
# hex_OIDs = []
# with arcpy.da.SearchCursor(thiessen,fields) as cursor:
#     for row in cursor:
#         if int(row[1]) < hex_area+10 and int(row[1]) > hex_area-10:         #NOTE: THERE IS A RANGE FOR THE HEXAGON AREAS.  Shouldn't matter because large areas in feet, and "roughly equal variations" were +-1ft
#             hex_OIDs.append(row[0])


# num_hex = len(hex_OIDs)
# i = 0
# for ID in hex_OIDs:
# 	arcpy.AddMessage("Created for hex {0}:".format(str(i)))
# 	for layer in ascii_layers:
# 		layer_ext = layer[0]
# 		layer_name = layer[1]
# 		OID = str(ID)
# 		ascii_output = os.path.join(farsite_input, str(i)+"_"+layer_name+".asc")
# 		hex_name = os.path.join(scratchgdb,"hex_" + str(i))
# 		where_clause = "OBJECTID = "+ OID
# 		arcpy.Select_analysis(thiessen, hex_name, where_clause)
# 		ready = ExtractByMask(layer_ext, hex_name)
# 		arcpy.RasterToASCII_conversion(ready, ascii_output)
# 		arcpy.AddMessage("    - {0}".format(layer_name))
# 	i += 1
# 	arcpy.AddMessage("Completed {0} of {1}.".format(str(i), num_hex))