import os
import time
import subprocess
import random
import shutil

class SimpleCamera:
    def __init__(self):
        self.capture_path = "static/img/captured.jpg"
        self.live_path = "static/img/live.jpg"
        self.is_streaming = False
        
    def capture_image(self):
        """Capture a still image using libcamera-still command line tool with enhanced quality"""
        try:
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(self.capture_path), exist_ok=True)
            
            # Make sure we're not streaming when we try to capture
            if self.is_streaming:
                # Adding a small delay to ensure any previous camera operations are fully complete
                time.sleep(0.5)
                
                # Kill any ongoing libcamera processes to ensure the camera is free
                try:
                    subprocess.run(["pkill", "-f", "libcamera"], stderr=subprocess.DEVNULL)
                    time.sleep(1)  # Wait for processes to terminate
                except:
                    pass
                
                self.is_streaming = False
            
            # Use libcamera-still command line tool with improved quality settings
            # width and --height for higher resolution
            # quality for better JPEG quality
            # sharpness for sharper images
            # shutter for faster shutter to reduce motion blur
            cmd = [
                "libcamera-still", 
                "-n", 
                "-o", self.capture_path, 
                "--immediate",
                "--width", "1280",      
                "--height", "960",       
                "--quality", "95",      
                "--sharpness", "1",    
                "--contrast", "1",      
                "--saturation", "1",     
                "--ev", "1",             
                "--awb", "auto",        
                "-t", "2000"         
            ]
            
            print(f"Running camera capture command: {' '.join(cmd)}")
            
            # Use timeout to prevent hanging
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"Image captured and saved to {self.capture_path}")
                return True, self.capture_path
            else:
                print(f"Error capturing image: {result.stderr}")
                
                # Try with a more direct command as fallback
                fallback_cmd = [
                    "libcamera-jpeg", 
                    "-o", self.capture_path, 
                    "--width", "1280",
                    "--height", "960",
                    "--quality", "95",
                    "--nopreview"
                ]
                print(f"Trying fallback command: {' '.join(fallback_cmd)}")
                fallback_result = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=10)
                
                if fallback_result.returncode == 0:
                    print(f"Image captured with fallback command and saved to {self.capture_path}")
                    return True, self.capture_path
                else:
                    print(f"Fallback capture also failed: {fallback_result.stderr}")
                    
                    # Create demo image as last resort
                    self._create_demo_image()
                    return True, self.capture_path
        except subprocess.TimeoutExpired:
            print("Camera command timed out")
            self._create_demo_image()
            return True, self.capture_path
        except Exception as e:
            print(f"Error capturing image: {e}")
            import traceback
            traceback.print_exc()
            
            # Create demo image as last resort
            self._create_demo_image()
            return True, self.capture_path
    
    def update_live_view(self):
        """Update the live view image with improved settings"""
        try:
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(self.live_path), exist_ok=True)
            
            # Create temp path with timestamp to avoid caching
            timestamp = int(time.time() * 1000)
            temp_path = f"static/img/temp_{timestamp}.jpg"
            
            # Use libcamera-still command with improved settings
            cmd = [
                "libcamera-still", 
                "-n", 
                "-o", temp_path, 
                "--immediate",
                "--width", "640",      
                "--height", "480",     
                "--quality", "85",   
                "--contrast", "1",    
                "--saturation", "1",  
                "--awb", "auto",       
                "--ev", "0.5",       
                "-t", "300"           
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            
            if result.returncode == 0:
                # Copy the temp file to the live path
                shutil.copy(temp_path, self.live_path)
                
                # Delete the temp file
                try:
                    os.remove(temp_path)
                except:
                    pass
                
                # Mark as streaming
                self.is_streaming = True
                
                # Add timestamp parameter for cache busting
                return True, f"{self.live_path}?t={timestamp}"
            else:
                print(f"Error updating live view: {result.stderr}")
                self.is_streaming = False
                return False, result.stderr
        except Exception as e:
            print(f"Error updating live view: {e}")
            self.is_streaming = False
            return False, str(e)
    
    def release_camera(self):
        """Release the camera resources by killing any libcamera processes"""
        try:
            # Kill any libcamera processes
            subprocess.run(["pkill", "-f", "libcamera"], stderr=subprocess.DEVNULL)
            self.is_streaming = False
            print("Camera resources released")
        except:
            pass
    
    def _create_demo_image(self):
        """Create a dummy image when camera capture fails"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (640, 480), color=(73, 109, 137))
            d = ImageDraw.Draw(img)
            d.text((10, 10), "Camera Capture Failed", fill=(255, 255, 0))
            d.text((10, 50), f"Time: {time.ctime()}", fill=(255, 255, 0))
            d.rectangle([(50, 100), (590, 380)], outline=(255, 255, 0))
            img.save(self.capture_path)
            print(f"Created demo image at {self.capture_path}")
        except Exception as e:
            print(f"Error creating demo image: {e}")
            # If even this fails, create an empty file
            with open(self.capture_path, 'wb') as f:
                f.write(b'')