# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


#bl_info = {
#	'name': 'Control Render Regions',
#	'author': 'nukkio',
#	'version': (1.0.9),
#	'blender': (3, 0, 0),
#	'location': 'Render > Render Regions',
#	'description': 'Manage renders in region',
#	'wiki_url': '',
#	'tracker_url': '',
#	'category': 'Render'}


import bpy
import os,subprocess
from subprocess import run
import math
import platform
from bpy.types import (
						Panel, 
						Operator, 
						Scene, 
						PropertyGroup, 
						WindowManager, 
						AddonPreferences
					)
from bpy.props import (
						BoolProperty,
						IntProperty,
						FloatProperty,
						StringProperty,
						EnumProperty,
						PointerProperty,
						CollectionProperty,
					)
from bpy.app.handlers import render_pre, render_post, render_cancel
from bpy.app import driver_namespace

#oiioOK=False
#try:
#	import OpenImageIO as oiio
#	oiioOK=True
#except ImportError:
#	oiioOK=False

pilOK=False
try:
	from PIL import Image, ImageDraw, ImageFont
#	print("PIL ok")
	pilOK=True
except ImportError:
#	print("PIL ko")
	pilOK=False

#>>> import os
#>>> os.name
#'posix'
#'nt'
#'posix'
#>>> import platform
#>>> platform.system()
#'Linux'
#'Windows'
#'Darwin'
#>>> platform.release()
#'2.6.22-15-generic'

#handler_key = "DEV_FUNC_HKRR"

class RenderRegionSettings(PropertyGroup):

	def method_update(self,context):
#		print("method_update")
#		print(str(self.RR_method))
		if self.RR_method=="DIVIDE":
			self.RR_rowscols=True
			self.RR_dim_region=False
		else:
			self.RR_rowscols=False
			self.RR_dim_region=True
	
	def checkColsRows(self,context):
#		print("checkColsRows")
		delta_x=0
		delta_y=0
		resx=context.scene.render.resolution_x
		resy=context.scene.render.resolution_y
		if self.RR_dim_region==False:
			delta_x = 1/self.RR_reg_columns
			delta_y = 1/self.RR_reg_rows
			count_decimal_x = str(delta_x)[::-1].find('.')
			count_decimal_y = str(delta_y)[::-1].find('.')
			msgerr=""
			if(count_decimal_x>7):
				print("RenderRegion - cols warning: "+str(count_decimal_x))
				delta_x2=resx/self.RR_reg_columns
				count_decimal_x2 = str(delta_x2)[::-1].find('.')
#				print(str(resx)+"/"+str(self.RR_reg_columns)+"="+str(delta_x2)+" -> "+str(count_decimal_x2))
				if(count_decimal_x2>5):
					msgerr="The value for Columns"
					print("RenderRegion - value for Columns can generate rounding error")
				else:
					msgerr=""
				
			if(count_decimal_y>7):
				print("RenderRegion - rows warning: "+str(count_decimal_y))
				delta_y2=resy/self.RR_reg_rows
				count_decimal_y2 = str(delta_y2)[::-1].find('.')
				if(count_decimal_y2>5):
					if(msgerr!=""):
						msgerr=msgerr+" and for rows"
					else:
						msgerr=msgerr+"The value for Rows"
					print("RenderRegion - value for Rows can generate rounding error")
				else:
					if(msgerr==""):
						msgerr=""
					
			if(msgerr!=""):
				msgerr=msgerr+" can lead to rounding errors in regions dimension"
				print("RenderRegion addon - "+msgerr+" - change value")
			self.RR_msg1=msgerr
			
	#all properties for the gui in the panel
	is_enabled: BoolProperty(
		name="isEnabled",
		default=True,
		description="descrizione 1 "
		)
	unit_from: EnumProperty(
		name="Set from",
		description="Set from",
		items=(
			("CM_TO_PIXELS", "CM -> Pixel", "Centimeters to Pixels"),
			("PIXELS_TO_CM", "Pixel -> CM", "Pixels to Centermeters")
			),
		default="CM_TO_PIXELS",
		)
	
	
	RR_method: EnumProperty(
		name="Method",
		description="Render region method",
		items=(
			("DIVIDE", "Divide","Divide actual resolution in rows and columns"),
			("MULTIPLY","Multiply","Multiply actual resolution by a multiplier, and render each regions using actual resolution")
		),
		default="DIVIDE",
		update=method_update,
		)

	RR_rowscols:BoolProperty(
		name = "Use rows and columns",
		description = "Divide render resolution into rows and columns",
		default = True)
#		update=rowcol_update)
	
	RR_reg_rows:IntProperty(
		name = "Rows",
		description = "Set number of rows",
		default = 2,
		min = 1,
		max = 1000,
		update=checkColsRows
		)

	RR_reg_columns:IntProperty(
		name = "Columns",
		description = "Set number of columns",
		default = 2,
		min = 1,
		max = 1000,
		update=checkColsRows
		)


	RR_dim_region:BoolProperty(
		name = "Use render dimension",
		description = "Multiply resolution by a multiplier, and render regions using actual dimension",
		default = False)
#		update=multip_update)

	RR_multiplier:IntProperty(
		name = "Multiplier",
		description = "Set number of tiles",
		default = 2,
		min = 1,
		max = 100)

	RR_who_region:StringProperty(
		name = "Regions to render",
		description = "Regions to render: all= render all regions; x,y,z= render the region number x, y and z; x-z= render the region from number x to z",
		default = "all")

#	RR_save_region:BoolProperty(
#		name = "Join and save",
#		description = "Join and save the regions",
#		default = False)
	
	RR_activeRendername:StringProperty(
		name = "RR_activeRendername",
		description = "The name of the active rendered image",
		default = "")
	
	RR_msg1:StringProperty(
		name = "RR_msg1",
		description = "msg1",
		default = "")
#	RR_msg2:StringProperty(
#		name = "RR_msg2",
#		description = "msg2",
#		default = "")
		
	RR_oldoutputfilepath:StringProperty(
		name = "RR_oldoutputfilepath",
		description = "RR_oldoutputfilepath",
		default = "")
		
	RR_oldPerc:IntProperty(
		name = "RR_oldPerc",
		description = "RR_oldPerc",
		default = 100,
		min = 1,
		max = 1000)
	
	RR_outputImgName:StringProperty(
		name = "RR_outputImgName",
		description = "RR_outputImgName",
		default = "")
	
	RR_renderGo: BoolProperty(
		name="RR_renderGo",
		default=False,
		description="RR_renderGo",
		)
		
	RR_cntrnd:IntProperty(
		name = "RR_cntrnd",
		description = "RR_cntrnd",
		default = 0,
		min = 0,
		max = 10000)
		
	RR_maxrnd:IntProperty(
		name = "maxrnd",
		description = "maxrnd",
		default = 0,
		min = 0,
		max = 10000)
		
	RR_createScript: BoolProperty(
#		name="Create bash and python script",
		name="Create scripts for render, save and join images",
		default=True,
		description="Create script for render from command line and python script for join regions rendered",
		)
	
	RR_useMargins: BoolProperty(
		name="Add margins to regions",
		default=False,
		description="Add margins to regions, only within the image",
		)
	
	RR_mrg_w:IntProperty(
		name = "W",
		description = "pixels to add to the width of the regions",
		default = 0,
		min = 0,
		max = 1000
		)

	RR_mrg_h:IntProperty(
		name = "H",
		description = "pixels to add to the height of the regions",
		default = 0,
		min = 0,
		max = 1000
		)
	
	RR_mrgmax:IntProperty(
		name = "Max margin",
		description = "Max margin",
		default = 100,
		min = 0,
		max = 1000
		)
	
class RENDER_PT_Region(Panel):
	bl_label = "Render Region"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "output"
	
	def draw(self, context):
		layout = self.layout
		scn = context.scene
		ps = scn.renderregionsettings
		
		rowList=[]
		box = layout.box()
		row1 = box.row()
		rowList.append(row1)
		row2 =  box.row()
		rowList.append(row2)
		row3 =  box.row()
		rowList.append(row3)
		row4 =  box.row()
		rowList.append(row4)
		
		box = layout.box()
		row5 =  box.row()
		rowList.append(row5)
		row6 =  box.row()
		rowList.append(row6)
		row7 =  box.row()
		rowList.append(row7)
#		layout.row().separator()		

		box = layout.box()
		
		row8 =  box.row()
		rowList.append(row8)
		row9 =  box.row()
		rowList.append(row9)
		row10 =  box.row()
		rowList.append(row10)
		row11 =  box.row()
		rowList.append(row11)
		row12 =  box.row()
		rowList.append(row12)
		row13 =  box.row()
		rowList.append(row13)
		row14 =  box.row()
		rowList.append(row14)

		col = layout.column(align=True)
		
		rn=0
		rowList[rn].prop(ps, "RR_method")
		rn+=1

		rowList[rn].label(text="Use rows and columns")
		rowList[rn].active = ps.RR_rowscols
		rowList[rn].enabled = ps.RR_rowscols
		sub = rowList[rn].row()
		sub.active = ps.RR_rowscols
		sub.enabled = ps.RR_rowscols
		sub.prop(ps, "RR_reg_columns")
		sub.prop(ps, "RR_reg_rows")
		rn+=1

		rowList[rn].label(text="Use render dimension")
		rowList[rn].active = ps.RR_dim_region
		rowList[rn].enabled = ps.RR_dim_region
		sub = rowList[rn].row()
		sub.active = ps.RR_dim_region
		sub.enabled = ps.RR_dim_region
		sub.prop(ps, "RR_multiplier")
		
		rn+=1
		rowList[rn].prop(ps, "RR_who_region")
		
		####parte margini
		rn+=1
		rowList[rn].prop(ps, "RR_useMargins")
		rn+=1
		rowList[rn].label(text="Margin (px)")
		rowList[rn].active = ps.RR_useMargins
		rowList[rn].enabled = ps.RR_useMargins
		sub = rowList[rn].row()
		sub.active = ps.RR_useMargins
		sub.enabled = ps.RR_useMargins
		sub.prop(ps, "RR_mrg_w")
		sub.prop(ps, "RR_mrg_h")
		
		rn+=1
		rowList[rn].prop(ps, "RR_mrgmax")
		rowList[rn].operator("margin.calculate", text="Calculate margins", icon='MOD_MULTIRES')
		rowList[rn].enabled = ps.RR_useMargins==True
		rowList[rn].active = ps.RR_useMargins==True
		####

		rn+=1
		rowList[rn].prop(ps, "RR_createScript")
		label_btnRender="Render Region"
		if (ps.RR_createScript==True):
			label_btnRender="Create script"

		rn+=1
		rowList[rn].operator("render.regions", text=label_btnRender, icon="RENDER_STILL")
		rowList[rn].enabled = ps.RR_renderGo==False
		rn+=1
		rowList[rn].operator("render.stop", text="Stop render", icon="CANCEL")
		rowList[rn].enabled = ps.RR_renderGo==True
		rn+=1
		rowList[rn].operator("reference.create", text="Create reference image", icon="IMAGE_PLANE")
		rn+=1
		rowList[rn].label(text=ps.RR_msg1)
		rn+=1
#		rowList[rn].label(text=ps.RR_msg2)
#		rn+=1
		
		

class testVar(Operator):
	bl_idname = 'rr.test'
	bl_label = "test"
	bl_description = "test var"
	bl_options = {'REGISTER', 'UNDO'}
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "output"
	
	def execute(self, context):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
		ar=AreaRegion()
		ar.minx=44
		ar2 = {"x1":1,"x2":2,"y1":3,"y2":4}
		ar2['x1']=33
		return {'FINISHED'}

class RenderObject:
	def __init__(self, regionarea=0, imageName="", resolution=0, resolutionPercent=0, usecrop=False,currframe=0,render=False):
		self.regionarea=regionarea
		self.imageName=imageName
		self.resolution=resolution
		self.resolutionPercent=resolutionPercent
		self.usecrop=usecrop
		self.currframe=currframe
		self.render=render
	def getObject(self):
		tmpOb={
			"regionarea":self.regionarea,
			"imageName":self.imageName,
			"resolution":self.resolution,
			"resolutionPercent":self.resolutionPercent,
			"usecrop":self.usecrop,
			"currframe":self.currframe,
			"render":self.render
		}
		return tmpOb
	
class AreaRegion:
	def __init__(self, minx=0,miny=0,maxx=0,maxy=0):
		self.minx = minx
		self.miny = miny
		self.maxx = maxx
		self.maxy = maxy
	def getObject(self):
		tmpOb={
			"minx":self.minx,
			"miny":self.miy,
			"maxx":self.maxx,
			"maxy":self.maxy
		}
		return tmpOb

class RenderStop(Operator):
	bl_idname = 'render.stop'
	bl_label = "Render stop"
	bl_description = "Stop render regions"
	bl_options = {'REGISTER', 'UNDO'}
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "output"
	
	def execute(self, context):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
		ps.RR_renderGo=False;
#		self.remove_handlers(context)
		print("----------------------STOPPED - CANCELLED")
		return{'CANCELLED'}

