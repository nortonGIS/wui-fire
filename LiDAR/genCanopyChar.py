#-------------------------------------------------------------------------------
# Name:        genCanopyChar Tool
# Purpose:     
#
#             Primary Steps:
#               - 

# Author:      Peter Norton
#
# Created:     09/29/2017
# Updated:     -
# Copyright:   (c) Peter Nortonb 2017
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# USER LOG
date = "genCanopyChar"
# Summary
#
#
#

# Geographic
projection = "UTMZ10"  #["UTMZ10", "UTMZ11", "SPIII", "SPIV"]
max_height = 350

# Inputs
input_lidar = "tahoe_plot_1.lasd"
first_pulse_classes = [1]
last_pulse_classes = [2]

#
cell_size = 1
find_surfaces = "No"
classify_segmented ="No"
find_canopies = "No"
find_cbh = "Yes"
#-----------------------------------------------
#-----------------------------------------------
# Processing - DO NOT MODIFY BELOW
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
# Import modules
import arcpy
import os
import sys
import shutil
from arcpy import env
from arcpy.sa import *
from tableJoin import one_to_one_join

# Overwrite Setting
arcpy.env.overwriteOutput = True
#script_db = "K:\\TFS_Fire\\Tools"
#-----------------------------------------------
#-----------------------------------------------


#-----------------------------------------------
#-----------------------------------------------
# File Structure
folder_structure = [
  "Scripts",
  "Inputs",
  "Outputs",
  "Scratch"
]

# Dependent scripts
dependent_scripts = [
]

# Create new project folder and set environment
scriptpath = sys.path[0] # Find script
toolpath = os.path.dirname(scriptpath)  # Find parent directory
current_project = os.path.join(toolpath)
if os.path.basename(toolpath) == date:
  arcpy.AddMessage("File structure is setup.")
elif os.path.basename(scriptpath) != date:
    if os.path.basename(scriptpath) == "Scripts":
      new_toolpath = os.path.dirname(toolpath)
      current_project = os.path.join(new_toolpath,date)
    else:
      current_project = os.path.join(toolpath,date)
    os.makedirs(current_project)        # Make new project folder
    for folder_name in folder_structure:
      folder = os.path.join(current_project, folder_name)
      os.makedirs(folder)
      if folder_name == "Inputs":
        if os.path.basename(scriptpath) == "Scripts":
          input_path = os.path.join(toolpath, "Inputs")
          for root, dirs, inputs in os.walk(scriptpath):
            for input_file in inputs:
              script_folder = os.path.join(current_project, "Scripts")
              base=os.path.basename(input_file)
              extension = os.path.splitext(input_file)[1]
              if extension == ".py" and input_file not in dependent_scripts:
                arcpy.Copy_management(input_file, os.path.join(script_folder, date+".py")) # copies main to script folde
              else:
                arcpy.Copy_management(input_file, os.path.join(script_folder, base))
        else:
          input_path = scriptpath
        for root, dirs, inputs in os.walk(input_path):
          for input_file in inputs:
            base=os.path.basename(input_file)
            extension = os.path.splitext(input_file)[1]
            
            if extension not in [".py", ".tbx"]:
                              
              input_folder = os.path.join(current_project, folder_name)
              arcpy.Copy_management(os.path.join(input_path,input_file), os.path.join(input_folder, base)) # copies main to script folder
            else:
              input_folder = os.path.join(current_project, "Scripts")
              if extension == ".py":
                arcpy.Copy_management(input_file, os.path.join(input_folder, date+".py")) # copies main to script folde
              else:
                arcpy.Copy_management(input_file, os.path.join(input_folder, base)) # copies main to script folde
      elif folder_name == "Scratch":
        arcpy.CreateFileGDB_management(folder, "Scratch.gdb")
      elif folder_name == "Scripts":
        input_folder = os.path.join(current_project, folder_name)
              
        #for dependent_script in dependent_scripts:
        #  shutil.copy2(os.path.join(script_db, dependent_script), os.path.join(input_folder, dependent_script)) # copies main to script folder 

#Setting inputs, outputs, scratchws, scratch.gdb
inputs = os.path.join(current_project, "Inputs")
outputs = os.path.join(current_project, "Outputs")
scratchws = os.path.join(current_project, "Scratch") 
scratchgdb = os.path.join(scratchws, "Scratch.gdb")   
dll_path = os.path.join(current_project, "Scripts")

#-----------------------------------------------
#-----------------------------------------------
# Set Global Variables
# Inputs
lidar = os.path.join(inputs, input_lidar)     # Replace LAS, create lasd manually

