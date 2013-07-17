import bpy, mathutils, bmesh
from macouno import mesh_extras


# Get the bmesh data from the current mesh object
def get_bmesh():
	
	# Get the active mesh
	ob = bpy.context.object
	me = ob.data
	
	sel = 0
	for f in me.polygons:
		if f.select:
			sel += 1

	# Get a BMesh representation
	if ob.mode == 'OBJECT':
		#print('ob')
		bm = bmesh.new()
		#print('ob 2',me, len(me.vertices), sel)
		#bm.from_object(ob, bpy.context.scene)
		bm.from_mesh(me)   # fill it in from a Mesh
		#print('ob 3')
	else:
		#print('ed')
		bm = bmesh.from_edit_mesh(me) # Fill it from edit mode mesh
	
	return bm
	
	
	
# Put the bmesh data back into the current mesh object
def put_bmesh(bm):
	
	# Get the active mesh
	ob = bpy.context.object
	me = ob.data
	
	# Flush selection
	bm.select_flush_mode() 
	
	# Finish up, write the bmesh back to the mesh
	if ob.mode == 'OBJECT':
		#print('ob 4')
		bm.to_mesh(me)
		#print('ob 5')
		bm.free()
		#print('ob 6')
	else:
		bmesh.update_edit_mesh(me, True)
	
	
	
# Get a list of all selected faces
def get_selected(bm):
	return [f for f in bm.faces if f.select]

	
	
# Select all
def all(bm):

	for f in bm.faces:
		f.select_set(True)

	return bm

	
	
# Select none (deselect)
def none(bm):

	for f in bm.faces:
		f.select_set(False)

	return bm
	

	
# Select the innermost faces of your current selection
def inner(bm):

	selFaces = get_selected(bm)
	
	# no need to continue if there are no selected faces
	if len(selFaces):
	
		outerFaces = []
		outerVerts = []
	
		while len(outerFaces) < len(selFaces):
		
			# Deselect the outer faces if there are any
			if len(outerFaces):
				for f in outerFaces:
					f.select_set(False)
					
				# Reset the list
				outerFaces = []
				outerVerts = []
			
			# Select the faces connected to unselected faces
			for f1 in selFaces:
				found = False
				for v in f1.verts:
					
					# If we know this vert is on the outside... no need to loop through the linked faces
					if v.index in outerVerts:
						outerFaces.append(f1)
						break
						
					# Loop through the connected faces to see if they're unselected
					for f2 in v.link_faces:
						if not f2.select:
							outerVerts.append(v.index)
							outerFaces.append(f1)
							found = True
							break
					if found:
						break

	return bm
	
	
	
# Select the outermost faces of your current selection
def outer(bm, invert=False):
	#print('x outer start')
	selFaces = get_selected(bm)
	selLen = len(selFaces)
	
	# no use continueing if there's no selection
	if not selLen:
		return bm
	
	outerFaces = []
	outerVerts = []
	
	# Find faces connected to unselected faces
	for f1 in selFaces:
		out = False
		for v in f1.verts:
			
			# No need to loop through connected faces if this vert is on the outside
			if v.index in outerVerts:
				outerFaces.append(f1)
				break
			
			# Loop through the faces connected to this vert
			for f2 in v.link_faces:
				if not f2.select:
					outerFaces.append(f1)
					outerVerts.append(v.index)
					out = True
					break
			if out:
				break
	
	# Unselect those that don't need to be kept
	if len(outerFaces) < selLen:
		for f in selFaces:
			if invert and f in outerFaces:
				f.select_set(False)
			elif not invert and not f in outerFaces:
				f.select_set(False)
	#print('y outer end')
	return bm
	
	
	
# SELECT ALL FACES CONNECTED BY A VERT TO THE CURRENT SELECTION
def connected(bm, extend=False):

	# Make a list of unselected faces that have a selected vert
	selThese = []
	
	for f in bm.faces:
		if not f.select:
			for v in f.verts:
				if v.select:
					selThese.append(f)
					break
					
	# Loop through all faces, and if the face is in the list select it
	# If the face is selected and we're not extending deselect it
	for f in bm.faces:
		if f.select and not extend:
			f.select_set(False)
		elif f in selThese:
			f.select_set(True)
	
	return bm
	

	
