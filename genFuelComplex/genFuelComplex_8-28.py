#-------------------------------------------------------------------------------
# Name:        Generate Fuel Model Tool
# Purpose:     				
#
# Author:      Peter Norton
#
# Created:     04/17/2017
# Updated:     08/28/2017
# Copyright:   (c) Peter Norton 2017
#-------------------------------------------------------------------------------

import arcpy
import os
import sys
import ctypes
from arcpy import env
from arcpy.sa import *
arcpy.env.overwriteOutput = True
from tableJoin import one_to_one_join, replace


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

projection = "PROJCS['NAD_1983_UTM_Zone_10N',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-123.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"

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


#Take classified svm, join to classified_image, if objects <> "confused", replace(classified_image, "svm", "object")

#-----------------------------------------------
#-----------------------------------------------
# Generate fuel complex
#

def classify(x):
    
    # Anderson 13
    building = "13"
    tree = "8"
    shrub = "6"
    grass = "1"
    water = "98"
    pavement = "99"
        
        if x == "fuel":
            return ("def classify(x):\\n"+
                    "  if x == \"building\":\\n"+
                    "    return "+building+"\\n"+
                    "  elif x == \"P\": \\n"+
                    "    return "+pavement+"\\n"+
                    "  elif x == \"water\":\\n"+
                    "    return "+water+"\\n"+
                    "  elif x == \"grass\":\\n"+
                    "    return "+grass+"\\n"+
                    "  elif x == \"shrub\":\\n"+
                    "    return "+shrub+"\\n"+
                    "  elif x == \"tree\":\\n"+
                    "    return "+tree+"\\n"
                    )
    
        elif x == "canopy":
            return ("def classify(x):\\n"+
                    "  if x == \"tree\" or x == \"building\":\\n"+
                    "    return 100\\n"+
                    "  return 0"
                    )
        
        elif x == "stand":
            return("def classify(x):\\n"+
                   "  return x"
                   )

def fuelComplex(model, sms_fc):
    model = "13"
    land_cover = sms_fc
	
    land_cover_fields = [["fuel", "object"], ["canopy", "object"], ["stand", "height"]]
    for field in land_cover_fields:
 		input_field = field[1]
 		output_field = field[0]
 		arcpy.AddField_management(land_cover, output_field, "INTEGER")
 		fxn = "classify(!"+input_field+"!)"
 		label_class = classify(output_field)
 		arcpy.CalculateField_management(landscape, output_field, fxn, "PYTHON_9.3", label_class)
 		arcpy.AddMessage("{0} created.".format(output_field))
    
    #-----------------------------------------------
    #-----------------------------------------------
    text = "Fuel Complex created."
    generateMessage(text)
    #-----------------------------------------------

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
			arcpy.DefineProjection_management(temp_raster,projection)
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
			arcpy.DefineProjection_management(temp_raster,projection)
			ready = ExtractByMask(temp_raster, final)
			ready.save(temp_raster)
		 	ascii_layers.append([temp_raster, layer])
			arcpy.RasterToASCII_conversion(ready, ascii_output)
			arcpy.AddMessage("The {0} file was created.".format(layer))

		arcpy.AddMessage("{0} is finished.".format(y))
	convertToAscii(landscape, mitigation_type)
arcpy.AddMessage("All ascii are created.")

#-----------------------------------------------
#-----------------------------------------------
# Create .LCP
#
landscape_file = created.LCP


#-----------------------------------------------
#-----------------------------------------------
# Burn in FlamMap
#

dll = ctypes.cdll.LoadLibrary("C:\\Temp\\FlamMapF.dll") #Need to change to FlamMap folder
fm = getattr(dll, "?Run@@YAHPBD000NN000HHN@Z")
fm.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_double]
fm.restype = ctypes.c_int

Landscape = landscape_file
FuelMoist = "claremont.fms"
OutputFile = "Burn"
FuelModel = "-1"
Windspeed = 20.0	# mph
WindDir = 0.0		# Direction angle in degrees
Weather = "-1"
WindFileName = "-1"
DateFileName = "-1"
FoliarMoist = 100	# 50%
CalcMeth = 0		# 0 = Finney 1998, 1 = Scott & Reinhardt 2001
Res = -1.0

e = fm(Landscape, FuelMoist, OutputFile, FuelModel, Windspeed, WindDir, Weather, WindFileName, DateFileName, FoliarMoist, CalcMeth, Res)
if e > 0:
    arcpy.AddError("Problem with parameter {0}".format(e))

burn_metrics = [ros, fml, fli]

for root, dirs, fm_outputs in os.walk(outputs): #Check to confirm outputs are saved here
    for flamMap_output in fm_outputs:
        if flamMap_output[:-3].lower() in burn_metrics:
            metric = flamMap_output[-4:].lower()
            burn_ascii = os.path.join(scratchgdb, metric+".asc")
            burn_ras = os.path.join(scratchgdb, metric+".tif")
            outTable = os.path.join(scratchgdb, "zonal_"+metric)
            
            os.rename(flamMap_output, burn_ascii)

            arcpy.ASCIIToRaster( burn_ascii,  burn_ras, "FLOAT")
            arcpy.DefineProjection_management(burn_ras, projection)
            z_stat = ZonalStatisticsAsTable(sms_fc, "JOIN", burn_ras, outTable, "NODATA", "MAXIMUM")
            arcpy.AddField_management(outTable, metric, "FLOAT")
            arcpy.CalculateField_management(outTable, metric, "[MAX]")
            one_to_one_join(sms_fc, outTable, metric, "FLOAT")




