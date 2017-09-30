#-------------------------------------------------------------------------------
# Name:        genMitigation Tool
# Purpose:     
#
#             Primary Steps:
#               - 

# Author:      Peter Norton
#
# Created:     09/29/2017
# Updated:     -
# Copyright:   (c) Peter Norton and Matt Ashenfarb 2017
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# USER LOG
date = "9_29"
# Summary
#
#
#

# Geographic Data
location_name = "Tahoe"
bioregion = "Tahoe" #[Tahoe, Richmond]
projection = "UTMZ10"  #["UTMZ10", "UTMZ11", "SPIII", "SPIV"]

# Settings
coarsening_size = "5" #meters
tile_size = "1" #square miles
model = "13"  # Fuel Model set
pipe_analysis = "yes"  # Assess infrastructure
buff_distance = "1000 feet" # Buffer around infrastructure

# Mitigation Strategy 
mitigation_surface = "path"
mitigation_height = 0
buff_distance = "30 FEET"

# inputs
input_bnd = "bnd.shp" 
input_naip = "naip.tif"
input_heights = "heights.tif"
input_dem = "dem.tif"
input_pipeline = "pipeline.shp"

input_fuel_moisture = "fuel_moisture.fms"
input_wind = ""
input_weather = ""
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Processing - DO NOT MODIFY BELOW
#-----------------------------------------------
#-----------------------------------------------

# Import modules
import arcpy
import os
import sys
from arcpy import env
from arcpy.sa import *
arcpy.env.overwriteOutput = True

# Create new project folder and set environment
scriptpath = sys.path[0] # Find script
toolpath = os.path.dirname(scriptpath)  # Find parent directory
current_project = os.path.join(toolpath)

#Setting inputs, outputs, scratchws, scratch.gdb
inputs = os.path.join(current_project, "Inputs")
outputs = os.path.join(current_project, "Outputs")
scratchws = os.path.join(current_project, "Scratch") 
scratchgdb = os.path.join(scratchws, "Scratch.gdb")   
dll_path = os.path.join(current_project, "Scripts")

#-----------------------------------------------
#-----------------------------------------------
# Set Global Variables
# Raw inputs
raw_naip = os.path.join(inputs, input_naip) # NAIP Imagery at 1m res
raw_heights = os.path.join(inputs, input_heights) # Heights
raw_dem = os.path.join(inputs, input_dem) # DEM
pipeline = os.path.join(inputs, input_pipeline) # Pipeline 
fuel_moisture = os.path.join(inputs, input_fuel_moisture) # Fuel Moisture
wind = os.path.join(inputs, input_wind) # Wind
weather = os.path.join(inputs, input_weather) # Weather
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Set Create Layers
# Inputs
bnd_zones = os.path.join(inputs, input_bnd) # Bounding box for each tile

# Outputs
asset = os.path.join(outputs, "pipeline.shp")
pipe_buffer = os.path.join(outputs, "pipe_buffer.shp")

mitigated = os.path.join(outputs, "mitigated.shp")
classified = os.path.join(outputs, "classified.shp")
scaled_heights = os.path.join(outputs, "scaled_heights.tif")  # Heights in project units
scaled_dem = os.path.join(outputs, "scaled_dem.tif")  # DEM in project units

naip = os.path.join(outputs, "naip.tif")  # NAIP in project units
naip_b1 = os.path.join(naip, "Band_1")
naip_b2 = os.path.join(naip, "Band_2")
naip_b3 = os.path.join(naip, "Band_3")
naip_b4 = os.path.join(naip, "Band_4")
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Alert function with step counter
count = 1
def generateMessage(text):
  global count
  arcpy.AddMessage("Step " + str(count) + ": " +text),
  count += 1

