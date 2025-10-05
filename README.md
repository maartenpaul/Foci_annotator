# Spot Tracker GUI

A Jython script for Fiji/ImageJ to track fluorescent spots in time-lapse microscopy images with an easy-to-use graphical interface.

## Installation

1. Copy `TrackSpotStack_.py` to your Fiji scripts folder, or just open it in the script manager.
2. Restart Fiji or run `Plugins > Scripting > Refresh Jython Scripts`
3. Open your time-lapse image
4. Run the script from `Plugins > Scripts`

## Features

### Tracking Functions

**Track Spot Forward**
- Draw a ROI around your spot on the current frame
- Click this button to automatically track the spot through all subsequent frames
- The tracker finds the brightest point within a small search radius and follows it

**Re-track from Current Frame**
- Retrack from the current frame onwards
- Useful if tracking went wrong and you want to restart from a specific timepoint
- Deletes all ROIs from the current frame forward and starts fresh tracking

**Add ROI at Current Frame**
- Manually add a ROI at the current timepoint
- Prompts you to add custom text after the dash in the ROI name
- Useful for marking specific events (e.g., "n01f001-start", "n01f001-extend")
- Automatically selects the new ROI in the ROI Manager

**Create New Focus ROI**
- Automatically creates a new focus with the next available ID number
- Analyzes existing ROI names (e.g., n01f001, n01f002) and creates the next number
- New ROI is named with "-start" suffix (e.g., n01f003-start)
- Perfect for starting to track a new spot

### ROI Management

**Clear All ROIs**
- Removes all ROIs from the ROI Manager and the image
- Use this to start fresh

**Crop Stack from ROIs**
- Creates a new image stack with cropped regions based on your ROIs
- Each frame is cropped using the ROI at that timepoint
- All ROIs must have the same size
- Preserves calibration and display settings

**Save ROIs to OMERO**
- *Currently not functional* - marked as TODO
- Intended to save ROIs back to an OMERO server

## Workflow Example

1. Open your time-lapse image in Fiji
2. Run the Spot Tracker GUI script
3. Navigate to the first frame where you want to start tracking
4. Draw a rectangular ROI around your spot
5. Click "Create New Focus ROI" to create `n01f001-start`
6. Click "Track Spot Forward" to automatically track through all frames
7. If tracking fails at some point:
   - Navigate to that frame
   - Adjust the ROI position manually
   - Click "Re-track from Current Frame"
8. Add manual annotations using "Add ROI at Current Frame"
9. Export cropped regions with "Crop Stack from ROIs"

## ROI Naming Convention

The script uses a naming convention: `n[nucleus_id]f[focus_id]-[label]`

Examples:
- `n01f001-start` - First focus of nucleus 1, marked as start
- `n01f001-extend` - Same focus, marked as extend
- `n01f002-start` - Second focus of nucleus 1

## Requirements

- Fiji/ImageJ with Jython support
- Time-lapse image (hyperstack with time dimension)
- ROI Manager (automatically opened by the script)

## Version

**Version 1.1** (5 October 2025)

### Changelog
- Added "Add ROI at Current Frame" with custom text input
- Added "Create New Focus ROI" with automatic ID generation
- Improved ROI positioning for correct timepoint assignment
- Added ROI selection in manager after adding

## Author

Maarten Paul (maarten.paul@gmail.com)

## License

[Add your license here]

## Known Issues

- Save to OMERO functionality not yet implemented
- Tracking algorithm uses simple brightest-point detection (may fail with complex movements)