# Outputs
first_pulse = os.path.join(inputs, "FirstPulse.lasd")
last_pulse = os.path.join(inputs, "LastPulse.lasd")

# Surfaces
dem = os.path.join(outputs,"dem.tif")
dsm = os.path.join(outputs,"dsm.tif")
heights = os.path.join(outputs,"heights.tif")

# Canopies
tree_heights = os.path.join(outputs, "tree_hts.tif")
area_heights = os.path.join(outputs, "area_heights.tif")
trees = os.path.join(outputs, "trees.shp")
existing_canopy_centroids = os.path.join(outputs, "canopy_cntrs.shp")
tree_thiessen = os.path.join(outputs, "treeThiessen.shp")
canopy_stack = os.path.join(outputs, "canopy_stack.shp")
cbh_rast = os.path.join(outputs, "cbh_rast.tif")
cbh_stack = os.path.join(outputs, "cbh_stack.shp")
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
count = 1
def generateMessage(text):
  global count
  arcpy.AddMessage("Step " + str(count) + ": " +text),
  count += 1
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
def findSurfaces(dem, dsm, heights):
  # Create First Pulse lasd
  arcpy.MakeLasDatasetLayer_management(lidar, first_pulse, first_pulse_classes)

  text = "First Pulses separated."
  generateMessage(text)

  # Create Last Pulse lasd
  arcpy.MakeLasDatasetLayer_management(lidar, last_pulse, last_pulse_classes)
  text = "Last Pulses separated."
  generateMessage(text)
  #-----------------------------------------------
  #-----------------------------------------------

  #-----------------------------------------------
  #-----------------------------------------------
  # Create DEM
  arcpy.LasDatasetToRaster_conversion(last_pulse, dem, "ELEVATION", "BINNING AVERAGE NATURAL_NEIGHBOR", "FLOAT", "CELLSIZE", cell_size, "1")
  text = "Digital Elevation Model created."
  generateMessage(text)

  # Create DSM
  temp = os.path.join(scratchgdb,"temp")

  arcpy.LasDatasetToRaster_conversion(first_pulse, temp, "ELEVATION", "BINNING MAXIMUM SIMPLE", "FLOAT", "CELLSIZE", cell_size, "1")
  this = Con(IsNull(Float(temp)),Float(dem),Float(temp))
  this.save(dsm)
  text = "Digital Surface Model created."
  generateMessage(text)

  # Create Heights
  no_clip_heights = os.path.join(scratchgdb,"no_clip_heights")
  hts_interm1 = os.path.join(scratchgdb,"hts_interm1")
  hts_interm2 = os.path.join(scratchgdb,"hts_interm2")


  this = Float(dsm)-Float(dem)  #Equation for heights
  this = Con(IsNull(Float(this)), 0, Float(this))    # Make any null value the ground
  this = Con(Float(this) < 0, 0, Float(this))    # Make any negative value the ground
  this = SetNull(Float(this),Float(this),"VALUE > "+str(max_height))  # Set maximum height to remove flying birds
  if int(arcpy.GetRasterProperties_management(this,"ANYNODATA").getOutput(0)):
      
      text = "Removing points reflected by birds."
      generateMessage(text)
      
      cloudrast = os.path.join(scratchgdb,"cloudrast")
      cloudpts = os.path.join(scratchgdb,"cloudpts")
      cloudpts_buf30 = os.path.join(scratchgdb,"cloudptsbuf30")
      interppts = os.path.join(scratchgdb,"interppts")
      NNinterp = os.path.join(scratchgdb,"NNinterp")
      
      heights.save(hts_interm1)
      heights.save(hts_interm2)
      del heights
      
      arcpy.gp.Reclassify_sa(hts_interm1, "VALUE", "-10000 10000 NODATA;NODATA 1", cloudrast, "DATA")
      
      arcpy.RasterToPoint_conversion(cloudrast,cloudpts,"VALUE")
      
      arcpy.Buffer_analysis(cloudpts, cloudpts_buf30, "30 Feet", "FULL", "ROUND", "ALL", "", "PLANAR")
      nocloudmask = ExtractByMask(hts_interm2,cloudpts_buf30)
      
      arcpy.RasterToPoint_conversion(nocloudmask, interppts,"")
      
      arcpy.gp.NaturalNeighbor_sa(interppts, "grid_code", NNinterp, hts_interm2)
      arcpy.MosaicToNewRaster_management(hts_interm2+";"+NNinterp,scratchfolder, no_clip_heights, "", "32_BIT_FLOAT", "", "1", "FIRST", "FIRST")

  this.save(heights)  
  text = "Heights created."
  generateMessage(text) 