# Details
arcpy.AddMessage("Site: "+location_name)
arcpy.AddMessage("Projection: "+projection)
arcpy.AddMessage("Resolution: "+coarsening_size + "m")
arcpy.AddMessage("Fuel Model: "+model)
arcpy.AddMessage("-----------------------------")
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Projection and scaling information
if projection == "UTMZ10":
  scale_height = 1
  scale_naip = 1
  unit = "Meters"
  projection = "PROJCS['NAD_1983_UTM_Zone_10N',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-123.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"
elif projection == "UTMZ11":
  scale_height = 1
  scale_naip = 1
  unit = "Meters"
  projection = "PROJCS['NAD_1983_UTM_Zone_11N',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-117.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"
elif projection == "SPIII":
  scale_height = 1
  scale_naip = 3.28084
  unit = "Feet"
  projection = "PROJCS['NAD_1983_StatePlane_California_III_FIPS_0403_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',6561666.666666666],PARAMETER['False_Northing',1640416.666666667],PARAMETER['Central_Meridian',-120.5],PARAMETER['Standard_Parallel_1',37.06666666666667],PARAMETER['Standard_Parallel_2',38.43333333333333],PARAMETER['Latitude_Of_Origin',36.5],UNIT['Foot_US',0.3048006096012192]]"
elif projection == "SPIV":
  scale_height = 1
  scale_naip = 3.28084
  unit = "Feet"
  projection = "PROJCS['NAD_1983_StatePlane_California_VI_FIPS_0406_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',6561666.666666666],PARAMETER['False_Northing',1640416.666666667],PARAMETER['Central_Meridian',-116.25],PARAMETER['Standard_Parallel_1',32.78333333333333],PARAMETER['Standard_Parallel_2',33.88333333333333],PARAMETER['Latitude_Of_Origin',32.16666666666666],UNIT['Foot_US',0.3048006096012192]]"
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
arcpy.AddMessage("-----------------------------")
arcpy.AddMessage("Processing Started.")
arcpy.AddMessage("-----------------------------")
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
text = "Creating "+str(buff_distance)+" buffer around pipeline."
generateMessage(text)

#Variables
classified_no_asset = os.path.join(scratchgdb, "classified_no_asset")
pipe_seg = os.path.join(outputs, "pipe_seg.shp")
pipe_rast = os.path.join(scratchgdb, "pipe_rast")
pipe_proj = os.path.join(scratchgdb, "pipe_proj")


# Clip pipeline to study area, buffer pipeline
arcpy.Clip_analysis(pipeline, bnd_zones, asset)
arcpy.Buffer_analysis(asset, pipe_buffer, buff_distance, "", "", "ALL")
arcpy.PolygonToRaster_conversion(pipe_buffer, "FID", pipe_rast, "CELL_CENTER", "", coarsening_size)#int(coarsening_size))
arcpy.ProjectRaster_management(pipe_rast, pipe_proj, classified, "BILINEAR", str(coarsening_size) +" "+str(coarsening_size))
arcpy.RasterToPolygon_conversion(pipe_proj, pipe_buffer, "NO_SIMPLIFY")


arcpy.Erase_analysis(classified_unmitigated, pipe_buffer, classified_no_asset)
# Removing unnecessary fields for training samples
classified_fields = [[f.name, f.type] for f in arcpy.ListFields(classified)]
asset_fields = [f.name for f in arcpy.ListFields(pipe_buffer)]
add_fields = []
for f_name,f_type in classified_fields:
 if f_name not in asset_fields:
   add_fields.append([f_name, f_type])
for f_name, f_type in add_fields:
	arcpy.AddField_management(pipe_buffer, f_name, f_type)
	if f_name == "height":
		arcpy.CalculateField_management(pipe_buffer, f_name, mitigation_height)
	elif f_name == "S2":
		arcpy.CalculateField_management(pipe_buffer, f_name, mitigation_surface)
#-----------------------------------------------
#-----------------------------------------------
text = "Merging mitigated buffer back to classified image."
generateMessage(text)

