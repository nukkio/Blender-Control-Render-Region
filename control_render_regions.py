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
from bpy.types import Panel, Operator, Scene, PropertyGroup, WindowManager
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
#from pprint import pprint

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
#		print("checkColsRows")
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
		name="Create bash and python script",
		default=False,
		description="Create bash script for render from command line and python script for join regions rendered",
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
	
#	RR_msgMargins:StringProperty(
#		name = "Margins message",
#		description = "Margins message",
#		default = "")
		

class RENDER_PT_Region(Panel):
	bl_label = "Render Region"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "output"
	
	def draw(self, context):
		layout = self.layout
		scn = context.scene
		ps = scn.renderregionsettings
		
#		rowList=[]
#		row1 = layout.row(align=True)
#		rowList.append(row1)
#		row2 = layout.row(align=True)
#		rowList.append(row2)
#		row3 = layout.row(align=True)
#		rowList.append(row3)
#		row4 = layout.row(align=True)
#		rowList.append(row4)
#		row5 = layout.row(align=True)
#		rowList.append(row5)
#		layout.row().separator()
#		row6 = layout.row(align=True)
#		rowList.append(row6)
#		row7 = layout.row(align=True)
#		rowList.append(row7)
#		row8 = layout.row(align=True)
#		rowList.append(row8)
#		row9 = layout.row(align=True)
#		rowList.append(row9)
#		row10 = layout.row(align=True)
#		rowList.append(row10)
		
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
#		row14 =  box.row()
#		rowList.append(row14)

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
		rowList[rn].label(text=ps.RR_msg1)
		rn+=1
#		rowList[rn].label(text=ps.RR_msg2)
#		rn+=1
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
		
#		self.report({'INFO'}, "Message %d %d" % (1, 2))
		
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
#		ps.RR_renderGo=False;

#		scene.renderregionsettings.RR_msgMargins=
#		ps.RR_msgMargins="calculating..."
#		print("----------------------MarginCalculate")

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
#		arMargW2=[]
		arMargW=self.calcMarg(context, resx, nregionsw, min(ps.RR_mrgmax,resx))
		arMargH=[]
		arMargH=self.calcMarg(context, resy, nregionsh, min(ps.RR_mrgmax,resy))
		
		##sort based on the length of the strings in array
#		print("***************************")
##		arMargW=[ ["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99],["0.0012345",95], ["0.0012345",97], ["0.00123456",3], ["0.0013245",99] ]
##		arMargW=[["0.5512345",99],
##		["0.555",98],
##		["0.55123456",90],
##		["0.5513245",89],
##		["0.5512345",85],
##		["0.5512345",81],
##		["0.55123456",80],
##		["0.5513245",79],
##		["0.5512345",75],
##		["0.5512345",72],
##		["0.55123456",70],
##		["0.5513245",69],
##		["0.5512345",65],
##		["0.5512345",62],
##		["0.55",60],
##		["0.55",59],
##		["0.5512345",55],
##		["0.5512345",50],
##		["0.55123456",49],
##		["0.5513245",45],
##		["0.5512345",40],
##		["0.5512345",39],
##		["0.55123456",35],
##		["0.5513245",30],
##		["0.5512345",29],
##		["0.5512345",25],
##		["0.55123456",20],
##		["0.5513245",19],
##		["0.5512345",15],
##		["0.5512345",10],
##		["0.55123456",9],
##		["0.5513245",5],
##		["0.5512345",3]]
##		arMargW=[["0.5515625", 99], ["0.55", 96], ["0.5484375", 93], ["0.546875", 90], ["0.5453125", 87], ["0.54375", 84], ["0.5421875", 81], ["0.540625", 78], ["0.5390625", 75], ["0.5375", 72], ["0.5359375", 69], ["0.534375", 66], ["0.5328125", 63], ["0.53125", 60], ["0.5296875", 57], ["0.528125", 54], ["0.5265625", 51], ["0.525", 48], ["0.5234375", 45], ["0.521875", 42], ["0.5203125", 39], ["0.51875", 36], ["0.5171875", 33], ["0.515625", 30], ["0.5140625", 27], ["0.5125", 24], ["0.5109375", 21], ["0.509375", 18], ["0.5078125", 15], ["0.50625", 12], ["0.5046875", 9], ["0.503125", 6], ["0.5015625", 3]]
#		print(arMargW)
#		print("----")
##		arMargW2 = sorted(arMargW, key = lambda x: (len(x[0]), -x[1]))
##		print(arMargW2)
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
#		scene.renderregionsettings.RR_msg2="rendering :"+scene.renderregionsettings.RR_activeRendername

	def post(self, scene, context=None):
		self.rendering = False
		self.render_ready=False