# SELECT ALL IN A VERTEX GROUP (takes the group iindex)
def grouped(bm, extend=False, group=0):

	gi = bpy.context.active_object.vertex_groups.active_index
	
	# only ever one deform weight layer
	dvert_lay = bm.verts.layers.deform.active
			
	for f in bm.faces:
		
		# Count all the verts that are in the vertex group (in this face)
		fLen = 0
		for v in f.verts:
			
			if group in v[dvert_lay]:
				fLen += 1
				
		# Only if all verts are in the group, do we select the face
		if fLen and fLen == len(f.verts):
			f.select_set(True)
		elif f.select and not extend:
			f.select_set(False)
			
	return bm
	
	

# SELECT ALL FACES WITH A NORMAL IN A SPECIFIC DIRECTION
def directional(bm, extend=False, direction=(0.0,0.0,1.0), limit=1.57):
	
	# Make sure the direction is a vector object
	direction = mathutils.Vector(direction)
	
	# Make sure the direction has a length
	if direction.length:
	
		for f in bm.faces:
		
			f.normal_update()
			
			n = f.normal
		
			# Find the angle between the face normal and the direction
			if n.length:
				angle = direction.angle(n)
			else:
				angle = 0.0
				
			# Check against the limit
			if angle <= limit:
				f.select_set(True)
			elif f.select and not extend:
				f.select_set(False)
	
	return bm
	
	
	
# Make sure there are less polygons selected than the limit
def limit(bm, limit=1, key=''):

	from macouno import liberty
	lib = liberty.liberty('string', key)

	selFaces = lib.makeDict([f for f in bm.faces if f.select])
	nuLen = len(selFaces)
	
	while nuLen > limit:
	
		deFace = lib.Choose('select',selFaces)
		
		deFace.select_set(False)
	
		selFaces = lib.makeDict([f for f in bm.faces if f.select])
		nuLen = len(selFaces)
		
	return bm
	
	

# Find all faces connected to the current one (face)
def get_connected(conFaces, checkFaces, face):

	# Find all faces that share an edge with the current one (if they are in the list to check)
	for e in face.edges:
		for f in e.link_faces:
			if f in checkFaces:
				checkFaces.remove(f)
				conFaces.append(f)
				
				conFaces, checkFaces = get_connected(conFaces, checkFaces, f)
	
	return conFaces, checkFaces
	
# Make sure there's no multiple islands selected
def island_check(bm):
	
	selFaces = get_selected(bm)

	if len(selFaces):

		checkFaces = get_selected(bm)

		biggestLen = False
		biggestCon = False
		
		# For each face check how many are connected to it
		for f in selFaces:
			
			if len(checkFaces) and f in checkFaces:
				
				conFaces, checkFaces = get_connected([], checkFaces, f)
				
				cnt = len(conFaces)
				if cnt > biggestLen or biggestLen is False:
					biggestLen = cnt
					biggestCon = conFaces
		
		# Deslect all selected faces that arent part of the biggest island.
		if not biggestLen is False:
			for f in bm.faces:
				if f.select and not f in biggestCon:
					f.select_set(False)
	
	return bm
	
	
	
# INITIATE >>> This way we don't have to do the same thing over and over
def go(mode='ALL', invert=False, extend=False, group=0, direction=(0.0,0.0,1.0), limit=1.57, key=''):
	
	bm = get_bmesh()
	
	if mode == 'ALL':
		bm = all(bm)
	
	elif mode == 'NONE':
		bm = none(bm)

	elif mode == 'INNER':
		bm = inner(bm)

	elif mode == 'OUTER':
		bm = outer(bm, invert)
		
	elif mode == 'CONNECTED':
		bm = connected(bm, extend)		
		
	elif mode == 'DIRECTIONAL':
		bm = directional(bm, extend, direction, limit)
		
	elif mode == 'GROUPED':
		bm = grouped(bm, extend, group)
		
	elif mode == 'LIMIT':
		bm = grouped(bm, limit, key)		
		
	elif mode == 'ISLAND':
		bm = island_check(bm)

	put_bmesh(bm)