# @ImagePlus imp
"""
Spot Tracker GUI
Version: 1.1
Date: 5 October 2025
Author: Maarten Paul (maarten.paul@gmail.com)

A GUI tool for tracking spots in time-lapse microscopy images with ROI management.

Changelog:
Version 1.1 (5 October 2025):
- Added "Add ROI at Current Frame" button for manual ROI addition at specific timepoints
- Added "Create New Focus ROI" button to automatically generate new focus IDs
- Improved ROI naming: automatic cleanup of names after dash
- Fixed ROI position setting to ensure correct timepoint assignment

Version 1.0:
- Initial release with basic tracking functionality
- Track Spot Forward and Re-track from Current Frame
- ROI management: Clear, Crop Stack, Save to OMERO

TODO:
- Fix "Save ROIs to OMERO" functionality (currently not working)
- Add keyboard shortcuts for common actions
- Add option to configure search radius for spot tracking
- Add undo functionality for tracking operations
"""

from javax.swing import JFrame, JPanel, JButton, BoxLayout, Box
from java.awt import Dimension, Component
from ij import IJ, ImagePlus, WindowManager, ImageStack
from ij.plugin.frame import RoiManager
from ij.gui import Roi, GenericDialog
from ij.plugin import Duplicator
import omero
from omero.model import RectangleI, RoiI, ImageI
from omero.rtypes import rdouble, rint
from java.lang import Long

