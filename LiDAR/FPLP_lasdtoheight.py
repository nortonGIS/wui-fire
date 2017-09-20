#-------------------------------------------------------------------------------
# Name:        FPLP_lasdtoheight
# Purpose:     FP.lasd,LP.lasd --> Height Raster
#
# Author:      Matthew
#
# Created:     23/05/2017
# Copyright:   (c) Matthew 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# Import modules
import arcpy
import os
import sys
from arcpy import env
from arcpy.sa import *
arcpy.env.overwriteOutput = True

arcpy.AddMessage("print 1")

# Set scratch workspace and environment settings
scriptpath = sys.path[0]
ToolData = os.path.dirname(scriptpath)
toolpath = os.path.dirname(ToolData)
scratchfolder = os.path.join(ToolData,"Scratch")
scratchws = env.scratchWorkspace
scratchgdb = os.path.join(scratchfolder, "Scratch.gdb")
if not env.scratchWorkspace:
  scratchws = scratchgdb

arcpy.AddMessage("print 2")  

# -----------------Set Paths----------------------
outputs_path = os.path.join(toolpath, "Outputs")
inputs_path = os.path.join(toolpath, "Inputs")
LAS_path = os.path.join(inputs_path, "LAS")
FPlasdpath = os.path.join(inputs_path,"FP_Crockett.lasd")     # Replace LAS, create lasd manually and store relative pathnames
LPlasdpath = os.path.join(inputs_path, "LP_Crockett.lasd")    # Replace LAS, create lasd manually and store relative pathnames
naippath = os.path.join(inputs_path,"Crockett.tif")

# ---------------Set extent properties---------------------------
##naippath = os.path.join(inputs_path,"Concord_Test_unprocessedNAIP.tif")
##naipdesc = arcpy.Describe(naippath)
##naipclip = os.path.join(outputs_path,"naip.tif")
##outputextent = str(naipdesc.extent.XMin)+" "+str(naipdesc.extent.XMax)+" "+str(naipdesc.extent.YMin)+" "+str(naipdesc.extent.YMax)
##arcpy.Clip_management(naippath, outputextent, naipclip,"","","","")
###
### Create Boundary
##ZeroValueRast = Int(naippath)*0
##bndrast = os.path.join(scratchfolder,"bndrast.tif")
##ZeroValueRast.save(bndrast)
##bnd = os.path.join(outputs_path,"bnd.shp")
##arcpy.RasterToPolygon_conversion(Raster(bndrast),bnd,"NO_SIMPLIFY","")
##arcpy.AddMessage("bnd.shp created in Outputs folder.")

# -------------Create DEM, DSM, Heights--------------------
#
#cell_size = str(arcpy.GetRasterProperties_management(naippath,"CELLSIZEX",""))
cell_size = str(3.28084*5)
arcpy.AddMessage("print 3")
#
# Create DEM
DEMpath = os.path.join(outputs_path,"DEM.tif")
arcpy.AddMessage("print 4")
arcpy.LasDatasetToRaster_conversion(LPlasdpath, DEMpath, "ELEVATION", "BINNING MINIMUM LINEAR", "FLOAT", "CELLSIZE", cell_size, "")
arcpy.AddMessage("DEM.tif created in Outputs folder.")
arcpy.env.snapRaster = DEMpath
#
# Create DSM
DSMpath = os.path.join(outputs_path,"DSM.tif")
arcpy.LasDatasetToRaster_conversion(FPlasdpath, DSMpath, "ELEVATION", "BINNING MAXIMUM SIMPLE", "FLOAT", "CELLSIZE", cell_size, "")
arcpy.AddMessage("DSM.tif created in Outputs folder.")
###
### Create Intensity
##intensitypath = os.path.join(outputs_path, "lidar_intensity.tif")
##arcpy.LasDatasetToRaster_conversion(combined_lasdpath,intensitypath, "INTENSITY", "BINNING AVERAGE NONE", "FLOAT", "CELLSIZE", cell_size, "1")
##arcpy.AddMessage("lidar_intensity.tif created in Outputs folder")
#
# Create Heights
out_heights = os.path.join(outputs_path,"heights.tif")
hts_interm1 = os.path.join(scratchfolder,"hts_interm1.tif")
hts_interm2 = os.path.join(scratchfolder,"hts_interm2.tif")
heights = Float(DSMpath)-Float(DEMpath)
heights = Con(IsNull(Float(heights)), 0, Float(heights))
heights = Con(Float(heights) < 0, 0, Float(heights))
heights = SetNull(Float(heights),Float(heights),"VALUE > 350")                      # Minimum "Cloud" heights defined here.  NOTE UNITS
if arcpy.GetRasterProperties_management(heights,"ANYNODATA").getOutput(0):
    arcpy.AddMessage("Interpolating under clouds/birds.")
    heights.save(hts_interm1)
    heights.save(hts_interm2)
    del heights
    cloudrast = os.path.join(scratchws,"cloudrast")
    arcpy.gp.Reclassify_sa(hts_interm1, "VALUE", "0 500 NODATA;NODATA 1", cloudrast, "DATA")
    cloudpts = os.path.join(scratchws,"cloudpts")
    arcpy.RasterToPoint_conversion(cloudrast,cloudpts,"VALUE")
    cloudpts_buf30 = os.path.join(scratchws,"cloudptsbuf30")
    arcpy.Buffer_analysis(cloudpts, cloudpts_buf30, "30 Meters", "FULL", "ROUND", "ALL", "", "PLANAR")
    nocloudmask = ExtractByMask(hts_interm2,cloudpts_buf30)
    interppts = os.path.join(scratchws,"interppts")
    arcpy.RasterToPoint_conversion(nocloudmask, interppts,"")
    NNinterp = os.path.join(scratchws,"NNinterp")
    arcpy.gp.NaturalNeighbor_sa(interppts, "grid_code", NNinterp, hts_interm2)
    arcpy.MosaicToNewRaster_management(hts_interm2+";"+NNinterp,outputs_path,"heights.tif", "", "32_BIT_FLOAT", "", "1", "FIRST", "FIRST")
    arcpy.AddMessage("heights.tif created in Outputs folder.")
else:
    heights.save(out_heights)
    arcpy.AddMessage("heights.tif created in Outputs folder.")

#
# Create Boundary
heights = os.path.join(scratchfolder,"heights.tif")
ZeroValueRast = Int(heights)*0
bndrast = os.path.join(scratchfolder,"bndrast.tif")
ZeroValueRast.save(bndrast)
bnd = os.path.join(outputs_path,"bnd.shp")
arcpy.RasterToPolygon_conversion(Raster(bndrast),bnd,"NO_SIMPLIFY","")
arcpy.AddMessage("bnd.shp created in Outputs folder.")

#out_heights = os.path.join(outputs_path,"heights.tif")
#out_naip = os.path.join(outputs_path,"naip.tif")
#arcpy.Clip_management(naippath, bnd,out_naip)
#arcpy.AddMessage("naip.tif created in outputs folder.")
