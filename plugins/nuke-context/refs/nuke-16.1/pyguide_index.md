# Nuke Python Developer Guide — page map

27 pages. Routing only: to understand a topic, open the linked Foundry page and read it there.

The Python guide — scripting the node graph: knobs, animation, callbacks, custom panels, channels, threading, performance.

- **Introduction** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/intro.html
  Info
- **Start-up Scripts** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/startup.html
  Evaluation Order · menu.py · init.py
- **Getting Started** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/basics.html
  Creating Nodes and Setting Their Controls · Creating a Node in the User Interface · Creating a Node for Scripting · Setting Controls at Node Creation · Assigning Variables · Getting the Node Object for Existing Nodes · Accessing Selected Nodes in the Node Graph · Adding Controls to Nodes · Showing and Hiding a Node’s Properties Panel · Connecting Nodes and Setting Their Inputs · Setting Default Values for Controls · Rendering with the Write Node · Flipbooking with External Applications · Listing a Node’s Controls · Undoing and Redoing Actions · Frame Navigation · Setting Frame Ranges · Marking Frame Numbers in File Names · Copying an Animation Curve Between Nodes · Overriding the Creation of a Particular Node · Getting Information on the NUKE Environment You Are Running · Accessing Node Metadata · Creating Dialogs and Panels · Creating Modal Dialogs · Python Dialog Example · Creating Non-Modal Panels · Non-Modal Panel Example · Creating Progress Bar Dialogs · Clearing out the Current NUKE (.nk) Script · Creating Views for a Stereoscopic Project · Adjusting Control Values in Stereo Projects
- **Nuke as a Python Module** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/nuke_as_python_module.html
  Licensing
- **Animation** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/animation.html
  Setting Keys · Detecting Keys · Examples · Baking Animation
- **Using the Command-line** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/command_line.html
  Running NUKE in Python Mode · Using Command-line Arguments · Modifying Existing NUKE Scripts · Executing Frame Ranges
- **Callbacks** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/callbacks.html
  OnUserCreate · onCreate · onScriptLoad · onScriptSave · onScriptClose · onDestroy · knobChanged · updateUI · autolabel · beforeRender · beforeFrameRender · afterFrameRender · afterRender · afterBackgroundRender · afterBackgroundFrameRender · filenameFilter · validateFilename · autoSaveFilter · autoSaveRestoreFilter · autoSaveDeleteFilter · Using Autosave Callbacks to Implement a Rolling Autosave · Using Callbacks on Root to Add Stereo Setup · Default Colorspaces
- **Stereo** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/stereo.html
  Multi View Knob Values · Examples · Creating/Converting a Stereo Camera · Setting Up Stereo
- **3D** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/3D.html
  Getting basic selection information · Working with the current selection · Examples · Extending the classic snap menu · Accessing Geometry (Surface Scatter) · Extending the new snap menu · Animation with the new snap menu · USD Tools
- **Roto and RotoPaint** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/rotopaint.html
  Examples · paintTrajectory · trackShape · path Controller · trackCV
- **Accessing Image Data** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/image_data.html
  Using the CurveTool · Using the Sample Method · Examples · getMinMax · Using Sample
- **Custom Panels** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/custom_panels.html
  Extending NUKE with PySide · Simple Panel Commands · Simple Panel Object · Python Panels · ShapePanel · ShapeAndCVPanel · Search and Replace Panel · Extending NUKE with PySide · My First PySide Window · Dockable PySide Widgets · Migrating from PyQt Applications
- **Customizing the UI** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/custom_ui.html
  Creating a Custom Menu · Creating a Custom Toolbar · Creating a Custom Menu Item · Assigning a Hotkey · Defining Knob Defaults
- **Custom Flipbooks** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/flipbook.html
  Using Tweak Software’s RV as the Default Flipbook Application
- **Metadata** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/metadata.html
  Reading Metadata · Setting Metadata · Examples · createMetaDatCam
- **Working with Channels and Layers** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/channels.html
  Reading Channels · Adding New Channels · Examples · autoComp
- **Manipulating the Node Graph** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/dag.html
  Getting and Setting Node Positions · Controlling the Node Graph’s Pan and Zoom · Examples · A Circle Made of Dot Nodes · A Spiral · Controlling the Distance between Nodes
- **Formats** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/formats.html
  Reading Formats · Adding a New Format · Setting Formats
- **Math** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/math.html
  Using matrix · Example · paintPoints
- **Asset Management Systems / Pipeline Integration** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/asset.html
  Custom Script Save Workflow · Custom Script Load Workflow · Custom Write Node · Custom Read Node · Custom UDIM Parsing function
- **OpenAssetIO Integration** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/openassetio.html
  File Knob evaluation · Deassetization · Performance
- **Graph Scope Variables / Multi-shot Set-up** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/gsv.html
  Removing and Editing Variables and Sets · Specifying GSV Value Options · Adding GSVs to the Variables Panel · Variable Scopes and Overrides · Callbacks · Available GSV Callbacks · Callback Parameters · Removing GSV Callbacks · Example: Logging GSV Changes · Example: Enforcing GSV Naming Conventions
- **Threading** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/threading.html
  Examples · MirrorNodes
- **Render Farm Integration (Concept)** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/render_farm.html
- **Performance Profiling** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/performance.html
  Using Performance Timers · A Note on Nuke’s Architecture · Obtaining Performance Timings via Python · Other Performance Statistics · Writing Performance Information to an XML File
- **Installing Plug-ins** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/installing_plugins.html
  Home Directory · Custom Plug-in Repository
- **Sample Scripts** — https://learn.foundry.com/nuke/developers/16.1/pythondevguide/samples.html

