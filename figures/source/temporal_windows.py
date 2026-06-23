#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "matplotlib==3.10.6",
#     "numpy>=2.3.0",
#     "pandas>=2.3.1",
# ]
# ///
"""
Generate a figure illustrating the temporal windows used in the monarch butterfly analysis.
Shows both 30-minute lag windows and the Next Day Window analysis approach.
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = SCRIPT_DIR / "temporal_windows_max_count_timing.csv"
DEFAULT_OUTPUT_PATH = SCRIPT_DIR.parent / "temporal_windows.png"

parser = argparse.ArgumentParser(
    description="Generate the temporal_windows PNG for manuscript.tex.",
)
parser.add_argument(
    "--data",
    type=Path,
    default=DEFAULT_DATA_PATH,
    help="Path to the max count timing CSV.",
)
parser.add_argument(
    "--output",
    type=Path,
    default=DEFAULT_OUTPUT_PATH,
    help="Path for the generated PNG.",
)
args = parser.parse_args()

data_path = args.data.expanduser().resolve()
output_path = args.output.expanduser().resolve()
output_path.parent.mkdir(parents=True, exist_ok=True)

# Set up the figure
fig, ax = plt.subplots(figsize=(12, 6))

# Define time range (2 days)
start_time = datetime(2024, 1, 1, 0, 0)  # Arbitrary date
hours = np.arange(0, 48, 0.5)  # Every 30 minutes for 2 days
times = [start_time + timedelta(hours=h) for h in hours]

# Define sunrise/sunset times (approximate for California winter)
day1_sunrise = 7.0  # 7:00 AM
day1_sunset = 17.5  # 5:30 PM
day2_sunrise = 31.0  # 7:00 AM next day (24 + 7)
day2_sunset = 41.5  # 5:30 PM next day (24 + 17.5)

# Create gradient background for day/night
for i in range(len(hours) - 1):
    hour = hours[i]

    # Determine color based on time of day
    if (day1_sunrise <= hour <= day1_sunset) or (day2_sunrise <= hour <= day2_sunset):
        # Daytime - calculate gradient based on position in day
        if hour < 24:  # Day 1
            day_progress = (hour - day1_sunrise) / (day1_sunset - day1_sunrise)
        else:  # Day 2
            day_progress = (hour - day2_sunrise) / (day2_sunset - day2_sunrise)

        # Peak brightness at midday
        if day_progress < 0.5:
            brightness = 0.3 + 0.7 * (day_progress * 2)
        else:
            brightness = 0.3 + 0.7 * (2 - day_progress * 2)

        # Light yellow at peak, transitioning to light blue at edges
        r = 1.0
        g = 0.95 + 0.05 * (1 - brightness)
        b = 0.85 + 0.15 * (1 - brightness)
        color = (r, g, b, 0.3)  # Semi-transparent
    else:
        # Nighttime - darker blue/gray
        color = (0.7, 0.75, 0.85, 0.2)

    # Draw background rectangle
    rect = patches.Rectangle((times[i], -0.1),
                            timedelta(hours=0.5), 1.2,
                            facecolor=color, edgecolor='none')
    ax.add_patch(rect)

# Create histogram first to determine observation point positions
# Load the max count timing data
df_max = pd.read_csv(data_path)

# Convert hours_since_sunrise to time of day (starting from 7 AM = day1_sunrise)
max_times_hours = day1_sunrise + df_max['hours_since_sunrise'].values

# Filter to reasonable range (during Day 1 daylight hours)
max_times_day1 = max_times_hours[(max_times_hours >= day1_sunrise) & (max_times_hours <= day1_sunset)]

# Convert to datetime objects for plotting
max_times_dt = [start_time + timedelta(hours=h) for h in max_times_day1]

# Create histogram with bins for each 30-minute interval during daylight
# Day 1 bins - from sunrise to sunset in 30-minute intervals
day1_bins_hours = np.arange(day1_sunrise, day1_sunset + 0.5, 0.5)
day1_bins_dt = [start_time + timedelta(hours=h) for h in day1_bins_hours]

# Day 2 bins - same pattern
day2_bins_hours = np.arange(day2_sunrise, day2_sunset + 0.5, 0.5)
day2_bins_dt = [start_time + timedelta(hours=h) for h in day2_bins_hours]

# Create histogram data for Day 1
counts, bins = np.histogram([mdates.date2num(t) for t in max_times_dt],
                           bins=[mdates.date2num(t) for t in day1_bins_dt])

# Normalize counts to fit in the plot (scale to max height of 0.25)
max_count = counts.max()
if max_count > 0:
    scaled_counts = counts * 0.25 / max_count
else:
    scaled_counts = counts

# Draw histogram bars directly on the x-axis
histogram_base = 0.0
for i in range(len(counts)):
    if counts[i] > 0:
        bar_left = mdates.num2date(bins[i])
        bar_width = mdates.num2date(bins[i+1]) - bar_left
        bar_height = scaled_counts[i]
        rect = patches.Rectangle((bar_left, histogram_base), bar_width, bar_height,
                                facecolor='orange', alpha=0.7, edgecolor='darkorange',
                                linewidth=0.5, zorder=4)
        ax.add_patch(rect)

# Add histogram label to the left of the histogram
ax.text(start_time + timedelta(hours=day1_sunrise - 1), 0.125, 'Max BI\nfrequency',
        fontsize=16, ha='right', va='center', color='darkorange', weight='bold')

# Now add observation points aligned with histogram bin centers
observation_y = 0.5
observation_times = []

# Add Day 1 observation points at center of each bin
for i in range(len(day1_bins_dt) - 1):
    bin_center = day1_bins_dt[i] + (day1_bins_dt[i+1] - day1_bins_dt[i]) / 2
    ax.plot(bin_center, observation_y, 'ko', markersize=6, zorder=5)
    observation_times.append((bin_center, (bin_center - start_time).total_seconds() / 3600))

# Add Day 2 observation points at center of each bin
for i in range(len(day2_bins_dt) - 1):
    bin_center = day2_bins_dt[i] + (day2_bins_dt[i+1] - day2_bins_dt[i]) / 2
    ax.plot(bin_center, observation_y, 'ko', markersize=6, zorder=5)
    observation_times.append((bin_center, (bin_center - start_time).total_seconds() / 3600))

# Add ALL 30-minute lag windows
lag_y = 0.35
# Draw all consecutive pairs
for i in range(len(observation_times) - 1):
    t1 = observation_times[i][0]
    t2 = observation_times[i + 1][0]

    # Check if they are consecutive (30 minutes apart)
    time_diff = (t2 - t1).total_seconds() / 60
    if abs(time_diff - 30) < 5:  # Allow small tolerance
        # Draw bracket using matplotlib's native bracket annotation
        ax.annotate('', xy=(mdates.date2num(t1), lag_y),
                   xytext=(mdates.date2num(t2), lag_y),
                   arrowprops=dict(arrowstyle='|-|', color='darkblue',
                                 linewidth=1, shrinkA=0, shrinkB=0, alpha=0.7))

        # Add small connecting lines (make them lighter)
        ax.annotate('', xy=(t1, observation_y), xytext=(t1, lag_y + 0.05),
                   arrowprops=dict(arrowstyle='-', color='darkblue',
                                 linewidth=0.5, linestyle='dashed', alpha=0.5))
        ax.annotate('', xy=(t2, observation_y), xytext=(t2, lag_y + 0.05),
                   arrowprops=dict(arrowstyle='-', color='darkblue',
                                 linewidth=0.5, linestyle='dashed', alpha=0.5))

# Add Next Day Window
# Start at last observation of Day 1
day1_obs = [t for t, h in observation_times if h < 24]
if len(day1_obs) >= 1:
    day1_max_time = day1_obs[-1]  # Last observation of Day 1
else:
    # Fallback if not enough observations
    day1_max_time = start_time + timedelta(hours=17.0)  # Default to 5:00 PM

# Last observation of day 2 (get actual last observation)
day2_obs = [t for t, h in observation_times if h >= 24]
if len(day2_obs) > 0:
    day2_last_time = day2_obs[-1]  # Last observation
else:
    day2_last_time = start_time + timedelta(hours=day2_sunset)

# Draw Next Day Window bracket
nextday_window_y = 0.75
ax.annotate('', xy=(mdates.date2num(day1_max_time), nextday_window_y),
           xytext=(mdates.date2num(day2_last_time), nextday_window_y),
           arrowprops=dict(arrowstyle='|-|', color='darkred',
                         linewidth=2, shrinkA=0, shrinkB=0))

# Add arrows for Next Day Window
ax.annotate('', xy=(day1_max_time, observation_y), xytext=(day1_max_time, nextday_window_y - 0.05),
           arrowprops=dict(arrowstyle='-', color='darkred',
                         linewidth=1.5, linestyle='dashed'))
ax.annotate('', xy=(day2_last_time, observation_y), xytext=(day2_last_time, nextday_window_y - 0.05),
           arrowprops=dict(arrowstyle='-', color='darkred',
                         linewidth=1.5, linestyle='dashed'))

# Add dashed extension lines to show Next Day Window start can vary
# Get first observation of Day 1
if len(day1_obs) > 0:
    day1_first_time = day1_obs[0]

    # Horizontal dashed line from first observation to last observation of Day 1
    day1_last_time = day1_obs[-1]  # Last observation of Day 1
    ax.plot([day1_first_time, day1_last_time], [nextday_window_y, nextday_window_y],
            color='darkred', linestyle='--', linewidth=1.5, alpha=0.6)

    # Vertical dashed line from first observation
    ax.plot([day1_first_time, day1_first_time], [observation_y, nextday_window_y],
            color='darkred', linestyle='--', linewidth=1.5, alpha=0.6)

    # Add solid vertical line at first observation intersecting the dashed horizontal line (like a scale bar)
    ax.plot([day1_first_time, day1_first_time], [nextday_window_y - 0.02, nextday_window_y + 0.02],
            color='darkred', linestyle='-', linewidth=2.5, zorder=6)

    # Add "Variable start time" label above the horizontal dashed line
    mid_dashed = day1_first_time + (day1_last_time - day1_first_time) / 2
    ax.text(mid_dashed, nextday_window_y + 0.02, 'Variable start time',
            fontsize=16, ha='center', color='darkred', style='italic')

# Add labels for both days - closer to the blue lines
# Find middle of day 1 observations (recalculate after using above)
day1_obs = [t for t, h in observation_times if h < 24]
if len(day1_obs) > 0:
    mid_day1_time = day1_obs[len(day1_obs) // 2]
    ax.text(mid_day1_time, lag_y - 0.08,
            '30-minute windows',
            fontsize=18, ha='center', color='darkblue', weight='bold')

# Find middle of day 2 observations
day2_obs = [t for t, h in observation_times if h >= 24]
if len(day2_obs) > 0:
    mid_day2_time = day2_obs[len(day2_obs) // 2]
    ax.text(mid_day2_time, lag_y - 0.08,
            '30-minute windows',
            fontsize=18, ha='center', color='darkblue', weight='bold')

# Calculate midpoint of Next Day Window for label
nextday_window_midpoint = day1_max_time + (day2_last_time - day1_max_time) / 2
ax.text(nextday_window_midpoint, nextday_window_y + 0.05,
        'Next Day Window',
        fontsize=18, ha='center', color='darkred', weight='bold')

# Add day/night labels
ax.text(start_time + timedelta(hours=3), 0.95, 'Night',
        fontsize=16, ha='center', style='italic', color='gray')
ax.text(start_time + timedelta(hours=(day1_sunrise + day1_sunset)/2), 0.95, 'Day 1',
        fontsize=16, ha='center', weight='bold')
ax.text(start_time + timedelta(hours=24), 0.95, 'Night',
        fontsize=16, ha='center', style='italic', color='gray')
ax.text(start_time + timedelta(hours=(day2_sunrise + day2_sunset)/2), 0.95, 'Day 2',
        fontsize=16, ha='center', weight='bold')
# Add legend for observation points
ax.plot([], [], 'ko', markersize=6, label='Observations')
ax.legend(loc='upper left', fontsize=16)

# Format the plot, ending at Day 2 sunset.
ax.set_xlim(times[0], start_time + timedelta(hours=day2_sunset + 1))
ax.set_ylim(0, 1.1)

# Format x-axis
ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:00'))
ax.xaxis.set_minor_locator(mdates.HourLocator(interval=3))

# Labels
ax.set_xlabel('Time (hours)', fontsize=18)
ax.tick_params(axis='x', labelsize=14)

# Remove y-axis
ax.set_yticks([])
ax.spines['left'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)

# Adjust layout
plt.tight_layout()

# Save the figure used by manuscript.tex.
plt.savefig(output_path, dpi=600, bbox_inches='tight')

print(f"Figure saved as {output_path}")