class CreateReferenceImage(Operator):
	bl_idname = 'reference.create'
	bl_label = "Create reference image"
	bl_description = "Create a reference image with all regions numbered and margins"
	bl_options = {'REGISTER', 'UNDO'}
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "output"
	
	def execute(self, context):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings

		resx=rnd.resolution_x
		resy=rnd.resolution_y
		
		nregionsw=0
		nregionsh=0
		if ps.RR_method=="DIVIDE":
			nregionsw=ps.RR_reg_rows
			nregionsh=ps.RR_reg_columns
		else:
			nregionsw=ps.RR_multiplier
			nregionsh=ps.RR_multiplier
			resx=rnd.resolution_x*ps.RR_multiplier
			resy=rnd.resolution_y*ps.RR_multiplier
#		print("resx",str(resx))
#		print("resy",str(resy))
#		print("nregionsw",str(nregionsw))
#		print("nregionsh",str(nregionsh))
#		print("ps.RR_mrg_w",str(ps.RR_mrg_w))
#		print("ps.RR_mrg_h",str(ps.RR_mrg_h))

		scaleres=1
		maxresRefImg=2048
		if (resx>maxresRefImg or resy>maxresRefImg):
			maxres=max(resx, resy)
			scaleres=round((maxresRefImg/maxres),4)
			resx=round(resx*scaleres)
			resy=round(resy*scaleres)
#		print("maxres",str(maxres))
#		print("scaleres",str(scaleres))
#		print("resy",str(resy))
#		print("resy",str(resy))
		
#		mainPath=bpy.path.abspath("//")
#		self.outputFolderAbs + os.path.sep + self.region_name

		mrg_w=ps.RR_mrg_w*scaleres
		mrg_h=ps.RR_mrg_h*scaleres
		if ps.RR_useMargins==False:
			mrg_w=0
			mrg_h=0
		
		imagePath=self.drawRef(resx,resy,nregionsw,nregionsh,mrg_w,mrg_h,bpy.path.abspath("//"))
		if imagePath=="":
			print("problem in creation image, check imagemagick installation.")
			return{"FINISHED"}
		cam = bpy.context.scene.camera

		for bgi in cam.data.background_images:
#			print(bgi.image.name)
			if bgi.image and bgi.image.name.startswith("rrref"):
				img=bpy.data.images[bgi.image.name]
				cam.data.background_images.remove(bgi)
				img.user_clear()
				if not img.users: 
				    bpy.data.images.remove(img)
		cam.data.background_images.update()

		#cam = bpy.data.scenes["Scene"].camera
		img = bpy.data.images.load(imagePath)
		cam.data.show_background_images = True
		bg = cam.data.background_images.new()
		bg.image = img
		cam.data.background_images[0].display_depth='FRONT'
		cam.data.background_images.update()
		
		return{"FINISHED"}
	
	def drawRef(self,ww,hh,rows, cols, mrgw=0, mrgh=0,path="//"):
		name=path+"rrref_"+str(ww)+"x"+str(hh)+"-"+str(rows)+"x"+str(cols)+".png"
		
#		PIL installed by extension, use PIL
		if(pilOK==True):
			print("create reference image using PIL")
			strokeColor=("#ff0000")
			strokeColorMarg=("#ff000020")
			strokeWidth=4
			#inizializza immagine
			buffertmp = Image.new("RGBA", (ww,hh), (0, 0, 0, 0))
			
			drawCmnd=""
			dh=round(hh/rows)
			dw=round(ww/cols)
			tmp=0
			startX=0
			startY=0
			# create lines image
			imgLines = ImageDraw.Draw(buffertmp)
			for n in range(rows-1):
				startY+=dh
				imgLines.line([( startX, int(startY-(strokeWidth/2))),(ww, int(startY+(strokeWidth/2)))], fill=strokeColor, width=strokeWidth) 
				if(mrgh!=0):
#					print("m")
					imgLines.rectangle([(startX, int(startY-(mrgh))),(ww, int(startY+(mrgh)))], fill=strokeColorMarg, outline=None, width=1)
			startX=0
			startY=0
			for n in range(cols-1):
				startX+=dw
				imgLines.line([( int(startX-(strokeWidth/2)), startY), ( int(startX+(strokeWidth/2)), hh)], fill=strokeColor, width=strokeWidth) 
				if(mrgw!=0):
#					print("m")
					imgLines.rectangle([(int(startX-(mrgw)), startY), (int(startX+(mrgw)), hh)], fill=strokeColorMarg, outline=None, width=1)
			#region number
			dh3=round(dh/3)
			dw3=round(dw/3)
			tmph=dh3*2
			tmpw=dw3
			cnt=0
			textSize=(min(dh3,dw3))
			fontNumber = ImageFont.load_default(size=textSize)
			for nr in range(rows):
				tmpw=dw3
				for nc in range(cols):
					imgLines.text((tmpw, tmph), str(cnt), fill=strokeColor, font=fontNumber, anchor="mm")
					cnt=cnt+1
					tmpw+=dw
				tmph+=dh

			#region name
			dh4=round(dh/6)
			dw4=0#round(dw/6)
			tmph4=dh4*1
			textSize=(dh4)
			fontNumber = ImageFont.load_default(size=textSize)
			cntRows=0
			cntCols=0
			strRC=""
			for nr in range(rows):
				tmpw=dw4
				for nc in range(cols):
					strRC=str(cntRows)+"-"+str(cntCols)
					imgLines.text((tmpw, tmph4), strRC, fill=strokeColor, font=fontNumber, anchor="lm")
					cnt=cnt+1
					tmpw+=dw
					cntCols+=1
				tmph4+=dh
				cntRows+=1
				cntCols=0
			buffertmp.save(name)
			
#		elif(oiioOK==True):
#			print("use OpenImageIO for reference image")
#			#################################
#			#################################
#			##using openimageio##############
#			#################################
#			print("create reference image using OpenImageIO")
#			strokeColor=(1, 0, 0, 1)
#			strokeColorMarg=(1, 0, 0, 0.3)
#			strokeWidth=4
#			#inizializza immagine
#			buffertmp = oiio.ImageBuf(oiio.ImageSpec(ww, hh, 4, "float"))
#			
#			drawCmnd=""
#			dh=round(hh/rows)
#			dw=round(ww/cols)
#			tmp=0
#			startX=0
#			startY=0
#			for n in range(rows-1):
#				startY+=dh
#				oiio.ImageBufAlgo.render_box(buffertmp, startX, int(startY-(strokeWidth/2)), ww, int(startY+(strokeWidth/2)), strokeColor, True)
#				if(mrgh!=0):
#					oiio.ImageBufAlgo.render_box(buffertmp, startX, int(startY-(mrgh)), ww, int(startY+(mrgh)), strokeColorMarg, True)
#			startX=0
#			startY=0
#			for n in range(cols-1):
#				startX+=dw
#				oiio.ImageBufAlgo.render_box(buffertmp, int(startX-(strokeWidth/2)), startY, int(startX+(strokeWidth/2)), hh, strokeColor, True)
#				if(mrgw!=0):
#					oiio.ImageBufAlgo.render_box(buffertmp, int(startX-(mrgw)), startY, int(startX+(mrgw)), hh, strokeColorMarg, True)
#			
#			#region number
#			dh3=round(dh/3)
#			dw3=round(dw/3)
#			tmph=dh3*2
#			tmpw=dw3
#			cnt=0
#			textSize=(min(dh3,dw3))
#			texterror=""
#			for nr in range(rows):
#				tmpw=dw3
#				for nc in range(cols):
#					if not oiio.ImageBufAlgo.render_text(buffertmp, tmpw, tmph, "**"+str(cnt), textSize, "", strokeColor, alignx="center", aligny="center"):
#						er="ControlRender Region-oiio error: " + buffertmp.geterror()
#						print(er)
#						texterror=er
#					cnt=cnt+1
#					tmpw+=dw
#				tmph+=dh

#			#region name
#			dh4=round(dh/6)
#			dw4=0#round(dw/6)
#			tmph4=dh4*1
#			textSize=(dh4)
#			cntRows=0
#			cntCols=0
#			strRC=""
#			for nr in range(rows):
#				tmpw=dw4
#				for nc in range(cols):
#					strRC=str(cntRows)+"-"+str(cntCols)
#					if not oiio.ImageBufAlgo.render_text(buffertmp, tmpw, tmph4, strRC, textSize, "Arial", (0,0,0,1), alignx="center", aligny="center"):
#						er="ControlRender Region-oiio error: " + buffertmp.geterror()
#						print(er)
#						texterror=er
#					cnt=cnt+1
#					tmpw+=dw
#					cntCols+=1
#				tmph4+=dh
#				cntRows+=1
#				cntCols=0
#			if(texterror!=""):
#				self.report({'ERROR'},texterror+", image reference without region number")
#			buffertmp.write(name)
#			#################################
#			##using openimageio end##########
#			#################################
		else:
			print("use ImageMagick for reference image")
			#################################
			#################################
			##using imagemagick##############
			#################################
			#check imagemagick
			#version 7.1
			cmd="magick --version"
			newmagick=0
			data = run(cmd, capture_output=True, shell=True)
			output = data.stdout.splitlines()
			errors = data.stderr.splitlines()
			
			if (len(errors)>0) or (len(output)<1):
				print("no imagemagick new (7)")
				newmagick=0
				
				cmd="convert --version"
				data = run(cmd, capture_output=True, shell=True)
				output = data.stdout.splitlines()
				errors = data.stderr.splitlines()
				if (len(errors)>0) or (len(output)<1):
					newmagick=-1
					print("no imagemagick")
				else:
					newmagick=0

			else:
				newmagick=1
#			print("newmagick",str(newmagick))
			if newmagick==-1:
				self.report({'ERROR'},"Imagemagick not found, no image created")
				return ""
				
			print("create reference image using Imagemagick")
			drawCmnd=""
			dh=round(hh/rows)
			dw=round(ww/cols)
			tmp=0
			strokeSetLine=" -stroke red -strokewidth 4"
			strokeSetMarg=" -stroke \"#ff000040\" -strokewidth "
			for n in range(rows-1):
				tmp+=dh
				drawCmnd=drawCmnd+strokeSetLine+" -draw \"path 'M 0,"+str(tmp)+" l "+str(ww)+",0'\""
				if(mrgh!=0):
					drawCmnd=drawCmnd+strokeSetMarg+str(mrgh*2)+" -draw \"path 'M 0,"+str(tmp)+" l "+str(ww)+",0'\""
			tmp=0
			for n in range(cols-1):
				tmp+=dw
				drawCmnd+=strokeSetLine+" -draw \"path 'M "+str(tmp)+",0 l 0,"+str(hh)+"'\""
				if(mrgw!=0):
					drawCmnd+=strokeSetMarg+str(mrgw*2)+" -draw \"path 'M "+str(tmp)+",0 l 0,"+str(hh)+"'\""
			
			#region number
			dh3=round(dh/3)
			dw3=round(dw/3)
			tmph=dh3*2
			tmpw=dw3
			cnt=0
			drawCmnd+=" -pointsize "+str(min(dh3,dw3))+" -fill red -stroke none"
			for nr in range(rows):
				tmpw=dw3
				for nc in range(cols):
					drawCmnd+=" -draw \"text "+str(tmpw)+","+str(tmph)+" '"+str(cnt)+"'\""
					cnt=cnt+1
					tmpw+=dw
				tmph+=dh

			#region name
			dh4=round(dh/6)
			dw4=0#round(dw/6)
			tmph4=dh4*1
			drawCmnd+=" -pointsize "+str(dh4)+" -fill black -stroke none"
			cntRows=0
			cntCols=0
			strRC=""
			for nr in range(rows):
				tmpw=dw4
				for nc in range(cols):
					strRC=str(cntRows)+"-"+str(cntCols)
					drawCmnd+=" -draw \"text "+str(tmpw)+","+str(tmph4)+" '"+strRC+"'\""
					cnt=cnt+1
					tmpw+=dw
					cntCols+=1
				tmph4+=dh
				cntRows+=1
				cntCols=0


			if newmagick==0:
				#old
				cmdDraw="convert -size "+str(ww)+"x"+str(hh)+" xc:none -fill none "+drawCmnd+" "+name
			else:
				#new
				cmdDraw="magick -size "+str(ww)+"x"+str(hh)+" xc:none -fill none "+drawCmnd+" "+name
			subprocess.call(cmdDraw, shell=True)
			#################################
			##using imagemagick end##########
			#################################

		return name

class MarginCalculate(Operator):
	bl_idname = 'margin.calculate'
	bl_label = "Calculate best margins"
	bl_description = "Calculate the margins compatible with the rendering size starting from the 'max margins' value; if no compatible margins are found, zero is returned: try changing render size or increasing 'max margins'"
	bl_options = {'REGISTER', 'UNDO'}
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "output"
	
	def execute(self, context):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings

		resx=rnd.resolution_x
		resy=rnd.resolution_y

		nregionsw=0
		nregionsh=0
		if ps.RR_method=="DIVIDE":
#		if ps.RR_dim_region==False:
			nregionsw=ps.RR_reg_rows
			nregionsh=ps.RR_reg_columns
		else:
			nregionsw=ps.RR_multiplier
			nregionsh=ps.RR_multiplier
			resx=rnd.resolution_x*ps.RR_multiplier
			resy=rnd.resolution_y*ps.RR_multiplier

		arMargW=[]
		arMargW=self.calcMarg(context, resx, nregionsw, min(ps.RR_mrgmax,resx))
		arMargH=[]
		arMargH=self.calcMarg(context, resy, nregionsh, min(ps.RR_mrgmax,resy))
		
		arMargW.sort(key = lambda x: (len(x[0]), -x[1]))
		arMargH.sort(key = lambda y: (len(y[0]), -y[1]))
