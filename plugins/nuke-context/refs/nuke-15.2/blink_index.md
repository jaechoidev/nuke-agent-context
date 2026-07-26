# BlinkScript built-in API index

70 built-ins. A kernel that calls anything not listed here (and not a param/local you declared) will fail to compile in Nuke.

| Symbol | Kind | Signature | Docs |
| --- | --- | --- | --- |
| `acos` | builtin | `acos(floatn a)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `asin` | builtin | `asin(floatn a)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `atan` | builtin | `atan(floatn a)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `atan2` | builtin | `atan2(pixel , pixel)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `ceil` | builtin | `ceil(pixel)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `clamp` | builtin | `clamp(floatn x, floatn y, floatn z)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `cos` | builtin | `cos(floatn a)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `cross` | builtin | `cross(float3 x, float3 y)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `dot` | builtin | `dot(floatn x, floatn y)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `exp` | builtin | `exp(pixel)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `fabs` | builtin | `fabs(pixel)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `floor` | builtin | `floor(pixel)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `fmod` | builtin | `fmod(pixel , SampleType ( dst)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `length` | builtin | `length(floatn x)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `lerp` | builtin |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `log` | builtin | `log(floatn x)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `log10` | builtin | `log10(floatn x)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `log2` | builtin | `log2(floatn x)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `max` | builtin | `max(floatn x, floatn y)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `min` | builtin | `min(floatn x, floatn y)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `normalize` | builtin | `normalize(floatn x)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `pow` | builtin | `pow(floatn x, floatn a)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `round` | builtin |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `rsqrt` | builtin | `rsqrt(pixel + 1.0f)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `sign` | builtin | `sign(pixel)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `sin` | builtin | `sin(float2(1.0f, 2.0f)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `sqrt` | builtin | `sqrt(floatn x)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `tan` | builtin | `tan(floatn a)` | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `ImageComputationKernel` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `ImageReductionKernel` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `ImageRollingKernel` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `at` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `bounds` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `define` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `eAccessPoint` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `eAccessRandom` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `eAccessRanged` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `eComponentWise` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `eEdit` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `ePixelWise` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `eRead` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `eReadWrite` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `eWrite` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `init` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `kernel` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `local` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `median` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `param` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `print` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `process` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `setAxis` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `setRange` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `void` | keyword |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `Image` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `ImageInfo` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `bool` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `bool2` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `bool3` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `bool4` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `float` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `float2` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `float3` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `float3x3` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `float4` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `float4x4` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `int` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `int2` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `int3` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `int4` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
| `recursive` | type |  | https://learn.foundry.com/nuke/developers/15.2/BlinkUserGuide/BlinkKernelAPIReference.html |
