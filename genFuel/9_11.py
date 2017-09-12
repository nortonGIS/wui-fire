#-------------------------------------------------------------------------------
# Name:        genFuel Tool
# Purpose:     Takes raw naip and raw heights data and segments the data into
#              objects and classifies these objects using a fuzzy classifier
#              rule and the SVM algorithm. Once objects are classified, they
#              are prepared as ASCIIs to be burned in FlamMap.
#
#             Steps:
#               - Segment heights into unique objects using SMS
#               - Calculate and join mean height to objects with Zonal Stastics
#               - Separate ground and nonground features and mask naip
# Author:      Peter Norton
#
# Created:     05/25/2017
# Updated:     09/11/2017
# Copyright:   (c) Peter Norton and Matt Ashenfarb 2017
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# USER INPUT PARAMETERS
location_name = "Glen Frazer - Kinder Morgan Pipeline"
projection = "SPIII"  #["UTMZ10", "UTMZ11", "SPIII", "SPIV"]
coarsening_size = "5" #meters
input_naip = "naip.tif"
input_bnd = "kinder_bnd.shp"
input_heights = "heights.tif"
model = "13"

#-----------------------------------------------
#-----------------------------------------------
# Processing - DO NOT MODIFY BELOW
#-----------------------------------------------
#-----------------------------------------------

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# Import modules
import arcpy
import os
import sys
from arcpy import env
from arcpy.sa import *
arcpy.env.overwriteOutput = True
from tableJoin import one_to_one_join
from random import randint

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
bnd_zones = os.path.join(inputs, input_bnd)
raw_naip = os.path.join(inputs, input_naip)
raw_heights = os.path.join(inputs, input_heights)

#-----------------------------------------------
# Outputs
#-----------------------------------------------
naip = os.path.join(outputs, "naip.tif")
naip_b1 = os.path.join(naip, "Band_1")
naip_b2 = os.path.join(naip, "Band_2")
naip_b3 = os.path.join(naip, "Band_3")
naip_b4 = os.path.join(naip, "Band_4")
heights = os.path.join(outputs, "heights.tif")

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
arcpy.AddMessage("Site: "+location_name)
arcpy.AddMessage("Projection: "+projection)
arcpy.AddMessage("Resolution: "+coarsening_size + "m")
arcpy.AddMessage("Fuel Model: "+model)
arcpy.AddMessage("-----------------------------")
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Projection information
#
if projection == "UTMZ10":
  scale_height = 0.3048
  unit = "Meters"
  projection = "PROJCS['NAD_1983_UTM_Zone_10N',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-123.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"
elif projection == "UTMZ11":
  scale_height = 0.3048
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
# Resample raw_NAIP and raw_heights to align cells
# Resampled layers will be saved to output folder
#

#-----------------------------------------------
#-----------------------------------------------
text = "Aligning cells."
generateMessage(text)
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Coarsen NAIP Pixel size
#

naip = os.path.join(outputs,"naip_"+coarsening_size+"m.tif")
cell_size = int(coarsening_size)*scale_naip
naip_cell_size = str(cell_size) +" "+str(cell_size)
arcpy.Resample_management(raw_naip, naip, naip_cell_size, "BILINEAR")    
arcpy.DefineProjection_management(naip, projection)

scaled_heights = os.path.join(outputs, "scaled_heights.tif")
resample_heights = os.path.join(outputs, "heights_1m.tif")
arcpy.env.snapRaster = naip
factor = float(cell_size)/float(3.28084)
arcpy.Resample_management(raw_heights, resample_heights, "3.28084 3.28084", "BILINEAR")

this = Aggregate(resample_heights, factor, "MAXIMUM")
this.save(heights)

this = Float(heights) * scale_height
this.save(scaled_heights)
arcpy.DefineProjection_management(scaled_heights, projection)
#-----------------------------------------------

