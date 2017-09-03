#-------------------------------------------------------------------------------
# Name:        generateTraining Tool
# Purpose:     Takes raw naip and lidar data, uses thresholds to classify data
#              and generates training samples by identifying tight thresholds.
#
#             Steps:
#               - Segment heights into unique objects using SMS
#               - Calculate and join mean height to objects with Zonal Stastics
#               - Separate ground and nonground features and mask naip
# Author:      Peter Norton
#
# Created:     05/25/2017
# Updated:     08/23/2017
# Copyright:   (c) Peter Norton and Matt Ashenfarb 2017
#-------------------------------------------------------------------------------
# ---------------------------------------------------------------------------

# Import modules
import arcpy
import os
import sys
from arcpy import env
from arcpy.sa import *
arcpy.env.overwriteOutput = True
from tableJoin import one_to_one_join
from random import randint
from genFuelComplex_8-28 import fuelComplex

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

# Set projection. OPTIONS = ["UTMZ10", "UTMZ11", "SPIII", "SPIV"]
projection = "SPIII"

# NAIP Imagery Inputs
raw_naip = os.path.join(inputs, "naip.tif")
naip = os.path.join(outputs, "naip.tif")
naip_b1 = os.path.join(naip, "Band_1")
naip_b2 = os.path.join(naip, "Band_2")
naip_b3 = os.path.join(naip, "Band_3")
naip_b4 = os.path.join(naip, "Band_4")

# Heights (DSM- DEM)
raw_heights = os.path.join(inputs, "heights.tif")
heights = os.path.join(outputs, "heights.tif")

# Max number of training samples
num_training = 100
sample_type = "random" #OPTIONS = ["random", "all"]

# Coarsen cell size in meters
coarsening_size = "5"

#-----------------------------------------------
# Outputs
#-----------------------------------------------

#segmented naip
naip_sms = os.path.join(scratchgdb, "naip_sms")

#feature objects
sms_fc = os.path.join(scratchgdb, "sms_fc")

#classified objects (training_samples)
classified_image = os.path.join(outputs, "classified_image.shp")

#-----------------------------------------------
# Alert function
#-----------------------------------------------
count = 1
def generateMessage(text):
  global count
  arcpy.AddMessage("Step " + str(count) + ": " +text),
  count += 1

#-----------------------------------------------
#-----------------------------------------------
# Processing - DO NOT MODIFY
#-----------------------------------------------
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Projection information
#
if projection == "UTMZ10":
  scale_height = 0.3048
  unit = meter
  projection = "PROJCS['NAD_1983_UTM_Zone_10N',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-123.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"
elif projection == "UTMZ11":
  scale_height = 0.3048
  unit = meter
  projection = "PROJCS['NAD_1983_UTM_Zone_11N',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-117.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"
elif projection == "SPIII":
  scale_height = 1
  unit = feet
  projection = "PROJCS['NAD_1983_StatePlane_California_III_FIPS_0403_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',6561666.666666666],PARAMETER['False_Northing',1640416.666666667],PARAMETER['Central_Meridian',-120.5],PARAMETER['Standard_Parallel_1',37.06666666666667],PARAMETER['Standard_Parallel_2',38.43333333333333],PARAMETER['Latitude_Of_Origin',36.5],UNIT['Foot_US',0.3048006096012192]]"
elif projection == "SPIV":
  scale_height = 1
  unit = feet
  projection = "PROJCS['NAD_1983_StatePlane_California_VI_FIPS_0406_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',6561666.666666666],PARAMETER['False_Northing',1640416.666666667],PARAMETER['Central_Meridian',-116.25],PARAMETER['Standard_Parallel_1',32.78333333333333],PARAMETER['Standard_Parallel_2',33.88333333333333],PARAMETER['Latitude_Of_Origin',32.16666666666666],UNIT['Foot_US',0.3048006096012192]]"


