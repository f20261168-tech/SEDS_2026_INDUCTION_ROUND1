import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy.signal import savgol_filter


data = pd.read_csv("Depth Data.csv")  #Reading of the Csv file

#selecting columns
depths = data['Depth (m)']

depths = pd.to_numeric(depths, errors='coerce')  #force a column to numbers which has text or any other junk values

print(depths.dtype) #checking if all are numerical by checking their datatype

missing_rows = data[depths.isna()] # checking if values are missing or not, if value is NaN it shows True, otherwise False
print(missing_rows) # printing out the missing row

'''function of interpolate is to fill the gap with valid data on both the sides of the gap,by  default it checks 
   both the sides and if say the first index 0  has NaN then it remains on NaN hence we add 
   limit_direction = ' both' so that it will fill from which ever side is available if both are not available'''

depths = depths.interpolate(method='linear', limit_direction='both') # Help fixing the missing values

missing_rows = data[depths.isna()] # checking if values are missing or not, if value is NaN it shows True, otherwise False
print(missing_rows) # printing out the missing row, it should be empty data frame as we are interpolating a value

# should detect and remove spikes/outliers
diff_fwd = depths.diff().abs()      # jump from the previous point, difference between row 2 and row 1, considering row 2 is selected
diff_bwd = depths.diff(-1).abs()    # jump to the next point, difference between row 3 and row 2, considering row 2 is selected
                                    # .abs() gives the absolute mod value removing the negative value if any

Spike_Threshold = 60 # this defines a threshold that any jump above 60m is seen as an outlying point or a spike
Spike = (diff_fwd > Spike_Threshold) & (diff_bwd > Spike_Threshold) # It's a Series of True/False values for every point checking weather if it above or below threshold, True for Above Threshold
print(f"Spikes detected: {Spike.sum()}") # Counting the number of spikes
print(data[Spike == True]) # Checking which values are showing the spikes

depths_clean = depths.copy() # copying the depths data set to modify and clean the values with no spikes
depths_clean[Spike == True] = np.nan # changes the spike values to NaN
# now we interpolate the Nan values to get a cleaner curve/value which matches the real world
depths_clean = depths_clean.interpolate(method='linear', limit_direction = 'both') # This gives a set of values matching the real world case

# We SMOOTH the curve using the library scipy
'''Working of scipy
For each point, it looks at a small window around it (11 points here:
5 before, the center, 5 after), fits a quadratic curve (polyorder=2)
through those points using least-squares, then replaces the center
point with that curve's value at that position. The window then
slides forward by one and repeats for every point in the series.

We dont use a plain moving average because an average treats every point equally
and lags behind real trends (rising/falling seafloor). A polynomial
fit can follow that trend, so peaks and slopes survive smoothing
instead of getting flattened.

The window lenght must be odd because the filter needs one exact center
point (e.g. 11 points = 5 before + center + 5 after).

poly-order < window_length, this is because a quadratic needs only 3 points to
define its shape (a, b, c) - the extra points in an 11-point window
are what create the smoothing effect, since the curve has to
compromise across all of them rather than pass through each exactly.

Edge points (start/end of array) are handled automatically by scipy
using a one-sided window - no extra handling needed here.

Chosen window_length=11 (~11 seconds of readings) and
polyorder=2 (gentle curves) because it is big enough to smooth out per-second
jitter, small enough to still track the seafloor's real rises/dips.'''


smoothed = savgol_filter(depths_clean, window_length=11, polyorder=2)


'''NO ANIMATION

fig , ax = plt.subplots(figsize=(12, 6))  # fig - for the whole window/image, ax - for axes and drawing of lines

ax.plot(depths_clean.index, depths, color='lightcoral', linewidth=0.5, label='Original Data')
ax.plot(depths_clean.index, depths_clean, color='skyblue', alpha=0.5, linewidth = 2, label='Cleaned raw') #alpha is the transparency of the line 0<=alpha<=1
ax.plot(depths_clean.index, smoothed, color='navy', linewidth=2, label='Smoothed')

ax.set_xlim(0 - 10, len(depths_clean) + 10) # setting the limit for x-axis values
ax.set_ylim(depths_clean.min() - 50, depths_clean.max() + 50) # setting the limit for y-axis values
#ax.invert_yaxis()
ax.set_xlabel("Points") # labelling x-axis
ax.set_ylabel("Depth (m)") # labelling y-axis
ax.set_title("Ship Depth Sensor") # naming the graph
ax.legend(loc='upper right') # setting the legend location

plt.show()'''


fig, ax = plt.subplots(figsize=(12, 6))

# Create empty lines
line_original, = ax.plot([], [], color='lightcoral', linewidth=0.5, label='Original Data')
line_cleaned, = ax.plot([], [], color='skyblue', alpha=0.5, linewidth=2, label='Cleaned raw')
line_smoothed, = ax.plot([], [], color='navy', linewidth=2, label='Smoothed')

# Set axis limits
ax.set_xlim(0 - 10, len(depths_clean) + 10)
ax.set_ylim(depths_clean.min() - 50, depths_clean.max() + 50)

# Labels
ax.set_xlabel("Points")
ax.set_ylabel("Depth (m)")
ax.set_title("Ship Depth Sensor")
ax.legend(loc='upper right')

# Animation function
def update(frame):   # in matplotlib .FuncAnimation when filling out the frames it automatically gets the variable frame everytime it updates from 0 to len()-1

    x = depths_clean.index[:frame]  # :frame is used slicing the Series such as depths, depths_clean, smoothed

    line_original.set_data(x, depths.iloc[:frame])
    line_cleaned.set_data(x, depths_clean.iloc[:frame])
    line_smoothed.set_data(x, smoothed[:frame])

    return line_original, line_cleaned, line_smoothed


# Create animation
ani = animation.FuncAnimation(fig, update, frames=len(smoothed), interval=100, blit=True, repeat=False)

plt.show()