searchcursor = arcpy.SearchCursor(bnd_zones)
zones = searchcursor.next()
while zones:
  field = "FID"
  zone_num = zones.getValue(field)
  bnd = os.path.join(outputs, "zone_"+str(zone_num)+".shp")
  where_clause = field+" = " + str(zone_num)
  naip_zone = os.path.join(outputs, "naip_zone_"+str(zone_num)+".tif")
  naip_zone_b1 = os.path.join(naip_zone, "Band_1")
  naip_zone_b2 = os.path.join(naip_zone, "Band_2")
  naip_zone_b3 = os.path.join(naip_zone, "Band_3")
  naip_zone_b4 = os.path.join(naip_zone, "Band_4")                         
  heights_zone = os.path.join(outputs, "height_zone_"+str(zone_num)+".tif")

#segmented naip
  naip_sms = os.path.join(scratchgdb, "naip_sms_"+str(zone_num))

  #feature objects
  sms_fc = os.path.join(scratchgdb, "sms_fc_"+str(zone_num))
  lst_merge = []
  #-----------------------------------------------
  text = "Extracting NAIP and heights by zone "+str(zone_num)+" boundary."
  generateMessage(text)
  #-----------------------------------------------
  #-----------------------------------------------
  
  arcpy.Select_analysis(bnd_zones, bnd, where_clause)
                         
  this = ExtractByMask(naip, bnd)
  this.save(naip_zone)
  this = ExtractByMask(scaled_heights, bnd)
  this.save(heights_zone)

  #-----------------------------------------------
  text = "Creating ground and non-ground surfaces."
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

  mask = SetNull(Int(heights_zone),Int(heights_zone),"VALUE > " + str(ground_ht_threshold))
  arcpy.RasterToPolygon_conversion(mask, ground_mask_raw, "NO_SIMPLIFY", "VALUE", )
  arcpy.Dissolve_management(ground_mask_raw, ground_dissolve_output)

  #Find cell size of imagery
  cell_size = str(arcpy.GetRasterProperties_management(naip, "CELLSIZEX", ""))

  arcpy.Erase_analysis(bnd, ground_dissolve_output, nonground_mask_raw)

  arcpy.PolygonToRaster_conversion(nonground_mask_raw, "OBJECTID", nonground_mask_raster, "CELL_CENTER", "", cell_size)
  arcpy.RasterToPolygon_conversion(nonground_mask_raster, nonground_mask_raw, "NO_SIMPLIFY", "VALUE")
  where_clause = "Shape_Area > " + str(min_cell_area)
  arcpy.Select_analysis(nonground_mask_raw, nonground_mask_poly, where_clause)

  arcpy.Erase_analysis(bnd, nonground_mask_poly, ground_mask_poly)
  arcpy.PolygonToRaster_conversion(ground_mask_poly, "OBJECTID", ground_mask_raster, "CELL_CENTER", "", cell_size)
  arcpy.RasterToPolygon_conversion(ground_mask_raster, ground_mask_raw, "NO_SIMPLIFY", "VALUE")
  arcpy.Select_analysis(ground_mask_raw, ground_mask_poly, where_clause)

  arcpy.Erase_analysis(bnd, ground_mask_poly, nonground_mask_poly)

  #-----------------------------------------------
  #-----------------------------------------------
  #Segment each surface separately using SMS
  #

  spectral_detail = 20
  spatial_detail = 20
  min_seg_size = 1

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
    this = ExtractByMask(naip_zone, mask)
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

  #-----------------------------------------------
  #-----------------------------------------------
  # Create Image Enhancements and join to objects
  #

  image_enhancements = ["ndvi", "ndwi", "gndvi", "osavi", "height"]


  def normalize(index):
      return (2 * (Float(index) - Float(index.minimum)) / (Float(index.maximum) - Float(index.minimum))) - 1

  def createImageEnhancements(x, join, cell_size, created_enhancements):

     for field in image_enhancements:
       enhancement_path = os.path.join(scratchgdb, field+"_"+str(zone_num))
       outTable = os.path.join(scratchgdb, "zonal_"+field)

       # -----------------------------------------------
       # -----------------------------------------------
       text = "Computing " + field + " at "+cell_size+"m."
       generateMessage(text)
       # -----------------------------------------------

       if field == "ndvi":
         inValueRaster = ((Float(naip_zone_b4))-(Float(naip_zone_b1))) / ((Float(naip_zone_b4))+(Float(naip_zone_b1)))
         inValueRaster.save(enhancement_path)
         ie = enhancement_path
       elif field == "ndwi":
         inValueRaster = ((Float(naip_zone_b2))-(Float(naip_zone_b4))) / ((Float(naip_zone_b2))+(Float(naip_zone_b4)))
         inValueRaster.save(enhancement_path)
         ie = enhancement_path
       elif field == "gndvi":
         inValueRaster = ((Float(naip_zone_b4))-(Float(naip_zone_b2))) / ((Float(naip_zone_b4))+(Float(naip_zone_b2)))
         inValueRaster.save(enhancement_path)
         ie = enhancement_path
       elif field == "osavi":
         inValueRaster = normalize((1.5 * (Float(naip_zone_b4) - Float(naip_zone_b1))) / ((Float(naip_zone_b4)) + (Float(naip_zone_b1)) + 0.16))
         inValueRaster.save(enhancement_path)
         ie = enhancement_path
       elif field == "height":
         enhancement_path = heights_zone

       created_enhancements.append(enhancement_path)
       if join == "yes":

         # -----------------------------------------------
         # -----------------------------------------------
         text = "Joining mean " + field + " to each object."
         generateMessage(text)
         # -----------------------------------------------
         
         z_stat = ZonalStatisticsAsTable(sms_fc, "JOIN", enhancement_path, outTable, "NODATA", "MEAN")

         arcpy.AddField_management(outTable, field, "FLOAT")
         arcpy.CalculateField_management(outTable, field, "[MEAN]")
         one_to_one_join(sms_fc, outTable, field, "FLOAT")
     return created_enhancements

   created_enhancements_1m = createImageEnhancements(image_enhancements, "yes", "1", [])
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

  def classify(stage, landcover, field):
    if stage == "S1":
      if field == "S1_grid":
        #-----------------------------------------------
        #-----------------------------------------------
        # Thresholds
        healthy = ">= 250" #[250,255]
        dry = "<= 249"  #[0, 249]
        #con = ""
        #-----------------------------------------------
        return("def landcover(x):\\n"+
               "  if x "+healthy+":\\n"+
               "    return \"healthy\"\\n"+
               "  elif x "+dry+":\\n"+
               "    return \"senescent\"\\n"+
               "  return \"impervious\""
               )
    
      elif field == "S1_ndvi":
        #-----------------------------------------------
        #-----------------------------------------------
        # Thresholds
        imp = "-0.88 <= x <= -0.2" #[-0.88, -0.2]
        veg = "-0.18 <= x <= 0.5"  #[-0.18, 0.5]
        #-----------------------------------------------
        return ("def landcover(x):\\n"+
               "  membership = \"\"\\n"+
               "  if "+imp+":\\n"+
               "    membership += \"I\"\\n"+
               "  if "+veg+":\\n"+
               "    membership += \"V\"\\n"+
               "  return membership\\n"
               )

      elif field == "S1_ndwi":
        #-----------------------------------------------
        #-----------------------------------------------
        # Thresholds
        imp = "0.24 <= x <= 0.91"  #[0.24, 0.91]
        veg = "-0.41 <= x <= 0.18" #[-0.41, 0.18]
        #-----------------------------------------------
        return ("def landcover(x):\\n"+
               "  membership = \"\"\\n"+
               "  if "+imp+":\\n"+
               "    membership += \"I\"\\n"+
               "  if "+veg+":\\n"+
               "    membership += \"V\"\\n"+
               "  return membership\\n"
               )
      
      elif field == "S1_gndv":
        #-----------------------------------------------
        #-----------------------------------------------
        # Thresholds
        imp = "-0.94<= x <= -0.17"  #[-0.94, -0.17]
        veg = "-0.3 <= x <= 0.38" #[-0.3, 0.38]
        #-----------------------------------------------
        return ("def landcover(x):\\n"+
               "  membership = \"\"\\n"+
               "  if "+imp+":\\n"+
               "    membership += \"I\"\\n"+
               "  if "+veg+":\\n"+
               "    membership += \"V\"\\n"+
               "  return membership\\n"
               )

      elif field == "S1_osav":
        #-----------------------------------------------
        #-----------------------------------------------
        # Thresholds
        imp = "-0.94 <= x <= -0.25"  #[-0.94, -0.25]
        veg = "-0.15 <= x <= 0.76" #[-0.15, 0.76]
        #-----------------------------------------------
        return ("def landcover(x):\\n"+
               "  membership = \"\"\\n"+
               "  if "+imp+":\\n"+
               "    membership += \"I\"\\n"+
               "  if "+veg+":\\n"+
               "    membership += \"V\"\\n"+
               "  return membership\\n"
               )
      
      elif field == "S1":
        return("def landcover(a,b,c,d):\\n"+
               "  membership = a+b+c+d\\n"+
               "  V,I = 0,0\\n"+
               "  for m in membership:\\n"+
               "    if m == \"V\":\\n"+
               "      V += 1\\n"+
               "    if m == \"I\":\\n"+
               "      I += 1\\n"+                  
               "  if V > I:\\n"+
               "    return \"vegetation\"\\n"+
               "  elif I > V:\\n"+
               "    return \"impervious\"\\n"+
               "  else:\\n"+
               "    return \"confusion\"\\n"
               )

    elif stage == "S2":
      if landcover == "vegetation":
        if field == "S2_grid":
          #-----------------------------------------------
          #-----------------------------------------------
          # Thresholds
          dry = ">= 250"    #[250, 255]
          healthy = "<= 249"    #(0, 249]
          #con = ""
          #-----------------------------------------------
          return("def landcover(x):\\n"+
                 "  if x "+dry+":\\n"+
                 "    return \"dry\"\\n"+
                 "  elif x "+shr+":\\n"+
                 "    return \"healthy\"\\n"+
                 "  else:\\n"+
                 "    return \"confusion\""
                 )
                
        elif field == "S2_heig":
          #-----------------------------------------------
          #-----------------------------------------------
          # Thresholds
          gra = "x <= 2"    #[0, 2]
          shr = "x <= 6"    #(2, 6]
          #tre = ""
          #-----------------------------------------------
          return("def landcover(x):\\n"+
                 "  if "+gra+":\\n"+
                 "    return \"grass\"\\n"+
                 "  elif "+shr+":\\n"+
                 "    return \"shrub\"\\n"+
                 "  else:\\n"+
                 "    return \"tree\""
                 )
      
        elif field == "S2":
          return("def landcover(a, b):\\n"+
                 "  if b != \"confusion\":\\n"+
                 "    return a "
                 )

      elif landcover == "impervious":
        
        if field == "S2_heig":
          #-----------------------------------------------
          #-----------------------------------------------
          # Thresholds
          pat = "x <= 2" #[0, 2]
          #bui = ""
          #-----------------------------------------------
          return("def landcover(x):\\n"+
                 "  if "+pat+":\\n"+
                 "    return \"path\"\\n"+
                 "  else:\\n"+
                 "    return \"building\""
                 )
      
        elif field == "S2_ndwi":
          #-----------------------------------------------
          #-----------------------------------------------
          # Thresholds
          imp = "0.1 <= x <= 0.91" #[0.1, 0.91]
          #-----------------------------------------------
          return ("def landcover(x):\\n"+
                  "  if "+imp+":\\n"+
                  "    return \"I\"\\n"+
                  "  return \"confusion\""
                  )

        elif field == "S2":
          return ("def landcover(a, b):\\n"+
                  "  if b == \"I\":\\n"+
                  "    return a\\n"+
                  "  else:\\n"+
                  "    return \"confusion\""
                  )

  def createClassMembership(stage, landcover, field, field_lst, output):
    if field in stages:
      field_lst = field_lst[:-2]
      fxn = "landcover("+field_lst+")"

    else:
      index = field
      field = stage+"_"+field[:4]
      field_lst += "!"+field+"!, "
      fxn = "landcover(!"+index+"!)"
        
    label_class = classify(stage, landcover, field)
    arcpy.AddField_management(output, field, "TEXT")
    arcpy.CalculateField_management(output, field, fxn, "PYTHON_9.3", label_class)
    return field_lst
  #-----------------------------------------------
  #-----------------------------------------------
  # Classifier methods
  #

  stages = ["S1","S2"]
  class_structure = [
                     ["vegetation",
                          ["grass", "shrub", "tree"]],
                     ["impervious",
                          ["building", "path"]]
                    ]

  s1_indices = ["ndvi", "ndwi", "gndvi", "osavi"]#, "gridcode"]
  s2_indices = ["height", "ndwi"]#, "gridcode"]

  for stage in stages:
    #-----------------------------------------------
    #-----------------------------------------------
    text = "Executing Stage "+str(stage)+" classification."
    generateMessage(text)
    #-----------------------------------------------
    if stage == "S1":
      s1_indices.extend([stage])
      field_lst = ""
      
      for field in s1_indices:

        if field == "S1":
          #-----------------------------------------------
          #-----------------------------------------------
          text = "Creating primitive-type objects."
          generateMessage(text)
          #-----------------------------------------------
          createClassMembership(stage, "", field, field_lst, sms_fc)

          for primitive in class_structure:
              output = os.path.join(outputs, primitive[0]+"_"+str(zone_num)+".shp")
              where_clause = field + " = '" + primitive[0] + "'"
              arcpy.Select_analysis(sms_fc, output, where_clause)
              if primitive == "vegetation":
                lst_merge.append(output)
              
                
        else:
          #-----------------------------------------------
          #-----------------------------------------------
          text = "Classifying objects by "+field+"."
          generateMessage(text)
          #-----------------------------------------------
          field_lst = createClassMembership(stage, "", field, field_lst, sms_fc)

    if stage == "S2":
      s2_indices.extend([stage])
      merge_lst = []
      for primitive in class_structure:
        stage_output = os.path.join(outputs, primitive[0]+"_"+str(zone_num)+".shp")
        landcover = primitive[0]
        field_lst = ""

        for field in s2_indices:
          if field == "S2":
            #-----------------------------------------------
            #-----------------------------------------------
            text = "Creating "+primitive[0]+"-class objects."
            generateMessage(text)
            #-----------------------------------------------
            createClassMembership(stage, landcover, field, field_lst, stage_output)
                  
          else:
            #-----------------------------------------------
            #-----------------------------------------------
            text = "Classifying "+primitive[0]+" objects by "+field+"."
            generateMessage(text)
            #-----------------------------------------------
            
            field_lst = createClassMembership(stage, landcover, field, field_lst, stage_output)


  zones = searchcursor.next()

