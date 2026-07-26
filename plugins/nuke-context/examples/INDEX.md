# Examples index

One row per example, generated from each file's `Teaches:` header.

| Example | Teaches |
| --- | --- |
| `blink/Dilate2D.blink` | eAccessRanged2D, a 2D neighbourhood window |
| `blink/Exposure.blink` | the simplest ePixelWise kernel, param + process |
| `blink/HorizontalMax.blink` | eAccessRanged1D, setRange/setAxis in init() |
| `blink/RadialBlur.blink` | eAccessRandom, sampling arbitrary coordinates |
| `blink/SDFRaymarcher.blink` | a 3D signed-distance-field renderer in Blink |
| `blink/bookofshaders/01_gradient.blink` | normalized st coords -> value ramp |
| `blink/bookofshaders/02_circle.blink` | distance field + a hand-rolled smooth edge |
| `blink/bookofshaders/03_colormix.blink` | lerp between two colours across st.x |
| `blink/bookofshaders/04_grid.blink` | fract (via floor) of scaled coords -> grid |
| `blink/bookofshaders/08_matrix.blink` | rotating the coordinate space (2D rotation) |
| `blink/bookofshaders/10_random.blink` | a hash-based pseudo-random per cell |
| `blink/bookofshaders/11_noise.blink` | value noise = smooth-interpolated random |
| `blink/bookofshaders/12_cellular.blink` | Voronoi -- nearest random feature point |
| `blink/bookofshaders/13_fbm.blink` | fractal brownian motion (summed octaves) |
| `ndk/DeepGain.cpp` | per-sample processing in a DeepPixelOp |
| `ndk/DeepPrune.cpp` | plane-level doDeepEngine with DeepInPlaceOutputPlane |
| `ndk/EdgeDetect.cpp` | Iop reading neighbouring pixels via a Tile |
| `ndk/Exposure.cpp` | PixelIop, output depends only on the input pixel |
| `ndk/FrameBlend.cpp` | split_input + per-split inputContext for multi-frame access |
| `ndk/Gradient.cpp` | a source Iop with no input, setting its own info_ |
| `ndk/MinimalReader.cpp` | the smallest Reader subclass + Reader::Description registration |
| `ndk/MixInputs.cpp` | a two-input Iop reading both inputs per scanline |
| `ndk/Premult.cpp` | PixelIop channel math across channels |
| `ndk/TimeOffset.cpp` | reading a different frame via inputContext() |
| `ndk/Vignette.cpp` | position-aware PixelIop using the format |
| `python/backdrop_selected.py` | node position is data; sizing a BackdropNode |
| `python/bake_expression.py` | the knob animation model over a frame range |
| `python/dockable_panel_stateful.py` | panel state persisted onto node knobs, surviving save/reload |
| `python/gizmo_builder.py` | a gizmo is an authored Group with promoted knobs |
| `python/knob_linker.py` | knobChanged callbacks and deferred, event-driven UI |
| `python/pyqt_panel.py` | a PySide6 widget registered as a Nuke panel |
| `python/render_submitter_shape.py` | the architecture of a render submitter - introspect, build a job, confirm, emit |
| `python/select_downstream.py` | the graph as a data structure you traverse |
