# Blender Addon: Control Render Region

![ScreenshotRenderRegion_20230319_16-35](https://user-images.githubusercontent.com/8025606/226186936-127534d7-b0cb-4480-8894-a08a85448027.png)

A Blender Addon to manage renders with [Render Region](https://docs.blender.org/manual/en/latest/editors/3dview/navigate/regions.html#render-region). 
This addon divides the render of a project into regions and allows you to render all or only some of them.

Useful in several cases, for example:
- Probability or need to interrupt very long renderings (computer availability problems, risk of power outages).
- Divide the render of the same image among multiple computers, assigning each computer different regions.
- Handle complex scenes / heavy renders.
- Render very large images.

The regions are rendered top to bottom left to right, so the first one will be the top left and the last one will be the bottom right.

![divisioneRegioni](https://user-images.githubusercontent.com/8025606/221556263-5f167ce8-4864-4b61-a575-e4c86a7b89ac.png)

You can add margins to regions to have overlapping areas: this way you can avoid problems due to denoise in cycles or effects in the compositor, for example "glare", when merging regions.

Tested with Cycles and Eevee with Blender 3.4.0 and 4.2.0, in Ubuntu 24.04 and Windows 10.

To merge all images from script (created by this addon) [imagemagick](https://imagemagick.org/script/download.php) and [python 3](https://www.python.org/downloads/) must be installed.

Blender version: 3.4 - 4.2.0.

## Installation
- copy `control_render_regions.py` in the blender scripts/addons folder on your system (linux: ~/.config/blender/2.81/scripts/addons/)
- in blender go to `Edit > Preferences > Add-ons`, and enable "Render: Control Render Region"

## Use
- in Properties > Output Properties tab > Render Region panel, set the desired render mode and click on "Render Region"


## How the addon works
There are two methods: Divide and Multiply

### Divide
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
  - 6 images will be rendered and saved, in the output path, each 960x360 pixel (1920/2 and 1080/3).
  - Their name indicates the region, counting from 0, left to right, top to bottom:
    - testRR_2x3_0_0.png it is the first region of the first row, the the upper left region, the first;
    - testRR_2x3_0_1.png first row, second region;
    - testRR_2x3_1_0.png second row, first region;
    - ...
    - testRR_2x3_2_1.png: third row, second region, the bottom right region, the last.
  - By merging the rendered images, you get the final image, 1920x1080.
  - If a non-multiple number is indicated in "Columns" or "Rows" which would produce a dimension with decimals, the dimension of the various regions could be different due to rounding: in this case a message is displayed under the render buttons and in terminal.

### Multiply
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

### Margins
This addon can be used with both Cycles and Eevee, but with Cycles there are problems using "Denoise" (Tab Render Properties > Sampling panel > Render - Denoise check): the "denoise" produces artifacts along the edges of the image, usually only for single pixels along the edges: by merging the images these artifacts will be clearly visible as they are all close and aligned.
Other possible problems during merging can be given by effects in compositor, such as the "glare" which adds a halo around the brightest pixels: if these pixels are located near the edge of the region the effect will add the halo which may be larger than the edge distance and therefore be cut off. Combining the images you will see the halo cut out.

To fix this problem, the regions need to be enlarged by adding a margin which will then be cropped before merging the images.

Since the regions are calculated in a relative way and not in pixels, it is difficult to find a value for the margin compatible with the render size, because you have to avoid rounding problems that would affect the render size.

The button "Calculate Margins" finds the largest margin, starting from the value in "Max Margin" going backwards, which generates values with fewer decimals, safer.

The first best values found are written in the "w" and "h" fields. Any other values are reported in the terminal.

If no safe values are found, 0 is returned. In this case you need to change the rendering size, or the number of regions, or increase the "Max Margin" value.

You can choose the value of the margins without calculating it with the "Calculate margins" button, but rounding errors will be possible.

### Bash and Python script
Selecting "Create bash and python script" the "render region" button will not launch the renders, but will write a script (.sh bash script in Linux and MacOS, .bat batch script in Windows), and a python script in the output folder.

The bash script launches renders of the selected regions.
In the script there are commands for all rendering; the regions not to be rendered are commented out.
At the end of the script is the command to run the python script; is commented. To launch the images cropping/appending procedure after rendering, uncomment the line with the command "python _name of blender project_.py".
  In .bat it will be: "::python xxxx.py" and in .sh: "#python xxxx.py"; in both cases it must become: "python xxxx.py"

The python script crops and merges all regions to get the final image.

### Create Reference Image
The "Create Reference Image" button generates a reference image (using imagemagick); region borders are drawn with red lines, and margins (or overlapping areas) with semi-transparent areas. All regions are numbered.
![ScreenshotRR_refImg_20230319_16-45](https://user-images.githubusercontent.com/8025606/226187571-7f40a382-6988-4f9f-b767-d7f149ee9429.png)

### Values
- **Method**: Divide or Multiply: the method used for create region
- **Columns**: Only for method "Divide", number of columns, how much the width of the image is divided
- **Rows**: Only for method "Divide", number of rows, how much the height of the image is divided
- **Multiplier**: Only for method "Multiply", multiplier for render dimension, or number of tiles
- **Regions to render**: which regions to render, possible values:
  - 'all': render all the regions;
  - n (number): only render the n region (counting by row, from 0, top to bottom, left to right);
  - n,x,y,z: only the region n, x, y and z;
  - n-z: render region from n to z
- **Add Margins to regions**: add margins to render dimension, only to the inner edges of regions
- **W**: value, in pixels, for the margin to add to the width of the region
- **H**: value, in pixels, for the margin to add to the height of the region
- **Max margin**: value from which the margin calculation starts, going backwards
- **Calculate margins**: starts the margin calculation; if acceptable values are found, the best ones are written in the "W" and "H" fields, and are all displayed in the terminal
- **Create bash and python script**: create, in output location, a bash or batch script (.sh for Linux and MacOS, .bat for Windows) for launch the render process from command line, and create a python script with the procedure for create the final image using imagemagick (convert -crop and convert -+append)
- **Render region**: render the regions indicated in "Regions to render" and save it in the output folder (Output properties > Output > Output path).
If Compositor is activated and there are "File output"nodes, the file name will be changed according to the name assigned to the region.

## License

Control Render Region is distributed under the terms of the GNU General Public License, version 3