confused = os.path.join(outputs, "confused.shp")
veg_join = os.path.join(scratchgdb, "veg_join")
training_samples = os.path.join(outputs, "training_fc.shp")

#-----------------------------------------------
#-----------------------------------------------
text = "Preparing 'Confused' objects for SVM."
generateMessage(text)
#-----------------------------------------------
vegetation = os.path.join(outputs, "vegetation_0.shp")
impervious = os.path.join(outputs, "impervious_0.shp")

if len(lst_merge) > 1:
  arcpy.Merge_management(lst_merge, veg_join)
else:
  veg_join = vegetation#lst_merge[0]
arcpy.Dissolve_management(veg_join, training_samples, ["S2"])

arcpy.Erase_analysis (sms_fc, veg_join, confused)

band_lst = ["ndvi", "ndwi", "height"]

composite = os.path.join(outputs, "composite.tif")
def createLayerComposite(bands):
   bands_5m = createImageEnhancements(bands, "no", "5", [])
   arcpy.CompositeBands_management(bands_5m, composite)
   arcpy.DefineProjection_management(composite, projection)
createLayerComposite(band_lst)



#-----------------------------------------------
#-----------------------------------------------
text = "Preparing training samples for SVM."
generateMessage(text)
#-----------------------------------------------
svm_training = os.path.join(outputs, "svm_training.shp")
arcpy.FeatureClassToFeatureClass_conversion (training_samples, outputs, "svm_training")
training_fields = [["Classname", "TEXT"], ["Classvalue", "LONG"], ["RED", "LONG"], ["GREEN", "LONG"], ["BLUE", "LONG"], ["Count", "LONG"]]
for field in training_fields:
  field_name = field[0]
  field_type = field[1]
  arcpy.AddField_management(svm_training, field_name, field_type)