#		print(arMargW)
#		print("***************************")
		
		if len(arMargW)<1:
			print("change render w res: no compatible margins")
			ps.RR_mrg_w=0
		else:
			print("margins compatible with render w res: "+str(arMargW))
			ps.RR_mrg_w=int(arMargW[0][1])

		if len(arMargH)<1:
			print("change render h res: no compatible margins")
			ps.RR_mrg_h=0
		else:
			print("margins compatible with render h res: "+str(arMargH))
			ps.RR_mrg_h=int(arMargH[0][1])
			

		return{"FINISHED"}

	def Sort(self,List):
		List.sort(key=lambda l: len(l[0]))
		return List

	def calcMarg(self, context, dimrend, nreg, maxm):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
		
		w=dimrend
		arM=[]
		deltarel=(1/w)*(w/nreg)
		reldimtmp=0
		for imarg in range(maxm, 1, -1):
			reldimtmp=round((deltarel+((1/w)*imarg)),8)
			if len(str(reldimtmp))<10 :
					#print(str(imarg)+" - "+str(imarg/w))
					arM.append([str(reldimtmp),imarg])

		return arM

class RenderRegions(Operator):
	bl_idname = 'render.regions'
	bl_label = "Render regions"
	bl_description = "Start render regions"
	bl_options = {'REGISTER', 'UNDO'}
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "output"
	
	_timer = None
	current_frame = 0
	last_frame = 1
	stop = None
	rendering = None
	render_ready = False
	finished=False
	shots = None
	arrayRegion=[]
	
	tot_reg=-1
	num_rows=-1
	num_cols=-1

	min_x = 0
	max_x = 0
	min_y = 0
	max_y = 0
	delta_x = 0
	delta_y = 0
	
	outputImgName=""
	outputFolder=""
	region_name=""
	
	control=-1
	
	allRegions=[]

	def pre(self, scene, context=None):
#		print("event PRE")
		self.rendering = True
		scene.renderregionsettings.RR_msg1="render "+str(scene.renderregionsettings.RR_cntrnd)+"/"+str(scene.renderregionsettings.RR_maxrnd)

	def post(self, scene, context=None):
		self.rendering = False
		self.render_ready=False
#		print("event POST---------------"+str(self.rendering))
#		scene.renderregionsettings.RR_msg2="rendered :"+scene.renderregionsettings.RR_activeRendername
#		print("**************end")
		for x in self.saveFileOutputs:
			tempNodeFO=scene.node_tree.nodes[str(x[0])]
			tempslotcount=len(tempNodeFO.file_slots)
#			print("riprendo fo= " + str(tempNodeFO) + " - slots=" + str(tempslotcount))
			for xSlot in range(tempslotcount):
#				print("prima:" + str(tempNodeFO.file_slots[xSlot].path))
#				print("vecchio:" + str(x[xSlot+1]))
				tempNodeFO.file_slots[xSlot].path=str(x[xSlot+1])
#				print("dopo:" + str(tempNodeFO.file_slots[xSlot].path))
#		print("**************end")

	def cancelled(self, scene, context=None):
#		print("event CANCELLED")
		self.stop = True
		
	def add_handlers(self, context):
		render_pre.append(self.pre)
		render_post.append(self.post)
		render_cancel.append(self.cancelled)

		self._timer = context.window_manager.event_timer_add(3, window=context.window)
		context.window_manager.modal_handler_add(self)
	
	def remove_handlers(self, context):
		if self.pre in render_pre:
			render_pre.remove(self.pre)
		if self.post in render_post:
			render_post.remove(self.post)
		if self.cancelled in render_cancel:
			render_cancel.remove(self.cancelled)
		
		if self._timer is not None:
			context.window_manager.event_timer_remove(self._timer)
		
		scn = context.scene
		rnd = scn.render
		ps = scn.renderregionsettings
		
		if ps.RR_oldoutputfilepath!="":
			rnd.filepath=ps.RR_oldoutputfilepath
		rnd.resolution_percentage=ps.RR_oldPerc

	def createScript(self, context):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
		
		arObRegions=[]
		
		imgExtension=str.lower(rnd.image_settings.file_format)
		
#		for el in range(0,len(self.arrayRegion)):
#		for el in self.arrayRegion:
		for el in self.allRegions:
			tmpOb=RenderObject()
			ret_regionArea=0
			ret_resolutionPercent=0
			ret_resolution=0
			ret_imageName=""
			ret_usecrop=False
			
			tempRegionData=el
			
#			tempRegionName = "###_" + str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_row + "_" + n_col
			tempRegionName = tempRegionData.baseNameNoExtScript
			self.region_name = tempRegionName# + rnd.file_extension
			ret_imageName=self.outputFolderAbs + os.path.sep + self.region_name
			
			ret_regionArea = AreaRegion(
				tempRegionData.minx,
				tempRegionData.maxy,
				tempRegionData.maxx,
				tempRegionData.miny
				)
			
#			if (tempRegionData.render==True):
#			print("self.region_name",self.region_name)
			rnd.border_min_x=tempRegionData.minx
			rnd.border_min_y=tempRegionData.maxy
			rnd.border_max_x=tempRegionData.maxx
			rnd.border_max_y=tempRegionData.miny
			####################################################################
			####################################################################
			
			if (ps.RR_dim_region==True):
				ret_resolutionPercent=ps.RR_multiplier*100
				ret_usecrop = True
			else:
				ret_resolutionPercent=rnd.resolution_percentage
				ret_usecrop = rnd.use_crop_to_border
			
			tmpOb.regionarea=ret_regionArea
			tmpOb.imageName=ret_imageName
			tmpOb.resolution=ret_resolution
			tmpOb.resolutionPercent=ret_resolutionPercent
			tmpOb.usecrop=ret_usecrop
			tmpOb.nrow=tempRegionData.nrow
			tmpOb.ncol=tempRegionData.ncol
			tmpOb.render=tempRegionData.render
			tmpOb.regionName=tempRegionData.regionName
			
			current_frame = scn.frame_current
			tmpOb.currframe=current_frame
			
			arObRegions.append(tmpOb)
		
		
#		folder blender file
		mainPath=bpy.path.abspath("//")

#		path blender file
		filepath = bpy.data.filepath
		
#		nome del file
#		bpy.path.basename(bpy.context.blend_data.filepath)
		fileName=bpy.path.basename(bpy.data.filepath)
		
#		executable path
		blenderPath=bpy.app.binary_path

#		path render
#		ps.RR_activeRendername=self.outputFolder + os.path.sep + self.region_name
		
		####################
##		##control file path, if outpur folder exist
#		check exist self.outputFolderAbs+ os.path.sep
		renderFolder=self.outputFolderAbs
		renderFolderExist = os.path.exists(renderFolder)
		creatingFolder=""
#		print("**")
#		print(renderFolderExist)
#		print("**")
		if (renderFolderExist==False):
			try:
#				os.mkdir(renderFolder)
				os.makedirs(renderFolder)
				print(f"render folder '{renderFolder}' created.")
				creatingFolder="created"
				renderFolderExist=True
			except FileExistsError:
				print(f"render folder '{renderFolder}' already exists.")
				creatingFolder="already exists"
				renderFolderExist=True
			except PermissionError:
				print(f"Permission denied: Unable to create '{renderFolder}'.")
				creatingFolder=f"Permission denied: Unable to create '{renderFolder}'."
			except Exception as e:
				print(f"An error occurred: {e}")
				creatingFolder=f"An error occurred: {e}"
		if (renderFolderExist==False):
			self.report({'ERROR'},"Error creating render folder, no script created, error: "+ creatingFolder)
			return('FINISHED')
		####################
	
		#platform.system()
		#'Linux'
		#'Windows'
		#'Darwin'
		platSyst=platform.system()
		print("platSyst",platSyst)
		scriptExt=".sh"
#		platSyst="Windows"
		# platSyst="Linux"
		if (platSyst=="Windows"):
			strScript=self.getScriptBatch(context, arObRegions)
			scriptExt=".bat"
		else:
			strScript=self.getScriptShell(context, arObRegions)
		
		#nome del file blend
		blendName= bpy.path.basename(bpy.context.blend_data.filepath).split(".")[0]
		
##		#add n frame
#		nframescript="_"+str(scn.frame_current)+"_"
		cfs=scn.frame_current
		nframescript = "_"+str(f'{cfs:0{3}d}')
	
		####################
##		##control file path, if outpur folder exist
		####################
#		
#		fileScript=self.outputFolderAbs+ os.path.sep+blendName+scriptExt
		fileScript=self.outputFolderAbs+ os.path.sep+blendName+nframescript+scriptExt
			
		with open(fileScript, 'w') as file:
			file.write(strScript)
			file.close()

		ps.RR_msg1="created "+fileScript
		##todo add timer to empty msg

		self.report({'INFO'},ps.RR_msg1)
#		'DEBUG', 'INFO', 'OPERATOR', 'PROPERTY', 'WARNING', 'ERROR', 'ERROR_INVALID_INPUT', 'ERROR_INVALID_CONTEXT', 'ERROR_OUT_OF_MEMORY')
		return('FINISHED')
		
	def getScriptBatch(self,context,arObRegions):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
		
#		folder blender file
		mainPath=bpy.path.abspath("//")

#		path blender file
		filepath = bpy.data.filepath
		
#		nome del file
#		bpy.path.basename(bpy.context.blend_data.filepath)
		fileName=bpy.path.basename(bpy.data.filepath)
		
#		executable path
		blenderPath=bpy.app.binary_path
		
		strScript=""
		strScript+="@echo off"+"\n"
		strScript+=""+"\n"
		strScript+="SETLOCAL"+"\n"
		strScript+="set mainPath="+mainPath+"\n"
#		strScript+="file=\""+filepath+"\""+"\n"
		strScript+="set file=%mainPath%"+fileName+"\n"
		strScript+="set blenderPath="+blenderPath+"\n"
		
		strScript+=":: set cyclesSamples="+str(scn.cycles.samples)+"\n"
		strScript+=":: set eeveeSamples="+str(scn.eevee.taa_render_samples)+"\n"
		strScript+=":: set renderEngine="+str(scn.render.engine)+"\n"
		strScript+=":: BLENDER_EEVEE CYCLES"+"\n"
		
		strScript+="set pythonName=renderscriptRRegion"+"\n"
		strScript+="set pyfile=%mainPath%%pythonName%.py"+"\n"

		strScript+="\n"
		
		# strScript+=""+"\n"
		# strScript+=""+"\n"

		tmprow=0
		for ireg in arObRegions:
			comm=""
			if(ireg.render==False):
				comm="::"
			
			strScript+=comm+"set tmpImgName=\""+ireg.imageName+"\""+"\n"
			strScript+=comm+"set datarender=%TIME% "+"\n"
			strScript+=comm+"set datascript=%TIME% "+"\n"
			strScript+=comm+"CALL :startrender "
			strScript+=str(ireg.regionarea.minx)+", "
			strScript+=str(ireg.regionarea.miny)+", "
			strScript+=str(ireg.regionarea.maxx)+", "
			strScript+=str(ireg.regionarea.maxy)+", "
			strScript+="%tmpImgName%, "
			strScript+=str(ireg.resolution)+", "
			strScript+=str(ireg.resolutionPercent)+", "
			strScript+=str(ireg.usecrop)+", "
			strScript+=str(ireg.currframe)+", "
			strScript+="\""+str(ireg.regionName)+"\" "
			strScript+="\n"
			strScript+=comm+"CALL :msg \"ok "+str(ireg.nrow)+" "+str(ireg.ncol)+"\""+"\n"
			strScript+="\n"
		
		pyJoin=self.writeJoinPython(context)
		
		strScript+="\n"
		strScript+="::crop and join image"+"\n"