#-----------------------------------------------
#-----------------------------------------------
# Resample raw_NAIP and raw_heights to align cells
# Resampled layers will be saved to output folder
#
naip_cell_size = str(arcpy.GetRasterProperties_management(raw_naip, "CELLSIZEX", "")) + " " + str(arcpy.GetRasterProperties_management(raw_naip, "CELLSIZEX", ""))
arcpy.Resample_management(raw_naip, naip, naip_cell_size, "")
arcpy.DefineProjection_management(naip, projection)

arcpy.env.snapRaster = naip
arcpy.Resample_management(raw_heights, heights, naip_cell_size, "")
scaled_heights = Float(heights) * scale_height
arcpy.DefineProjection_management(scale_heights, projection)
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
text = "Creating boundary."
generateMessage(text)
#-----------------------------------------------
bnd = os.path.join(inputs, "bnd.shp")
null_boundary = Int(naip) * 0
arcpy.RasterToPolygon_conversion(null_boundary, bnd, "NO_SIMPLIFY", "VALUE")

#-----------------------------------------------
#-----------------------------------------------
text = "Creating ground and nonground masks."
generateMessage(text)
#-----------------------------------------------
#-----------------------------------------------

#Variables
ground_mask_poly = os.path.join(scratchgdb, "ground_mask_poly")
nonground_mask_poly = os.path.join(scratchgdb, "nonground_mask_poly")
ground_mask_raw = os.path.join(scratchgdb, "ground_mask_raw")
nonground_mask_raw = os.path.join(scratchgdb, "nonground_mask_raw")
ground_dissolve_output = os.path.join(scratchgdb, "ground_mask_dis")
nonground_dissolve_output = os.path.join(scratchgdb, "nonground_mask_dis")
ground_mask_raster = os.path.join(scratchgdb, "ground_mask_raster")
nonground_mask_raster = os.path.join(scratchgdb, "nonground_mask_raster")
nonground_mask_resample = os.path.join(scratchgdb, "nonground_mask_resample")
ground_mask_resample = os.path.join(scratchgdb, "ground_mask_resample")


#Find minimum cell area
min_cell_area = int(float(str(arcpy.GetRasterProperties_management(naip, "CELLSIZEX", "")))**2)+1
where_clause = "Shape_Area > " + str(min_cell_area)

#Create masks for ground and nonground features according to ground_ht_threshold
ground_ht_threshold = 2 #ft

mask = SetNull(Int(heights),Int(heights),"VALUE > " + str(ground_ht_threshold))
arcpy.RasterToPolygon_conversion(mask, ground_mask_raw, "NO_SIMPLIFY", "VALUE", )
arcpy.Dissolve_management(ground_mask_raw, ground_dissolve_output)

#Find cell size of imagery
cell_size = str(arcpy.GetRasterProperties_management(naip, "CELLSIZEX", ""))

arcpy.Erase_analysis(bnd, ground_dissolve_output, nonground_mask_raw)

arcpy.PolygonToRaster_conversion(nonground_mask_raw, "ID", nonground_mask_raster, "CELL_CENTER", "", cell_size)
arcpy.RasterToPolygon_conversion(nonground_mask_raster, nonground_mask_raw, "NO_SIMPLIFY", "VALUE")
where_clause = "Shape_Area > " + str(min_cell_area)
arcpy.Select_analysis(nonground_mask_raw, nonground_mask_poly, where_clause)

arcpy.Erase_analysis(bnd, nonground_mask_poly, ground_mask_poly)
arcpy.PolygonToRaster_conversion(ground_mask_poly, "ID", ground_mask_raster, "CELL_CENTER", "", cell_size)
arcpy.RasterToPolygon_conversion(ground_mask_raster, ground_mask_raw, "NO_SIMPLIFY", "VALUE")
arcpy.Select_analysis(ground_mask_raw, ground_mask_poly, where_clause)

arcpy.Erase_analysis(bnd, ground_mask_poly, nonground_mask_poly)

#-----------------------------------------------
#-----------------------------------------------
#Segment each surface separately using SMS
#

