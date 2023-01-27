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


bl_info = {
	'name': 'Control Render Regions',
	'author': 'nukkio',
	'version': (0,1),
	'blender': (3, 0, 0),
	'location': 'Render > Render Regions',
	'description': 'Manage renders in region',
	'wiki_url': '',
	'tracker_url': '',
	'category': 'Render'}


import bpy
import os,subprocess
import math
from bpy.types import Panel, Operator, Scene, PropertyGroup
from bpy.props import (
						BoolProperty,
						IntProperty,
						FloatProperty,
						StringProperty,
						EnumProperty,
						PointerProperty,
					)
from bpy.app.handlers import render_pre, render_post, render_cancel
from bpy.app import driver_namespace

#from bpy.app.handlers import persistent, frame_change_pre

#		FloatVectorProperty,
#		IntVectorProperty,

#scn = bpy.types.Scene

handler_key = "DEV_FUNC_HKRR"

#@persistent 
#def nr_animation_update(scn):
#	""" Function for updating the effects when the scene update """    
#	print("-----------------------------------------")
##	scn = context.scene
#	ps = scn.renderregionsettings
#	print(str(ps.RR_renderGo))

class RenderRegionSettings(PropertyGroup):

	def method_update(self,context):
		print("method_update")
		print(str(self.RR_method))
#		print(str(self.RR_rowscols))
#		print(str(self.RR_dim_region))
		if self.RR_method=="DIVIDE":
			self.RR_rowscols=True
			self.RR_dim_region=False
		else:
			self.RR_rowscols=False
			self.RR_dim_region=True
	
	def checkColsRows(self,context):
		print("checkColsRows")
		delta_x=0
		delta_y=0
		resx=context.scene.render.resolution_x
		resy=context.scene.render.resolution_y
#		tot_reg=0
#		num_cols=0
#		num_rows=0
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
			
#			print(delta_x)
#			print(delta_y)
#			print(count_decimal_x)
#			print(count_decimal_y)

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
#		description = "Use render dimension for each region",
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

	RR_save_region:BoolProperty(
		name = "Join and save",
		description = "Join and save the regions",
		default = False)
	
	RR_activeRendername:StringProperty(
		name = "RR_activeRendername",
		description = "The name of the active rendered image",
		default = "")
	
	RR_msg1:StringProperty(
		name = "RR_msg1",
		description = "msg1",
		default = "")
	RR_msg2:StringProperty(
		name = "RR_msg2",
		description = "msg2",
		default = "")
		
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
		name="Create bash script for render from command line",
		default=False,
		description="Create bash script",
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
		row1 = layout.row(align=True)
		rowList.append(row1)
		row2 = layout.row(align=True)
		rowList.append(row2)
		row3 = layout.row(align=True)
		rowList.append(row3)
		row4 = layout.row(align=True)
		rowList.append(row4)
		row5 = layout.row(align=True)
		rowList.append(row5)
		row6 = layout.row(align=True)
		rowList.append(row6)
		row7 = layout.row(align=True)
		rowList.append(row7)
		row8 = layout.row(align=True)
		rowList.append(row8)
		row9 = layout.row(align=True)
		rowList.append(row9)

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
		rowList[rn].label(text=ps.RR_msg1)
		rn+=1
		rowList[rn].label(text=ps.RR_msg2)
		rn+=1
#		rowList[rn].operator("rr.test", text="test var", icon="CANCEL")
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
#		print(str(bpy.app.binary_path))

#		executable path
#		bpy.app.binary_path
#		/home/ernes3/Programs/blender/blender

#		path progetto
#		bpy.data.filepath
#		#/media/dati_1tb/lavoro/blender_addon/renderregion/test-renderegion.blend

#		path render
#		ps.RR_activeRendername=self.outputFolder + os.path.sep + self.region_name
		
#		print("*******")
		ar=AreaRegion()
		ar.minx=44
#		print(str(ar.getObject()))
		ar2 = {"x1":1,"x2":2,"y1":3,"y2":4}
		ar2['x1']=33
#		print(str(ar2))
#		 bpy.data.texts.new(
#		return{'CANCELLED'}
		return {'FINISHED'}