#		strScript+="::python "+pyJoin+"\n"
		strScript+="python \""+pyJoin+"\"\n"
		
		strScript+="\n"
		strScript+="echo \"done\"\n"
		strScript+="EXIT /B %ERRORLEVEL% \n"
		strScript+="\n"

		strScript+=":msg"+"\n"
		strScript+="SETLOCAL"+"\n"
		strScript+="set msg=%~1"+"\n"
		strScript+="set datamsg=%TIME%"+"\n"
		strScript+="::telegram-send \"%datarender% - %datamsg% - render %msg%\""+"\n"
		strScript+="echo \"%datascript% -- %datarender% - %datamsg% - render %msg%\""+"\n"
		strScript+="ENDLOCAL"+"\n"
		strScript+="EXIT /B 0"+"\n"
		strScript+="\n"
		
		strScript+=":startrender"+"\n"
		strScript+="SETLOCAL"+"\n"
		strScript+="set minx=%~1"+"\n"
		strScript+="SHIFT"+"\n"
		strScript+="set miny=%~1"+"\n"
		strScript+="set maxx=%~2"+"\n"
		strScript+="set maxy=%~3"+"\n"
		strScript+="set imageName=%~4"+"\n"
		strScript+="set resolution=%~5"+"\n"
		strScript+="set resolutionPercent=%~6"+"\n"
		strScript+="set usecrop=%~7"+"\n"
		strScript+="set curframe=%~8"+"\n"
		strScript+="set foPath=%~9"+"\n"
		strScript+="IF EXIST \"%pyfile%\" ("+"\n"
		strScript+="    DEL \"%pyfile%\""+"\n"
		strScript+=")"+"\n"
		# strScript+="echo \"%pyfile%\""+"\n"
		# strScript+="copy /y NUL %pyfile% >NUL"+"\n"
		strScript+="echo import bpy > \"%pyfile%\""+"\n"
		strScript+="echo scn = bpy.context.scene >> \"%pyfile%\""+"\n"
		strScript+="echo rnd = scn.render >> \"%pyfile%\""+"\n"
		strScript+="echo rnd.border_min_x=%minx% >> \"%pyfile%\""+"\n"
		strScript+="echo rnd.border_min_y=%miny% >> \"%pyfile%\""+"\n"
		strScript+="echo rnd.border_max_x=%maxx% >> \"%pyfile%\""+"\n"
		strScript+="echo rnd.border_max_y=%maxy% >> \"%pyfile%\""+"\n"
		# strScript+="echo rnd.filepath=\"%imageName%\" >> \"%pyfile%\""+"\n"
		strScript+="echo rnd.resolution_percentage=%resolutionPercent% >> \"%pyfile%\""+"\n"
		strScript+="echo rnd.use_crop_to_border = %usecrop% >> \"%pyfile%\""+"\n"
		strScript+="echo scn.frame_set(%curframe%) >> \"%pyfile%\""+"\n"
		strScript+="echo scn.frame_current = %curframe% >> \"%pyfile%\""+"\n"
		strScript+="echo scn.render.use_overwrite=True >> \"%pyfile%\""+"\n"
		
		strScript+="::echo scn.cycles.samples=%cyclesSamples% >> \"%pyfile%\""+"\n"
		strScript+="::echo scn.eevee.taa_render_samples=%eeveeSamples% >> \"%pyfile%\""+"\n"
		strScript+="::echo scn.render.engine='%renderEngine%' >> \"%pyfile%\""+"\n"
		
		strScript+="echo if(scn.node_tree!=None): >> \"%pyfile%\""+"\n"
		strScript+="echo     for xfo in scn.node_tree.nodes: >> \"%pyfile%\""+"\n"
		strScript+="echo         if (xfo.type=='OUTPUT_FILE'): >> \"%pyfile%\""+"\n"
		strScript+="echo             tempslotcount=len(xfo.file_slots) >> \"%pyfile%\""+"\n"
		strScript+="echo             for xSlot in range(tempslotcount): >> \"%pyfile%\""+"\n"
		strScript+="echo                 xfo.file_slots[xSlot].path=xfo.file_slots[xSlot].path + '%foPath%' + '_' >> \"%pyfile%\""+"\n"
		
		strScript+="CALL \"%blenderPath%\" -b \"%file%\" -x 1 -o \"%imageName%\" -P \"%pyfile%\" -f %curframe%"+"\n"
		strScript+="ENDLOCAL"+"\n"
		strScript+="EXIT /B 0"+"\n"

		strScript+="\n"
		return strScript

	def getScriptShell(self,context,arObRegions):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
		
#		folder blender file
		mainPath=bpy.path.abspath("//")

#		path blender file
		filepath = bpy.data.filepath
		
#		nome del file
#		bpy.path.basename(bpy.context.blend_data.filepath)
		fileName=bpy.path.basename(bpy.data.filepath)
		
#		executable path
		blenderPath=bpy.app.binary_path
		
		strScript=""

		strScript+="#! /bin/bash"+"\n"
		strScript+=""+"\n"
		strScript+="mainPath=\""+mainPath+"\""+"\n"
#		strScript+="file=\""+filepath+"\""+"\n"
		strScript+="file=$mainPath\""+fileName+"\""+"\n"
		strScript+="blenderPath="+blenderPath+""+"\n"
		strScript+="datarender=$(date +\"%Y%m%d_%H-%M\")"+"\n"
		strScript+="datascript=$(date +\"%Y%m%d_%H-%M\")"+"\n"
		
		
		strScript+="#cyclesSamples="+str(scn.cycles.samples)+"\n"
		strScript+="#eeveeSamples="+str(scn.eevee.taa_render_samples)+"\n"
		strScript+="#renderEngine="+str(scn.render.engine)+"\n"
		strScript+="#### BLENDER_EEVEE CYCLES"+"\n"
		
		strScript+="\n"
		
		strScript+="msg()"+"\n"
		strScript+="{"+"\n"
		strScript+="msg=$1"+"\n"
		strScript+="nomelog=$2"+"\n"
		strScript+="datamsg=$(date +\"%Y%m%d_%H-%M\")"+"\n"
		strScript+="#telegram-send \"$datarender - $datamsg - render $1\""+"\n"
		strScript+="echo \"$datascript -- $datarender - $datamsg - render $1\""+"\n"
		strScript+="}"+"\n"
		
#		strScript+="renderregion()"+"\n"
#		strScript+="{"+"\n"
#		strScript+="pyname=$1"+"\n"
#		strScript+="imageName=$2"+"\n"
#		strScript+="frame=$3"+"\n"
#		strScript+="$blenderPath -b \"$file\" -x 1 -o \"$imageName\" -P $pyname -f $frame"+"\n"
#		strScript+="}"+"\n"
		
		strScript+="function startrender()"+"\n"
		strScript+="{"+"\n"
		strScript+="minx=$1"+"\n"
		strScript+="miny=$2"+"\n"
		strScript+="maxx=$3"+"\n"
		strScript+="maxy=$4"+"\n"
		strScript+="imageName=$5"+"\n"
		strScript+="resolution=$6"+"\n"
		strScript+="resolutionPercent=$7"+"\n"
		strScript+="usecrop=$8"+"\n"
		strScript+="curframe=$9"+"\n"
		strScript+="foPath=${10}"+"\n"
		strScript+="if test -f \"$pyfile\"; then"+"\n"
		strScript+="    echo \"$pyfile exists.\""+"\n"
		strScript+="    rm $pyfile"+"\n"
		strScript+="fi"+"\n"
		strScript+="echo \"$pyfile\""+"\n"
		strScript+="touch $pyfile"+"\n"
		strScript+="echo \"import bpy\" >> $pyfile"+"\n"
		strScript+="echo \"scn = bpy.context.scene\" >> $pyfile"+"\n"
		strScript+="echo \"rnd = scn.render\" >> $pyfile"+"\n"
#		strScript+="echo \"def setRender():\" >> $pyfile"+"\n"
		strScript+="echo \"rnd.border_min_x=\"$minx >> $pyfile"+"\n"
		strScript+="echo \"rnd.border_min_y=\"$miny >> $pyfile"+"\n"
		strScript+="echo \"rnd.border_max_x=\"$maxx >> $pyfile"+"\n"
		strScript+="echo \"rnd.border_max_y=\"$maxy >> $pyfile"+"\n"
		strScript+="echo \"rnd.filepath='\"$imageName\"'\" >> $pyfile"+"\n"
		strScript+="echo \"rnd.resolution_percentage=\"$resolutionPercent >> $pyfile"+"\n"
		strScript+="echo \"rnd.use_crop_to_border = \"$usecrop >> $pyfile"+"\n"
		strScript+="echo \"\" >> $pyfile"+"\n"
#		strScript+="echo \"setRender()\" >> $pyfile"+"\n"
		strScript+="echo \"\" >> $pyfile"+"\n"
		strScript+="echo \"scn.frame_set(\"$curframe\")\" >> $pyfile"+"\n"
		strScript+="echo \"scn.frame_current = \"$curframe >> $pyfile"+"\n"
		strScript+="echo \"scn.render.use_overwrite=True\" >> $pyfile"+"\n"
		
		strScript+="#echo \"scn.cycles.samples=\"$cyclesSamples >> $pyfile"+"\n"
		strScript+="#echo \"scn.eevee.taa_render_samples=\"$eeveeSamples >> $pyfile"+"\n"
		strScript+="#echo \"scn.render.engine='\"$renderEngine\"'\" >> $pyfile"+"\n"
		
		strScript+="echo \"if(scn.node_tree!=None):\" >> $pyfile"+"\n"
		strScript+="echo \"    for xfo in scn.node_tree.nodes:\" >> $pyfile"+"\n"
		strScript+="echo \"        if (xfo.type=='OUTPUT_FILE'):\" >> $pyfile"+"\n"
		strScript+="echo \"            tempslotcount=len(xfo.file_slots)\" >> $pyfile"+"\n"
		strScript+="echo \"            for xSlot in range(tempslotcount):\" >> $pyfile"+"\n"
		strScript+="echo \"                xfo.file_slots[xSlot].path=xfo.file_slots[xSlot].path + '\"$foPath\"' + '_'\" >> $pyfile"+"\n"
		
		strScript+="echo \"\" >> $pyfile"+"\n"
#		strScript+="renderregion $pyfile $imageName $curframe"+"\n"
		######call the active scene when the script was created
		strScript+="$blenderPath -b --factory-startup \"$file\" -x 1 -o \"$imageName\" -S '"+scn.name+"' -P $pyfile -f $curframe"+"\n"
		######
		
		strScript+="}"+"\n"
		strScript+="pythonName=\"renderscriptRRegion\""+"\n"
		strScript+="pyfile=$mainPath$pythonName\".py\""+"\n"
		strScript+=""+"\n"
		strScript+=""+"\n"
#		if (ps.RR_who_region=="all"):
#			strScript+="arrayImgNamesPerRow=()"+"\n"
#			strScript+="strRowNames=()"+"\n"
#			strScript+="tmpImgNamesPerRow=()"+"\n"
		strScript+=""+"\n"
		strScript+="frame="+str(arObRegions[0].currframe)+"\n"
		strScript+="resperc="+str(arObRegions[0].resolutionPercent)+"\n"
		strScript+=""+"\n"
		tmprow=0
#		for ireg in range(0,len(arObRegions)):
		for ireg in arObRegions:
			
			comm=""
			if(ireg.render==False):
				comm="#"
			
			strScript+=comm+"sleep 5s"+"\n"
			strScript+=comm+"tmpImgName=\""+ireg.imageName+"\""+"\n"
####			in ireg.imageName c'è l'indicazione del frame (###)
####			che blender vuole mettere da qualche parte
####			quando si registrano i nomi delle immagini
####			per costruire poi le righe e l'immagine finale
####			si deve sostituire ### col frame
#			imgPre=ireg.imageName
#			cf=ireg.currframe
#			new_nframe = f'{cf:0{3}d}'
#			imgPost = imgPre.replace("###", str(new_nframe))
#			strScript+=comm+"tmpImgNameFrm=\""+imgPost+"\""+"\n"
#			
#			if (ps.RR_who_region=="all"):
#				if (tmprow!=ireg.nrow):
#					strScript+="arrayImgNamesPerRow+=(\"$tmpImgNamesPerRow\")"+"\n"
#					strScript+="tmpImgNamesPerRow=()"+"\n"
#					strScript+="tmpImgNamesPerRow+=\"$tmpImgNameFrm\"\"."+imgExtension+" \"\n"
#					tmprow=ireg.nrow
#				else:
#					strScript+="tmpImgNamesPerRow+=\"$tmpImgNameFrm\"\"."+imgExtension+" \"\n"
			
			strScript+=comm+"datarender=$(date +\"%Y%m%d_%H-%M\") "+"\n"
			strScript+=comm+"startrender "
			strScript+=str(ireg.regionarea.minx)+" "
			strScript+=str(ireg.regionarea.miny)+" "
			strScript+=str(ireg.regionarea.maxx)+" "
			strScript+=str(ireg.regionarea.maxy)+" "
#			strScript+=ireg.imageName+"_### "
#			strScript+=ireg.imageName+" "
			strScript+="\"$tmpImgName\" "
			strScript+=str(ireg.resolution)+" "
#			strScript+=str(ireg.resolutionPercent)+" "
			strScript+="$resperc"+" "
			strScript+=str(ireg.usecrop)+" "
#			strScript+=str(ireg.currframe)+" "
			strScript+="$frame"+" "
			strScript+="\""+str(ireg.regionName)+"\" "
			
			
			strScript+="\n"
			strScript+=comm+"msg \"ok "+str(ireg.nrow)+" "+str(ireg.ncol)+"\""+"\n"
			strScript+="\n"
		
#		if (ps.RR_who_region=="all"):
#				strScript+="arrayImgNamesPerRow+=(\"$tmpImgNamesPerRow\")"+"\n"
#				strScript+="tmpImgNamesPerRow=()"+"\n"
		
		pyJoin=self.writeJoinPython(context)
		
		strScript+="\n"
		strScript+="#crop and join image"+"\n"
		if(ps.RR_reg_columns>1 or ps.RR_reg_rows>1):
			strScript+="python3 \""+pyJoin+"\"\n"
		else:
			strScript+="#python3 \""+pyJoin+"\"\n"
		
		strScript+="\n"
		#20241213