#		print("event POST---------------"+str(self.rendering))
#		scene.renderregionsettings.RR_msg2="rendered :"+scene.renderregionsettings.RR_activeRendername
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
			
			####################################################################
			####################################################################
			####################################################################
			####################################################################
			
#			pos_row=int(el/self.num_cols)
#			pos_col=int( ( el - ( pos_row*self.num_cols) ) )
#			
#			border_min_x=self.min_x+(self.delta_x*pos_col)
#			border_max_x=self.max_x+(self.delta_x*pos_col)
#			border_min_y=(self.delta_y*self.num_rows)- ((pos_row)*self.delta_y)
#			border_max_y=(self.delta_y*self.num_rows)- ((pos_row+1)*self.delta_y)
#			
#			##############################
#			##margins
#			resx=rnd.resolution_x
#			resy=rnd.resolution_y
#			relativeMargW=(1/resx)*ps.RR_mrg_w
#			relativeMargH=(1/resy)*ps.RR_mrg_h
#			if(ps.RR_useMargins==True):
#				border_min_x=round(min(max((border_min_x-relativeMargW),0),1),8)
#				border_max_x=round(min(max((border_max_x+relativeMargW),0),1),8)
#				border_min_y=round(min(max((border_min_y+relativeMargH),0),1),8)
#				border_max_y=round(min(max((border_max_y-relativeMargH),0),1),8)
#			
#			ret_regionArea = AreaRegion(
#				border_min_x,
#				border_max_y,
#				border_max_x,
#				border_min_y
#				)

#			tempRegionName=self.getRegionName(context,el)[0]
#			#forse non corretto ma si ordinano bene le immagini
#			self.region_name = self.outputImgName +"_"+tempRegionName# + rnd.file_extension

##			#forse corretto ma non si ordinano bene le immagini
##			self.region_name = self.outputImgName +"_"+str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_col + "_" + n_row# + rnd.file_extension

#			ret_imageName=self.outputFolderAbs + os.path.sep + self.region_name
			
			####################################################################
			####################################################################
			####################################################################
			####################################################################
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
			strScript+="tmpImgNamesPerRow=()"+"\n"
		strScript+=""+"\n"
#		bpy.data.texts.new("ciao.py")
		tmprow=0
#		for ireg in range(0,len(arObRegions)):
		for ireg in arObRegions:
#			print(str(ireg.getObject()))
			
			comm=""
			if(ireg.render==False):
				comm="#"
			
			strScript+=comm+"tmpImgName=\""+ireg.imageName+"\""+"\n"
