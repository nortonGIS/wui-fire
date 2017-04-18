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

# Set Scratch Workspace
scratchws = env.scratchWorkspace
scriptpath = sys.path[0]    
toolpath = os.path.dirname(scriptpath)

# Set environment settings
if not env.scratchWorkspace:
	scratchws = os.path.join(toolpath, "Scratch")
scratchgdb = os.path.join(scratchws, "Scratch.gdb")

# Set Paths
stack = os.path.join(toolpath, "Stack")
composite = os.path.join(stack, "composite")
height = os.path.join(stack, "height")
svmpath = os.path.join(toolpath, "SVM")
training_samples = os.path.join(svmpath, "training_classes.shp")
outputspath = os.path.join(toolpath, "output")
sms_fc = os.path.join(scratchgdb, "sms_fc")
landscape = os.path.join(scratchgdb, "landscape")
dem = os.path.join(scratchgdb, "dem")
temp_raster = os.path.join(scratchgdb, "temp_raster")
farsite_input = os.path.join(toolpath, "input")
mask = os.path.join(scratchgdb, "dem")

#SVM
in_raster = composite
in_training_features = training_samples
classifier_definition = os.path.join(svmpath, "svm_class.ecd")
max_samples = "500"
additional = height
attributes = "COLOR;MEAN;STD;COUNT;COMPACTNESS;RECTANGULARITY"
#arcpy.gp.TrainSupportVectorMachineClassifier(in_raster, in_training_features, classifier_definition, additional, max_samples, attributes)
arcpy.AddMessage("Classifier definition created.")

# Classiy Raster
svm_fuel_model = os.path.join(scratchgdb, "svm_fuel_model")
#classified = ClassifyRaster(in_raster, classifier_definition, additional)
#classified.save(svm_fuel_model)
arcpy.AddMessage("Fuel Model raster generated.")

def classify(x):
	if x == "fuel":
		return ("def fuelmodel(x):\\n  if x == \"B\":\\n    return 0\\n  elif x == \"P\": \\n    return 99\\n  elif x == \"W\":\\n    return 98\\n  elif x == \"HG\":\\n    return 1\\n  elif x == \"HS\":\\n    return 6\\n  elif x == \"HT\":\\n    return 10\\n  elif x == \"SG\":\\n    return 1\\n  elif x == \"SS\":\\n    return 6\\n  elif x == \"ST\":\\n    return 8\\n")
	elif x == "canopy":
		return ("def fuelmodel(x):\\n  if x == \"HT\" or x == \"ST\" or x == \"B\":\\n    return 100\\n  return 0")
	elif x == "stand":
		return("def fuelmodel(x):\\n  return x")

#height


# Fuel Model
stage = "fuel_model"
svm_fuel_model_poly = os.path.join(scratchgdb, "svm_fuel_model_poly")
#arcpy.RasterToPolygon_conversion(svm_fuel_model, svm_fuel_model_poly, "NO_SIMPLIFY", "CLASS_NAME")
#arcpy.Union_analysis([svm_fuel_model_poly, sms_fc], landscape, "ALL", "", "NO_GAPS")
arcpy.AddMessage("union!")


landscape_fields = [["fuel", "CLASS_NAME"], ["canopy", "CLASS_NAME"], ["stand", "height"]]
#for field in landscape_fields:
	#input_field = field[1]
	#output_field = field[0]
	#arcpy.AddField_management(landscape, output_field, "INTEGER")
	#fxn = "fuelmodel(!"+input_field+"!)"
	#label_class = classify(output_field)
	#arcpy.CalculateField_management(landscape, output_field, fxn, "PYTHON_9.3", label_class)	
arcpy.AddMessage("Landscape created!")

# FARSITE INPUT VARIABLES
landscape_lst = ["fuel", "canopy", "stand"]
elevation_lst = ["elevation"] #, "aspect", "slope"]

for layer in elevation_lst:
	temp = os.path.join(scratchgdb, "t_" + layer)
	if layer == "slope":
		arcpy.Slope_3d(dem, temp, "DEGREE", 1)
	elif layer == "aspect":
		arcpy.Aspect_3d(dem, temp)
	elif layer == "elevation":
		temp = dem
	temp_raster = os.path.join(scratchgdb, "t_"+layer+"_r")
	arcpy.CopyRaster_management(temp, temp_raster, "", "", "0", "NONE", "NONE", "32_BIT_SIGNED","NONE", "NONE", "GRID", "NONE")
	arcpy.DefineProjection_management(temp_raster,"PROJCS['NAD_1983_StatePlane_California_III_FIPS_0403_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',6561666.666666666],PARAMETER['False_Northing',1640416.666666667],PARAMETER['Central_Meridian',-120.5],PARAMETER['Standard_Parallel_1',37.06666666666667],PARAMETER['Standard_Parallel_2',38.43333333333333],PARAMETER['Latitude_Of_Origin',36.5],UNIT['Foot_US',0.3048006096012192]]")
	ready = ExtractByMask(temp_raster, mask)
	ascii_output = os.path.join(farsite_input, layer + ".asc")
	arcpy.RasterToASCII_conversion(ready, ascii_output)
	arcpy.AddMessage("The {0} file was created.".format(layer))

for layer in landscape_lst:
 	ascii_output = os.path.join(farsite_input, layer + ".asc")
 	where_clause = layer +" <> 9999"
 	temp = os.path.join(scratchgdb, "t_"+layer)
 	temp_raster = os.path.join(scratchgdb, "t_"+layer+"_r")
 	arcpy.Select_analysis(landscape, temp, where_clause)
 	arcpy.PolygonToRaster_conversion(temp, layer, temp_raster, "CELL_CENTER", "", dem)
	arcpy.DefineProjection_management(temp_raster,"PROJCS['NAD_1983_StatePlane_California_III_FIPS_0403_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',6561666.666666666],PARAMETER['False_Northing',1640416.666666667],PARAMETER['Central_Meridian',-120.5],PARAMETER['Standard_Parallel_1',37.06666666666667],PARAMETER['Standard_Parallel_2',38.43333333333333],PARAMETER['Latitude_Of_Origin',36.5],UNIT['Foot_US',0.3048006096012192]]")
	final = os.path.join(scratchgdb, layer)
	arcpy.CopyRaster_management(temp_raster, final, "", "", "0", "NONE", "NONE", "32_BIT_SIGNED","NONE", "NONE", "GRID", "NONE")
	ready = ExtractByMask(final, mask)
 	arcpy.RasterToASCII_conversion(ready, ascii_output)
 	arcpy.AddMessage("The {0} file was created.".format(layer))