spectral_detail = 20
spatial_detail = 20
min_seg_size = 2

surfaces = ["ground", "nonground"]
naip_lst = []
ground_mask_poly = []

for surface in surfaces:

# Try running SMS on each surface
  sms_raster = os.path.join(scratchgdb, surface+"_sms_raster")
  naip_fc =  os.path.join(scratchgdb, surface + "_naip_fc")
  mask_poly = os.path.join(scratchgdb, surface+ "_mask_poly")
  mask = mask_poly
  sms = os.path.join(scratchgdb, surface+"_sms")
  naip_mask = os.path.join(scratchgdb,surface + "_naip")
  mask_raw = os.path.join(scratchgdb, surface + "_mask_raw")
  dissolve_output = os.path.join(scratchgdb, surface + "_mask_dis")

  #-----------------------------------------------
  #-----------------------------------------------
  text = "Extracting NAIP imagery by "+ surface + " mask."
  generateMessage(text)
  #-----------------------------------------------
  this = ExtractByMask(naip, mask)
  this.save(naip_mask)
  surface_raster_slide = Con(IsNull(Float(naip_mask)),-10000,Float(naip_mask))

  #-----------------------------------------------
  #-----------------------------------------------
  text = "Segmenting NAIP imagery into "+ surface + " objects."
  generateMessage(text)
  #-----------------------------------------------

  seg_naip = SegmentMeanShift(surface_raster_slide, spectral_detail, spatial_detail, min_seg_size) #, band_inputs)
  seg_naip.save(sms_raster)
  arcpy.RasterToPolygon_conversion(sms_raster, naip_fc, "NO_SIMPLIFY", "VALUE")

  #-----------------------------------------------
  #-----------------------------------------------
  text = "Clipping "+ surface + " objects to mask."
  generateMessage(text)
  #-----------------------------------------------
  arcpy.Clip_analysis(naip_fc, mask_poly, sms)

  naip_lst.extend([sms])

#-----------------------------------------------
#-----------------------------------------------
text = "Merging ground and nonground objects."
generateMessage(text)
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Merge surface layers
#

arcpy.Merge_management(naip_lst, sms_fc)
arcpy.AddField_management(sms_fc, "JOIN", "INTEGER")
rows = arcpy.UpdateCursor(sms_fc)
i = 1
for row in rows:
  row.setValue("JOIN", i)
  rows.updateRow(row)
  i+= 1


# -----------------------------------------------
# -----------------------------------------------
text = "Creating image enhancements."
generateMessage(text)
# -----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Create Image Enhancements and join to objects
#

image_enhancements = ["ndvi", "ndwi", "gndvi", "osavi", "height"]


def normalize(index):
    return (2 * (Float(index) - Float(index.minimum)) / (Float(index.maximum) - Float(index.minimum))) - 1

for field in image_enhancements:

  enhancement_path = os.path.join(scratchgdb, field+"_raster")
  outTable = os.path.join(scratchgdb, "zonal_"+field)

  # -----------------------------------------------
  # -----------------------------------------------
  text = "Calculating and joining mean " + field + " to each object."
  generateMessage(text)
  # -----------------------------------------------

  ie = os.path.join(scratchgdb, field)

  if field == "ndvi":
    inValueRaster = ((Float(naip_b4))-(Float(naip_b1))) / ((Float(naip_b4))+(Float(naip_b1)))
    inValueRaster.save(enhancement_path)
    ie = enhancement_path
  elif field == "ndwi":
    inValueRaster = ((Float(naip_b2))-(Float(naip_b4))) / ((Float(naip_b2))+(Float(naip_b4)))
    inValueRaster.save(enhancement_path)
    ie = enhancement_path
  elif field == "gndvi":
    inValueRaster = ((Float(naip_b4))-(Float(naip_b2))) / ((Float(naip_b4))+(Float(naip_b2)))
    inValueRaster.save(enhancement_path)
    ie = enhancement_path
  elif field == "osavi":
    inValueRaster = normalize((1.5 * (Float(naip_b4) - Float(naip_b1))) / ((Float(naip_b4)) + (Float(naip_b1)) + 0.16))
    inValueRaster.save(enhancement_path)
    ie = enhancement_path
  elif field == "height":
    enhancement_path = heights

  z_stat = ZonalStatisticsAsTable(sms_fc, "JOIN", enhancement_path, outTable, "NODATA", "MEAN")

  arcpy.AddField_management(outTable, field, "FLOAT")
  arcpy.CalculateField_management(outTable, field, "[MEAN]")
  one_to_one_join(sms_fc, outTable, field, "FLOAT")
