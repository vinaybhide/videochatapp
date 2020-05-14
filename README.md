# videochatapp
Video and Text chat app
# Prerequisites
  - Python 3.8.2 for windows along with pip, venv, setuptools, wheel, virtualenv
  - Kivy for 3.8.2 (follow the kivy installation instructions)
  - Numpy
  - OpenCV
  - sounddevice
  - I also use python python image library (PIL). This is part of standard python installation
  - Good to have - Visual Code with python extension. This will allow you to debug in case of problem as I have not yet included any log
# Installation for Visual Code
  1. Go to https://code.visualstudio.com/
  2. Download for windows and follow instructions

# Installation Python
  1 https://www.python.org/
  1 Download windows version 3.8.2
  1 Verify python version
      py --version
# pip, venv
  1. pip, venv is part of the python installation
  2. wheel, setuptools are installed as part of pip installation
  3. venv is recommended for python 3. But if you want to install virtualenv
      py -m pip install --user virtualenv
  4. Ensure latest version of pip, venv, wheel, setuptools, virtualenv is installed
      python -m pip install --upgrade pip venv wheel setuptools virtualenv
  5. pip - it is installed as part of python 3 installation. If not installed
      Refer: https://pip.pypa.io/en/stable/installing/#do-i-need-to-install-pip 
      Download: https://bootstrap.pypa.io/get-pip.py
      Execute from command: python get-pip.py
      Follow the Installing with get-pip.py instructions.
      To install behind proxy - 
        python get-pip.py --proxy="http://[user:passwd@]proxy.server:port"
# Install Numpy
  1. To install 
  	pip install numpy
# Install kivy
  1. First install dependencies
      python -m pip install docutils pygments pypiwin32 kivy_deps.sdl2==0.1.* kivy_deps.glew==0.1.*
	    python -m pip install kivy_deps.gstreamer==0.1.*
      
      Note:	If you encounter a MemoryError while installing, add after pip install the –no-cache-dir option
      
      For Python 3.5+, you can also use the angle backend instead of glew. 
        This can be installed with: python -m pip install kivy_deps.angle==0.1.*
  
      Warning: When installing, pin kivy’s dependencies to the specific version that was released on pypi when your kivy version was released, like above. Otherwise you may get an incompatible dependency when it is updated in the future.
  
  2. To install kivy for python 3.8.2 (step 3 gave me errors while installing kivy 1.11.1 for python 3.8. I found following solution from   "https://github.com/kivy/kivy/issues/6563"
                                  
      pip install kivy[base] kivy_examples --pre --extra-index-url https://kivy.org/downloads/simple/
      
  3. Install latest released version 1.11.1
      python -m pip install kivy==1.11.1
  4. Optionally install examples for 1.11.1
      	python -m pip install kivy_examples==1.11.1
        The examples are installed in the share directory under the root directory where python is installed.
        
# To install OpenCV  ---- TO INSTALL UNOFFICIAL OpenCV-----
  1. Packages for standard desktop environments (Windows, macOS, almost any GNU/Linux distribution)
      run pip install opencv-python if you need only main modules
      
      run pip install opencv-contrib-python if you need both main and contrib modules (check extra modules listing from OpenCV documentation)
# To install sounddevice
  1. To install the latest release from PyPI, use:
	python3 -m pip install sounddevice --user
	
	If you want to install it system-wide for all users (assuming you have the necessary rights), you can just drop the --user 	option. If you have installed the module already, you can use the --upgrade flag to get the newest release.
  2. To un-install, use:
	python3 -m pip uninstall sounddevice
  3. If you install the sounddevice module with pip on macOS or Windows, the PortAudio library (with ASIO support on Windows) will be installed automagically. On other platforms, you might have to install PortAudio with your package manager (the package might be called libportaudio2 or similar).

  4. You might also have to install CFFI (from a package called python3-cffi or similar). This is installed as part of python 3

  5. NumPy is only needed if you want to play back and record NumPy arrays. 
  	The classes sounddevice.RawStream, sounddevice.RawInputStream and sounddevice.RawOutputStream use plain Python buffer objects and don’t need NumPy at all. 
	If you need NumPy, you should install it with your package manager (from a package named python3-numpy or similar) or use a Python distribution that already includes NumPy (see above).
	You can also install NumPy with pip, but depending on your platform, this might require a compiler and several additional libraries.