#		strScript+="msg \"fine\"\n"
		strScript+="msg \"end\"\n"
		strScript+="echo \"done\"\n"
		strScript+="\n"
		return strScript
	
	def getRegionName(self,context,index):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
		
		strname=""
		strnameScript=""
		
		pos_row=int(index/self.num_cols)
		pos_col=int( ( index - ( pos_row*self.num_cols) ) )
		
		decCol=math.ceil(math.log(self.num_cols,10))
		decRows=math.ceil(math.log(self.num_rows,10))
		dec=max(decCol,decRows)
		n_row = f'{pos_row:0{dec}d}'
		n_col = f'{pos_col:0{dec}d}'
		
##		nome della regione: colonnexrighe riga colonna
		strname = str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_row + "_" + n_col
		strnameScript = "###_" + str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_row + "_" + n_col
		strnameScript2 = "###_" + str(self.num_cols)+"x"+str(self.num_rows)
#		print("strname",strname)
		
		return [strname,n_row,n_col,strnameScript,strnameScript2]

	def setRender(self, context):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
#		if ps.RR_cntrnd<len(self.arrayRegion):
		if ps.RR_cntrnd<len(self.allRegions):
#			tempRegionData=self.allRegions[self.arrayRegion[ps.RR_cntrnd]]
			tempRegionData=self.allRegions[ps.RR_cntrnd]
			
			if (tempRegionData.render==True):
				self.region_name=tempRegionData.baseName
				ps.RR_activeRendername=tempRegionData.fullName
				rnd.border_min_x=tempRegionData.minx
				rnd.border_min_y=tempRegionData.maxy
				rnd.border_max_x=tempRegionData.maxx
				rnd.border_max_y=tempRegionData.miny
				
				rnd.filepath=ps.RR_activeRendername
				ps.RR_msg1="render "+str(ps.RR_cntrnd)+"/"+str(ps.RR_maxrnd)
#				ps.RR_msg2="rendering :"+ps.RR_activeRendername


				#ciclo per cambiare i path nei fileoutput
				#alla fine del render dovrebbero essere rimessi a posto
#				print("****----****----****----****----")
				for x in self.saveFileOutputs:
					tempNodeFO=scn.node_tree.nodes[str(x[0])]
					tempslotcount=len(tempNodeFO.file_slots)
	#				print("cambio fo= " + str(tempNodeFO) + " - slots=" + str(tempslotcount))
					for xSlot in range(tempslotcount):
						tempNodeFO.file_slots[xSlot].path=str(x[xSlot+1]) + tempRegionData.regionName + "_"
				#####################


				
				if (ps.RR_dim_region==True):
					rnd.resolution_percentage=ps.RR_multiplier*100
					rnd.use_crop_to_border = 1
	#				rnd.use_crop_to_border = 0
				ps.RR_cntrnd=ps.RR_cntrnd+1
				return 1
			else:
				ps.RR_cntrnd=ps.RR_cntrnd+1
				return -1
		else:
			self.finished=True
			ps.RR_msg1=""
#			ps.RR_msg2=""
			return 0

	def execute(self, context):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
		
		self.stop = False
		self.rendering = False
		self.render_ready = False
		
		ps.RR_activeRendername=""
		ps.RR_msg1=""
#		ps.RR_msg2=""
		ps.RR_cntrnd=0;
		ps.RR_maxrnd=0;
		
		file_name=os.path.splitext( os.path.split(bpy.data.filepath)[1])[0]
		self.outputFolderAbs=os.path.split( bpy.path.abspath(rnd.filepath) )[0]
		
		#######################
		#check filepath, if "" or "/tmp\" alert user
		if(rnd.filepath=="" or rnd.filepath=="/tmp\\"):
			self.report({'ERROR'},"Error in Output path, set a valid path")
			return {"CANCELLED"}
		#######################
		#######################
		#self.outputFolder=os.path.split( bpy.path.relpath(rnd.filepath) )[0]
#		print("self.outputFolder")
#		print(self.outputFolder)
		#errore in relpath se progetto e path di render in dischi diversi in win10
		#fallisce: bpy.path.relpath(rnd.filepath)
		#provare 
		#os.path.relpath(rnd.filepath, os.path.splitdrive(rnd.filepath)[0])
		#test relpath, se fallisce rimane abs
		relp=""
		try:
			relp=bpy.path.relpath(rnd.filepath)
		except:
			relp=bpy.path.abspath(rnd.filepath)
		
		self.outputFolder=os.path.split( relp )[0]
#		print("self.outputFolder")
#		print(self.outputFolder)
		#######################
		
		#ok linux##self.outputImgName=os.path.splitext(os.path.split( bpy.path.relpath(rnd.filepath) )[1])[0]
		self.outputImgName=os.path.splitext(os.path.split( bpy.path.abspath(rnd.filepath) )[1])[0]
		# print("----")
		# print(os.path.splitext(os.path.split( bpy.path.relpath(rnd.filepath) )[1]))
		# print(os.path.splitext(os.path.split( bpy.path.abspath(rnd.filepath) )[1]))
		# print("----")
		ps.RR_oldoutputfilepath=rnd.filepath
		ps.RR_oldPerc=rnd.resolution_percentage
#		print(self.outputFolderAbs)
#		print(self.outputFolder)
		
#		print("change FileOutput........")
		self.saveFileOutputs=[]
		tempArrFO=[]
		#ciclo per cambiare i path all'eventuale file output
		if(scn.node_tree!=None):
			for xfo in scn.node_tree.nodes:
				if (xfo.type=="OUTPUT_FILE"):
					tempArrFO=[]
					tempArrFO.append(xfo.name)
					tempslotcount=len(xfo.file_slots)
	#				print("registro fo= " + str(xfo.name) + " - slots=" + str(tempslotcount))
					for xSlot in range(tempslotcount):
						oldFOpath=xfo.file_slots[xSlot].path
						tempArrFO.append(oldFOpath)
					self.saveFileOutputs.append(tempArrFO)
		
		##todo
#		if bpy.data.scenes["Scene"].render.image_settings.color_mode=="RGBA"
#			if bpy.data.scenes["Scene"].render.film_transparent=True:
#				bpy.data.scenes["Scene"].render.use_crop_to_border = False and True
#			else:
#				bpy.data.scenes["Scene"].render.use_crop_to_border = True
#		else:
#			bpy.data.scenes["Scene"].render.use_crop_to_border = True
		
		if ps.RR_dim_region==False:
			self.delta_x = 1/ps.RR_reg_columns
			self.delta_y = 1/ps.RR_reg_rows
		else:
			self.delta_x = 1/ps.RR_multiplier
			self.delta_y = 1/ps.RR_multiplier

		self.min_x = 0
		self.max_x = self.delta_x

		self.min_y = 0
		self.max_y = self.delta_y
		
		rnd.use_border = 1
		rnd.use_crop_to_border=True
		
		if ps.RR_dim_region==False:
			self.tot_reg=ps.RR_reg_columns*ps.RR_reg_rows
			self.num_cols=ps.RR_reg_columns
			self.num_rows=ps.RR_reg_rows
		else:
			self.tot_reg=ps.RR_multiplier*ps.RR_multiplier
			self.num_cols=ps.RR_multiplier
			self.num_rows=ps.RR_multiplier

		reg=self.prepareAllRegions(context)
		
		if reg[1]==False:
			self.arrayRegion=reg[0]
			print ("Regions to render:")
			print (self.arrayRegion)
#			ps.RR_maxrnd=len(self.arrayRegion)
			ps.RR_maxrnd=len(reg[0])
			ps_RR_cntrnd=0;
			ps.RR_renderGo=True
			
			if ps.RR_createScript==True:
				self.createScript(context)
				ps.RR_renderGo=False
				return {"FINISHED"}
			else:
				self.add_handlers(context)
	#			print("added handlers")
				return {"RUNNING_MODAL"}
		else:
			return {"CANCELLED"}


	def prepareAllRegions(self, context):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
		
		reg=[]
		errorInsertRegions=False
		
		control=""
		reg_temp=[]
		
		if "all" in ps.RR_who_region:
			for a in range(0,(self.tot_reg)):
				reg.append(a)
		elif "," in ps.RR_who_region:
			control=ps.RR_who_region.replace(',','')
			if (control.isdigit()):
				reg_temp=ps.RR_who_region.split(",")
				for a in range(0,len(reg_temp)):
					if int(reg_temp[a])<self.tot_reg:
						reg.append(int(reg_temp[a]))
					else:
						errorInsertRegions=True
			else:
				reg=[]
		elif "-" in ps.RR_who_region:
			control=ps.RR_who_region.replace('-','')
			if (control.isdigit()):
				reg_temp=ps.RR_who_region.split("-")
				for a in range(int(reg_temp[0]),int(reg_temp[1])+1):
#					print("reg_temp[a]",a)
#					print("self.tot_reg",self.tot_reg)
					if int(a)<self.tot_reg:
						reg.append(int(a))
					else:
						errorInsertRegions=True
			else:
				reg=[]
		elif ps.RR_who_region.isdigit():
			if int(ps.RR_who_region)<self.tot_reg:
				reg.append(int(ps.RR_who_region))
			else:
				errorInsertRegions=True
		else:
			reg=[]
		
##		in reg ci sono gli indici delle regioni da renderizzare
##		allRegions array con tutte le regioni
##		class Region oggetto con i valori delle singole regioni
##		ar=AreaRegion()
		
		if(errorInsertRegions==False):
			self.allRegions=[]
			
			for ireg in range(0,(self.tot_reg)):
				tmpReg=Region()
				tmpReg.index=ireg
				
				tempRegionName=self.getRegionName(context,ireg)
#				print("tempRegionName",tempRegionName)
				tmpReg.outImg = self.outputImgName
				tmpReg.regionName = tempRegionName[0]
				tmpReg.baseName = self.outputImgName +"_"+tempRegionName[0] + rnd.file_extension
				tmpReg.baseNameNoExt = self.outputImgName +"_"+tempRegionName[0]
				tmpReg.baseNameNoExtScript = self.outputImgName +"_"+tempRegionName[3]
				tmpReg.baseNameNoExtScriptGen = self.outputImgName +"_"+tempRegionName[4]
				tmpReg.fullName=self.outputFolder + os.path.sep + tmpReg.baseName
				
				# print("tmpReg.regionName",tmpReg.regionName)
				# print("tmpReg.baseName",tmpReg.baseName)
				# print("tmpReg.baseNameNoExt",tmpReg.baseNameNoExt)
				# print("tmpReg.baseNameNoExtScript",tmpReg.baseNameNoExtScript)
				# print("tmpReg.fullName",tmpReg.fullName)
				
				tmpReg.nrow=int(tempRegionName[1])
				tmpReg.ncol=int(tempRegionName[2])
				
				tmpReg.minx=self.min_x+(self.delta_x*tmpReg.ncol)
				tmpReg.maxx=self.max_x+(self.delta_x*tmpReg.ncol)
				tmpReg.miny=(self.delta_y*self.num_rows)- ((tmpReg.nrow)*self.delta_y)
				tmpReg.maxy=(self.delta_y*self.num_rows)- ((tmpReg.nrow+1)*self.delta_y)
				
				##############################
				##margins
				if(ps.RR_useMargins==True):
					resx=rnd.resolution_x
					resy=rnd.resolution_y
					relativeMargW=((1/resx)*ps.RR_mrg_w)
					relativeMargH=((1/resy)*ps.RR_mrg_h)
					if ps.RR_method=="MULTIPLY":
						resx=rnd.resolution_x*ps.RR_multiplier
						resy=rnd.resolution_y*ps.RR_multiplier
						relativeMargW=((1/resx)*ps.RR_mrg_w)#*ps.RR_multiplier
						relativeMargH=((1/resy)*ps.RR_mrg_h)#*ps.RR_multiplier
					
					tmpReg.minx=round(min(max((tmpReg.minx-relativeMargW),0),1),8)
					tmpReg.maxx=round(min(max((tmpReg.maxx+relativeMargW),0),1),8)
					tmpReg.miny=round(min(max((tmpReg.miny+relativeMargH),0),1),8)
					tmpReg.maxy=round(min(max((tmpReg.maxy-relativeMargH),0),1),8)
				
#				print("tmpReg.maxx",tmpReg.maxx)
				######################################################################
				######################################################################
				if ps.RR_method=="DIVIDE":
					tmpReg.rows=ps.RR_reg_rows
					tmpReg.cols=ps.RR_reg_columns
				else:
					tmpReg.rows=ps.RR_multiplier
					tmpReg.cols=ps.RR_multiplier
				tmpReg.frame=scn.frame_current
				if ireg in reg:
					tmpReg.render=True
				else:
					tmpReg.render=False
				self.allRegions.append(tmpReg)
		else:
			print("error create regions, check values")
			self.report({'ERROR'},"Error create regions, check values")
		return [reg,errorInsertRegions]

	def writeJoinPython(self, context):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
		
		resx=rnd.resolution_x
		resy=rnd.resolution_y
		
		###############################################
		###############################################
		#check imagemagick
		#version 7.1
		cmd="magick --version"
		newmagick=0
		data = run(cmd, capture_output=True, shell=True)
		output = data.stdout.splitlines()
		errors = data.stderr.splitlines()
		
		if (len(errors)>0) or (len(output)<1):