if find_surfaces == "Yes":
  findSurfaces(dem, dsm, heights)
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------


def classifySegments():
  
  text = "Classifying heights into vegetation types."
  generateMessage(text)

  cover = os.path.join(scratchgdb, "cover")
  temp_tree = os.path.join(scratchgdb, "temp_tree")

  def classify(unit):
    if unit == "Meters":
      ground_threshold = 0
      grass_threshold = 0.6096
      shrub_threshold = 1.8288
      tree_threshold = 1.8288
    elif unit == "Feet":
      ground_threshold = 0
      grass_threshold = 2
      shrub_threshold = 6
      tree_threshold = 6 
    return("def classify(x):\\n"+
           "  if x < "+str(ground_threshold)+":\\n"+
           "    return \"ground\"\\n"+
           "  elif x < "+str(grass_threshold)+":\\n"+
           "    return \"grass\"\\n"+
           "  elif x < "+str(shrub_threshold)+":\\n"+
           "    return \"shrub\"\\n"+
           "  elif x >= "+str(shrub_threshold)+":\\n"+
           "    return \"tree\""
          )

  this = Int(heights)
  this.save(area_heights)
  arcpy.RasterToPolygon_conversion(area_heights, cover, "NO_SIMPLIFY", "VALUE")
  arcpy.AddField_management(cover, "veg", "STRING")
  arcpy.CalculateField_management(cover, "veg", "classify(!gridcode!)", "PYTHON_9.3", classify(unit))
  arcpy.Select_analysis (cover, temp_tree, "veg = 'tree'")
  arcpy.Dissolve_management(temp_tree, trees,"veg", "", "MULTI_PART")
