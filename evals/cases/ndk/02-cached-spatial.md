# Spatial blur with a scanline cache
Write a Nuke NDK plugin in C++ called `CachedBoxBlur` that performs a vertical box
blur. It needs to read several input scanlines per output scanline, so it must hold
an appropriate cache rather than re-requesting rows. Provide the complete .cpp file.