#			print("no imagemagick new (7)")
			newmagick=0
		else:
			newmagick=1
		cmd="convert --version"
		data = run(cmd, capture_output=True, shell=True)
		output = data.stdout.splitlines()
		errors = data.stderr.splitlines()
		if (len(errors)>0) or (len(output)<1):
			newmagick=-1
			print("no imagemagick")
		else:
			newmagick=0
		print("newmagick",str(newmagick))
		if newmagick==-1:
			print("no imagemagick installation, install before launch script")
			newmagick=1
		###############################################
		###############################################

		strScriptPy="import subprocess"+"\n"
		strScriptPy+="import os"+"\n"
		strScriptPy+="\n"
		strScriptPy+="oiioOK=False"+"\n"
#		if(oiioOK==False):
#			strScriptPy+="#try:"+"\n"
#			strScriptPy+="#\timport OpenImageIO as oiio"+"\n"
#			strScriptPy+="#\tprint(\"found OpenImageIO\")"+"\n"
#			strScriptPy+="#\toiioOK=True"+"\n"
#			strScriptPy+="#except ImportError:"+"\n"
#			strScriptPy+="#\tprint(\"Not found OpenImageIO, using ImageMagick\")"+"\n"
#			strScriptPy+="#\toiioOK=False"+"\n"
#		else:
		strScriptPy+="try:"+"\n"
		strScriptPy+="\timport OpenImageIO as oiio"+"\n"
		strScriptPy+="\tprint(\"found OpenImageIO\")"+"\n"
		strScriptPy+="\toiioOK=True"+"\n"
		strScriptPy+="except ImportError:"+"\n"
		strScriptPy+="\tprint(\"OpenImageIO not found \")"+"\n"
		strScriptPy+="\toiioOK=False"+"\n"
		
		strScriptPy+="pilOK=False"+"\n"
		strScriptPy+="try:"+"\n"
		strScriptPy+="\tfrom PIL import Image"+"\n"
		strScriptPy+="\tprint(\"found PIL\")"+"\n"
		strScriptPy+="\tpilOK=True"+"\n"
		strScriptPy+="except ImportError:"+"\n"
		strScriptPy+="\tprint(\"PIL not found \")"+"\n"
		strScriptPy+="\tpilOK=False"+"\n"
	
#		strScriptPy+="arrayImg=[]"+"\n"
		
		#2024-12-13
#		imgExtension=str.lower(rnd.image_settings.file_format)
		imgExtension=(str.lower(rnd.file_extension))[1:]

		strScriptPy+="\n"
		strScriptPy+="scale="+(str(rnd.resolution_percentage/100))+"\n"
		strScriptPy+="extension=\""+imgExtension+"\""+"\n"
		strScriptPy+="arrayImg=[]"+"\n"
#		strScriptPy+="\n"
#		strScriptPy+="\n"
#		strScriptPy+="def cropJoinImages(path,pre,post,extension):"+"\n"
#		strScriptPy+="\tarrayImg=[]"+"\n"


		tmprow=0
		tmparray=""
		for el in self.allRegions:
			outputFolderAbs=os.path.split( bpy.path.abspath(rnd.filepath) )[0]
			imgPre=outputFolderAbs + os.path.sep + el.baseNameNoExtScript
			cf=el.frame
			new_nframe = f'{cf:0{3}d}'
			name = imgPre.replace("###", str(new_nframe))
			name += "."+imgExtension
			
#			print("resx "+str(resx))
#			print("ps.RR_reg_rows "+str(ps.RR_reg_rows))
#			print("resy "+str(resy))
#			print("RR_reg_columns "+str(ps.RR_reg_columns))
			
#			cropW=resx/ps.RR_reg_rows
			cropW=resx/ps.RR_reg_columns
#			cropH=resy/ps.RR_reg_columns
			cropH=resy/ps.RR_reg_rows
			cropX=ps.RR_mrg_w
			cropY=ps.RR_mrg_h
			nrow=el.nrow
			ncol=el.ncol
			crop=ps.RR_useMargins
			scriptResx=resx
			scriptResy=resy
			if ps.RR_method=="MULTIPLY":
				cropW=resx#(resx/ps.RR_reg_rows)*ps.RR_multiplier
				cropH=resy#(resy/ps.RR_reg_columns)*ps.RR_multiplier
				scriptResx=resx*ps.RR_multiplier
				scriptResy=resy*ps.RR_multiplier
			
			if(ncol==0):
				cropX=0
			if(nrow==0):
				cropY=0
			
			if tmprow==nrow:
#				tmparray+="[r\""+name+"\","+str(int(cropW))+","+str(int(cropH))+","+str(int(cropX))+","+str(int(cropY))+","+str(nrow)+","+str(ncol)+",\""+imgExtension+"\","+str(crop)+"],"
				tmparray+="["+str(int(cropW))+","+str(int(cropH))+","+str(int(cropX))+","+str(int(cropY))+","+str(nrow)+","+str(ncol)+",extension,"+str(crop)+"],"
			else:
				tmprow=nrow
				tmparray = tmparray[:-1]
				strScriptPy+="arrayImg.append(["+tmparray+"])"+"\n"
				tmparray=""
#				tmparray+="[r\""+name+"\","+str(int(cropW))+","+str(int(cropH))+","+str(int(cropX))+","+str(int(cropY))+","+str(nrow)+","+str(ncol)+",\""+imgExtension+"\","+str(crop)+"],"
				tmparray+="["+str(int(cropW))+","+str(int(cropH))+","+str(int(cropX))+","+str(int(cropY))+","+str(nrow)+","+str(ncol)+",extension,"+str(crop)+"],"
		
		tmparray = tmparray[:-1]
		##last item
		strScriptPy+="arrayImg.append(["+tmparray+"])"+"\n"
		strScriptPy+="\n"
		
		strScriptPy+="def oiioJoinImages(path,pre,post,extension):"+"\n"
		strScriptPy+="\tprint(\"oiioJoinImages\")"+"\n"
		strScriptPy+="\tglobal arrayImg"+"\n"
		strScriptPy+="\tfullWidth=int("+str(scriptResx)+"*scale)\n"
		strScriptPy+="\tfullHeight=int("+str(scriptResy)+"*scale)\n"
		strScriptPy+="\tregionW=int("+str(int(cropW))+"*scale)\n"
		strScriptPy+="\tregionH=int("+str(int(cropH))+"*scale)\n"
		strScriptPy+="\t"+"\n"
		strScriptPy+="\t#takes the first image as a reference, useful for openexr multilayer"+"\n"
		strScriptPy+="\timg=arrayImg[0][0]"+"\n"
		strScriptPy+="\trow=str(img[4])"+"\n"
		strScriptPy+="\tcol=str(img[5])"+"\n"
		strScriptPy+="\tname=path+pre+row+\"_\"+col+post+\".\"+extension"+"\n"
		strScriptPy+="\tb0 = oiio.ImageBuf(name)"+"\n"
		strScriptPy+="\n"
		strScriptPy+="\troi = oiio.ROI()"+"\n"
		strScriptPy+="\tfullspec = b0.spec().copy()"+"\n"
		strScriptPy+="\tfullspec.width=fullWidth"+"\n"
		strScriptPy+="\tfullspec.height=fullHeight"+"\n"
		strScriptPy+="\t#create the container image where to copy all the regions"+"\n"
		strScriptPy+="\tfull_size = oiio.ImageBuf(fullspec)"+"\n"
		strScriptPy+="\toiio.ImageBufAlgo.zero(full_size)"+"\n"
		strScriptPy+="\n"
		strScriptPy+="\tnmcrop=\"__crop__\""+"\n"
		strScriptPy+="\tnmrow=\"__row__\""+"\n"
		strScriptPy+="\tcmdcrop=\"\""+"\n"
		strScriptPy+="\tnrow=0"+"\n"
		strScriptPy+="\text=\"\""+"\n"
		strScriptPy+="\tstrImgCropped=\"\""+"\n"
		strScriptPy+="\ttmprownm=\"\""+"\n"
		strScriptPy+="\tfinalImg=path+pre+post+\"_joined\"+\".\"+extension"+"\n"
		strScriptPy+="\t"+"\n"
		strScriptPy+="\tfor arRow in arrayImg:"+"\n"
		strScriptPy+="\t\tstrImgCropped=\"\""+"\n"
		strScriptPy+="\t\tfor img in arRow:"+"\n"
		strScriptPy+="\t\t\tif img[7]==True:"+"\n"
		strScriptPy+="\t\t\t\tcropW=int((img[0])*scale)"+"\n"
		strScriptPy+="\t\t\t\tcropH=int((img[1])*scale)"+"\n"
		strScriptPy+="\t\t\t\tcropX=int((img[2])*scale)"+"\n"
		strScriptPy+="\t\t\t\tcropY=int((img[3])*scale)"+"\n"
		strScriptPy+="\t\t\t\trow=(img[4])"+"\n"
		strScriptPy+="\t\t\t\tcol=(img[5])"+"\n"
		strScriptPy+="\t\t\t\text=img[6]"+"\n"
		strScriptPy+="\t\t\t\tname=path+pre+str(row)+\"_\"+str(col)+post+\".\"+extension"+"\n"
		strScriptPy+="\t\t\t\tbuffertmp = oiio.ImageBuf(name)"+"\n"
		strScriptPy+="\t\t\t\tbuffertmp.set_full(cropX, (cropW+cropX), cropY, (cropH+cropY), 0, 1)"+"\n"
		strScriptPy+="\t\t\t\txbegin=(cropW*col)-cropX"+"\n"
		strScriptPy+="\t\t\t\tybegin=(cropH*row)-cropY"+"\n"
		strScriptPy+="\t\t\t\toiio.ImageBufAlgo.paste(full_size, xbegin, ybegin, 0, 0, buffertmp, buffertmp.roi)"+"\n"
		strScriptPy+="\t\t\telse:"+"\n"
		
		strScriptPy+="\t\t\t\tcropW=int((img[0])*scale)"+"\n"
		strScriptPy+="\t\t\t\tcropH=int((img[1])*scale)"+"\n"
		strScriptPy+="\t\t\t\trow=img[4]"+"\n"
		strScriptPy+="\t\t\t\tcol=img[5]"+"\n"
		strScriptPy+="\t\t\t\text=img[6]"+"\n"
		strScriptPy+="\t\t\t\tname=path+pre+str(row)+\"_\"+str(col)+post+\".\"+extension"+"\n"
		strScriptPy+="\t\t\t\tbuffertmp = oiio.ImageBuf(name)"+"\n"
		strScriptPy+="\t\t\t\txbegin=cropW*col"+"\n"
		strScriptPy+="\t\t\t\tybegin=cropH*row"+"\n"
		strScriptPy+="\t\t\t\toiio.ImageBufAlgo.paste(full_size, xbegin, ybegin, 0, 0, buffertmp)"+"\n"
		strScriptPy+="\n"
		strScriptPy+="\t\tnrow=nrow+1"+"\n"
		strScriptPy+="\n"
