#-------------------------------------------------------------------------------
# Name:        genMitigation
# Purpose:     Input fuel.asc, classified.shp, *asset.shp*
#              Output mitigated.tif
#
# Author:      Matthew
#
# Created:     27/09/2017
# Copyright:   (c) Matthew 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

mitigated_fuel = "99"

# Import modules
import arcpy
import os
import sys
from arcpy import env
from arcpy.sa import *
arcpy.env.overwriteOutput = True

# Set scratch workspace and environment settings
scriptpath = sys.path[0]
toolpath = os.path.dirname(scriptpath)
scratchfolder = os.path.join(toolpath,"Scratch")
scratchws = env.scratchWorkspace
scratchgdb = os.path.join(scratchfolder, "Scratch.gdb")
if not env.scratchWorkspace:
  scratchws = scratchgdb

# Set Paths
outputs_path = os.path.join(toolpath, "Outputs")
inputs_path = os.path.join(toolpath, "Inputs")          # Assumed projected in UTM (meters)
asset_shp = os.path.join(inputs_path, "pipeline.shp")      # Assumed Pipeline Clipped to Study Site (classified.shp extent)
classified_unmitigated = os.path.join(inputs_path,"classified.shp")
fuel_asc = os.path.join(inputs_path,"fuel.asc")
canopy_asc = os.path.join(inputs_path, "canopy.asc")
stand_asc = os.path.join(inputs_path, "stand.asc")

# ------------------------------------------------------------------------------
# Create fuels raster (to be mitigated, and as snap raster setting)
# ------------------------------------------------------------------------------
fuel_tif = os.path.join(scratchfolder,"fuel.tif")
arcpy.ASCIIToRaster_conversion(fuel_asc,fuel_tif,"INTEGER")
arcpy.DefineProjection_management(fuel_tif, "PROJCS['NAD_1983_UTM_Zone_10N',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-123.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]")

canopy_tif = os.path.join(scratchfolder,"canopy.tif")
arcpy.ASCIIToRaster_conversion(canopy_asc,canopy_tif,"INTEGER")
arcpy.DefineProjection_management(canopy_tif, "PROJCS['NAD_1983_UTM_Zone_10N',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-123.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]")

stand_tif = os.path.join(scratchfolder,"stand.tif")
arcpy.ASCIIToRaster_conversion(stand_asc,stand_tif,"INTEGER")
arcpy.DefineProjection_management(stand_tif, "PROJCS['NAD_1983_UTM_Zone_10N',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-123.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]")


# Set extent properties
naipdesc = arcpy.Describe(fuel_tif)
arcpy.env.snapRaster = fuel_tif
outputextent = str(naipdesc.extent.XMin)+" "+str(naipdesc.extent.XMax)+" "+str(naipdesc.extent.YMin)+" "+str(naipdesc.extent.YMax)

# ------------------------------------------------------------------------------
# Buffer Pipeline Defensible Space, label as grass
# ------------------------------------------------------------------------------
asset_buffer_shp = os.path.join(scratchfolder, "asset_buff30.shp")
arcpy.Buffer_analysis(asset_shp,asset_buffer_shp,"30 FEET","","","ALL","","")

# Ascribe field with attribute "1" to represent grass Anderson Fuel, set canopy and stand to 0

arcpy.AddField_management(asset_buffer_shp,"mitfuel","INTEGER","","","","","","","")
arcpy.CalculateField_management(asset_buffer_shp,"mitfuel",mitigated_fuel,"","")
arcpy.AddField_management(asset_buffer_shp,"mitcanop","INTEGER","","","","","","","")
arcpy.CalculateField_management(asset_buffer_shp,"mitcanop","0","","")
arcpy.AddField_management(asset_buffer_shp,"mitstand","INTEGER","","","","","","","")
arcpy.CalculateField_management(asset_buffer_shp,"mitstand","0","","")


# Buffered Pipeline to raster, clip to study site with aligned cells
arcpy.AddMessage("Field added.  Converting to raster.")
asset_buffer_fuel_tif_noclip = r"K:\TFS_Fire\Tools\Mitigation\asset_fuel_buff30_noclip.tif"
asset_buffer_canopy_tif_noclip = r"K:\TFS_Fire\Tools\Mitigation\asset_canopy_buff30_noclip.tif"
asset_buffer_stand_tif_noclip = r"K:\TFS_Fire\Tools\Mitigation\asset_stand_buff30_noclip.tif"

arcpy.PolygonToRaster_conversion(asset_buffer_shp,"mitfuel",asset_buffer_fuel_tif_noclip,"","","5")
arcpy.PolygonToRaster_conversion(asset_buffer_shp,"mitcanop",asset_buffer_canopy_tif_noclip,"","","5")
arcpy.PolygonToRaster_conversion(asset_buffer_shp,"mitstand",asset_buffer_stand_tif_noclip,"","","5")


asset_buffer_fuel_tif = r"K:\TFS_Fire\Tools\Mitigation\asset_fuel_buff30.tif"
asset_buffer_canopy_tif = r"K:\TFS_Fire\Tools\Mitigation\asset_canopy_buff30.tif"
asset_buffer_stand_tif = r"K:\TFS_Fire\Tools\Mitigation\asset_stand_buff30.tif"

#arcpy.Clip_management(asset_buffer_tif_noclip,outputextent,asset_buffer_fuel_tif,fuel_tif,"255","NONE","MAINTAIN_EXTENT")
#arcpy.Clip_management(asset_buffer_tif_noclip,outputextent,asset_buffer_canopy_tif,fuel_tif,"255","NONE","MAINTAIN_EXTENT")
#arcpy.Clip_management(asset_buffer_tif_noclip,outputextent,asset_buffer_stand_tif,fuel_tif,"255","NONE","MAINTAIN_EXTENT")


# ------------------------------------------------------------------------------
# Create Mitigated Asset Layer
# ------------------------------------------------------------------------------
fuelMitig = r"K:\TFS_Fire\Tools\Mitigation\fuelMitig.tif"
canopyMitig = r"K:\TFS_Fire\Tools\Mitigation\canopyMitig.tif"
standMitig = r"K:\TFS_Fire\Tools\Mitigation\standMitig.tif"

fuelMitig_save = Con(IsNull(asset_buffer_fuel_tif),fuel_tif,asset_buffer_fuel_tif)
fuelMitig_save.save(fuelMitig)
canopyMitig_save = Con(IsNull(asset_buffer_canopy_tif),canopy_tif,asset_buffer_canopy_tif)
canopyMitig_save.save(canopyMitig)
standMitig_save = Con(IsNull(asset_buffer_stand_tif),stand_tif,asset_buffer_stand_tif)
standMitig_save.save(standMitig)

fuelMitig_asc = os.path.join(outputs_path,"fuelMitig.asc")
canopyMitig_asc = os.path.join(outputs_path,"canopyMitig.asc")
standMitig_asc = os.path.join(outputs_path,"standMitig.asc")
arcpy.AddMessage("Converting mitigated fuel raster to ascii.")
arcpy.RasterToASCII_conversion(fuelMitig, fuelMitig_asc)
arcpy.RasterToASCII_conversion(canopyMitig, canopyMitig_asc)
arcpy.RasterToASCII_conversion(standMitig, standMitig_asc)