####			in ireg.imageName c'è l'indicazione del frame (###)
####			che blender vuole mettere da qualche parte
####			quando si registrano i nomi delle immagini
####			per costruire poi le righe e l'immagine finale
####			si deve sostituire ### col frame
			imgPre=ireg.imageName
			cf=ireg.currframe
			new_nframe = f'{cf:0{3}d}'
			imgPost = imgPre.replace("###", str(new_nframe))
			strScript+=comm+"tmpImgNameFrm=\""+imgPost+"\""+"\n"
			
			if (ps.RR_who_region=="all"):
				if (tmprow!=ireg.nrow):
					strScript+="arrayImgNamesPerRow+=(\"$tmpImgNamesPerRow\")"+"\n"
					strScript+="tmpImgNamesPerRow=()"+"\n"
					strScript+="tmpImgNamesPerRow+=\"$tmpImgNameFrm\"\"."+imgExtension+" \"\n"
					tmprow=ireg.nrow
				else:
					strScript+="tmpImgNamesPerRow+=\"$tmpImgNameFrm\"\"."+imgExtension+" \"\n"
			
			strScript+=comm+"startrender "
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
			strScript+=comm+"msg \"ok "+str(ireg.nrow)+" "+str(ireg.ncol)+"\""+"\n"
			strScript+="\n"
		
		if (ps.RR_who_region=="all"):
				strScript+="arrayImgNamesPerRow+=(\"$tmpImgNamesPerRow\")"+"\n"
				strScript+="tmpImgNamesPerRow=()"+"\n"
		
#		bpy.data.texts['ciao.py'].write(strScript)
		
		pyJoin=self.writeJoinPython(context)
		
		strScript+="\n"
		strScript+="#crop and join image"+"\n"
		strScript+="#python "+pyJoin+"\n"
		
		strScript+="\n"
		strScript+="echo \"done\"\n"
		strScript+="\n"

		#nome del file blend
		blendName= bpy.path.basename(bpy.context.blend_data.filepath).split(".")[0]
		
		####################
##		##control file path, if outpur folder exist
		####################
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
	
	def getRegionName(self,context,index):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
		
		strname=""
		strnameScript=""
		
#		pos_row=int(self.arrayRegion[ps.RR_cntrnd]/self.num_cols)
#		pos_col=int( ( self.arrayRegion[ps.RR_cntrnd] - ( pos_row*self.num_cols) ) )
		
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
#		print("strname",strname)
		
		return [strname,n_row,n_col,strnameScript]

	def setRender(self, context):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
#		if ps.RR_cntrnd<len(self.arrayRegion):
		if ps.RR_cntrnd<len(self.allRegions):
			##prende i valori dall'array di tutte le regioni allRegions
			################################################################
			################################################################
			################################################################
			################################################################
			
			
#			pos_row=int(self.arrayRegion[ps.RR_cntrnd]/self.num_cols)
#			pos_col=int( ( self.arrayRegion[ps.RR_cntrnd] - ( pos_row*self.num_cols) ) )
#			
#			border_min_x=self.min_x+(self.delta_x*pos_col)
#			border_max_x=self.max_x+(self.delta_x*pos_col)
#			border_min_y=(self.delta_y*self.num_rows)- ((pos_row)*self.delta_y)
#			border_max_y=(self.delta_y*self.num_rows)- ((pos_row+1)*self.delta_y)
#			
#			##############################
#			##margins
#			if(ps.RR_useMargins==True):
#				resx=rnd.resolution_x
#				resy=rnd.resolution_y
#				relativeMargW=(1/resx)*ps.RR_mrg_w
#				relativeMargH=(1/resy)*ps.RR_mrg_h
#				
#				border_min_x=round(min(max((border_min_x-relativeMargW),0),1),8)
#				border_max_x=round(min(max((border_max_x+relativeMargW),0),1),8)
#				border_min_y=round(min(max((border_min_y+relativeMargH),0),1),8)
#				border_max_y=round(min(max((border_max_y-relativeMargH),0),1),8)

#			rnd.border_min_x=border_min_x
#			rnd.border_min_y=border_max_y
#			rnd.border_max_x=border_max_x
#			rnd.border_max_y=border_min_y

