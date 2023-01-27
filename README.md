# Blender Addon: Control Render Region

Addon to divide the render of a project into regions, rendering all regions or only some.
Useful in several cases, for example:
Probability or need to interrupt very long renderings (computer availability problems, risk of power outages).
Divide the render of the same image among multiple computers, assigning each computer different regions.
Handle complex scenes / heavy renders.
Render very large images.

Blender version: 3.4.

## Installation
- copy `control_render_regions.py` in the blender scripts/addons folder on your system (linux: ~/.config/blender/2.81/scripts/addons/)
- in blender go to `Edit > Preferences > Add-ons`, and enable "Render: Control Render Region"

## Use
- in Properties > Output Properties tab > Render Region panel, set the desired render mode and click on "Render Region"


## How the addon works
there are two methods: Divide and Multiply

###### Divide
The render is divided into regions according to the values indicated in the "Columns" and "Rows" fields.
"Columns" indicates how many parts the width of the render is divided into, while "Rows" indicates the division of the height.
The "regions to render" field indicate the regions to render.
For example:
- render set to 1920 x 1080 resolution (Format panel)
- output as PNG , with path //render/testRR_ (Output panel)
- in Render Region:
-- Method: Divide
-- "Columns": 2 and "Rows": 3
-- regions to render: all
- click on the "Render Region" button:
  - 6 images will be rendered and saved, in the indicated path, each 960x360 pixel (1920/2 and 1080/3).
  - Their name indicates the region, counting from 0, left to right, top to bottom:
    - testRR_2x3_0_0.png it is the first region of the first row, the the upper left region, the first;
    - testRR_2x3_0_1.png first row, second region;
    - testRR_2x3_1_0.png second row, first region;
    - ...
    - testRR_2x3_2_1.png: third row, second region, the bottom right region, the last.
  - By merging the rendered images, you get the final image, 1920x1080.
  - If a non-multiple number is indicated in "Columns" or "Rows" which would produce a dimension with decimals, the dimension of the various regions could be different due to rounding: in this case a message is displayed under the render buttons.

###### Multiply
The resolution, X and Y, is multiplied by the value indicated in "multipler" and the render is divided into regions, all with the original resolution
Example:
- render set to 1920 x 1080 resolution (Format panel)
- output as PNG , with path //render/testRR_ (Output panel)
- in Render Region:
  - Method: Multiply
  - "Multiplier": 2
  - regions to render: all
  - click on the "Render Region" button:
    - 4 images (2x2) will be rendered and saved, in the output path, each 1920x1080;
    - in their name the relative region is indicated, counting from 0, from left to right, from top to bottom:
      - testRR_2x2_0_0.png this is the first region of the first row, so the top left, the first;
      - testRR_2x2_0_1.png first row, second region;
      - testRR_2x2_1_0.png second row, first region;
      - testRR_2x2_1_1.png second row, second region, bottom right, last.
    - By merging the rendered images, you get the final image, 3840x2160.

###### Problems
This addon can be used with both Cycles and Eevee, but with Cycles there are problems using "Denoise" (Tab Render Properties > Sampling panel > Render - Denoise check):
The "denoise" produces artifacts along the edges of the image, usually only for single pixels along the edges: by merging the images these artifacts will be clearly visible as they are all close and aligned. To solve this problem, the regions must be enlarged by adding margin which will then be cut before merging the images: this is in progress...


### Values
- **Method**: Divide or Multiply: the method used for create region
- **Columns**: Only for method "Divide", number of columns, how much the width of the image is divided
- **Rows**: Only for method "Divide", number of rows, how much the height of the image is divided
- **Multiplier**: Only for method "Multiply", multiplier for render dimension, or number of tiles
- **Regions to render**: 'all': render all the regions; n (number): only render the n region (counting by row, from 0, top to bottom, left to right); n,x,y,z: only the region n, x, y and z; n-z: render region from n to z
- **Create bash script**: >>Experimental - Linux only<< create, in output location, a bash script for launch the render process from command line; if "regions to render" is "all" the script add the procedure for create the final image using imagemagick (convert append); problem with "File Output" node in compositor: save with same name all regions, need add control like in internal mode, in progress...

## License

Control Render Region is distributed under the terms of the GNU General Public License, version 3
