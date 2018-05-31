'''
Evaluate data from different antennae tested on the ground
HMH: 28-02-2018
'''

#import pyfits
import matplotlib.pyplot as plt 
import numpy as np
import glob, time
from astropy.io import fits
import platform, string
#-------------------------------------------------------------------------------
def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth
#-------------------------------------------------------------------------------
def get_data(name):
    data_unsorted = glob.glob(name)
    return data_unsorted
#-------------------------------------------------------------------------------
def plot_raw_data(bgs,timestamp,freqs,files,show_plots,plot_path):
    plt.figure(figsize=(12,8))
    extent = (timestamp[0], timestamp[-1], freqs[-1], freqs[0])
    plt.imshow(bgs, extent = extent, aspect = 'auto',cmap='jet', interpolation = 'none', vmin=3,vmax=30)    
    plt.tick_params(labelsize=14)
    plt.xlabel('Sampling time [s]',fontsize=15)
    plt.ylabel('Frequency [channel number]',fontsize=15)
    plt.title('Raw data, full size, background subtracted of: '+files,fontsize=15)
    savename = plot_path+files+'_raw.png'
    plt.savefig(savename)
    if show_plots==True:
        plt.show()
    else:
        plt.close()
    
#-------------------------------------------------------------------------------
def plot_lightcurve(timestamp,channel,lc1,dB2,freqs,files,show_plots,plot_path):
    
    plt.figure(figsize=(12,8))
    title = 'Light curve at channel {:3d} = {:5.1f} MHz'.format(channel,freqs[channel])

    plt.plot(timestamp,dB2)
    plt.tick_params(labelsize=14)
    plt.xlabel('Sampling time [s] of '+files,fontsize=15)
    plt.ylabel('Intensity [dB]',fontsize=15)
    plt.title(title,fontsize=15)
    plt.grid(axis='both')
        
    savename = plot_path+files+'_lightcurve.png'
    plt.savefig(savename)
    if show_plots==True:
        plt.show()
    else:
        plt.close()
#-------------------------------------------------------------------------------
def plot_hist(dB2,files,show_plots,plot_path):
    plt.figure(figsize=(12,8))
    bins = np.linspace(50, 80, 60)  # -> x.axis
    plt.hist(dB2, bins, alpha=0.5,color='r',histtype='stepfilled',linewidth=3.0)

    plt.xlabel('Intensity distribution [dB]',fontsize=15)
    plt.ylabel('Number of on/off values',fontsize=15)
    plt.title('Hot/cold histogram to derive Y-factor',fontsize=15)
    plt.tick_params(labelsize=14)
    plt.grid(axis='both')
    savename = plot_path+files+'_Histogram.png'
    plt.savefig(savename)
    if show_plots==True:
        plt.show()
    else:
        plt.close()
#-------------------------------------------------------------------------------
def plot_spectrum_manual(bgs,timestamp,data,files,freqs,plot_path):
    
    plt.ion()
    fig, axes = plt.subplots(nrows=2,figsize=(12,10))
    ax = axes[0]
    ax.imshow(bgs,aspect='auto',cmap='jet', interpolation = 'none',vmin=3,vmax=30)
    ax.set_xlabel('Sample number',fontsize=12)
    ax.set_ylabel('Frequency [channel number]',fontsize=12)
    ax.set_title('Raw data, full size, background subtracted of: '+files,fontsize=15)
    
    plt.ioff()
    
    x = []
    def onclick(event):
        x1 = event.xdata
        x.append(x1)
        print 'hot pixel = %d' %(x1)
        
        if len(x) == 2:
            fig.canvas.mpl_disconnect(cid)      
        
    select_values = raw_input('Press enter when ready to select values')
            
    cid = fig.canvas.mpl_connect('button_press_event', onclick)
    move_on = raw_input('Select hot value, then cold value. Then press enter to continue')
    pixel1 = int(round(x[0]))
    pixel0 = int(round(x[1]))
    print 'hot: ',pixel1
    print 'cold: ',pixel0
            
    sp1 = data[:,pixel1] # select channel near burst
    sp0 = data[:,pixel0] # select channel near burst
    dB = (sp1-sp0)/255.0*2500.0/25.4 # ((Imax-Imin)/bit_range)*(voltage_range/sensitivity)

    ax=axes[1]
    time_val = str(int(round(timestamp[pixel1])))
    title = 'Single spectrum at T='+time_val+' sec after start'
    ax.plot(freqs,dB,'*-r',linewidth=3.0)
    ax.set_xlabel('Frequency [MHz] of: '+files,fontsize=12)
    ax.set_ylabel('Intensity [dB] above background',fontsize=12)
    ax.set_title(title,fontsize=15)
    plt.grid(axis='both')
    plt.ylim(0,np.median(dB)+10)
    plt.xlim(350,850)
    savename = plot_path+files+'_Spectrum_at_T_'+time_val+'_manual.png'
    plt.savefig(savename)
    plt.show()
    
 #-------------------------------------------------------------------------------
