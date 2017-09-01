
# coding: utf-8

# In[1]:

import netCDF4
import pandas as pd
import numpy as np
import numpy.ma as ma
import glob
import multiprocessing



# In[2]:

def parse_a_scenario(path,POI):
    # get the time-series LOCA value at the POI
    data = netCDF4.Dataset(path, mode='r')
    lats = data.variables['Lat'][:]
    lngs = data.variables['Lon'][:]
    time = data.variables['Time'][:]
    name = path.split("\\")[-1].split(".")[0]
    variable = data.variables[name][:]
    lat_idx = np.abs(lats-POI['lat']).argmin()
    lon_idx = np.abs(lngs-POI['lon']).argmin()
    return time, ma.getdata(variable)[:,lat_idx,lon_idx]


# In[3]:

def parse_scenarios(LOCA_path,gcm,rcp,variable,POI):
    # get the time-series LOCA value of a gcm, rcp, variable, and at POI
    all_data = pd.DataFrame()
    files = glob.glob(r'%s\%s\%s\%s*.nc'%(LOCA_path,gcm,rcp,variable))
    for file in files:
        year = int(file.split('\\')[-1].split(".")[1])
        if year<=2040: # define upper limit (e.g. 2040) of the time series.
            print ('I am reading year %.0f'%year)
            time,data = parse_a_scenario(file,POI)
            sub = pd.DataFrame(time)
            sub.columns  = ['time']
            sub[variable] = data
            sub['year'] = year
            all_data = pd.concat([all_data,sub])
    all_data = all_data.reset_index()
    return all_data


# In[4]:

def attribute_location(sf,keyword):
    # find a field's location in a shapefile
    for field in sf.fields:
        if keyword in field:
             return sf.fields.index(field)     


# In[5]:

def cell_in_boundary(boundary,nc):
    # get the LOCA cells in a boundary
    import shapefile as shp #need the package pyshp
    import matplotlib.pyplot as plt
    import matplotlib.path as mplp
    nc = netCDF4.Dataset(nc,mode = 'r')
    lats = nc.variables['Lat'][:]
    lngs = nc.variables['Lon'][:]
    X, Y = np.meshgrid(lngs, lats)
    points = np.array((X.flatten(), Y.flatten())).T
    
    sf = shp.Reader(boundary)
    HUC_loc = attribute_location(sf,'HUC12')
    in_cells = pd.DataFrame()
    
    plt.figure()
    
    for shape in sf.shapeRecords():
        temp = pd.DataFrame()
        x = [i[0] for i in shape.shape.points[:]]
        y = [i[1] for i in shape.shape.points[:]]
        HUC = shape.record[HUC_loc-1]
        plt.plot(x,y)
        line = np.asarray(shape.shape.points[:])
        mpath = mplp.Path(line)
        mask = mpath.contains_points(points).reshape(X.shape)
        plt.plot(X[mask],Y[mask],'ro')
        temp['X'] = X[mask]
        temp['Y'] = Y[mask]
        temp['HUC'] = HUC
        in_cells = in_cells.append(temp, ignore_index=True)
    return in_cells


# In[6]:

def find_event(GCM,RCP,nc,boundary,DIR,variable):
    # find the date with the highest value
    in_cells= cell_in_boundary(boundary,nc)
    for HUC in in_cells['HUC'].unique():
        print('I am working on %s %s for %s'%(GCM,RCP,HUC))
        sub_cells = in_cells[in_cells['HUC']==HUC]
        master = pd.DataFrame()
        for i in sub_cells.index:
            POI = {'name': 'Concord', 'lat': sub_cells.loc[i,'Y'], 'lon':sub_cells.loc[i,'X']}
            profile = parse_scenarios(DIR,GCM,RCP,variable,POI)
            master[i] = profile['rainfall']
        master.head()
        master['average']= master.mean(1)
        master['time']= profile['time']
        master['year']= profile['year']
        idx = master['average'].idxmax()
        event = master.loc[idx,:]
        event[['time','year','average']].to_csv(r'E:\01_Data\08_rainfall_projections\%s_%s_%s.csv'%(HUC,RCP,GCM))
        print ('I am done with %s %s for %s'%(GCM,RCP,HUC))

# In[6]:

def main():
    GCMs = ['CanESM2','CNRM-CM5','HadGEM2-ES','MIROC5']
    RCPs = ['rcp45','rcp85']
    nc= r'J:\LOCA\CA_NV_VIC_output_2016-09-10\CA_NV_VIC_output_2016-09-10\CanESM2\rcp85\rainfall.2006.v0.CA_NV.nc'
    boundary = r"G:\3Di\LA\Dominguez_huc12.shp"
    DIR =  r'J:\LOCA\CA_NV_VIC_output_2016-09-10\CA_NV_VIC_output_2016-09-10'
    variable = 'rainfall'
    
    inputs = pd.DataFrame()
    i=0
    for GCM in GCMs:
        for RCP in RCPs:
            inputs.loc[i,'GCM'] = GCM
            inputs.loc[i,'RCP'] = RCP
            i=i+1
    inputs['nc'] = nc
    inputs['boundary'] = boundary
    inputs['LOCA_DIR'] = DIR
    inputs['variable'] = variable

    # run in parellel
    pool = multiprocessing.Pool(8)
    pool.starmap(find_event,inputs.as_matrix())
    pool.close()
    pool.join()


# In[ ]:

if __name__ == '__main__':
    main()