arcpy.DefineProjection_management(sms_fc, projection)

#-----------------------------------------------
#-----------------------------------------------
# Fuzzy rule classifier
#
#Primitive types = [vegetation, impervious, water, confusion]
#Land cover types = [tree, shrub, grass, pavement, building, water]
#
# Stages:
#   1. Classify object based on majority primitive type
#   2. Classify each primitive object based on IE and height

def classify(stage, field):
  if stage == "primitive":
    if field == "c_ndvi":
        #-----------------------------------------------
        #-----------------------------------------------
        # Thresholds
        imp = "<= -0.05" #[-1, -0.05]
        veg = ">= 0.02"  #[0.02, 1]
        #con = ""       #(-0.05, 0.02)
        #-----------------------------------------------
        return("def landcover(x):\\n"+
               "  if x "+imp+":\\n"+
               "    return \"impervious\"\\n"+
               "  elif x "+veg+":\\n"+
               "    return \"vegetation\"\\n"+
               "  return \"confusion\""
               )

    elif field == "c_ndwi":
        #-----------------------------------------------
        #-----------------------------------------------
        # Thresholds
        imp = "<= 0.66"  #[0.085, 0.66]
        veg = "<= 0.085" #[-1, 0.085]
        #wat = ""    #(0.85, 1)
        #-----------------------------------------------
        return ("def landcover(x):\\n"+
                "  if x "+veg+":\\n"+
                "    return \"vegetation\"\\n"+
                "  elif x "+imp+":\\n"+
                "    return \"impervious\"\\n"+
                "  return \"water\""
                )
    
    elif field == "c_gndvi":
        #-----------------------------------------------
        #-----------------------------------------------
        # Thresholds
        imp = "<= -0.03" #[-1, -0.03]
        veg = ">= 0.16"  #[0.16, 1]
        #con = ""   #(-0.03, 0.16)
        #-----------------------------------------------
        return ("def landcover(x):\\n"+
                "  if x "+imp+":\\n"+
                "    return \"impervious\"\\n"+
                "  elif x "+veg+":\\n"+
                "    return \"vegetation\"\\n"+
                "  return \"confusion\""
                )

    elif field == "c_osavi":
        #-----------------------------------------------
        #-----------------------------------------------
        # Thresholds
        imp = "<= 0"     #[-1,0]
        veg = ">= 0.2"   #[0.2, 1]
        #con = ""
        #-----------------------------------------------
        return ("def landcover(x):\\n"+
                "  if x "+imp+":\\n"+
                "    return \"impervious\"\\n"+
                "  elif x "+veg+":\\n"+
                "    return \"vegetation\"\\n"+
                "  return \"confusion\""
                )
    
    elif field == "prim":
        # Need to evaluate TCC and height for special cases
        #   - (dry grass) if under 2ft and TCC == yellow, then veg
        #   - (dry tree) if above 6ft and tcc == brown greenish, then veg
        return("def landcover(a,b,c,d):\\n"+
               "  ies = [a,b,c,d]\\n"+
               "  V,I,W,C = 0,0,0,0\\n"+
               "  for ie in ies:\\n"+
               "    if ie == \"vegetation\":\\n"+
               "      V += 1\\n"+
               "    elif ie == \"impervious\":\\n"+
               "      I += 1\\n"+
               "    elif ie == \"water\":\\n"+
               "      return \"water\"\\n"+
               "    else:\\n"+
               "      C += 1\\n"+
               "  if V > I:\\n"+
               "    if V > C:\\n"+
               "      return \"vegetation\"\\n"+
               "    return \"V confusion\"\\n"+
               "  elif I > C:\\n"+
               "    if I == C:\\n"+
               "      return \"I confusion\"\\n"+
               "    elif I == V:\\n"+
               "      return \"VI confusion\"\\n"+
               "    return \"impervious\"\\n"+
               "  elif C == I:\\n"+
               "    return \"I confusion\"\\n"+
               "  else:\\n"+
               "    return \"confusion\"\\n"
               )

  elif stage == "vegetation":
    if field == "c2_heig":
        #-----------------------------------------------
        #-----------------------------------------------
        # Thresholds
        gra = "<= 2"    #[0, 2]
        shr = "<= 6"    #(2, 6]
        #tre = ""
        #-----------------------------------------------
        return("def landcover(x):\\n"+
               "  if x "+str(gra)+":\\n"+
               "    return \"grass\"\\n"+
               "  elif x "+shr+":\\n"+
               "    return \"shrub\"\\n"+
               "  else:\\n"+
               "    return \"tree\""
               )
    
    elif field == "object":
        return("def landcover(a,b):\\n"+
               "  return a"
               )

  elif stage == "impervious":
      
    if field == "c2_heig":
        #-----------------------------------------------
        #-----------------------------------------------
        # Thresholds
        pat = "<= 2" #[0, 2]
        #bui = ""
        #-----------------------------------------------
        return("def landcover(x):\\n"+
               "  if x "+pat+":\\n"+
               "    return \"path\"\\n"+
               "  else:\\n"+
               "    return \"building\""
               )
    
    elif field == "c2_ndwi":
        #-----------------------------------------------
        #-----------------------------------------------
        # Thresholds
        imp = "<= 0.4" #[0, 0.4]
        #-----------------------------------------------
        return ("def landcover(x):\\n"+
                "  if x "+imp+":\\n"+
                "    return \"I\"\\n"+
                "  return \"confusion\""
                )

    elif field == "object":
        return ("def landcover(a, b):\\n"+
                "  if a == \"path\" and b == \"I\":\\n"+
                "    return \"path\"\\n"+
                "  elif a == \"building\" and b == \"I\":\\n"+
                "    return \"building\"\\n"+
                "  else:\\n"+
                "    return \"confusion\""
                )

  elif stage == "water":
    if field == "c2_heig":
        #-----------------------------------------------
        #-----------------------------------------------
        # Thresholds
        wat = "<= 2" #[0, 2]
        #-----------------------------------------------
        return("def landcover(x):\\n"+
               "  if x "+wat+":\\n"+
               "    return \"water\"\\n"+
               "  else:\\n"+
               "    return\"confusion\""
               )
    
    elif field == "c2_ndwi":
        #-----------------------------------------------
        #-----------------------------------------------
        # Thresholds
        #-----------------------------------------------
        return("def landcover(x):\\n"+
               "  return \"water\""
               )
    
    elif field == "object":
        return ("def landcover(a, b):\\n"+
                "  return a"
                )