# Merging all layers back together as classified layer
arcpy.Merge_management([pipe_buffer, classified], mitigated)
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
text = "Assigning fuel models and creating canopy cover assessments."
generateMessage(text)

# Variables
land_cover = m_classified
land_cover_fields = [["fuel", "S2"], ["canopy", "S2"], ["stand", "height"]]

def classify(model, x):
   
 # Anderson 13 fuel models
 if model == "13":
   building = "10"
   tree = "10"
   shrub = "6"
   grass = "1"
   water = "98"
   path = "99"
 elif model != "13":
   #-----------------------------------------------
   #-----------------------------------------------
   text = "Cannot classify fuels. Only Anderson 13 are available."
   generateMessage(text)
   #-----------------------------------------------
   classify("13", output_field)
 if x == "fuel":
   return ("def classify(x):\\n"+
           "  if x == \"building\":\\n"+
           "    return "+building+"\\n"+
           "  elif x == \"path\": \\n"+
           "    return "+path+"\\n"+
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
           "    return 75\\n"+ # 75% canopy cover b/c 
           "  return 0"
           )
 # Returns height attribute - May delete if cannot include into .LCP
 elif x == "stand":
   return("def classify(x):\\n"+
          "  return x"
          )

for field in land_cover_fields:
 input_field = field[1]
 output_field = field[0]
 arcpy.AddField_management(land_cover, output_field, "INTEGER")
 fxn = "classify(!"+input_field+"!)"
 label_class = classify(model, output_field)
 arcpy.CalculateField_management(land_cover, output_field, fxn, "PYTHON_9.3", label_class)

#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
text = "Fuel complex created."
generateMessage(text)
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
text = "Creating inputs for Landscape File."
generateMessage(text)

# Variables
fuel_lst = ["fuel", "canopy", "stand"]
elevation_lst = ["slope", "elevation", "aspect"]
ascii_layers = []
fuel = os.path.join(outputs, "m_fuel.asc")

def convertToAscii(x, landscape_elements):
 
 for layer in landscape_elements:

   # Variables
   ascii_output = os.path.join(outputs, "m_"layer + ".asc")
   where_clause = layer +" <> 9999"
   temp = os.path.join(scratchgdb, "mt_"+layer)
   temp_raster = os.path.join(scratchgdb, "mt_"+layer+"_r")
   final = os.path.join(scratchgdb, "m_"+layer)

   # Selecting layer and converting to raster
   if layer in fuel_lst:
     arcpy.Select_analysis(land_cover, temp, where_clause)
     arcpy.PolygonToRaster_conversion(temp, layer, temp_raster, "CELL_CENTER", "", scaled_dem)
   elif layer in elevation_lst:

     # Calculating elevation derived layers
     if layer == "slope":
       arcpy.Slope_3d(scaled_dem, temp_raster, "DEGREE")
     elif layer == "aspect":
       arcpy.Aspect_3d(scaled_dem, temp_raster)
     elif layer == "elevation":
       temp_raster = scaled_dem

   # Preparing raster for LCP specifications
   arcpy.CopyRaster_management(temp_raster, final, "", "", "0", "NONE", "NONE", "32_BIT_SIGNED","NONE", "NONE", "GRID", "NONE")
   arcpy.DefineProjection_management(temp_raster, projection)

   # Extracting layer by analysis area
   ready = ExtractByMask(final, naip)
   ready.save(temp_raster)

   # Converting to ascii format and adding to list for LCP tool
   arcpy.RasterToASCII_conversion(ready, ascii_output)
   ascii_layers.append(ascii_output)

   text = "The mitigated "+layer+" ascii file was created."
   generateMessage(text)

# Coding note: Check to see that lists are concatenated
convertToAscii(land_cover, fuel_lst + elevation_lst)

#-----------------------------------------------
#-----------------------------------------------
text = "Mitigation ASCIIs created for LCP."
generateMessage(text)
#-----------------------------------------------
#-----------------------------------------------