class RenderObject:
	def __init__(self, regionarea=0, imageName="", resolution=0, resolutionPercent=0, usecrop=False,currframe=0):
		self.regionarea=regionarea
		self.imageName=imageName
		self.resolution=resolution
		self.resolutionPercent=resolutionPercent
		self.usecrop=usecrop
		self.currframe=currframe
	def getObject(self):
		tmpOb={
			"regionarea":self.regionarea,
			"imageName":self.imageName,
			"resolution":self.resolution,
			"resolutionPercent":self.resolutionPercent,
			"usecrop":self.usecrop,
			"currframe":self.currframe
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
	

	
	def pre(self, scene, context=None):
#		print("event PRE")
		self.rendering = True
		scene.renderregionsettings.RR_msg1="render "+str(scene.renderregionsettings.RR_cntrnd)+"/"+str(scene.renderregionsettings.RR_maxrnd)
		scene.renderregionsettings.RR_msg2="rendering :"+scene.renderregionsettings.RR_activeRendername

	def post(self, scene, context=None):
		self.rendering = False
		self.render_ready=False
#		print("event POST---------------"+str(self.rendering))
		scene.renderregionsettings.RR_msg2="rendered :"+scene.renderregionsettings.RR_activeRendername
		#scene.renderregionsettings.RR_renderGo=False

#		print("**************end")
		for x in self.saveFileOutputs:
			tempNodeFO=scene.node_tree.nodes[str(x[0])]
#			tmpn=0
#			for xSlot in tempNodeFO.file_slots:
#				xSlot.path=str(x[tmpn+1])
#				tmpn=tmpn+1
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

		self._timer = context.window_manager.event_timer_add(2, window=context.window)
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
		for el in self.arrayRegion:
			tmpOb=RenderObject()
			ret_regionArea=0
			ret_resolutionPercent=0
			ret_resolution=0
			ret_imageName=""
			ret_usecrop=False
			pos_row=int(el/self.num_cols)
			pos_col=int( ( el - ( pos_row*self.num_cols) ) )
			
#			rnd.border_min_x=self.min_x+(self.delta_x*pos_col)
#			rnd.border_max_x=self.max_x+(self.delta_x*pos_col)
#			rnd.border_min_y=self.min_y+(self.delta_y*pos_row)
#			rnd.border_max_y=self.max_y+(self.delta_y*pos_row)

#			rnd.border_min_y=self.min_y+(self.delta_y*pos_row)
#			rnd.border_max_y=self.max_y+(self.delta_y*pos_row)
			border_min_x=self.min_x+(self.delta_x*pos_col)
			border_max_x=self.max_x+(self.delta_x*pos_col)
			border_min_y=self.min_y+(self.delta_y*pos_row)
			border_max_y=self.max_y+(self.delta_y*pos_row)
			
#			print("**")
#			print(self.delta_y)#0.5
#			print(self.num_rows)#2
#			print(pos_row)#0
#			print("**")
			#0.0 1.5 0.5 1.0 
			#0.0 1.0 0.5 0.5 
			
			border_min_y=(self.delta_y*self.num_rows)- ((pos_row)*self.delta_y)
			border_max_y=(self.delta_y*self.num_rows)- ((pos_row+1)*self.delta_y)
			
#			rnd.border_min_x=border_min_x
#			rnd.border_min_y=border_max_y
#			rnd.border_max_x=border_max_x
#			rnd.border_max_y=border_min_y

			ret_regionArea = AreaRegion(
				border_min_x,
				border_max_y,
				border_max_x,
				border_min_y
				)
#			ret_regionArea = {
#				"minx":self.min_x+(self.delta_x*pos_col),
#				"miny":self.min_y+(self.delta_y*pos_row),
#				"maxx":self.max_x+(self.delta_x*pos_col),
#				"maxy":self.max_y+(self.delta_y*pos_row)
#			}

#			n_row = f'{pos_row:05d}'
#			n_col = f'{pos_col:05d}'
			
#			n_row = f'{pos_row:03d}'
#			n_col = f'{pos_col:03d}'
			decCol=math.ceil(math.log(self.num_cols,10))
			decRows=math.ceil(math.log(self.num_rows,10))
			dec=max(decCol,decRows)
			n_row = f'{pos_row:0{dec}d}'
			n_col = f'{pos_col:0{dec}d}'

#			nome della regione: colonnexrighe riga colonna
#			tempRegionName = str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_row + "_" + n_col + "_###"
			tempRegionName = "###_" + str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_row + "_" + n_col

#			self.region_name = self.outputImgName +"_"+str(self.num_rows)+"x"+str(self.num_cols) + "_" + n_row + "_" + n_col + rnd.file_extension
##			self.region_name = self.outputImgName +"_"+str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_row + "_" + n_col
#			self.region_name = self.outputImgName +"_"+str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_col + "_" + n_row
			
			#forse non corretto ma si ordinano bene le immagini
#			self.region_name = self.outputImgName +"_"+str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_row + "_" + n_col# + rnd.file_extension
			self.region_name = self.outputImgName +"_"+tempRegionName# + rnd.file_extension

#			#forse corretto ma non si ordinano bene le immagini
#			self.region_name = self.outputImgName +"_"+str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_col + "_" + n_row# + rnd.file_extension

			ret_imageName=self.outputFolderAbs + os.path.sep + self.region_name
			
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
			tmpOb.nrow=pos_row
			tmpOb.ncol=pos_col
			
#			current_scene = bpy.context.scene
			current_frame = scn.frame_current
#			current_frame = bpy.data.scenes[0].frame_current
			tmpOb.currframe=current_frame
			
			arObRegions.append(tmpOb)
		
#		print("----")
#		print(str(len(arObRegions)))
#		print("++++")
		
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
		

		
		strScript=""

		strScript+="#! /bin/bash"+"\n"
		strScript+=""+"\n"
		strScript+="mainPath=\""+mainPath+"\""+"\n"
#		strScript+="file=\""+filepath+"\""+"\n"
		strScript+="file=$mainPath\""+fileName+"\""+"\n"
		strScript+="blenderPath="+blenderPath+""+"\n"
		
		strScript+="\n"
		
		strScript+="msg()"+"\n"
		strScript+="{"+"\n"
		strScript+="msg=$1"+"\n"
		strScript+="nomelog=$2"+"\n"
		strScript+="datamsg=$(date +\"%Y%m%d_%H-%M\")"+"\n"
		strScript+="#telegram-send \"$datarender - $datamsg - render $1\""+"\n"
		strScript+="echo \"$datarender - $datamsg - render $1\""+"\n"
		strScript+="}"+"\n"
		
		strScript+="renderregion()"+"\n"
		strScript+="{"+"\n"
		strScript+="pyname=$1"+"\n"
		strScript+="imageName=$2"+"\n"
		strScript+="frame=$3"+"\n"
		strScript+="$blenderPath -b \"$file\" -x 1 -o \"$imageName\" -P $pyname -f $frame"+"\n"
		strScript+="}"+"\n"
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
		strScript+="if test -f \"$pyfile\"; then"+"\n"
		strScript+="    echo \"$pyfile exists.\""+"\n"
		strScript+="    rm $pyfile"+"\n"
		strScript+="fi"+"\n"
		strScript+="echo \"$pyfile\""+"\n"
		strScript+="touch $pyfile"+"\n"
		strScript+="echo \"import bpy\" >> $pyfile"+"\n"
		strScript+="echo \"scn = bpy.context.scene\" >> $pyfile"+"\n"
		strScript+="echo \"rnd = scn.render\" >> $pyfile"+"\n"
		strScript+="echo \"def setRender():\" >> $pyfile"+"\n"
		strScript+="echo \"    rnd.border_min_x=\"$minx >> $pyfile"+"\n"
		strScript+="echo \"    rnd.border_min_y=\"$miny >> $pyfile"+"\n"
		strScript+="echo \"    rnd.border_max_x=\"$maxx >> $pyfile"+"\n"
		strScript+="echo \"    rnd.border_max_y=\"$maxy >> $pyfile"+"\n"
		strScript+="echo \"    rnd.filepath='\"$imageName\"'\" >> $pyfile"+"\n"
		strScript+="echo \"    rnd.resolution_percentage=\"$resolutionPercent >> $pyfile"+"\n"
		strScript+="echo \"    rnd.use_crop_to_border = \"$usecrop >> $pyfile"+"\n"
		strScript+="echo \"\" >> $pyfile"+"\n"
		strScript+="echo \"setRender()\" >> $pyfile"+"\n"
		strScript+="echo \"\" >> $pyfile"+"\n"
		strScript+="echo \"scn.frame_set(\"$curframe\")\" >> $pyfile"+"\n"
		strScript+="echo \"scn.frame_current = \"$curframe >> $pyfile"+"\n"
		strScript+="echo \"scn.render.use_overwrite=True\" >> $pyfile"+"\n"
		strScript+="echo \"\" >> $pyfile"+"\n"
		strScript+="renderregion $pyfile $imageName $curframe"+"\n"
		strScript+="}"+"\n"
		strScript+="pythonName=\"renderscriptRRegion\""+"\n"
		strScript+="pyfile=$mainPath$pythonName\".py\""+"\n"
		strScript+=""+"\n"
		strScript+=""+"\n"
		if (ps.RR_who_region=="all"):
			strScript+="arrayImgNamesPerRow=()"+"\n"
			strScript+="strRowNames=()"+"\n"
			strScript+="tmpImgNamesPerRow=\"\""+"\n"
		strScript+=""+"\n"
#		bpy.data.texts.new("ciao.py")
		tmprow=0
#		for ireg in range(0,len(arObRegions)):
		for ireg in arObRegions:
#			print(str(ireg.getObject()))
			#startrender 0.5 0.0 1.0 0.5 '/media/dati_1tb/lavoro/blender_addon/renderregion/render/tmp_2x2_00000_00001_####' 0 100 True 1
			
			strScript+="tmpImgName=\""+ireg.imageName+"\""+"\n"
####			in ireg.imageName c'è l'indicazione del frame (###)
####			che blender vuole mettere da qualche parte
####			quando si registrano i nomi delle immagini
####			per costruire poi le righe e l'immagine finale
####			si deve sostituire ### col frame
			imgPre=ireg.imageName
			cf=ireg.currframe
			new_nframe = f'{cf:0{3}d}'
			imgPost = imgPre.replace("###", str(new_nframe))
			strScript+="tmpImgNameFrm=\""+imgPost+"\""+"\n"
			
			if (ps.RR_who_region=="all"):
				if (tmprow!=ireg.nrow):
					strScript+="arrayImgNamesPerRow+=(\"$tmpImgNamesPerRow\")"+"\n"
#					strScript+="tmpImgNamesPerRow=\"\""+"\n"
					strScript+="tmpImgNamesPerRow=\"$tmpImgNameFrm\"\"."+imgExtension+" \"\n"
					tmprow=ireg.nrow
				else:
					strScript+="tmpImgNamesPerRow+=\"$tmpImgNameFrm\"\"."+imgExtension+" \"\n"
					
			strScript+="startrender "
			strScript+=str(ireg.regionarea.minx)+" "
			strScript+=str(ireg.regionarea.miny)+" "
			strScript+=str(ireg.regionarea.maxx)+" "
			strScript+=str(ireg.regionarea.maxy)+" "
#			strScript+=ireg.imageName+"_### "
#			strScript+=ireg.imageName+" "
			strScript+="\"$tmpImgName\" "
			strScript+=str(ireg.resolution)+" "
			strScript+=str(ireg.resolutionPercent)+" "
			strScript+=str(ireg.usecrop)+" "
			strScript+=str(ireg.currframe)+" "
			
			
			strScript+="\n"
			strScript+="msg \"ok "+str(ireg.nrow)+" "+str(ireg.ncol)+"\""+"\n"
			strScript+="\n"
		
		if (ps.RR_who_region=="all"):
				strScript+="arrayImgNamesPerRow+=(\"$tmpImgNamesPerRow\")"+"\n"
		
#		bpy.data.texts['ciao.py'].write(strScript)
		
		#parte unione immagini
		#solo se "all"
		if (ps.RR_who_region=="all"):
						#rows cycle
			strScript+="rowname=\"row_\""+"\n"
			strScript+="length=${#arrayImgNamesPerRow[@]}"+"\n"
			strScript+="\n"
			
			strScript+="echo \"loop for ${length} rows\""+"\n"
			strScript+="for (( j=0; j<length; j++ ));"+"\n"
			strScript+="do"+"\n"
#			strScript+="\t"+"tmpImgName=\"$rowname%d\"\"."+imgExtension+"\" $j"+"\n"
			strScript+="\t"+"tmpImgName=\"$rowname$j\"\"."+imgExtension+"\""+"\n"
			strScript+="\t"+"strRowNames+=$tmpImgName\" \""+"\n"
#			strScript+="\t"+"convert \( \"%s\" \) +append \"$tmpImgName\" \"${arrayImgNamesPerRow[$j]}\""+"\n"
			strScript+="\t"+"convert \( ${arrayImgNamesPerRow[$j]} \) +append \"$tmpImgName\""+"\n"
			strScript+="done"+"\n"
			strScript+="\n"
			strScript+="\n"
			strScript+="echo \"create final image\""+"\n"
			strScript+="convert \( $strRowNames \) -append \""+ self.outputFolderAbs + os.path.sep + self.outputImgName +"."+ imgExtension+"\""
			strScript+="\n"
			strScript+="echo \"delete temp file\""+"\n"
			strScript+="rm $strRowNames"+"\n"
			strScript+="\n"
		strScript+="\n"
		strScript+="echo \"done\"\n"
		strScript+="\n"
			

		#nome del file blend
		blendName= bpy.path.basename(bpy.context.blend_data.filepath).split(".")[0]
#		
		fileScript=self.outputFolderAbs+ os.path.sep+blendName+".sh"
#		fileScript="/media/dati_1tb/lavoro/blender_addon/renderregion/render/renderShell.sh"
		
		with open(fileScript, 'w') as file:
			file.write(strScript)
			file.close()

#		saveFile = open(fileScript, "w")
#		saveFile.write(strScript)
#		saveFile.close()
		
		ps.RR_msg1="created "+fileScript
		##todo add timer to empty msg

		#{'regionarea': {'minx': 0.5, 'miny': 0.0, 'maxx': 1.0, 'maxy': 0.5}, 'imageName': '//render/tmp_2x2_00000_00001.png', 'resolution': 0, 'resolutionPercent': 100, 'usecrop': True}

		return('FINISHED')
		
	def setRender(self, context):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
		if ps.RR_cntrnd<len(self.arrayRegion):
			pos_row=int(self.arrayRegion[ps.RR_cntrnd]/self.num_cols)
			pos_col=int( ( self.arrayRegion[ps.RR_cntrnd] - ( pos_row*self.num_cols) ) )
			
#			rnd.border_min_x=self.min_x+(self.delta_x*pos_col)
#			rnd.border_max_x=self.max_x+(self.delta_x*pos_col)
#			rnd.border_min_y=self.min_y+(self.delta_y*pos_row)
#			rnd.border_max_y=self.max_y+(self.delta_y*pos_row)

			border_min_x=self.min_x+(self.delta_x*pos_col)
			border_max_x=self.max_x+(self.delta_x*pos_col)
			border_min_y=self.min_y+(self.delta_y*pos_row)
			border_max_y=self.max_y+(self.delta_y*pos_row)
			
			border_min_y=(self.delta_y*self.num_rows)- ((pos_row)*self.delta_y)
			border_max_y=(self.delta_y*self.num_rows)- ((pos_row+1)*self.delta_y)
			
#			print("**")
#			print(str(border_min_x))
#			print(str(border_min_y))
#			print(str(border_max_x))
#			print(str(border_max_y))
#			print("**")
			
			rnd.border_min_x=border_min_x
			rnd.border_min_y=border_max_y
			rnd.border_max_x=border_max_x
			rnd.border_max_y=border_min_y

#			n_row = f'{pos_row:05d}'
#			n_col = f'{pos_col:05d}'
#			n_row = f'{pos_row:03d}'
#			n_col = f'{pos_col:03d}'
			decCol=math.ceil(math.log(self.num_cols,10))
			decRows=math.ceil(math.log(self.num_rows,10))
			dec=max(decCol,decRows)
			n_row = f'{pos_row:0{dec}d}'
			n_col = f'{pos_col:0{dec}d}'
			
			
#			nome della regione: colonnexrighe riga colonna
			tempRegionName = str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_row + "_" + n_col
			
			#ciclo per cambiare i path nei fileoutput
			#alla fine del render dovrebbero essere rimessi a posto
#			print("****----****----****----****----")
			for x in self.saveFileOutputs:
				tempNodeFO=scn.node_tree.nodes[str(x[0])]
				tempslotcount=len(tempNodeFO.file_slots)
#				print("cambio fo= " + str(tempNodeFO) + " - slots=" + str(tempslotcount))
				for xSlot in range(tempslotcount):
					tempNodeFO.file_slots[xSlot].path=str(x[xSlot+1]) + tempRegionName + "_"
			#####################

#			self.region_name = self.outputImgName +"_"+str(self.num_rows)+"x"+str(self.num_cols) + "_" + n_row + "_" + n_col + rnd.file_extension

			#forse non corretto ma si ordinano bene le immagini
#			self.region_name = self.outputImgName +"_"+str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_row + "_" + n_col + rnd.file_extension
			self.region_name = self.outputImgName +"_"+tempRegionName + rnd.file_extension
			
#			scn.node_tree.nodes["File Output"].name
#			#ciclo per cambiare i path all'eventuale file output
#			for xfo in scn.node_tree.nodes:
#				if (xfo.type=="OUTPUT_FILE"):
#					old
#			C.scene.node_tree.nodes["File Output"].file_slots[0].path

#			#forse corretto ma non si ordinano bene le immagini
#			self.region_name = self.outputImgName +"_"+str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_col + "_" + n_row + rnd.file_extension

			ps.RR_activeRendername=self.outputFolder + os.path.sep + self.region_name
			
			rnd.filepath=ps.RR_activeRendername
			ps.RR_msg1="render "+str(ps.RR_cntrnd)+"/"+str(ps.RR_maxrnd)
			ps.RR_msg2="rendering :"+ps.RR_activeRendername
			
			if (ps.RR_dim_region==True):
				rnd.resolution_percentage=ps.RR_multiplier*100
				rnd.use_crop_to_border = 1
#				rnd.use_crop_to_border = 0
			ps.RR_cntrnd=ps.RR_cntrnd+1
			return True
		else:
			self.finished=True
			ps.RR_msg1=""
			ps.RR_msg2=""
			return False

	def execute(self, context):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
		
		self.stop = False
		self.rendering = False
		self.render_ready = False
		
		ps.RR_activeRendername=""
		ps.RR_msg1=""
		ps.RR_msg2=""
		ps.RR_cntrnd=0;
		ps.RR_maxrnd=0;
		
#		ps.RR_createScript=True
		
		file_name=os.path.splitext( os.path.split(bpy.data.filepath)[1])[0]
		self.outputFolderAbs=os.path.split( bpy.path.abspath(rnd.filepath) )[0]
		self.outputFolder=os.path.split( bpy.path.relpath(rnd.filepath) )[0]
		self.outputImgName=os.path.splitext(os.path.split( bpy.path.relpath(rnd.filepath) )[1])[0]
		ps.RR_oldoutputfilepath=rnd.filepath
		ps.RR_oldPerc=rnd.resolution_percentage
#		print(self.outputFolderAbs)
#		print(self.outputFolder)
		
#		print("ciclo cambio FileOutput........")
		self.saveFileOutputs=[]
		tempArrFO=[]
		#ciclo per cambiare i path all'eventuale file output
		if(scn.node_tree!=None):
			for xfo in scn.node_tree.nodes:
				if (xfo.type=="OUTPUT_FILE"):
					tempArrFO=[]
					tempArrFO.append(xfo.name)
	#				tempslotcount=len(xfo.file_slots)-1
	#				for xSlot in xfo.file_slots:
	#					oldFOpath=xSlot.path
	#					tempArrFO.append(oldFOpath)
					tempslotcount=len(xfo.file_slots)
	#				print("registro fo= " + str(xfo.name) + " - slots=" + str(tempslotcount))
					for xSlot in range(tempslotcount):
						oldFOpath=xfo.file_slots[xSlot].path
						tempArrFO.append(oldFOpath)
					self.saveFileOutputs.append(tempArrFO)
		
#		print("ciclo cambio FileOutput fine........")
				
		
#		C.scene.node_tree.nodes["File Output"].file_slots[0].path

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
		
		reg=[]
		errorInsertRegions=False
		
		if ps.RR_dim_region==False:
			self.tot_reg=ps.RR_reg_columns*ps.RR_reg_rows
			self.num_cols=ps.RR_reg_columns
			self.num_rows=ps.RR_reg_rows
		else:
			self.tot_reg=ps.RR_multiplier*ps.RR_multiplier
			self.num_cols=ps.RR_multiplier
			self.num_rows=ps.RR_multiplier

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
				reg=""
		elif "-" in ps.RR_who_region:
			control=ps.RR_who_region.replace('-','')
			if (control.isdigit()):
				reg_temp=ps.RR_who_region.split("-")
				for a in range(int(reg_temp[0]),int(reg_temp[1])+1):
					if int(reg_temp[a])<self.tot_reg:
						reg.append(int(reg_temp[a]))
					else:
						errorInsertRegions=True
			else:
				reg=""
		elif ps.RR_who_region.isdigit():
			if int(ps.RR_who_region)<self.tot_reg:
				reg.append(int(ps.RR_who_region))
			else:
				errorInsertRegions=True
		else:
			reg=""
		
		if errorInsertRegions==True:
			reg=""
			self.report({"ERROR"}, "Error adding regions, check values")
				
		if reg!="":
			self.arrayRegion=reg
			print ("Regions to render:")
			print (self.arrayRegion)
			ps.RR_maxrnd=len(self.arrayRegion)
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


			if self.stop==True or ps.RR_renderGo==False:
				self.remove_handlers(context)
				ps.RR_msg1=""
				ps.RR_msg2=""
				ps.RR_renderGo=False
				print("****CANCELLED stop or stopped")
				return {"CANCELLED"}


			if self.finished==True or len(self.arrayRegion)<1:
				self.remove_handlers(context)
				ps.RR_msg1=""
				ps.RR_msg2=""
				ps.RR_renderGo=False
				print("****finished or empty array")
				return {"FINISHED"}
			
			if self.rendering==False: # Nothing is currently rendering.
				if self.render_ready==False:
#					print("****")
					if self.setRender(context)==True:
						self.render_ready=True
						print("to render: "+self.region_name)
#						
						bpy.ops.render.render("INVOKE_DEFAULT", write_still=True)
#						bpy.ops.render.render(write_still=True)
#						print("bpy.ops.render.render: "+str(self.render_ready))
					else:
						self.remove_handlers(context)
						self.finished=True
						ps.RR_msg1=""
						ps.RR_msg2=""
						ps.RR_renderGo=False
						self.saveFileOutputs=[]
						print("****************** finish")
						
						return {"FINISHED"}
				else:
					print("to render 2: "+self.region_name)
					bpy.ops.render.render("INVOKE_DEFAULT", write_still=True)
		
		return {"PASS_THROUGH"}


classes = (
	RenderRegions,
	RenderRegionSettings,
	RENDER_PT_Region,
	RenderStop,
	testVar
	)

def register():
	from bpy.utils import register_class
	for cls in classes:
		register_class(cls)

	bpy.types.Scene.renderregionsettings = PointerProperty(type=RenderRegionSettings)
#	bpy.app.handlers.frame_change_pre.append(nr_animation_update)

def unregister():
	from bpy.utils import unregister_class

	del bpy.types.Scene.renderregionsettings
#	bpy.utils.unregister_class(RenderRegions)	
	for cls in classes:
		unregister_class(cls)
	
#	bpy.app.handlers.frame_change_pre.remove(nr_animation_update)


if __name__ == "__main__":
	register()

