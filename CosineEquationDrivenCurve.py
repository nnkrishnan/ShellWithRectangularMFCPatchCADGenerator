# For more details see: https://capolight.wordpress.com/2018/07/02/how-to-sketch-equation-curves-in-fusion-360/
import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import math


def run(context):
    ui = None
    try:
#---------------------------------------------------Prepare Component---------------------------------------------------------
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Create a document.
        # document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)

        # Select current document

        product = app.activeProduct
        # Set Units to mm 
        designcast = adsk.fusion.Design.cast(product)
        unitsMgr = designcast.fusionUnitsManager
        unitsMgr.distanceDisplayUnits = adsk.fusion.DistanceUnits.MeterDistanceUnits

        # Get the root component of the active design.
        rootComp = designcast.rootComponent

        # Create a new sketch on the xy plane.
        sketches = rootComp.sketches
        xzPlane = rootComp.xZConstructionPlane 
        sketch = sketches.add(xzPlane)

        # Extract feature object for revovle feature
        features = rootComp.features

#---------------------------------------------------Create Curve---------------------------------------------------------
        # Create an object collection for the points.
        mainPoints = adsk.core.ObjectCollection.create()
        offsetPoints = adsk.core.ObjectCollection.create()

        
        # Curve Definition
        curveSpan = 130
        curveMidRise = 1.18
        ShellThickness = 0.48

        # correcting units
        curveSpan = curveSpan/10
        curveMidRise = curveMidRise/10
        ShellThickness = ShellThickness/10

        # Spline points
        startRange = 0  # Start of range to be evaluated.
        endRange = curveSpan/2  # End of range to be evaluated.
        splinePoints = 100  # Number of points that splines are generated.
        # WARMING: Using more than a few hundred points may cause your system to hang.
        i = 0

        while i <= splinePoints:
                t = startRange + ((endRange - startRange)/splinePoints)*i
                xCoord = (t)
                yCoord = (curveMidRise/2)*(1-math.cos(2*math.pi*t/curveSpan))
                # zCoord = (2**t)
                mainPoint = sketch.sketchPoints.add(adsk.core.Point3D.create(xCoord, yCoord))
                mainPoints.add(mainPoint)
                offsetPoint = sketch.sketchPoints.add(adsk.core.Point3D.create(xCoord, yCoord + ShellThickness))
                offsetPoints.add(offsetPoint)
                i = i + 1
        # Create the splines
        splines = sketch.sketchCurves.sketchFittedSplines 
        MainSplinespline = splines.add(mainPoints)
        OfsetSplinespline = splines.add(offsetPoints)

        # Join the spline end points
        sketchLines = sketch.sketchCurves.sketchLines
        startLine = sketchLines.addByTwoPoints(mainPoints.item(0),offsetPoints.item(0))
        endLine = sketchLines.addByTwoPoints(mainPoints.item(mainPoints.count-1),offsetPoints.item(offsetPoints.count-1))

        # Select the sketchProfile
        shellProfile = sketch.profiles.item(0)

#---------------------------------------------------Create Shell body---------------------------------------------------------
        # Revolve Sketch to create body

        # Extract revolve object form feature
        revolveFeatures = features.revolveFeatures

        # Creates a new RevolveFeatureInput object that is used to specify the 
        # input needed to create a new revolve feature.
        ShellrevInput = revolveFeatures.createInput(shellProfile, startLine, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

        # Define ans set the extent as factor of pi
        angle = adsk.core.ValueInput.createByReal(2*math.pi)
        ShellrevInput.setAngleExtent(False, angle)

        # Create the revolve.
        shellBodyRevolve = revolveFeatures.add(ShellrevInput)

#---------------------------------------------------Create Patch Profile---------------------------------------------------------
        #Use millimeter units
        centerOfPatchX = 29
        centerOfPatchY = 0
        centerOfPatchZ = 0
        widthOfPatch = 14
        lengthOfPatch = 28
        flipPatchPostion = True

        

        UnitCorrectionFactor =10
        multiplier = 1
        if flipPatchPostion:
                multiplier = -1

        widthOfPatch = widthOfPatch/(2*UnitCorrectionFactor*multiplier)
        lengthOfPatch = lengthOfPatch/(2*UnitCorrectionFactor*multiplier)
        centerOfPatchX = centerOfPatchX/(UnitCorrectionFactor*multiplier)
        centerOfPatchY = centerOfPatchY/(UnitCorrectionFactor*multiplier)
        centerOfPatchZ = centerOfPatchZ/(UnitCorrectionFactor*multiplier)
        # Create a sketch
        sketches = rootComp.sketches
        patchProfilesketch = sketches.add(rootComp.xYConstructionPlane)

        # Get sketch lines
        sketchLines = patchProfilesketch.sketchCurves.sketchLines

        # Create sketch rectangle
        # Define two points
        centerPoint = adsk.core.Point3D.create(centerOfPatchX, centerOfPatchY, centerOfPatchZ)
        cornerPoint = adsk.core.Point3D.create(centerOfPatchX+lengthOfPatch,centerOfPatchY+ widthOfPatch, 0) 
        patchProfile = sketchLines.addCenterPointRectangle(centerPoint, cornerPoint)

#---------------------------------------------------Create Top patch---------------------------------------------------------
               
        #Create Surface

        topOpenProfile = rootComp.createOpenProfile(MainSplinespline)
        topPatchSurfaceRevolveInput = revolveFeatures.createInput(topOpenProfile,startLine, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        topPatchSurfaceRevolveInput.isSolid = False
        # Define and set the extent as factor of pi
        topPatchSurfaceRevolveInput.setAngleExtent(False, angle)
        topPatchRevolveFeature = revolveFeatures.add(topPatchSurfaceRevolveInput)

        #Trim patch profile out of surface

        # Create trim feature
        trims = features.trimFeatures
        # trimInput = trims.createInput(patchProfile)
        trimInput = trims.createInput(topPatchRevolveFeature.bodies[0])
        # trimInput.targetBaseFeature = topPatchRevolveFeature
        cells = trimInput.bRepCells
        cells[0].isSelected = True
        trims.add(trimInput)


#---------------------------------------------------Create bottom patch---------------------------------------------------------
               
        #Create Surface

        bottomOpenProfile = rootComp.createOpenProfile(OfsetSplinespline)
        bottomPatchSurfaceRevolveInput = revolveFeatures.createInput(bottomOpenProfile,startLine, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        bottomPatchSurfaceRevolveInput.isSolid = False
        # Define and set the extent as factor of pi
        bottomPatchSurfaceRevolveInput.setAngleExtent(False, angle)
        bottomPatchRevolveFeature = revolveFeatures.add(bottomPatchSurfaceRevolveInput)

        

    # Error handeling
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
