# NDK dev guide — concept → page map

54 pages across 11 sections of the NDK Developer Guide. Routing only: to understand a part of the paradigm, open the linked Foundry page and read it there.

## intro

Orientation: terminology, the Op architecture, building and installing plug-ins.

- **Introduction** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/intro/intro.html
  Pre-requisites · How to Use This Guide · Info
- **Terminology** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/intro/terminology.html
  NDK · Op · Node · Direct Acyclic Graph (DAG)/Node Graph · Knobs · Plug-in · Channel · Region of Interest · Region of Definition · Format · Bounding Box (bbox) · Pixel · Interest · Tile
- **Fundamental Concepts** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/intro/oparchitecture.html
  Nodes vs Operators (Ops) · Ops · Knobs · Typical processing events
- **Building & Installing Plug-ins** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/intro/pluginbuildinginstallation.html
- **Versioning** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/intro/pluginversioning.html
  Plug-in Versioning · DDImage Versioning

## 2d

The 2D image pipeline — PixelIop, DrawIop, Iop, PlanarIop, channels, readers/writers.

- **2D Architecture** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/2d/architecture.html
  Scanline-Based · A Basic Node Graph · Fundamental Image Processing Unit - the Row · The Viewer and Large Image Sizes · Multi-Threading · The Row Cache · Tiles · The Viewer Cache · Memory · Iop Call Order · Call Safety · Coordinate System · Top-Down Rendering
- **PixelIop: Getting Started with Image Processing** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/2d/pixeliops.html
  The PixelIop Class Specifics & Required Virtual Calls · Getting Started: The Basic Node · Building the Grade Node · Exercise: Build a Mult Node
- **DrawIop: Generating Images from Scratch** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/2d/drawiops.html
  The DrawIop Class Specifics & Required Virtual Calls · Building the Rectangle Node · Building the Noise Node · Exercise: Build a Fractal Node
- **Iop: Spatial Operators** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/2d/iops.html
  The Iop Class Specifics & Required Virtual Calls · A Simple Iop Example - AddInputs · Working With Tiles: SimpleBlur · Full-Frame Processing and Interests · Exercise: Build a Median Node
- **Planar Iop: Image Processing with 2-Dimensional Outputs** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/2d/planariops.html
  Render Stripe · Request · Channels and Layers · Packed Preference · PlanarI · Image Planes · Low-level access · Higher-level access · Writing to ImagePlane
- **Working with Channels** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/2d/channels.html
  Adding & Removing Channels · Working with Multiple Channels Simultaneously · Accessing Other ChannelSets
- **Working with NukeWrapper** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/2d/nukewrapper.html
- **Writing Image Readers & Writers** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/2d/readerswriters.html
  Architecture · Readers · Writers · Colorspace Handling & LUTs

## 3d-usd

The current USD-based 3D API for geometry plug-ins.

- **NUKE’s 3D System** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/3d-usd/introduction.html
  Introduction
- **Basic Concepts** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/3d-usd/basic-concepts.html
  The Stage · The Scene Graph · Stages and Layers · Merging Workflows · Objects and Attributes · Authoring Controls · Materials and Shaders · Axis, Cameras and Lights
- **The New API** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/3d-usd/api.html
  The Math Library · The USD Wrapper
- **Basic API Usage** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/3d-usd/api-usage.html
  Defining a Prim · Getting and Setting Attributes · Raw USD
- **Writing a 3D Plugin** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/3d-usd/writing-plugins.html
  Time in Plugins · SourceGeo Plugins · ModifyGeo Plugins Plugins · Material and Shader Plugins
- **Using a Custom USD Build with FnUsdShim** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/3d-usd/using-custom-usd.html
  Contents

## 3d

The classic 3D system — GeoOp, attributes, geometry readers/writers.

- **NUKE’s Classic 3D Architecture** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/3d/architecture.html
  Introduction · Core Classes · Coordinate Systems
- **Writing a GeoOp** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/3d/geo-ops.html
  Base Classes for GeoOps · Extending SourceGeo · Extending ModifyGeo · Extending GeoOp Directly · Common Parts of All GeoOps · GeoOp Call Order for Rendering · GeoOp Call Order for Viewing · Creating Geometry
- **Attributes** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/3d/attributes.html
  Attribute Groups · Attribute Types · Attribute Contexts · Finding Out What Attributes are Available · Getting Attributes · Adding Attributes · Deleting attributes · Standard attributes
