# Hue-selective despill + chroma key
Write a Nuke BlinkScript kernel that despills a chosen screen colour and outputs a
chroma key. Expose knobs for the target hue, a tolerance, and despill strength. The
kernel should reduce the screen colour's contribution in the RGB where it dominates,
and produce an alpha from how close each pixel's hue is to the target. Provide the
complete .blink kernel.

<!-- concept: nukepedia.com/tools/blink/colour/apdespill (real community tool) -->
