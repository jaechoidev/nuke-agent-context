# 4x4 colour-matrix kernel
Write a Nuke BlinkScript kernel that multiplies each pixel's RGBA by an arbitrary
4x4 matrix supplied as 16 knob values, and outputs the result. It should be usable
for transforming vector passes such as Position or Normals, so treat the pixel as a
4-vector (rgb + 1 in the 4th component option) and expose a knob to choose whether
the 4th row/column is applied. Provide the complete .blink kernel.

<!-- concept: nukepedia.com/tools/blink/colour/c44kernel (real community tool) -->
