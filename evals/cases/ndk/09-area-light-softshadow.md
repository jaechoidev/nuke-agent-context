# Area light with soft shadows (GeomOp)
Write a Nuke NDK plugin in C++ that adds an area light usable by Nuke's scanline
renderer, casting soft (penumbra) shadows rather than the hard shadows of the
built-in point/spot lights. Expose knobs for the light's width, height, and sample
count. Be precise about the base class you derive from and which methods declare the
light's contribution. Provide the complete .cpp file.

<!-- concept: nukepedia.com/tools/plugins/3d/area-light-softbox (real community tool) -->