if classify_segmented == "Yes":
  classifySegments()
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
def findCanopy(canopy_stack, tree_thiessen):

  text = "Finding canopies."
  generateMessage(text)

  # Create raster of vegetation heights
  thiessen = os.path.join(scratchgdb, "thiessen")
  temp = os.path.join(scratchgdb, "temp")

  this = ExtractByMask(area_heights, trees)
  this.save(tree_heights)

  # Parameters
  this = Raster(tree_heights)
  max_canopy_height = Int(this.maximum)
  max_base_height = max_canopy_height
  incr = -1
  i = 0
  
  canopy_lst = []
  

  text = "Making horizontal slices (in "+unit+"):"
  generateMessage(text)
  while max_canopy_height > 0:
      upper = max_canopy_height
      max_canopy_height += incr
      lower = max_canopy_height
      if lower < 0:
        lower = 0

      ht_slice = os.path.join(scratchgdb, "slice_"+str(upper))
      canopy_select = os.path.join(scratchgdb, "canopy_select")
      slice_sms = os.path.join(outputs, "slice_sms.tif")
      slice_poly = os.path.join(scratchgdb, "slice_poly_"+str(upper))
      canopies = os.path.join(scratchgdb, "canopies_"+str(upper))
      new_canopies = os.path.join(scratchgdb, "new_canopies")
      new_canopy_centroids = os.path.join(scratchgdb, "new_canopy_cntr")
      existing_canopy_centroids = os.path.join(scratchgdb, "existing_canopy_cntr")
      
      existing_canopies = os.path.join(scratchgdb, "existing_canopies")
      temp = os.path.join(scratchgdb, "temp_"+str(count))
      
      #create slice
      if count < 10:
        if len(str(upper)) == 1 and len(str(lower)) == 1:
          text = "[0"+str(upper)+", 0"+str(lower)+"]     /\\"  
        elif upper <= 6:
          text = "[0"+str(upper)+", 0"+str(lower)+"]     ||"
        elif len(str(lower)) == 1:
          text = "["+str(upper)+", 0"+str(lower)+"]     /\\"
        elif len(str(upper)) == 1:
          text = "[0"+str(upper)+", "+str(lower)+"]     /\\"  
        else:
          text = "["+str(upper)+", "+str(lower)+"]     /\\"

      else:  
        if len(str(upper)) == 1 and len(str(lower)) == 1:
          text = "[0"+str(upper)+", 0"+str(lower)+"]    /\\"  
        elif upper <= 6:
          text = "[0"+str(upper)+", 0"+str(lower)+"]    ||"
        elif len(str(lower)) == 1:
          text = "["+str(upper)+", 0"+str(lower)+"]  ///\\\\"
        elif len(str(upper)) == 1:
          text = "[0"+str(upper)+", "+str(lower)+"]    /\\"  
        else:
          text = "["+str(upper)+", "+str(lower)+"]    /\\"
      generateMessage(text)

      vert_max = Con(Int(tree_heights)>= upper, upper, Int(tree_heights))
      vert_min = Con(Int(vert_max) <= lower, 0, Int(vert_max))
      vert_min.save(ht_slice)
      
      #convert slice to polygons and extract canopies
     
      arcpy.RasterToPolygon_conversion(ht_slice, slice_poly, "NO_SIMPLIFY", "VALUE")
      arcpy.Select_analysis (slice_poly, canopy_select, "gridcode <> 0")
      arcpy.Dissolve_management(canopy_select, canopies, "", "", "SINGLE_PART")
      arcpy.AddField_management(canopies, "h", "INTEGER")
      arcpy.CalculateField_management(canopies, "h", 1)
      canopy_lst.append(canopies)
      

      #join previous centroids to canopy polygons
      if i > 0:
        arcpy.SpatialJoin_analysis(canopies, existing_canopy_centroids, existing_canopies,  "JOIN_ONE_TO_ONE")
        where_clause = "Exist IS NULL AND Shape_Length > 14"
        arcpy.Select_analysis(existing_canopies, new_canopies, where_clause)

        #create new canopy centroids
        arcpy.FeatureToPoint_management(new_canopies, new_canopy_centroids, "INSIDE")
        arcpy.AddField_management(new_canopy_centroids, "Exist", "INTEGER")
        arcpy.CalculateField_management(new_canopy_centroids, "Exist", 1)
        
        new_cntr_fields = [f.name for f in arcpy.ListFields(new_canopy_centroids)]
        delete_fields = []
        for field in new_cntr_fields:
          if field not in ex_cntr_fields:
            arcpy.DeleteField_management(new_canopy_centroids, field)
        
        arcpy.Append_management(new_canopy_centroids, existing_canopy_centroids, "TEST")
          
      else:
        new_canopies = canopies
    
        #create new canopy centroids
        arcpy.FeatureToPoint_management(new_canopies, existing_canopy_centroids, "INSIDE")
        arcpy.AddField_management(existing_canopy_centroids, "Exist", "INTEGER")
        arcpy.CalculateField_management(existing_canopy_centroids, "Exist", 1)
        ex_cntr_fields = [f.name for f in arcpy.ListFields(existing_canopy_centroids)]

      i += 1

  text = "Creating Thiessen polygons from canopy centroids."
  generateMessage(text)
  arcpy.CreateThiessenPolygons_analysis(existing_canopy_centroids, thiessen)

  text = "Clipping Thiessen polygons by tree boundary."
  generateMessage(text)

  arcpy.Clip_analysis (thiessen, trees, tree_thiessen)
  arcpy.AddField_management(tree_thiessen, "treeID", "INTEGER")
  arcpy.CalculateField_management(canopy_stack, "treeID", "[FID]+1")


  arcpy.Union_analysis (canopy_lst, canopy_stack)
  stack_fields = [f.name for f in arcpy.ListFields(canopy_stack)]
  sum_fields = []
  for field in stack_fields:
    if field[0] == "h":
      sum_fields.append(field)
  calc = ""
  for field in sum_fields:
    calc+="["+field+"]+"
  fxn = calc[:-1]
  arcpy.AddField_management(canopy_stack, "tot", "INTEGER")
  arcpy.CalculateField_management(canopy_stack, "tot", fxn)
  for field in stack_fields:
    if field[0] == "h" or field[0] == "F":
      arcpy.DeleteField_management(canopy_stack, field)
  #arcpy.Union_analysis ([canopy_stack, tree_thiessen], tree_inventory)

if find_canopies == "Yes":
  findCanopy(canopy_stack, tree_thiessen)
#-----------------------------------------------
#-----------------------------------------------

