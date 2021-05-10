# Damage Utilities
Damage Utilities is a set of python scripts and examples for you to use in creating synthetic data with Blender. Setting up and making your dataset is as simple as a few clicks.

**Utility Scripts**
`damageutils.py` and `imageutils.py` are the actual 'library' portion of Damage Utilities. The functions contained range from data manipulation and exporting, to creating basic objects. Due to the semi-encapsulation of the Blender python environment, importing an outside script requires an extra chunk of code:
```python
import sys, os, importlib
if 'damageutils' in sys.modules: importlib.reload(sys.modules['damageutils'])
extra_path = os.environ["BLENDER_UTILITIES"]
if extra_path not in sys.path: sys.path.append(extra_path)
import damageutils
```

`imageutils.py` is meant to run outside of Blender, once the data has been generated. Currently, it only has one script, which depends on [Pillow](https://pypi.org/project/Pillow/). It writes a set of X, Y points to an image. This is the 'label' image critical for Machine Learning applications.

**Example Scripts**
Included in the repository are a few example scripts for your use and adaptation. Learning to use these requiers a little bit of Blender knowledge. The simplest provided script is `crack_wall.py`. Like the other examples, the script is just a for loop that constructs a scene and renders it however many times is wanted. The Damage Utilities libraries are used to set the resolution, random seed, and create a plane. The only part custom to the implementation is the `create()` function. This function creates a `BMesh` (an object that allows better and safer vertex manipulation) and applies the `voronoi_crack()` function from Damage Utilities to it. Then, it applies a material, adds a camera and light, and finally makes a projection (creating a CSV for use in `imageutils.py`)

The workflow would then move to the image example, `generate_mask.py`. Here, the mask writing function is called however many times is necessary.

**Workflow**
Generating data from an example script is quite easy to do.
1. Install Blender. These scripts are built off of Blender 2.9+ and have not been tested with earlier versions, though they'll probably still work.
2. (Optional but highly recommended) Install Visual Studio Code and [Blender VSC](https://github.com/JacquesLucke/blender_vscode). Press Ctrl+Shift+P to launch the Blender executable. While the scripts work fine on their own, Developing just using Blender's internal IDE is a nightmare. This also helps with the example scripts, which work off the assumption that you are launching Blender from the same working directory as your scripts.
3. Hit 'open' and select the `sandbox.blend` file. This file is completely blank save for a few internal materials for scripts to refer to.
4. Hit 'open' again, this time on the Scripting tab, and pick the example script you want. Then, just hit run! The example scripts look for folders with specific names one directory level above the working folder, so as to not mess with version control, but you can edit to suit your needs.
4. In VSC (or Notepad if you're feeling brave), open up a post-processing example like `generate_mask.py`. Populate the global variables with the correct information, and then run the script. Your dataset is done!