arcpy.AddField_management(svm_training, "JOIN", "INTEGER")
arcpy.CalculateField_management(svm_training, "JOIN", "[FID]")

zonal_training = os.path.join(scratchgdb, "zonal_train")

z_stat = ZonalStatisticsAsTable(svm_training, "JOIN", composite, zonal_training, "NODATA", "ALL")
one_to_one_join(svm_training, zonal_training, "JOIN", "INTEGER")
#
#search cursor
arcpy.CalculateField_management(svm_training, "Classname", "[S2]")
arcpy.CalculateField_management(svm_training, "Classvalue", "[JOIN]")
arcpy.CalculateField_management(svm_training, "RED", 1)
arcpy.CalculateField_management(svm_training, "GREEN", 1)
arcpy.CalculateField_management(svm_training, "BLUE", 1)
arcpy.CalculateField_management(svm_training, "Count", "[COUNT]")

fields = [f.name for f in arcpy.ListFields(svm_training)]
delete_fields = []
for field in fields:
  if field not in ["FID", "Shape", "Shape_Area", "Shape_Length", "Classname", "Classvalue", "RED", "GREEN", "BLUE", "Count"]:
    delete_fields.append(field)
arcpy.DeleteField_management(svm_training, delete_fields)


out_definition = os.path.join(outputs, "svm_classifier.ecd")
maxNumSamples = "100"
attributes = ""