######			decCol=math.ceil(math.log(self.num_cols,10))
######			decRows=math.ceil(math.log(self.num_rows,10))
######			dec=max(decCol,decRows)
######			n_row = f'{pos_row:0{dec}d}'
######			n_col = f'{pos_col:0{dec}d}'
######			
#######			nome della regione: colonnexrighe riga colonna
######			tempRegionName = str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_row + "_" + n_col
#			
#			tempRegionName=self.getRegionName(context,self.arrayRegion[ps.RR_cntrnd])[0]
#			
#			#ciclo per cambiare i path nei fileoutput
#			#alla fine del render dovrebbero essere rimessi a posto
##			print("****----****----****----****----")
#			for x in self.saveFileOutputs:
#				tempNodeFO=scn.node_tree.nodes[str(x[0])]
#				tempslotcount=len(tempNodeFO.file_slots)
##				print("cambio fo= " + str(tempNodeFO) + " - slots=" + str(tempslotcount))
#				for xSlot in range(tempslotcount):
#					tempNodeFO.file_slots[xSlot].path=str(x[xSlot+1]) + tempRegionName + "_"
#			#####################

##			self.region_name = self.outputImgName +"_"+str(self.num_rows)+"x"+str(self.num_cols) + "_" + n_row + "_" + n_col + rnd.file_extension

#			#forse non corretto ma si ordinano bene le immagini
##			self.region_name = self.outputImgName +"_"+str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_row + "_" + n_col + rnd.file_extension
#			self.region_name = self.outputImgName +"_"+tempRegionName + rnd.file_extension
#			
##			#forse corretto ma non si ordinano bene le immagini
##			self.region_name = self.outputImgName +"_"+str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_col + "_" + n_row + rnd.file_extension

#			ps.RR_activeRendername=self.outputFolder + os.path.sep + self.region_name
			
			################################################################
			################################################################
			################################################################
			################################################################
#			tempRegionData=self.allRegions[self.arrayRegion[ps.RR_cntrnd]]
			tempRegionData=self.allRegions[ps.RR_cntrnd]
			
			if (tempRegionData.render==True):
				self.region_name=tempRegionData.baseName
				ps.RR_activeRendername=tempRegionData.fullName
				rnd.border_min_x=tempRegionData.minx
				rnd.border_min_y=tempRegionData.maxy
				rnd.border_max_x=tempRegionData.maxx
				rnd.border_max_y=tempRegionData.miny
				################################################################
				################################################################
				
				rnd.filepath=ps.RR_activeRendername
				ps.RR_msg1="render "+str(ps.RR_cntrnd)+"/"+str(ps.RR_maxrnd)
#				ps.RR_msg2="rendering :"+ps.RR_activeRendername
				
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
		
#		reg=[]
#		errorInsertRegions=False
		
		if ps.RR_dim_region==False:
			self.tot_reg=ps.RR_reg_columns*ps.RR_reg_rows
			self.num_cols=ps.RR_reg_columns
			self.num_rows=ps.RR_reg_rows
		else:
			self.tot_reg=ps.RR_multiplier*ps.RR_multiplier
			self.num_cols=ps.RR_multiplier
			self.num_rows=ps.RR_multiplier

#		if "all" in ps.RR_who_region:
#			for a in range(0,(self.tot_reg)):
#				reg.append(a)
#		elif "," in ps.RR_who_region:
#			control=ps.RR_who_region.replace(',','')
#			if (control.isdigit()):
#				reg_temp=ps.RR_who_region.split(",")
#				for a in range(0,len(reg_temp)):
#					if int(reg_temp[a])<self.tot_reg:
#						reg.append(int(reg_temp[a]))
#					else:
#						errorInsertRegions=True
#			else:
#				reg=""
#		elif "-" in ps.RR_who_region:
#			control=ps.RR_who_region.replace('-','')
#			if (control.isdigit()):
#				reg_temp=ps.RR_who_region.split("-")
#				for a in range(int(reg_temp[0]),int(reg_temp[1])+1):
#					if int(reg_temp[a])<self.tot_reg:
#						reg.append(int(reg_temp[a]))
#					else:
#						errorInsertRegions=True
#			else:
#				reg=""
#		elif ps.RR_who_region.isdigit():
#			if int(ps.RR_who_region)<self.tot_reg:
#				reg.append(int(ps.RR_who_region))
#			else:
#				errorInsertRegions=True
#		else:
#			reg=""
#		
#		if errorInsertRegions==True:
#			reg=""
#			self.report({"ERROR"}, "Error adding regions, check values")
		