# -----stage 1--------
primitives = ["vegetation", "impervious", "water"]

#-----------------------------------------------
#-----------------------------------------------
text = "Executing Stage 1 classification."
generateMessage(text)
#-----------------------------------------------
stage = "primitive"
s1_indices = ["ndvi", "ndwi", "gndvi", "osavi"]
for index in s1_indices:

  #-----------------------------------------------
  #-----------------------------------------------
  text = "Classifying objects by " + index+"."
  generateMessage(text)
  #-----------------------------------------------

  field = "c_"+index
  fxn = "landcover(!"+index+"!)"
  arcpy.AddField_management(sms_fc, field, "TEXT")
  label_class = classify(stage, field)
  arcpy.CalculateField_management(sms_fc, field, fxn, "PYTHON_9.3", label_class)

fxn = "landcover(!c_ndvi!, !c_ndwi!, !c_gndvi!, !c_osavi!)"
label_class = classify(stage, "prim")
arcpy.AddField_management(sms_fc, "prim", "TEXT")
arcpy.CalculateField_management(sms_fc, "prim", fxn, "PYTHON_9.3", label_class)

for primitive in primitives:

  output = os.path.join(scratchgdb, primitive)
  where_clause = "\"prim\" = '" + primitive + "'"
  arcpy.Select_analysis(sms_fc, output, where_clause)