class SpotTrackerGUI(JFrame):
    def __init__(self):
        super(SpotTrackerGUI, self).__init__("Spot Tracker")
        self.imp = WindowManager.getCurrentImage()
        self.rm = self.get_roi_manager()
        self.setup_gui()
        
    def get_roi_manager(self):
        """Get or create ROI Manager instance"""
        rm = RoiManager.getInstance()
        if rm is None:
            rm = RoiManager()
        return rm
        
    def setup_gui(self):
        panel = JPanel()
        panel.setLayout(BoxLayout(panel, BoxLayout.Y_AXIS))
        
        # Create buttons grouped by functionality
        # Tracking buttons
        track_btn = JButton("Track Spot Forward", actionPerformed=self.track_spot)
        retrack_btn = JButton("Re-track from Current Frame", actionPerformed=self.retrack_from_current)
        add_roi_btn = JButton("Add ROI at Current Frame", actionPerformed=self.add_roi_at_current_frame)
        new_focus_btn = JButton("Create New Focus ROI", actionPerformed=self.create_new_focus_roi)
        
        # ROI management buttons
        clear_btn = JButton("Clear All ROIs", actionPerformed=self.clear_rois)
        crop_btn = JButton("Crop Stack from ROIs", actionPerformed=self.crop_stack)
        omero_btn = JButton("Save ROIs to OMERO", actionPerformed=self.save_to_omero)
        
        # Set preferred size for all buttons
        buttons = [track_btn, retrack_btn, add_roi_btn, new_focus_btn, clear_btn, crop_btn, omero_btn]
        for btn in buttons:
            btn.setAlignmentX(Component.CENTER_ALIGNMENT)
            btn.setMaximumSize(Dimension(550, 40))
            btn.setPreferredSize(Dimension(550, 40))
        
        # Add components with spacing
        # Tracking section
        panel.add(Box.createRigidArea(Dimension(0, 10)))
        panel.add(track_btn)
        panel.add(Box.createRigidArea(Dimension(0, 5)))
        panel.add(retrack_btn)
        panel.add(Box.createRigidArea(Dimension(0, 5)))
        panel.add(add_roi_btn)
        panel.add(Box.createRigidArea(Dimension(0, 5)))
        panel.add(new_focus_btn)
        
        # Separator
        panel.add(Box.createRigidArea(Dimension(0, 20)))
        
        # ROI management section
        panel.add(clear_btn)
        panel.add(Box.createRigidArea(Dimension(0, 5)))
        panel.add(crop_btn)
        panel.add(Box.createRigidArea(Dimension(0, 5)))
        panel.add(omero_btn)
        panel.add(Box.createRigidArea(Dimension(0, 10)))
        
        # Set panel size
        panel.setPreferredSize(Dimension(650, 400))
        
        self.add(panel)
        self.pack()
        self.setLocationRelativeTo(None)
    
    def save_to_omero(self, event):
        """Save ROIs to OMERO"""
        try:
            # Check if we have an OMERO connection
            client = self.imp.getProperty("omero.client")
            if not client:
                IJ.error("Not an OMERO image")
                return
                
            if self.rm.getCount() == 0:
                IJ.error("No ROIs to save")
                return
            
            # Get image ID from image properties
            image_id = self.imp.getProperty("omero.id")
            
            # Convert ROIs to OMERO format and save
            update_service = client.getSession().getUpdateService()
            roi_facility = gateway.getFacility(ROIFacility.class)
            
            # Get necessary services
            gateway = self.imp.getProperty("omero.gateway")
            ctx = gateway.getLoggedInContext()
            
            # Create ROI data
            rois = []
            # Add all ROIs from manager
            for i in range(self.rm.getCount()):
                roi = self.rm.getRoi(i)
                bounds = roi.getBounds()
                # Create rectangle shape
                rect = omero.model.RectangleI()
                rect.setX(omero.rtypes.rdouble(bounds.x))
                rect.setY(omero.rtypes.rdouble(bounds.y))
                rect.setWidth(omero.rtypes.rdouble(bounds.width))
                rect.setHeight(omero.rtypes.rdouble(bounds.height))
                
                # Set Z and T positions if available
                if hasattr(roi, 'getPosition'):
                    rect.setTheT(omero.rtypes.rint(roi.getPosition() - 1))
                
                # Create ROI
                omero_roi = omero.model.RoiI()
                omero_roi.setImage(omero.model.ImageI(Integer(image_id), False))
                omero_roi.addShape(rect)
                rois.append(omero_roi)
            
            # Save to OMERO
            update_service = client.getSession().getUpdateService()
            update_service.saveAndReturnArray(rois)
            
            IJ.log("Successfully saved ROIs to OMERO")
            
        except Exception as e:
            IJ.error("Error saving to OMERO: " + str(e))
    
    def clear_rois(self, event):
        """Clear all ROIs from manager and image"""
        self.rm.reset()
        self.imp.killRoi()
        IJ.log("Cleared all ROIs")
    
    def crop_stack(self, event):
        """Crop stack using ROIs from ROI manager"""
        if not self.imp:
            IJ.error("No image open")
            return
            
        if self.rm.getCount() == 0:
            IJ.error("No ROIs in ROI Manager")
            return
        
        # Check if all ROIs have same size
        first_roi = self.rm.getRoi(0)
        roi_width = first_roi.getBounds().width
        roi_height = first_roi.getBounds().height
        
        for i in range(self.rm.getCount()):
            roi = self.rm.getRoi(i)
            if (roi.getBounds().width != roi_width or 
                roi.getBounds().height != roi_height):
                IJ.error("All ROIs must have the same size")
                return
        
        # Create new stack with correct dimensions
        stack = ImageStack(roi_width, roi_height)
        
        # Copy each frame using the corresponding ROI
        for frame in range(1, self.imp.getNFrames() + 1):
            # Find ROI for this frame
            roi = None
            for i in range(self.rm.getCount()):
                if self.rm.getRoi(i).getPosition() == frame:
                    roi = self.rm.getRoi(i)
                    break
            
            if roi:
                # Set position in original image
                self.imp.setPosition(frame)
                ip = self.imp.getProcessor().duplicate()
                ip.setRoi(roi)
                ip = ip.crop()
                stack.addSlice("", ip)
        
        # Create new image plus with the stack
        cropped = ImagePlus("Cropped_" + self.imp.getTitle(), stack)
        
        # Copy scale from original image
        cropped.setCalibration(self.imp.getCalibration().copy())
        
        # Set display range and show
        cropped.setDisplayRange(self.imp.getDisplayRangeMin(), 
                              self.imp.getDisplayRangeMax())
        cropped.show()
        
        IJ.log("Created cropped stack from ROIs")
    
    def find_maximum_in_area(self, ip, roi, search_radius=5):
        """Find brightest point within search radius of ROI center"""
        bounds = roi.getBounds()
        center_x = bounds.x + bounds.width/2
        center_y = bounds.y + bounds.height/2
        
        max_intensity = float('-inf')
        max_x = center_x
        max_y = center_y
        
        for y in range(int(center_y - search_radius), int(center_y + search_radius)):
            for x in range(int(center_x - search_radius), int(center_x + search_radius)):
                if x >= 0 and y >= 0 and x < ip.getWidth() and y < ip.getHeight():
                    intensity = ip.getPixel(x, y)
                    if intensity > max_intensity:
                        max_intensity = intensity
                        max_x = x
                        max_y = y
        
        return (max_x, max_y)
    
    def track_from_frame(self, start_frame):
        """Track ROI from specified frame onwards"""
        roi = self.imp.getRoi()
        if not roi:
            IJ.error("Please draw a ROI first")
            return
        
        # Store current frame
        current_frame = self.imp.getFrame()
        
        # Clear ROIs from start_frame onwards
        for i in range(self.rm.getCount()-1, -1, -1):
            roi_at_i = self.rm.getRoi(i)
            if roi_at_i.getPosition() >= start_frame:
                self.rm.getRoi(i).setPosition(0)
                self.rm.select(i)
                self.rm.runCommand("Delete")
        
        # Add new starting ROI
        roi.setPosition(start_frame)
        self.rm.addRoi(roi)
        
        # Process all subsequent frames
        for frame in range(start_frame, self.imp.getNFrames()):
            self.imp.setPosition(frame + 1)
            previous_roi = self.rm.getRoi(self.rm.getCount()-1)
            
            # Find maximum intensity point
            ip = self.imp.getProcessor()
            max_pos = self.find_maximum_in_area(ip, previous_roi)
            
            if max_pos:
                # Create new ROI centered on maximum
                new_roi = Roi(
                    max_pos[0] - previous_roi.getBounds().width/2,
                    max_pos[1] - previous_roi.getBounds().height/2,
                    previous_roi.getBounds().width,
                    previous_roi.getBounds().height
                )
                new_roi.setPosition(frame + 1)
                self.rm.addRoi(new_roi)
                self.imp.setRoi(new_roi)
        
        # Remove ROI from display but keep in manager
        self.imp.setPosition(current_frame)
        self.imp.killRoi()
        IJ.log("Tracking complete from frame " + str(start_frame))
    
    def track_spot(self, event):
        """Start tracking from current frame forward"""
        if not self.imp:
            IJ.error("No image open")
            return
        current_frame = self.imp.getFrame()
        self.track_from_frame(current_frame)
    
    def retrack_from_current(self, event):
        """Start tracking from current frame"""
        if not self.imp:
            IJ.error("No image open")
            return
        current_frame = self.imp.getFrame()
        self.track_from_frame(current_frame)
    
    def add_roi_at_current_frame(self, event):
        """Add current selection as new ROI at current timepoint with cleaned name"""
        roi = self.imp.getRoi()
        if not roi:
            IJ.error("Please draw a ROI first")
            return
        
        # Get current frame and set it to the ROI
        current_frame = self.imp.getFrame()
        roi.setPosition(current_frame)
        
        # Add to ROI manager
        self.rm.addRoi(roi)
        
        # Get the newly added ROI (last one)
        new_index = self.rm.getCount() - 1
        new_roi = self.rm.getRoi(new_index)
        
        # Get and clean the name
        original_name = new_roi.getName()
        dash_index = original_name.find("-")
        if dash_index > 0:
            base_name = original_name[:dash_index + 1]
        else:
            base_name = original_name + "-"
        
        # Ask user for text to add after dash
        gd = GenericDialog("ROI Name")
        gd.addStringField("Add text after dash:", "", 20)
        gd.showDialog()
        
        if gd.wasCanceled():
            # If canceled, just use base name with dash
            new_name = base_name
        else:
            # Get user input and append to base name
            suffix = gd.getNextString()
            new_name = base_name + suffix
        
        self.rm.rename(new_index, new_name)
        
        # Select the ROI in the manager
        self.rm.select(new_index)
        
        IJ.log("Added ROI at frame " + str(current_frame) + " as '" + new_name + "'")
    
    def create_new_focus_roi(self, event):
        """Create new focus ROI with next available ID number"""
        roi = self.imp.getRoi()
        if not roi:
            IJ.error("Please draw a ROI first")
            return
        
        # Get current frame
        current_frame = self.imp.getFrame()
        
        # Find highest focus number from existing ROIs
        max_focus_num = 0
        for i in range(self.rm.getCount()):
            name = self.rm.getRoi(i).getName()
            # Look for pattern like "n01f001-" or "n01f001-start"
            if name.startswith("n") and "f" in name:
                try:
                    # Extract the part after 'f' and before '-'
                    f_index = name.index("f")
                    dash_index = name.index("-", f_index)
                    focus_num_str = name[f_index+1:dash_index]
                    focus_num = int(focus_num_str)
                    if focus_num > max_focus_num:
                        max_focus_num = focus_num
                except (ValueError, IndexError):
                    continue
        
        # Create new focus number
        new_focus_num = max_focus_num + 1
        
        # Create new ROI name (format: n01f00X-start)
        new_name = "n01f{:03d}-start".format(new_focus_num)
        
        # Set position and add to manager
        roi.setPosition(current_frame)
        self.rm.addRoi(roi)
        
        # Rename the newly added ROI
        new_index = self.rm.getCount() - 1
        self.rm.rename(new_index, new_name)
        
        IJ.log("Created new focus ROI: " + new_name + " at frame " + str(current_frame))

# Create and show GUI
gui = SpotTrackerGUI()
gui.setVisible(True)
