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
from tableJoin import one_to_one_join

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

heights = os.path.join(inputs, "heights.tif")
trees = os.path.join(inputs, "trees.shp")
naip = os.path.join(inputs, "naip.tif")

existing_canopy_centroids = os.path.join(outputs, "canopy_cntrs.shp")
tree_thiessen = os.path.join(outputs, "treeThiessen.shp")
thiessen = os.path.join(scratchgdb, "thiessen")

all_heights = Con(IsNull(Float(heights)),0,Float(heights))
all_heights.save(tree_heights)

height_range = []
for range in height_ranges:
    lower = slice[0]
    upper = slice[1]
    
    height_range = str(lower)+"_"+str(upper))
    slice = os.path.join(outputs, "slice_"+height_range)
    slice_poly = os.path.join(scratchgdb, "slice_poly_"+height_range)
    outTable = os.path.join(outputs, "zonal_"+height_range)
    canopies = os.path.join(outputs, "canopies_"+height_range)
    new_canopy_centroids = os.path.join(outputs, "new_canopy_cntr_"+height_range)
    
    #create slice
    vert_max = Con(Float(tree_heights) > upper, upper, Float(tree_heights))
    vert_min = Con(Float(vert_max) < lower, 0, Float(vert_max))
    vert_min.save(slice)
    
    #convert slice to polygons and extract canopies
    spectral_detail = 20
    spatial_detail = 20
    min_seg_size = 2
    
    seg_naip = SegmentMeanShift(slice, spectral_detail, spatial_detail, min_seg_size) #, band_inputs)
    seg_naip.save(slice_poly)
    arcpy.RasterToPolygon_conversion(slice, slice_poly, "NO_SIMPLIFY", "VALUE")
    where_clause = "Value > 0"
    arcpy.Select_analysis(slice_poly, canopies, where_clause)

    #join previous centroids to canopy polygons
    arcpy.SpatialJoin_analysis(canopies, existing_canopy_centroids, existing_canopies,  "JOIN_ONE_TO_MANY")

    #create new canopy centroids
    where_clause = "JOIN = NULL"
    arcpy.Select_analysis(existing_canopies, new_canopies, where_clause)
    arcpy.FeatureToPoint_management(new_canopies, new_canopy_centroids, "INSIDE")

    arcpy.Merge_management(existing_canopy_centroids, new_canopy_centroids)
    

arcpy.CreateThiessenPolygons_analysis(existing_canopy_centroids, thiessen)
this = ExtractByMask(thiessen, trees)
this.save(tree_thiessen)

#-----------------------------------------------
#-----------------------------------------------
text = "All processes are complete."
generateMessage(text)
#-----------------------------------------------