#-----------------------------------------------
#-----------------------------------------------
text = "Executing Stage 2 classification."
generateMessage(text)
#-----------------------------------------------

stages = []
primitives = ["vegetation", "impervious", "water"]
objects = [["grass", "shrub", "tree"], ["building", "path"], ["water"]]
for i in range(len(primitives)):
    stages.append(primitives[i], objects[i])
merge_lst = []

for classification_stage in stages:
  stage = classification_stage[0]
  landcover = classification_stage[1]
  stage_output = os.path.join(scratchgdb, stage)
  indices = ["height", "ndwi"]

  #-----------------------------------------------
  #-----------------------------------------------
  text = "Classifying "+ stage + " into landcover objects."
  generateMessage(text)
  #-----------------------------------------------
  for index in indices:
    field = "c2_"+index[:4]
    fxn = "landcover(!"+index+"!)"
    arcpy.AddField_management(stage_output, field, "TEXT")
    label_class = classify(stage, field)
    arcpy.CalculateField_management(stage_output, field, fxn, "PYTHON_9.3", label_class)
  label_class = classify(stage, "object")
  arcpy.AddField_management(stage_output, "object", "TEXT")
  fxn = "landcover(!c2_heig!, !c2_ndwi!)"
  arcpy.CalculateField_management(stage_output, "object", fxn, "PYTHON_9.3", label_class)


  for i in range(len(landcover)):
    landcover_output = os.path.join(scratchgdb, landcover[i])
    where_clause = "\"object\" = '" + landcover[i] + "'"

    arcpy.Select_analysis(stage_output, landcover_output, where_clause)
    merge_lst.extend([landcover_output])

#-----------------------------------------------
#-----------------------------------------------
text = "Merging all classified layers into one polygon."
generateMessage(text)
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Merging object layers
#
arcpy.Merge_management(merge_lst, classified_image)


#-----------------------------------------------
#-----------------------------------------------
text = "Fuzzy Rule Classifier processes complete."
generateMessage(text)
#-----------------------------------------------


#-----------------------------------------------
#-----------------------------------------------
text = "Generating " +str(num_training)+" samples for each landcover class."
generateMessage(text)
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Generate Training Samples
#

training_samples = os.path.join(outputs, "training_fc.shp")

def gen_samples(classes):
  def gen_training(num_training, num_samples, sample_type):
      
          def choose_samples(count, sample_selection, num_training, sample_type):
              while count < num_training:
                  #-----------------------------------------------
                  #-----------------------------------------------
                  # Generate Random Samples
                  #
                  if sample_type == "random":
                    row_num = randint(1, num_samples)
                    if row_num in sample_selection:
                      return choose_samples(count, sample_selection, num_training, sample_type)
                    sample_selection.append(row_num)
                    count += 1
                  #-----------------------------------------------
                  #-----------------------------------------------
                  # Generate All Samples
                  #
                  if sample_type == "all":
                      for i in range(num_training):
                        sample_selection.append(i+1)
                      count == num_training
              return sample_selection
          return choose_samples(0, [], num_training, sample_type)
  landcover = os.path.join(scratchgdb, classes[0])
  labels = classes[1]

  for label in labels:
    samples = os.path.join(scratchgdb, label)
    max_rows = int(arcpy.GetCount_management(samples).getOutput(0))
    training = os.path.join(scratchgdb, label + "_selects")
    training_dissolve = os.path.join(scratchgdb, label+ "_training")

    if max_rows >= num_training:
      where_clause = "\"stage2\"= '" + label + "'"
      arcpy.Select_analysis(landcover, samples, where_clause)
      num_samples = int(str(arcpy.GetCount_management(samples)))

      if num_samples > 0:
        row_num = gen_training(num_training, num_samples, sample_type)
        where_clause = "("
        for row in row_num:
            where_clause += str(row) + ", "
        where_clause = where_clause[:-2] + ")"
        arcpy.Select_analysis(samples, training, "OBJECTID in " + where_clause)
        arcpy.Dissolve_management(training, training_dissolve, "stage2")
        arcpy.AddMessage("Created {0} {1} training samples.".format(num_training, label))
        training_merge.extend([training_dissolve])

    else:
      arcpy.Select_analysis(samples, training)
      arcpy.Dissolve_management(training, training_dissolve, "stage2")
      training_merge.extend([training_dissolve])
      arcpy.AddMessage("Samples for " + label + " were limited to " + str(max_rows) + ".")