def plot_spectrum(bgs,timestamp,data,files,freqs,plot_path,hot_pixel,cold_pixel,show_plots):
    print hot_pixel,cold_pixel
    print np.shape(bgs[:,hot_pixel:cold_pixel])
    
          
    sp1 = data[:,hot_pixel] # select channel near burst
    sp0 = data[:,cold_pixel] # select channel near burst
    dB = (sp1-sp0)/255.0*2500.0/25.4 # ((Imax-Imin)/bit_range)*(voltage_range/sensitivity)
    #plt.plot(sp1,'k')
    #plt.plot(sp0,'r')
    #plt.plot(sp1-sp0)
    #plt.show()
    
    #time_val = str(int(round(timestamp[hot_pixel])))
    plt.figure(figsize=(12,8))
    title = 'Typical Spectrum for '+files
    plt.plot(freqs,dB,'*-r',linewidth=3.0)
    plt.xlabel('Frequency [MHz]',fontsize=12)
    plt.ylabel('Intensity [dB] above background',fontsize=12)
    plt.title(title,fontsize=15)
    plt.grid(axis='both')
    #plt.ylim(0,np.median(dB)+10)
    plt.ylim(0,30)
    plt.xlim(350,850)
    savename = plot_path+files+'_Spectrum.png'
    plt.savefig(savename)
    if show_plots==True:
        plt.show()
    else:
        plt.close()
      
def check_windows(path,plot_path):
    p = platform.system()
    iswin = 0
    if p == 'Windows':
        path = string.replace(path,'/','\\')
        plot_path = string.replace(plot_path,'/','\\')
        iswin = 1
    return path, plot_path, iswin

def find_nearest(array,value):
    idx = (np.abs(array-value)).argmin()
    return array[idx]

def find_peaks(bgs,plot_path,show_plots):
    m = np.median(bgs,axis=0)
    peaks = np.zeros(len(m))
    peaks.fill(np.nan)
    troughs = np.zeros(len(m))
    troughs.fill(np.nan)
    peak_ind = []
    trough_ind = []
    
    for i in range(1,len(m)-1):
        if (m[i-1] < m[i]) & (m[i+1] < m[i]) & (m[i] > 0):
            peaks[i]=m[i]
            
        if (m[i-1] > m[i]) & (m[i+1] > m[i]) & (m[i] < 0): 
            troughs[i]=m[i]
            
    # need to make sure we're not counting consecutive peaks
    diff = []
    for i in range(0,len(peaks)):
        if np.isnan(peaks[i]) == False:
            if np.nansum(troughs[i-3:i+3]) == 0:
                print 'no troughs', troughs[i-3:i+3]
            else:
                for k in range(i-3,i+3):
                    if np.isnan(troughs[k]) == False:
                        diff_val = peaks[i] - troughs[k]
                        peak_ind.append(i)
                        trough_ind.append(k)
                        diff.append(diff_val)
                        break
    
    med_diff_val = find_nearest(diff,np.median(diff)) 

    # whichever peak and trough have the median difference is the one we want
    for i in range(0,len(diff)):
        if diff[i] == med_diff_val:
            for k in range(0,len(m)):
                if m[k] == peaks[peak_ind[i]]:
                    hot_pixel = k
                elif m[k] == troughs[trough_ind[i]]:
                    cold_pixel = k

    pixelvals = np.zeros(len(m))
    pixelvals.fill(np.nan)
    pixelvals[hot_pixel] = m[hot_pixel]
    pixelvals[cold_pixel] = m[cold_pixel]
    plt.plot(m)
    plt.plot(peaks,'.')
    plt.plot(troughs,'.')
    plt.plot(pixelvals,'*')
    plt.title("Median power across entire spectrum")
    plt.xlabel("Sample Number")
    plt.ylabel("Median Power")
    savename = plot_path+files+'_Median_Power.png'
    plt.savefig(savename)
    if show_plots == True:
        plt.show()
    else:
        plt.close()
    return hot_pixel, cold_pixel
       
if __name__=="__main__":
    
    '''
    NOTE: Please set path, plot_path, and split_val to what it relevant for YOUR set up.
    '''
    
    path = './Data/Ground_based_individual_antennas/'
    plot_path = './Plots/'
    path,plot_path,iswin = check_windows(path,plot_path)
    pathname = path+'*.fit'
    data_files = get_data(pathname)
    if iswin == 0:
        split_val = 'nnas/'
    else:
        split_val = 'nnas\\'
    show_plots=False
    
    for i in range(0,len(data_files)):
        
        fds = fits.open(data_files[i])
        data  = fds[0].data
        freqs = fds[1].data['Frequency'][0] # extract frequency axis
        timestamp  = fds[1].data['Time'][0] # extract time axis
        bgs = data -  data.mean(axis=1, keepdims=True)  # subtract average background
        files = data_files[i].split(split_val)[1].split('.fit')[0]
        plot_raw_data(bgs,timestamp,freqs,files,show_plots,plot_path)
        
        channel = 59 #400 MHz=173, 500 MHz=135, 600 MHz=97, 700 MHz=59 and 800 MHz=20
        lc1 = data[channel,:] # select channel near burst
        lc1 = smooth(lc1,1)
        dB2 = (lc1)/255.0 * 2500.0/25.4 # converter into dB
        
        plot_lightcurve(timestamp,channel,lc1,dB2,freqs,files,show_plots,plot_path)
        plot_hist(dB2,files,show_plots,plot_path)
            #plot_spectrum_manual(bgs,timestamp,data,files,freqs,plot_path)
        print 'looking at ',files
        find_peaks(bgs,plot_path,show_plots)
        try:
            hot_pixel, cold_pixel = find_peaks(bgs,plot_path,show_plots)
            #pixels = [hot_pixel,cold_pixel]
            #pixels = np.sort(pixels)
            plot_spectrum(bgs,timestamp,data,files,freqs,plot_path,hot_pixel,cold_pixel,show_plots)
        except:
            print 'failed on ',files
            #plot_spectrum_manual(bgs,timestamp,data,files,freqs,plot_path)
        #plot_spectrum_manual(bgs,timestamp,data,files,freqs,plot_path)
        fds.close() # close fits file
        





    