#		print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
##		########################
##		costruzione dell'oggetto in cui si inseriscono 
##		tutti i dati di tutte le regioni.
##		al momento del render si decide se renderizzare la singola regione
##		in base agli stessi dati (una proprietà render=True/False).
##		nell'oggetto ci saranno
##			base del nome
##			righexcolonne
##			n riga
##			n colonna
##			frame
##			render (se renderizzare la regione)
##			valori della regione: minx, maxx, miny, maxy
##		nel render o nella scrittura dello script si cicla in questo oggetto
##		se render False si salta il render o si commenta la parte dello script
		reg=self.prepareAllRegions(context)
#		print(reg)
#		print(self.allRegions[0].baseName)
#		print(self.allRegions[0].__dir__())
#		for el in self.allRegions:
#			el.printAllProp()
#			print(el.minx)
#		print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
##		########################
		
#		reg=""
		
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
					print("reg_temp[a]",a)
					print("self.tot_reg",self.tot_reg)
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
				
	#			tmpReg.baseName=""
				######################################################################
				######################################################################
	#			pos_row=int(ireg/self.num_cols)
	#			pos_col=int( ( ireg - ( pos_row*self.num_cols) ) )
	#			decCol=math.ceil(math.log(self.num_cols,10))
	#			decRows=math.ceil(math.log(self.num_rows,10))
	#			dec=max(decCol,decRows)
	#			n_row = f'{pos_row:0{dec}d}'
	#			n_col = f'{pos_col:0{dec}d}'
	##			tempRegionName = str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_row + "_" + n_col

#				#forse non corretto ma si ordinano bene le immagini
#				self.region_name = self.outputImgName +"_"+tempRegionName# + rnd.file_extension
#	#			#forse corretto ma non si ordinano bene le immagini
#	#			self.region_name = self.outputImgName +"_"+str(self.num_cols)+"x"+str(self.num_rows) + "_" + n_col + "_" + n_row# + rnd.file_extension

				tempRegionName=self.getRegionName(context,ireg)
	#			print("tempRegionName",tempRegionName)
				tmpReg.outImg = self.outputImgName
				tmpReg.baseName = self.outputImgName +"_"+tempRegionName[0] + rnd.file_extension
				tmpReg.baseNameNoExt = self.outputImgName +"_"+tempRegionName[0]
				tmpReg.baseNameNoExtScript = self.outputImgName +"_"+tempRegionName[3]
				tmpReg.fullName=self.outputFolder + os.path.sep + tmpReg.baseName
				
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
##						cropW=(resx/ps.RR_reg_rows)*ps.RR_multiplier
##						cropH=(resy/ps.RR_reg_columns)*ps.RR_multiplier
##						cropX=(ps.RR_mrg_w)*ps.RR_multiplier
##						cropY=(ps.RR_mrg_h)*ps.RR_multiplier
						relativeMargW=((1/resx)*ps.RR_mrg_w)#*ps.RR_multiplier
						relativeMargH=((1/resy)*ps.RR_mrg_h)#*ps.RR_multiplier
					
					tmpReg.minx=round(min(max((tmpReg.minx-relativeMargW),0),1),8)
					tmpReg.maxx=round(min(max((tmpReg.maxx+relativeMargW),0),1),8)
					tmpReg.miny=round(min(max((tmpReg.miny+relativeMargH),0),1),8)
					tmpReg.maxy=round(min(max((tmpReg.maxy-relativeMargH),0),1),8)
				
				print("tmpReg.maxx",tmpReg.maxx)
				######################################################################
				######################################################################
				tmpReg.rows=ps.RR_reg_rows
				tmpReg.cols=ps.RR_reg_columns
				tmpReg.frame=scn.frame_current
				if ireg in reg:
					tmpReg.render=True
				else:
					tmpReg.render=False
				self.allRegions.append(tmpReg)
		
		return [reg,errorInsertRegions]

	def writeJoinPython(self, context):
		scn = context.scene
		rnd = context.scene.render
		ps = scn.renderregionsettings
		
		resx=rnd.resolution_x
		resy=rnd.resolution_y
		
		strScriptPy="import subprocess"
		strScriptPy+="\n"
		strScriptPy+="arrayImg=[]"+"\n"
		
		imgExtension=str.lower(rnd.image_settings.file_format)