training_merge = []
for classes in stages:
    gen_samples(classes)

#-----------------------------------------------
#-----------------------------------------------
text = "Merging newly created training samples into one layer."
generateMessage(text)
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Merging training samples
#
arcpy.Merge_management(training_merge, training_samples)

# Layer stack

#-----------------------------------------------
#-----------------------------------------------
text = "Creating a composite."
generateMessage(text)
#-----------------------------------------------
composite = os.path.join(outputs, "composite.tif")

layers = ["ndvi", "ndwi", "gndvi"]
bands = []

for layer in layers:
  sms_raster = os.path.join(scratchgdb, "sms_"+layer)
  arcpy.PolygonToRaster_conversion(sms_fc, layer, sms_raster, "CELL_CENTER", "", cell_size)
  bands.extend([sms_raster])

arcpy.CompositeBands_management(bands, composite)
arcpy.DefineProjection_management(composite, projection)

#-----------------------------------------------
#-----------------------------------------------
text = "Coarsening NAIP to "+coarsening_size+"m."
generateMessage(text)
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Coarsen NAIP Pixel size
#

coarsen_naip = os.path.join(outputs,"naip_"+coarsening_size+"m.tif")
coarse_cell_size = coarsening_size+" "+coarsening_size

arcpy.Resample_management(naip, coarsen_naip, coarse_cell_size, "BILINEAR")


#-----------------------------------------------
#-----------------------------------------------
# FORMAT TRAINING
# svm_training = os.path.join(scratchgdb, "svm_training.shp")
# arcpy.FeatureClassToFeatureClass_conversion (training_samples, outputs, "svm_training.shp")
# training_fields = [["Classname", "TEXT"], ["Classvalue", "LONG"], ["RED", "LONG"], ["GREEN", "LONG"], ["BLUE", "LONG"], ["Count", "LONG"]]
# for field in training_fields:
#   field_name = field[0]
#   field_type = field[1]
#   arcpy.AddField_management(svm_training, field_name, field_type)
# i = 1
# training_samples_rows = int(arcpy.GetCount_management(svm_training).getOutput(0))
# arcpy.ZonalStatisticsAsTable(svm_training, "OBJECTID", composite, zonal_training, "NODATA", "ALL")

# where_clause = "OBJECTID"
# arcpy.CalculateField_management(training_samples, "Classvalue", "[OBJECTID]")
# arcpy.CalculateField_management(training_samples, "Classname", "Class " + "[OBJECTID]")


#arcpy.AddMessage("All training samples created.")
#arcpy.Merge_management(testing_merge, testing_samples)
#arcpy.AddMessage("All testing samples created.")

#-----------------------------------------------
#-----------------------------------------------
# Generate Fuel Model
#
#fuelComplex("13")


#-----------------------------------------------
#-----------------------------------------------
text = "All processes are complete."
generateMessage(text)
#-----------------------------------------------
