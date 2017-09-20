#-------------------------------------------------------------------------------
# Name:        thresholdsLib Tool
# Purpose:     This tool adds a new column to the desired table and updates the 
# 				rows with values from a 1:1 matched table from zonal statistics.
#
#			
#
# Author:      Peter Norton
#
# Created:     09/19/2017
# Updated:     -
# Copyright:   (c) Peter Norton 2017
#-------------------------------------------------------------------------------
#-----------------------------------------------
#-----------------------------------------------


#-----------------------------------------------
#-----------------------------------------------
# Import modules
import arcpy
import os
import sys
from arcpy import env
from arcpy.sa import *

def thresholdsLib(bioregion, stage, field, unit):
	if unit == "Meters":
    	ground_ht_threshold = 0.6096
	elif unit == "Feet":
    	ground_ht_threshold = 2
	#returns list of values for index based on input name
	if bioregion == "Tahoe":
		if stage == "S1":
      		if field == "S1_grid":
		        healthy = ">= 250" #[250,255]
		        dry = "<= 249"  #[0, 249]
		        return [dry, healthy]
		    
		    elif field == "S1_ndvi":
		        imp = "-0.88 <= x <= -0.12" #[-0.88, -0.12]
		        veg = "-0.01 <= x <= 0.6"  #[-0.01, 0.6]
		        return [imp, veg]

		    elif field == "S1_ndwi":
		        imp = "-0.02 <= x <= 0.91"  #[-0.02, 0.91]
		        veg = "-0.46 <= x <= -0.03" #[-0.46, -0.03]
		        return [imp,veg]

		    elif field == "S1_gndv":
		        imp = "-0.94<= x <= -0.05"  #[-0.94, -0.05]
		        veg = "-0.02 <= x <= 0.38" #[-0.02, 0.38]
		        return [imp,veg]

		    elif field == "S1_osav":
		        imp = "-0.94 <= x <= -0.13"  #[-0.94, -0.13]
		        veg = "-0.08 <= x <= 0.76" #[-0.08, 0.76]
		        return [imp,veg]

		    elif stage == "S2":
		      	if landcover == "vegetation":
		        	if field == "S2_grid":
		          		dry = ">= 250"    #[250, 255]
		          		healthy = "<= 249"    #(0, 249]
		          		return [dry, healthy]
		                
		        elif field == "S2_heig":
			    	grass = "x <= "+str(ground_ht_threshold)
			        shrub = "x <= "+str(3*ground_ht_threshold)
			        tree = "x > "+str(3*ground_ht_threshold)
			        return [grass, shrub, tree]		     

		    elif landcover == "impervious":
		        if field == "S2_heig":
		          path = "x <= "+str(ground_ht_threshold)
		          building = "x > "+str(ground_ht_threshold)
		          return [path, building]

		        elif field == "S2_ndwi":
		          imp = "0 <= x <= 0.91" #[0.1, 0.91]
		          return [imp]