##nomecrop="crop.png"
##cmdcrop="convert \"/media/dati_1tb/lavoro/blender_addon/renderregion/render05/test05RR__000_2x2_0_0.png\" -crop 100x50+0+0 "+nomecrop
##subprocess.call(cmdcrop, shell=True)

##nomeriga="riga.png"
##cmd_str = "convert \( /media/dati_1tb/lavoro/blender_addon/renderregion/render05/test05RR__000_2x2_0_0.png /media/dati_1tb/lavoro/blender_addon/renderregion/render05/test05RR__000_2x2_0_1.png \) +append "+nomeriga
##subprocess.call(cmd_str, shell=True)
			
		tmprow=0
		tmparray=""
		for el in self.allRegions:
#			name=el.fullName
			
			outputFolderAbs=os.path.split( bpy.path.abspath(rnd.filepath) )[0]
			imgPre=outputFolderAbs + os.path.sep + el.baseNameNoExtScript
			cf=el.frame
			new_nframe = f'{cf:0{3}d}'
			name = imgPre.replace("###", str(new_nframe))
			name += "."+imgExtension
			
			cropW=resx/ps.RR_reg_rows
			cropH=resy/ps.RR_reg_columns
			cropX=ps.RR_mrg_w
			cropY=ps.RR_mrg_h
			nrow=el.nrow
			ncol=el.ncol
			crop=ps.RR_useMargins
			if ps.RR_method=="MULTIPLY":
				cropW=resx#(resx/ps.RR_reg_rows)*ps.RR_multiplier
				cropH=resy#(resy/ps.RR_reg_columns)*ps.RR_multiplier
#				cropX=(ps.RR_mrg_w)*ps.RR_multiplier
#				cropY=(ps.RR_mrg_h)*ps.RR_multiplier
			
			if(ncol==0):
				cropX=0
			if(nrow==0):
				cropY=0
			
			if tmprow==nrow:
				tmparray+="['"+name+"',"+str(int(cropW))+","+str(int(cropH))+","+str(int(cropX))+","+str(int(cropY))+","+str(nrow)+","+str(ncol)+",'"+imgExtension+"',"+str(crop)+"],"
			else:
				tmprow=nrow
				tmparray = tmparray[:-1]
				strScriptPy+="arrayImg.append(["+tmparray+"])"+"\n"
				tmparray=""
				tmparray+="['"+name+"',"+str(int(cropW))+","+str(int(cropH))+","+str(int(cropX))+","+str(int(cropY))+","+str(nrow)+","+str(ncol)+",'"+imgExtension+"',"+str(crop)+"],"
		
		