#-----------------------------------------------
#-----------------------------------------------
text = "Training Support Vector Machine."
generateMessage(text)
#-----------------------------------------------

arcpy.gp.TrainSupportVectorMachineClassifier(composite, svm_training, out_definition, "", maxNumSamples, attributes)

svm = os.path.join(scratchgdb, "svm")

#-----------------------------------------------
#-----------------------------------------------
text = "Classifying composite with Support Vector Machine."
generateMessage(text)
#-----------------------------------------------
classifiedraster = ClassifyRaster(composite, out_definition, "")
classifiedraster.save(svm)

#-----------------------------------------------
#-----------------------------------------------
text = "Joining SVM classified outputs to 'Confused' objects."
generateMessage(text)
#-----------------------------------------------
zonal_svm = os.path.join(scratchgdb, "zonal_svm")
z_stat = ZonalStatisticsAsTable(confused, "JOIN", svm, zonal_svm, "NODATA", "MAJORITY")
one_to_one_join(confused, zonal_svm, "JOIN", "LONG")

classified = os.path.join(outputs, "classified.shp")
arcpy.Merge_management([confused, vegetation, impervious], classified)

#-----------------------------------------------
#-----------------------------------------------
# Generate fuel complex
#

def classify(model, x):
    
  # Anderson 13
  if model == "13":
    building = "13"
    tree = "10"
    shrub = "6"
    grass = "1"
    water = "98"
    pavement = "99"
  elif model != "13":
    #-----------------------------------------------
    #-----------------------------------------------
    text = "Cannot classify fuels. Only Anderson 13 are available."
    generateMessage(text)
    #-----------------------------------------------
      
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
            "    return 75\\n"+
            "  return 0"
            )

  elif x == "stand":
    return("def classify(x):\\n"+
           "  return x"
           )


land_cover = classified
land_cover_fields = [["fuel", "S2"], ["canopy", "S2"], ["stand", "height"]]
for field in land_cover_fields:
  input_field = field[1]
  output_field = field[0]
  arcpy.AddField_management(land_cover, output_field, "INTEGER")
  fxn = "classify(!"+input_field+"!)"
  label_class = classify(model, output_field)
  arcpy.CalculateField_management(land_cover, output_field, fxn, "PYTHON_9.3", label_class)
  arcpy.AddMessage("{0} created.".format(output_field))

#-----------------------------------------------
#-----------------------------------------------
text = "Fuel complex created."
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
    arcpy.Select_analysis(land_cover, temp, where_clause)
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
convertToAscii(land_cover, mitigation_type)
arcpy.AddMessage("All ascii are created.")

#-----------------------------------------------
#-----------------------------------------------
text = "Next step: Manually create LCP file."
generateMessage(text)
#-----------------------------------------------


#-----------------------------------------------
#-----------------------------------------------
text = "All processes are complete."
generateMessage(text)
#-----------------------------------------------