#-----------------------------------------------
#-----------------------------------------------
def findCanopyBaseHeight(lidar, tree_heights, tree_thiessen, canopy_stack, cbh_rast):
  zonal_cbh = os.path.join(scratchgdb, "zonal_cbh")

  #tree_thiessen = os.path.join(outputs, "test_treeThiessen.shp")

  text = "Finding canopy base height for each tree."
  generateMessage(text)

  z_stat = ZonalStatisticsAsTable(tree_thiessen, "treeID", tree_heights, zonal_cbh, "NODATA", "MINIMUM")
  arcpy.AddField_management(zonal_cbh, "cbh", "FLOAT")
  arcpy.CalculateField_management(zonal_cbh, "cbh", "[MIN]")
  one_to_one_join(tree_thiessen, zonal_cbh, "cbh", "FLOAT")


  text = "Creating canopy base height raster."
  generateMessage(text)

  arcpy.PolygonToRaster_conversion(tree_thiessen, "cbh", cbh_rast, "CELL_CENTER", "", cell_size)

  
  boundary = os.path.join(outputs, "canopy_bnd.shp")

  this = Raster(tree_heights)
  max_canopy_height = Int(this.maximum)
  for i in range(max_canopy_height):
    field = "treeID"
    where_clause = "cbh = "+str(i)

    ladder_fuels = os.path.join(inputs, "ladder_fuels.lasd")
    ladders = os.path.join(outputs, "ladders.tif")
    ladder_heights = os.path.join(outputs, "ladder_heights.tif")

    #arcpy.Select_analysis(tree_thiessen, boundary, where_clause)
    #if arcpy.management.GetCount(boundary)[0] != "0":
    #  text = "Classifying ladder fuels for trees with a by cbh of "+str(i)+"."
    #  generateMessage(text)

      # Process: Classify LAS By Height
    #  arcpy.ClassifyLasByHeight_3d(lidar, "GROUND", "3 "+str(i), "NONE", "COMPUTE_STATS", boundary, "PROCESS_EXTENT", boundary)

  fuels = os.path.join(inputs, "test_Fuels.lasd")
  #arcpy.MakeLasDatasetLayer_management(fuels, ladder_fuels, [3])

  text = "Creating fuels ladder raster."
  generateMessage(text)
  #arcpy.LasDatasetToRaster_conversion(ladder_fuels, ladders, "ELEVATION", "BINNING AVERAGE NATURAL_NEIGHBOR", "FLOAT", "CELLSIZE", cell_size, "1")
  this = Float(ladders)-Float(dem)  #Equation for heights
  this = Con(IsNull(Float(this)), 0, Float(this))    # Make any null value the ground
  this = Con(Float(this) < 0, 0, Float(this))    # Make any negative value the groun
  this.save(ladder_heights)

  # Create raster of vegetation heights
  thiessen = os.path.join(scratchgdb, "thiessen")
  temp = os.path.join(scratchgdb, "temp")

  # Parameters
  this = Raster(ladder_heights)
  max_base_height = Int(this.maximum)
  incr = -1
  i = 0
  
  cbh_lst = []
  
  text = "Making horizontal slices (in "+unit+"):"
  generateMessage(text)
  while max_base_height > -1:
      upper = max_base_height
      max_base_height += incr
      lower = max_base_height
      if lower < 0:
        lower = 0

      ht_slice = os.path.join(scratchgdb, "cbh_slice_"+str(upper))
      cbh_select = os.path.join(scratchgdb, "cbh_select")
      slice_poly = os.path.join(scratchgdb, "cbh_slice_poly_"+str(upper))
      understory = os.path.join(scratchgdb, "understory_"+str(upper))
      
      #create slice
      text = "[0"+str(upper)+", 0"+str(lower)+"]"  
      generateMessage(text)

      vert_max = Con(Int(ladder_heights)>= upper, upper, Int(ladder_heights))
      vert_min = Con(Int(vert_max) <= lower, 0, Int(vert_max))
      vert_min.save(ht_slice)
      
      #convert slice to polygons and extract canopies
     
      arcpy.RasterToPolygon_conversion(ht_slice, slice_poly, "NO_SIMPLIFY", "VALUE")
      arcpy.Select_analysis (slice_poly, cbh_select, "gridcode <> 0")
      arcpy.Dissolve_management(cbh_select, understory, "", "", "SINGLE_PART")
      arcpy.AddField_management(understory, "h", "INTEGER")
      arcpy.CalculateField_management(understory, "h", 1)
      cbh_lst.append(understory)

      i += 1

  arcpy.Union_analysis (cbh_lst, cbh_stack)
  stack_fields = [f.name for f in arcpy.ListFields(cbh_stack)]
  sum_fields = []
  for field in stack_fields:
    if field[0] == "h":
      sum_fields.append(field)
  calc = ""
  for field in sum_fields:
    calc+="["+field+"]+"
  fxn = calc[:-1]
  arcpy.AddField_management(cbh_stack, "tot", "INTEGER")
  arcpy.CalculateField_management(cbh_stack, "tot", fxn)
  for field in stack_fields:
    if field[0] == "h" or field[0] == "F" and field != "FID" or field[0] == "S" and field != "Shape":
      arcpy.DeleteField_management(cbh_stack, field)
  #arcpy.Union_analysis ([canopy_stack, tree_thiessen], tree_inventory)

if find_cbh == "Yes":
  findCanopyBaseHeight(lidar, tree_heights, tree_thiessen, canopy_stack, cbh_rast)
  # text = "Canopy base heights found."
  # generateMessage(text)