#		strScriptPy+="\tarrayImg=[]"+"\n"
		strScriptPy+="\tfull_size.write(finalImg)"+"\n"
		strScriptPy+="\n"

		strScriptPy+="def PILcropJoinImages(path,pre,post,extension):"+"\n"
		strScriptPy+="\tprint(\"PILcropJoinImages\")"+"\n"
		strScriptPy+="\tglobal arrayImg"+"\n"
		strScriptPy+="\tfullWidth=int("+str(scriptResx)+"*scale)\n"
		strScriptPy+="\tfullHeight=int("+str(scriptResy)+"*scale)\n"
		strScriptPy+="\tregionW=int("+str(int(cropW))+"*scale)\n"
		strScriptPy+="\tregionH=int("+str(int(cropH))+"*scale)\n"
		strScriptPy+="\tnmcrop=\"__crop__\""+"\n"
		strScriptPy+="\tnmrow=\"__row__\""+"\n"
		strScriptPy+="\tcmdcrop=\"\""+"\n"
		strScriptPy+="\tnrow=0"+"\n"
		strScriptPy+="\text=\"\""+"\n"
		strScriptPy+="\tarImgCropped=[]"+"\n"
		strScriptPy+="\timagesCropped=[]"+"\n"
		strScriptPy+="\ttmprownm=\"\""+"\n"
		strScriptPy+="\tarImgRow=[]"+"\n"
		strScriptPy+="\tfinalImg=path+pre+post+\"_joined\"+\".\"+extension"+"\n"
		strScriptPy+="\t"+"\n"
		strScriptPy+="\tfor arRow in arrayImg:"+"\n"
		strScriptPy+="\t\tarImgCropped=[]"+"\n"
		strScriptPy+="\t\timagesCropped=[]"+"\n"
		strScriptPy+="\t\ttmpnmcrop=\"\""+"\n"
		strScriptPy+="\t\tfor img in arRow:"+"\n"
		strScriptPy+="\t\t\tif img[7]==True:"+"\n"
		strScriptPy+="\t\t\t\tcropW=int((img[0])*scale)"+"\n"
		strScriptPy+="\t\t\t\tcropH=int((img[1])*scale)"+"\n"
		strScriptPy+="\t\t\t\tcropX=int((img[2])*scale)"+"\n"
		strScriptPy+="\t\t\t\tcropY=int((img[3])*scale)"+"\n"
		strScriptPy+="\t\t\t\trow=str(img[4])"+"\n"
		strScriptPy+="\t\t\t\tcol=str(img[5])"+"\n"
		strScriptPy+="\t\t\t\text=img[6]"+"\n"
		strScriptPy+="\t\t\t\tname=path+pre+row+\"_\"+col+post+\".\"+extension"+"\n"
		strScriptPy+="\t\t\t\ttmpnmcrop=nmcrop+row+\"-\"+col+\".\"+ext"+"\n"
		strScriptPy+="\t\t\t\tprint(\"crop \"+row+\"-\"+col)"+"\n"
		strScriptPy+="\t\t\t\timg = Image.open(name)"+"\n"
		strScriptPy+="\t\t\t\timg_crop = img.crop((cropX, cropY, (cropX+cropW), (cropY+cropH))) "+"\n"
		strScriptPy+="\t\t\t\timg_crop.save(tmpnmcrop)"+"\n"
		strScriptPy+="\t\t\t\timg_crop.close()"+"\n"
		strScriptPy+="\t\t\t\tarImgCropped.append(tmpnmcrop)"+"\n"
		strScriptPy+="\t\t\telse:"+"\n"
		strScriptPy+="\t\t\t\trow=str(img[4])"+"\n"
		strScriptPy+="\t\t\t\tcol=str(img[5])"+"\n"
		strScriptPy+="\t\t\t\text=img[6]"+"\n"
		strScriptPy+="\t\t\t\tname=path+pre+row+\"_\"+col+post+\".\"+extension"+"\n"
		strScriptPy+="\t\t\t\tarImgCropped.append(name)"+"\n"
		strScriptPy+="\t"+"\n"
		strScriptPy+="\t\ttmprownm=str(nmrow)+str(nrow)+\".\"+str(ext)"+"\n"
		strScriptPy+="\t\tarImgRow.append(tmprownm)"+"\n"
		strScriptPy+="\t\tprint(\"append row \"+str(nrow))"+"\n"
		strScriptPy+="\t\trow_imgtmp = Image.open(arImgCropped[0])"+"\n"
		strScriptPy+="\t\trow_img=row_imgtmp.resize((fullWidth, regionH))"+"\n"
		strScriptPy+="\t\trow_imgtmp.close()"+"\n"
		strScriptPy+="\t\timagesCropped = [Image.open(x) for x in arImgCropped]"+"\n"
		strScriptPy+="\t\tx_offset=0"+"\n"
		strScriptPy+="\t\tfor im in imagesCropped:"+"\n"
		strScriptPy+="\t\t\trow_img.paste(im, (x_offset,0))"+"\n"
		strScriptPy+="\t\t\tx_offset += regionW"+"\n"
		strScriptPy+="\t\t\tim.close()"+"\n"
		strScriptPy+="\t\trow_img.save(tmprownm)"+"\n"
		strScriptPy+="\t\trow_img.close()"+"\n"
		strScriptPy+="\t\tnrow=nrow+1"+"\n"
		strScriptPy+="\t\tif(tmpnmcrop!=\"\"):"+"\n"
		strScriptPy+="\t\t\t#delete cropped images"+"\n"
		strScriptPy+="\t\t\tprint(\"delete cropped images\")"+"\n"
		strScriptPy+="\t\t\tfor im in arImgCropped:"+"\n"
		strScriptPy+="\t\t\t\tos.remove(im)"+"\n"
		strScriptPy+="\t\t"+"\n"
		strScriptPy+="\tprint(\"append all\")"+"\n"
		strScriptPy+="\tfinal_imgtmp = Image.open(arImgRow[0])"+"\n"
		strScriptPy+="\tfinal_img=final_imgtmp.resize((fullWidth, fullHeight))"+"\n"
		strScriptPy+="\tfinal_imgtmp.close()"+"\n"
		strScriptPy+="\timagesRows = [Image.open(x) for x in arImgRow]"+"\n"
		strScriptPy+="\ty_offset=0"+"\n"
		strScriptPy+="\tfor im in imagesRows:"+"\n"
		strScriptPy+="\t\tfinal_img.paste(im, (0,y_offset))"+"\n"
		strScriptPy+="\t\ty_offset += regionH"+"\n"
		strScriptPy+="\tfinal_img.save(finalImg)"+"\n"
		strScriptPy+="\tfinal_img.close()"+"\n"
		strScriptPy+="\t#delete rows images"+"\n"
		strScriptPy+="\tprint(\"delete rows images\")"+"\n"
		strScriptPy+="\tfor im in arImgRow:"+"\n"
		strScriptPy+="\t\tos.remove(im)"+"\n"
		strScriptPy+="\n"

		
#		strScriptPy+="def IMcropJoinImages(path,pre,post,extension):"+"\n"
##		strScriptPy+="\tarrayImg=[]"+"\n"
#		strScriptPy+="\tglobal arrayImg"+"\n"
#		strScriptPy+="\tnmcrop=\"__crop__\""+"\n"
#		strScriptPy+="\tnmrow=\"__row__\""+"\n"
#		strScriptPy+="\tcmdcrop=\"\""+"\n"
#		strScriptPy+="\tnrow=0"+"\n"
#		strScriptPy+="\text=\"\""+"\n"
#		strScriptPy+="\tstrImgCropped=\"\""+"\n"
#		strScriptPy+="\ttmprownm=\"\""+"\n"
#		strScriptPy+="\tstrImgRow=\"\""+"\n"
###		finalImg=outputFolderAbs+os.path.sep+bpy.path.basename(bpy.context.blend_data.filepath).split(".")[0]+"."+imgExtension
##		finalImg=outputFolderAbs+os.path.sep+bpy.path.basename(bpy.context.blend_data.filepath).split(".")[0]+"_"+str(new_nframe)+"."+imgExtension
##		strScriptPy+="finalImg=r\""+finalImg+"\""+"\n"
#		strScriptPy+="\tfinalImg=path+pre+post+\"_joined\"+\".\"+extension"+"\n"
#		strScriptPy+="\t\n"
#		strScriptPy+="\tfor arRow in arrayImg:"+"\n"
#		strScriptPy+="\t\tstrImgCropped=\"\""+"\n"
#		strScriptPy+="\t\tfor img in arRow:"+"\n"
#		strScriptPy+="\t\t\tif img[7]==True:"+"\n"
##		strScriptPy+="\t\t\t\tname=img[0]"+"\n"
#		strScriptPy+="\t\t\t\tcropW=str(img[0])"+"\n"
#		strScriptPy+="\t\t\t\tcropH=str(img[1])"+"\n"
#		strScriptPy+="\t\t\t\tcropX=str(img[2])"+"\n"
#		strScriptPy+="\t\t\t\tcropY=str(img[3])"+"\n"
#		strScriptPy+="\t\t\t\trow=str(img[4])"+"\n"
#		strScriptPy+="\t\t\t\tcol=str(img[5])"+"\n"
#		strScriptPy+="\t\t\t\text=img[6]"+"\n"
#		strScriptPy+="\t\t\t\tname=path+pre+row+\"_\"+col+post+\".\"+extension"+"\n"
#		strScriptPy+="\t\t\t\ttmpnmcrop=nmcrop+row+\"-\"+col+\".\"+ext"+"\n"
#		if newmagick==1:
#			strScriptPy+="\t\t\t\tcmdcrop=\"magick \"+name+\" -crop \"+cropW+\"x\"+cropH+\"+\"+cropX+\"+\"+cropY+\" +repage \"+tmpnmcrop"+"\n"
#			strScriptPy+="\t\t\t\t#cmdcrop=\"convert \"+name+\" -crop \"+cropW+\"x\"+cropH+\"+\"+cropX+\"+\"+cropY+\" +repage \"+tmpnmcrop"+"\n"
#		else:
#			strScriptPy+="\t\t\t\t#cmdcrop=\"magick \"+name+\" -crop \"+cropW+\"x\"+cropH+\"+\"+cropX+\"+\"+cropY+\" +repage \"+tmpnmcrop"+"\n"
#			strScriptPy+="\t\t\t\tcmdcrop=\"convert \"+name+\" -crop \"+cropW+\"x\"+cropH+\"+\"+cropX+\"+\"+cropY+\" +repage \"+tmpnmcrop"+"\n"
#		strScriptPy+="\t\t\t\tprint(\"crop \"+row+\"-\"+col)"+"\n"
#		strScriptPy+="\t\t\t\tsubprocess.call(cmdcrop, shell=True)"+"\n"
##		strScriptPy+="\t\t\t\timg[0]=tmpnmcrop"+"\n"
#		strScriptPy+="\t\t\t\tstrImgCropped+=tmpnmcrop+\" \""+"\n"
#		strScriptPy+="\t\t\telse:"+"\n"
#		strScriptPy+="\t\t\t\trow=str(img[4])"+"\n"
#		strScriptPy+="\t\t\t\tcol=str(img[5])"+"\n"
#		strScriptPy+="\t\t\t\tstrImgCropped+=(path+pre+row+\"_\"+col+post+\".\"+extension)+\" \""+"\n"
#		strScriptPy+="\t\t\t\text=img[6]"+"\n"
#		strScriptPy+="\t"+"\n"
#		strScriptPy+="\t\ttmprownm=str(nmrow)+str(nrow)+\".\"+str(ext)"+"\n"
#		strScriptPy+="\t\tstrImgRow+=tmprownm+\" \""+"\n"
#		if newmagick==1:
#			strScriptPy+="\t\tcmdAppRow = \"magick  \"+strImgCropped+\"  +append +repage \"+tmprownm"+"\n"
#			strScriptPy+="\t\t#cmdAppRow = \"convert  \"+strImgCropped+\"  +append +repage \"+tmprownm"+"\n"
#		else:
#			strScriptPy+="\t\t#cmdAppRow = \"magick  \"+strImgCropped+\"  +append +repage \"+tmprownm"+"\n"
#			strScriptPy+="\t\tcmdAppRow = \"convert  \"+strImgCropped+\"  +append +repage \"+tmprownm"+"\n"
#		strScriptPy+="\t\tprint(\"append row \"+str(nrow))"+"\n"
#		strScriptPy+="\t\tsubprocess.call(cmdAppRow, shell=True)"+"\n"
#		strScriptPy+="\t\tnrow=nrow+1"+"\n"
#		strScriptPy+="\t"+"\n"
#		if newmagick==1:
#			strScriptPy+="\tcmdAppAll = \"magick  \"+strImgRow+\"  -append +repage \"+finalImg"+"\n"
#			strScriptPy+="\t#cmdAppAll = \"convert  \"+strImgRow+\"  -append +repage \"+finalImg"+"\n"
#		else:
#			strScriptPy+="\t#cmdAppAll = \"magick  \"+strImgRow+\"  -append +repage \"+finalImg"+"\n"
#			strScriptPy+="\tcmdAppAll = \"convert  \"+strImgRow+\"  -append +repage \"+finalImg"+"\n"
#		strScriptPy+="\tprint(\"append all\")"+"\n"
#		strScriptPy+="\tsubprocess.call(cmdAppAll, shell=True)"+"\n"
##		strScriptPy+="\tarrayImg=[]"+"\n"
#		strScriptPy+="\n"
#		strScriptPy+="\n"
		
		strScriptPy+="def IMcropJoinImages(path,pre,post,extension):"+"\n"
		strScriptPy+="\tprint(\"IMcropJoinImages\")"+"\n"
		strScriptPy+="\tglobal arrayImg"+"\n"
		strScriptPy+="\tnmcrop=\"__crop__\""+"\n"
		strScriptPy+="\tnmrow=\"__row__\""+"\n"
		strScriptPy+="\tcmdcrop=\"\""+"\n"
		strScriptPy+="\tnrow=0"+"\n"
		strScriptPy+="\text=\"\""+"\n"
		strScriptPy+="\tarImgCropped=[]"+"\n"
		strScriptPy+="\ttmprownm=\"\""+"\n"
		strScriptPy+="\tarImgRow=[]"+"\n"
		strScriptPy+="\tfinalImg=path+pre+post+\"_joined\"+\".\"+extension"+"\n"
		strScriptPy+="\t"+"\n"
		strScriptPy+="\tfor arRow in arrayImg:"+"\n"
		strScriptPy+="\t\tarImgCropped=[]"+"\n"
		strScriptPy+="\t\ttmpnmcrop=\"\""+"\n"
		strScriptPy+="\t\tfor img in arRow:"+"\n"
		strScriptPy+="\t\t\tif img[7]==True:"+"\n"
		strScriptPy+="\t\t\t\tcropW=str(img[0])"+"\n"
		strScriptPy+="\t\t\t\tcropH=str(img[1])"+"\n"
		strScriptPy+="\t\t\t\tcropX=str(img[2])"+"\n"
		strScriptPy+="\t\t\t\tcropY=str(img[3])"+"\n"
		strScriptPy+="\t\t\t\trow=str(img[4])"+"\n"
		strScriptPy+="\t\t\t\tcol=str(img[5])"+"\n"
		strScriptPy+="\t\t\t\text=img[6]"+"\n"
		strScriptPy+="\t\t\t\tname=path+pre+row+\"_\"+col+post+\".\"+extension"+"\n"
		strScriptPy+="\t\t\t\ttmpnmcrop=nmcrop+row+\"-\"+col+\".\"+ext"+"\n"
		strScriptPy+="\t\t\t\tcmdcrop=\"convert \"+name+\" -crop \"+cropW+\"x\"+cropH+\"+\"+cropX+\"+\"+cropY+\" +repage \"+tmpnmcrop"+"\n"
		strScriptPy+="\t\t\t\tprint(\"crop \"+row+\"-\"+col)"+"\n"
		strScriptPy+="\t\t\t\tsubprocess.call(cmdcrop, shell=True)"+"\n"
		strScriptPy+="\t\t\t\tarImgCropped.append(tmpnmcrop)"+"\n"
		strScriptPy+="\t\t\telse:"+"\n"
		strScriptPy+="\t\t\t\trow=str(img[4])"+"\n"
		strScriptPy+="\t\t\t\tcol=str(img[5])"+"\n"
		strScriptPy+="\t\t\t\text=img[6]"+"\n"
		strScriptPy+="\t\t\t\tname=path+pre+row+\"_\"+col+post+\".\"+extension"+"\n"
		strScriptPy+="\t\t\t\tarImgCropped.append(name)"+"\n"
		strScriptPy+="\t"+"\n"
		strScriptPy+="\t\ttmprownm=str(nmrow)+str(nrow)+\".\"+str(ext)"+"\n"
		strScriptPy+="\t\tarImgRow.append(tmprownm)"+"\n"
		strScriptPy+="\t\tcmdAppRow = \"convert \""+"\n"
		strScriptPy+="\t\tfor im in arImgCropped:"+"\n"
		strScriptPy+="\t\t\tcmdAppRow+=im+\" \""+"\n"
		strScriptPy+="\t\tcmdAppRow+= \"  +append +repage \"+tmprownm"+"\n"
		strScriptPy+="\t\tprint(\"append row \"+str(nrow))"+"\n"
		strScriptPy+="\t\tsubprocess.call(cmdAppRow, shell=True)"+"\n"
		strScriptPy+="\t\tnrow=nrow+1"+"\n"
		strScriptPy+="\t\tif(tmpnmcrop!=\"\"):"+"\n"
		strScriptPy+="\t\t\t#delete cropped images"+"\n"
		strScriptPy+="\t\t\tprint(\"delete cropped images\")"+"\n"
		strScriptPy+="\t\t\tfor im in arImgCropped:"+"\n"
		strScriptPy+="\t\t\t\tos.remove(im)"+"\n"
		strScriptPy+="\t\t"+"\n"
		strScriptPy+="\tcmdAppAll = \"convert  \""+"\n"
		strScriptPy+="\tfor im in arImgRow:"+"\n"
		strScriptPy+="\t\tcmdAppAll+=(im+\" \")"+"\n"
		strScriptPy+="\tcmdAppAll+=\"  -append +repage \"+finalImg"+"\n"
		strScriptPy+="\tprint(\"append all\")"+"\n"
		strScriptPy+="\tsubprocess.call(cmdAppAll, shell=True)"+"\n"
		strScriptPy+="\t#delete rows images"+"\n"
		strScriptPy+="\tprint(\"delete rows images\")"+"\n"
		strScriptPy+="\tfor im in arImgRow:"+"\n"
		strScriptPy+="\t\tos.remove(im)"+"\n"
		strScriptPy+=""+"\n"
		
		#main render image
		outputFolderAbs=os.path.split( bpy.path.abspath(rnd.filepath) )[0]
		el=self.allRegions[0]