#		print("bpy.path.basename(bpy.context.blend_data.filepath).split(\".\")[0]",bpy.path.basename(bpy.context.blend_data.filepath).split(".")[0])
#		print("el.fullName",el.fullName)
#		print("el.baseName",el.baseName)
#		print("el.baseNameNoExt",el.baseNameNoExt)
#		print("el.baseNameNoExtScript",el.baseNameNoExtScript)
		
		tmparray = tmparray[:-1]
		strScriptPy+="arrayImg.append(["+tmparray+"])"+"\n"
		strScriptPy+="\n"
		strScriptPy+="nmcrop=\"__crop__\""+"\n"
		strScriptPy+="nmrow=\"__row__\""+"\n"
		strScriptPy+="cmdcrop=\"\""+"\n"
		strScriptPy+="nrow=0"+"\n"
		strScriptPy+="ext=\"\""+"\n"
		strScriptPy+="strImgCropped=\"\""+"\n"
		strScriptPy+="tmprownm=\"\""+"\n"
		strScriptPy+="strImgRow=\"\""+"\n"
		finalImg=outputFolderAbs+os.path.sep+bpy.path.basename(bpy.context.blend_data.filepath).split(".")[0]+"."+imgExtension
		strScriptPy+="finalImg=\""+finalImg+"\""+"\n"
		strScriptPy+="\n"
		strScriptPy+="for arRow in arrayImg:"+"\n"
		strScriptPy+="	strImgCropped=\"\""+"\n"
		strScriptPy+="	for img in arRow:"+"\n"
		strScriptPy+="		if img[8]==True:"+"\n"
		strScriptPy+="			name=img[0]"+"\n"
		strScriptPy+="			cropW=str(img[1])"+"\n"
		strScriptPy+="			cropH=str(img[2])"+"\n"
		strScriptPy+="			cropX=str(img[3])"+"\n"
		strScriptPy+="			cropY=str(img[4])"+"\n"
		strScriptPy+="			row=str(img[5])"+"\n"
		strScriptPy+="			col=str(img[6])"+"\n"
		strScriptPy+="			ext=img[7]"+"\n"
		strScriptPy+="			tmpnmcrop=nmcrop+row+\"-\"+col+\".\"+ext"+"\n"
		strScriptPy+="			cmdcrop=\"convert '\"+name+\"' -crop \"+cropW+\"x\"+cropH+\"+\"+cropX+\"+\"+cropY+\" \"+tmpnmcrop"+"\n"
		strScriptPy+="			print(\"crop \"+row+\"-\"+col)"+"\n"
		strScriptPy+="			subprocess.call(cmdcrop, shell=True)"+"\n"
		strScriptPy+="			img[0]=tmpnmcrop"+"\n"
		strScriptPy+="			strImgCropped+=tmpnmcrop+\" \""+"\n"
		strScriptPy+="		else:"+"\n"
		strScriptPy+="			strImgCropped+=img[0]+\" \""+"\n"
		strScriptPy+="			ext=img[7]"+"\n"
		strScriptPy+="	"+"\n"
		strScriptPy+="	tmprownm=str(nmrow)+str(nrow)+\".\"+str(ext)"+"\n"
		strScriptPy+="	strImgRow+=tmprownm+\" \""+"\n"
		strScriptPy+="	cmdAppRow = \"convert \( \"+strImgCropped+\" \) +append \"+tmprownm"+"\n"
		strScriptPy+="	print(\"append row \"+str(nrow))"+"\n"
		strScriptPy+="	subprocess.call(cmdAppRow, shell=True)"+"\n"
		strScriptPy+="	nrow=nrow+1"+"\n"
		strScriptPy+="	"+"\n"
		strScriptPy+="cmdAppAll = \"convert \( \"+strImgRow+\" \) -append \"+finalImg"+"\n"
		strScriptPy+="print(\"append all\")"+"\n"
		strScriptPy+="subprocess.call(cmdAppAll, shell=True)"+"\n"
		strScriptPy+="\n"
		strScriptPy+="print(\"done\")"+"\n"

		#nome del file python
		blendName= bpy.path.basename(bpy.context.blend_data.filepath).split(".")[0]
		filePython=outputFolderAbs+os.path.sep+blendName+".py"
		
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
##########						bpy.ops.render.render(write_still=True)
##########						print("bpy.ops.render.render: "+str(self.render_ready))
#					elif self.setRender(context)==0:
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
				else:
					print("to render 2: "+self.region_name)
					bpy.ops.render.render("INVOKE_DEFAULT", write_still=True)
		
		return {"PASS_THROUGH"}


class Region:
	index=-1
	outImg=""
	baseName=""
	baseNameNoExt=""
	baseNameNoExtScript=""
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

classes = (
	RenderRegions,
	RenderRegionSettings,
	RENDER_PT_Region,
	RenderStop,
	MarginCalculate,
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
