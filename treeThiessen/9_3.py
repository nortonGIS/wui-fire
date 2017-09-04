#-------------------------------------------------------------------------------
# Name:        treeThiessen Tool
# Purpose:     Slices heights into ranges and differentiates between new canopies and existing canopies, and
#              creates centroids for new canopies, and then creates a theissen diagram.
#
#
#             Steps:
# Author:      Peter Norton
#
# Created:     09/03/2017
# Updated:
# Copyright:   (c) Peter Norton 2017
#-------------------------------------------------------------------------------
# ---------------------------------------------------------------------------

#-----------------------------------------------
# Import modules
import arcpy
import os
import sys
from arcpy import env
from arcpy.sa import *
arcpy.env.overwriteOutput = True

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

heights = os.path.join(inputs, "heights_1.tif")
trees = os.path.join(inputs, "trees_1.shp")
naip = os.path.join(inputs, "naip.tif")

tree_heights = os.path.join(outputs, "tree_hts.tif")
existing_canopy_centroids = os.path.join(outputs, "canopy_cntrs.shp")
tree_thiessen = os.path.join(outputs, "treeThiessen.shp")
thiessen = os.path.join(scratchgdb, "thiessen")
temp = os.path.join(scratchgdb, "temp")

all_heights = Con(IsNull(Float(heights)),0,Float(heights))
all_heights.save(tree_heights)

count = 0
max_height = 50
incr = -1
while max_height > 6:
    upper = max_height
    max_height += incr
    lower = max_height
    
##    height_range = str(lower)+"_"+str(upper)
##    ht_slice = os.path.join(scratchgdb, "slice_"+height_range)
##    slice_dissolve = os.path.join(scratchgdb, "slice_dis_"+height_range)
##    slice_sms = os.path.join(outputs, "slice_sms"+height_range+".tif")
##    slice_poly = os.path.join(scratchgdb, "slice_poly_"+height_range)
##    outTable = os.path.join(scratchgdb, "zonal_"+height_range)
##    canopies = os.path.join(scratchgdb, "canopies_"+height_range)
##    new_canopies = os.path.join(scratchgdb, "new_canopies_"+height_range)
##    new_canopy_centroids = os.path.join(scratchgdb, "new_canopy_cntr_"+height_range)

    ht_slice = os.path.join(scratchgdb, "slice")
    slice_dissolve = os.path.join(scratchgdb, "slice_dis")
    slice_sms = os.path.join(outputs, "slice_sms.tif")
    slice_poly = os.path.join(scratchgdb, "slice_poly")
    canopies = os.path.join(scratchgdb, "canopies")
    new_canopies = os.path.join(scratchgdb, "new_canopies")
    new_canopy_centroids = os.path.join(scratchgdb, "new_canopy_cntr")
    
    existing_canopies = os.path.join(scratchgdb, "existing_canopies")
    temp = os.path.join(scratchgdb, "temp_"+str(count))
    
    #create slice
    arcpy.AddMessage("Making vertical slices between "+str(upper)+" and "+str(lower)+" feet.")                  

    vert_max = Con(Float(tree_heights)>= upper, upper, Float(tree_heights))
    vert_min = Con(Float(vert_max) <= lower, 0, Float(vert_max))
    vert_min.save(ht_slice)
    
    #convert slice to polygons and extract canopies
    this = Con(Float(ht_slice), Int(ht_slice))
    this.save(slice_sms)
    arcpy.RasterToPolygon_conversion(slice_sms, slice_poly, "NO_SIMPLIFY", "VALUE")
    arcpy.Dissolve_management(slice_poly, canopies,"", "", 
                          "SINGLE_PART")

    #join previous centroids to canopy polygons
    if count > 0:
        arcpy.SpatialJoin_analysis(canopies, existing_canopy_centroids, existing_canopies,  "JOIN_ONE_TO_ONE")
        where_clause = "Exist IS NULL AND Shape_Length > 14"
        arcpy.Select_analysis(existing_canopies, new_canopies, where_clause)

        #create new canopy centroids
        arcpy.FeatureToPoint_management(new_canopies, new_canopy_centroids, "INSIDE")
        arcpy.AddField_management(new_canopy_centroids, "Exist", "INTEGER")
        arcpy.CalculateField_management(new_canopy_centroids, "Exist", 1)
        arcpy.DeleteField_management (new_canopy_centroids, ["Join_Count", "TARGET_FID","Shape_Area_1", "Shape_Leng", "ORIG_FID"]) 

        arcpy.DeleteField_management (existing_canopy_centroids, ["Shape_Area", "Shape_Leng", "ORIG_FID"]) 
 
        
        arcpy.Append_management(new_canopy_centroids, existing_canopy_centroids, "TEST")
        
    else:
        new_canopies = canopies
    
        #create new canopy centroids
        arcpy.FeatureToPoint_management(new_canopies, existing_canopy_centroids, "INSIDE")
        arcpy.AddField_management(existing_canopy_centroids, "Exist", "INTEGER")
        arcpy.CalculateField_management(existing_canopy_centroids, "Exist", 1)

    count += 1
    
arcpy.AddMessage("Creating Thiessen polygons of canopy centroids.")
arcpy.CreateThiessenPolygons_analysis(existing_canopy_centroids, thiessen)
arcpy.AddMessage("Clipping thiessen by tree boundary.")
arcpy.Clip_analysis (thiessen, trees, tree_thiessen)