#		imgPre=outputFolderAbs + os.path.sep + el.baseNameNoExtScript
		imgPre=el.baseNameNoExtScriptGen
		cf=el.frame
		new_nframe = f'{cf:0{3}d}'
		name = imgPre.replace("###", str(new_nframe))
#		name += "."+imgExtension
		name += "_"
		
		strScriptPy+="path=r\""+outputFolderAbs+"/\""+"\n"
		strScriptPy+="\n"
		###############################################
		##start join main render
		###############################################
		strScriptPy+="print(\""+name+"\")"+"\n"
#		strScriptPy+="cropJoinImages(path,\""+name+"\",\"\",\""+imgExtension+"\")"+"\n"
		strScriptPy+="if(oiioOK==True):"+"\n"
		strScriptPy+="\toiioJoinImages(path,\""+name+"\",\"\",\""+imgExtension+"\")"+"\n"
		strScriptPy+="elif(pilOK==True):"+"\n"
		strScriptPy+="\tPILcropJoinImages(path,\""+name+"\",\"\",\""+imgExtension+"\")"+"\n"
		strScriptPy+="else:"+"\n"
		strScriptPy+="\tIMcropJoinImages(path,\""+name+"\",\"\",\""+imgExtension+"\")"+"\n"
		###############################################
		##end join main render
		###############################################
		strScriptPy+="\n"
		###############################################
		##start join compositor file output
		###############################################
#		print("*********************")
#		el.printAllProp()
		new_nframeFileout = f'{cf:0{4}d}'
		tmpFileOut=""
		outputFolderAbsFO=""
		if(scn.node_tree!=None):
			for xfo in scn.node_tree.nodes:
				if (xfo.type=='OUTPUT_FILE' and xfo.mute==False):
					tempslotcount=len(xfo.file_slots)
#					print(str(xfo.base_path))
					outputFolderAbsFO=os.path.split( bpy.path.abspath(xfo.base_path) )[0]
#					outputFolderAbsFO+="/"
#					print(str(outputFolderAbsFO))
					strScriptPy+="path=r\""+str(outputFolderAbsFO)+"/\""+"\n"
					for xSlot in range(tempslotcount):
						if (xfo.inputs[xSlot].is_linked==True):
							tmpFileOut = str( str(xfo.file_slots[xSlot].path) + str(el.cols) + "x" + str(el.rows) + "_" )
							strScriptPy+="print(\"" + tmpFileOut + "\")"+"\n"
#							strScriptPy+="cropJoinImages(path,\""+tmpFileOut+"\",\"_"+str(new_nframeFileout)+"\",\""+imgExtension+"\")"+"\n"
							strScriptPy+="if(oiioOK==True):"+"\n"
							strScriptPy+="\toiioJoinImages(path,\""+tmpFileOut+"\",\"_"+str(new_nframeFileout)+"\",\""+imgExtension+"\")"+"\n"
							strScriptPy+="elif(pilOK==True):"+"\n"
							strScriptPy+="\tPILcropJoinImages(path,\""+tmpFileOut+"\",\"_"+str(new_nframeFileout)+"\",\""+imgExtension+"\")"+"\n"
							strScriptPy+="else:"+"\n"
							strScriptPy+="\tIMcropJoinImages(path,\""+tmpFileOut+"\",\"_"+str(new_nframeFileout)+"\",\""+imgExtension+"\")"+"\n"
							strScriptPy+="\n"
#		print("*********************")
		#print("fileout_4x4_")
		#cropJoinImages(path,"fileout_4x4_","_0000","png")
		###############################################
		##end join compositor file output
		###############################################
		#print("fileout_4x4_")
		#cropJoinImages(path,"fileout_4x4_","_0000","png")		
		
		strScriptPy+="print(\"append done\")"+"\n"
		strScriptPy+="\n"
		strScriptPy+="\n"


		###############################################
		##write python file
		###############################################
		#nome del file python
		blendName= bpy.path.basename(bpy.context.blend_data.filepath).split(".")[0]
		
#		filePython=outputFolderAbs+os.path.sep+blendName+".py"
		#add frame
		filePython=outputFolderAbs+os.path.sep+blendName+"_"+str(new_nframe)+".py"
		
		with open(filePython, 'w') as file:
			file.write(strScriptPy)
			file.close()

		ps.RR_msg1="created "+filePython
		return filePython

	def modal(self, context, event):
		if event.type == 'TIMER':
			self.control=self.control+1
			scn = context.scene
			rnd = scn.render
			ps = scn.renderregionsettings
#			print("////////////////////////////event "+str(self.control))
#			print("stop        -- "+str(self.stop))
#			print("finished    -- "+str(self.finished))
#			print("rendering   -- "+str(self.rendering))
#			print("RR_renderGo -- "+str(ps.RR_renderGo))
#			print("render_ready-- "+str(self.render_ready))
#			print("timer")
			
			if self.stop==True or ps.RR_renderGo==False:
				self.remove_handlers(context)
				ps.RR_msg1=""
#				ps.RR_msg2=""
				ps.RR_renderGo=False
				print("****CANCELLED stop or stopped")
				return {"CANCELLED"}


			if self.finished==True or len(self.arrayRegion)<1:
				self.remove_handlers(context)
				ps.RR_msg1=""
#				ps.RR_msg2=""
				ps.RR_renderGo=False
				print("****finished or empty array")
				return {"FINISHED"}
			
			if self.rendering==False: # Nothing is currently rendering.
				if self.render_ready==False:
#					print("****")
					setrnd=self.setRender(context)
#					if self.setRender(context)==1:
					if setrnd==1:
						self.render_ready=True
						print("to render: "+self.region_name)
						bpy.ops.render.render("INVOKE_DEFAULT", write_still=True)
					elif setrnd==0:
						self.remove_handlers(context)
						self.finished=True
						ps.RR_msg1=""
#						ps.RR_msg2=""
						ps.RR_renderGo=False
						self.saveFileOutputs=[]
						print("****************** finish")
						
						return {"FINISHED"}
					else:
						print("not to render")
						tempRegionData=[]
#						print("loop from "+str(ps.RR_cntrnd-1)+ " to "+str(len(self.allRegions)-1))
						for cnt in range((ps.RR_cntrnd-1), (len(self.allRegions)-1)):
							tempRegionData=self.allRegions[cnt]
							if (tempRegionData.render==True):
#								print("found region to render: "+str(cnt))
								ps.RR_cntrnd=cnt
								break
						else:
							ps.RR_cntrnd=(len(self.allRegions))
							print("no other render to do - "+str(ps.RR_cntrnd))
###						#

###						#se si
###							#si incrementa il contatore e si controlla anche il successivo ecc...
###						#per evitare di aspettare troppo se ci sono molte regioni sa non fare
				else:
					print("to render 2: "+self.region_name)
					bpy.ops.render.render("INVOKE_DEFAULT", write_still=True)
		
		return {"PASS_THROUGH"}


class Region:
	index=-1
	outImg=""
	regionName=""
	baseName=""
	baseNameNoExt=""
	baseNameNoExtScript=""
	baseNameNoExtScriptGen=""
	fullName=""
	rows=0
	cols=0
	nrow=0
	ncol=0
	frame=0
	render=False
	minx=0
	maxx=0
	miny=0
	maxy=0
	def __init__(self, minx=0,miny=0,maxx=0,maxy=0):
		self.minx = minx
		self.miny = miny
		self.maxx = maxx
		self.maxy = maxy
	def printAllProp(self):
		print("----")
		print("index",self.index)
		print("outImg",self.outImg)
		print("baseName",self.baseName)
		print("baseNameNoExt",self.baseNameNoExt)
		print("baseNameNoExtScript",self.baseNameNoExtScript)
		print("baseNameNoExtScriptGen",self.baseNameNoExtScriptGen)
		print("fullName",self.fullName)
		print("rows",self.rows)
		print("cols",self.cols)
		print("nrow",self.nrow)
		print("ncol",self.ncol)
		print("frame",self.frame)
		print("render",self.render)
		print("minx",self.minx)
		print("maxx",self.maxx)
		print("miny",self.miny)
		print("maxy",self.maxy)
		print("----")
	def getObject(self):
		tmpOb={
			"minx":self.minx,
			"miny":self.miy,
			"maxx":self.maxx,
			"maxy":self.maxy
		}
		return tmpOb

#def checkoiio_update(self, context):
#	addon_prefs = context.preferences.addons[__package__].preferences
#	global oiioOK
#	oiioOK=addon_prefs.checkOpenImageIO

#class ControlRenderRegionPreferences(AddonPreferences):
#	bl_idname = __package__
#	checkOpenImageIO: BoolProperty(
#		name="Check python module OpenImageIO",
#		description="Check for the module 'OpenImageIO' when creating the reference image and python scripts. OpenImageIO is faster and supports openEXR multilayer, ImageMagick doesn't support openEXR multilayer but is easier to install",
#		default=True,
#		update=checkoiio_update)

#	def draw(self, context):
#		layout = self.layout
#		col = layout.column()
#		col.label(text="Show options")
#		flow = col.grid_flow(columns=0, even_columns=True, even_rows=False, align=False)
#		flow.prop(self, "checkOpenImageIO")

classes = (
	RenderRegions,
	RenderRegionSettings,
	RENDER_PT_Region,
	RenderStop,
	MarginCalculate,
	CreateReferenceImage,
	testVar
	)


	
def register():
	from bpy.utils import register_class
	for cls in classes:
		register_class(cls)
	
	bpy.types.Scene.renderregionsettings = PointerProperty(type=RenderRegionSettings)
#	bpy.app.handlers.frame_change_pre.append(nr_animation_update)
#	bpy.types.Scene.compmarglistW = bpy.props.CollectionProperty(
#		type=bpy.types.PropertyGroup
#	)


def unregister():
	from bpy.utils import unregister_class

	del bpy.types.Scene.renderregionsettings
#	bpy.utils.unregister_class(RenderRegions)	
	for cls in classes:
		unregister_class(cls)
	
#	bpy.app.handlers.frame_change_pre.remove(nr_animation_update)


if __name__ == "__main__":
	register()