- **SourceGeo Tutorial** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/3d/sourcegeo-example.html
  Tetrahedron 3D Coordinates · UV-mapping · Basic Setup: Includes and Namespaces · Constants · Declarations · The Easy Bits · Adding Some Knobs · Generating the Geometry · The Complete Code
- **GeoReader and GeoWriter: Supporting Custom 3D File Formats** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/3d/geo-read-write.html
  Introduction · Mapping File Types to Readers and Writers
- **Manipulating Data in 3D** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/3d/interaction.html
  Checking for 3D Mode · Check the Render Pass

## deep

Deep image data — DeepOp, DeepPixelOp, deep readers/writers, deep-to-2D.

- **Basic DeepOps** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/deep/deep.html
- **Simple DeepPixelOp** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/deep/deepsimple.html
- **Deep Reader** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/deep/deepreader.html
- **Deep Writer** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/deep/deepwriter.html
- **Deep to 2D Ops** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/deep/deepto2d.html

## particles

Custom particle-behaviour Ops and their performance.

- **Writing New Behaviour Ops** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/particles/particles.html
  Improving Particle Performance

## split-and-execute

Shared Op machinery — input handling, time/stereo splitting, executable Ops.

- **Introduction** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/split-and-execute/intro.html
- **Input Handling** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/split-and-execute/input.html
  Constant Number of Inputs · Dynamic Number of Inputs · Optional (Right Hand Side Mask) Inputs · Naming/Labelling Inputs · Input Class Testing · Default Inputs
- **Time & Stereo Ops** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/split-and-execute/split.html
  Architecture · Building The TemporalMedian Node · Exercise: Build a Stereo Median
- **Executable Ops** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/split-and-execute/executable.html

## knobs-and-handles

Knobs, control panels and in-viewer handles; dynamic and custom knobs.

- **Introduction** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/knobs-and-handles/intro.html
  Knob Classifications · Knob Naming
- **Knob Types** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/knobs-and-handles/knobtypes.html
  Knobs By ID · Knobs By Type & Call
- **Knob Flags, Ranges, and Tooltips** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/knobs-and-handles/knobflags.html
  Knob Flags · Knob Ranges · Knob Tooltips
- **Knob Changed and Linking Controls** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/knobs-and-handles/knobchanged.html
  The knob_changed() Method · The knob_changed_finished Method · Linking Controls · Buttons
- **Dynamic Creation of Knobs** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/knobs-and-handles/dynamic-knobs.html
  Exercise: Extending DynamicKnobs
- **Creating Custom Knobs** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/knobs-and-handles/writing-knobs.html
  Knob Architecture · Storing Arbitrary Data · Custom Knob Widgets Using Qt
- **Value Provider (Output Knobs)** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/knobs-and-handles/output-knobs.html

## advanced

The traps — hashing/caching, threading, memory, errors: correct-looking code that misbehaves.

- **Introduction** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/advanced/intro.html
- **Architecture** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/advanced/opscommon.html
  Op Lookup · Op Construction · Knobs · Validation
- **Op Hashing & Caching** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/advanced/hashing.html
- **Memory Management** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/advanced/memorymanagement.html
  Introduction · allocate_void/deallocate_void Functions · MemoryHolder · Allocators
- **Curve serialisation format** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/advanced/curveformat.html
- **Roto serialisation format** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/advanced/rotoformat.html
  Curve tree · Floating point format · Layers · Curve Groups · Keyframes and Animation · Flags · Attribute Names

## appendixa

Setting up projects and compilers per platform.

- **Microsoft Windows** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/appendixa/windows.html
- **macOS** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/appendixa/osx.html
- **Linux** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/appendixa/linux.html
  ABI issues

## appendixc

Plug-in compatibility across Nuke versions.

- **Breaking Changes** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/appendixc/breaking.html
  ImagePlane · Knob · LUT · LightContext · MultiTile · Op · OutputContext · Deep
- **Deprecated Changes** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/appendixc/deprecated.html
  Memory
- **New Features** — https://learn.foundry.com/nuke/developers/15.2/ndkdevguide/appendixc/new.html
  Box · ImagePlane · Iop · MultiTileIop · Op · PlanarI · Read · Row · UpRez · VConvolve · MemHolderFactory

