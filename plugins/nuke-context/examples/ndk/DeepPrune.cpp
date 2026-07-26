// DeepPrune — nuke-context example (original code).
// category: deep | teaches: plane-level doDeepEngine with DeepInPlaceOutputPlane
// verified: compile
#include "DDImage/DeepFilterOp.h"
#include "DDImage/Knobs.h"

#include <vector>

using namespace DD::Image;

// Drop every deep sample whose front depth is beyond a threshold. DeepGain
// shows the per-sample convenience wrapper (DeepPixelOp); this is the level
// below it — DeepFilterOp hands you a whole *plane* and you rebuild the
// output sample-by-sample. That is the level where samples can be added or
// removed, which the per-sample wrapper cannot do (see Foundry's
// DeepCrop.cpp for the canonical form).
class DeepPrune : public DeepFilterOp
{
  float _maxDepth;
public:
  DeepPrune(Node* node) : DeepFilterOp(node), _maxDepth(1000.0f) {}

  void _validate(bool for_real) override
  {
    // Base pulls the deep info from the input; sample counts may change but
    // the box and channels do not, so nothing else to declare.
    DeepFilterOp::_validate(for_real);
  }

  bool doDeepEngine(DD::Image::Box box, const ChannelSet& channels,
                    DeepOutputPlane& plane) override
  {
    if (!input0())
      return true;

    // Pull the input plane, making sure the channel we filter on comes too.
    ChannelSet needed = channels;
    needed += Mask_DeepFront;
    DeepPlane inPlane;
    if (!input0()->deepEngine(box, needed, inPlane))
      return false;

    DeepInPlaceOutputPlane outPlane(channels, box);
    outPlane.reserveSamples(inPlane.getTotalSampleCount());
    std::vector<size_t> keep;

    for (DD::Image::Box::iterator it = box.begin(), end = box.end(); it != end; ++it) {
      DeepPixel inPixel = inPlane.getPixel(it);
      const size_t nSamples = inPixel.getSampleCount();

      keep.clear();
      keep.reserve(nSamples);
      for (size_t s = 0; s < nSamples; ++s) {
        if (inPixel.getUnorderedSample(s, Chan_DeepFront) <= _maxDepth)
          keep.push_back(s);
      }

      // Declare this pixel's output sample count, then copy the survivors.
      outPlane.setSampleCount(it, keep.size());
      DeepOutputPixel outPixel = outPlane.getPixel(it);
      size_t outSample = 0;
      for (size_t s : keep) {
        const float* in = inPixel.getUnorderedSample(s);
        float* out = outPixel.getWritableUnorderedSample(outSample);
        for (int c = 0, n = channels.size(); c < n; ++c)
          *out++ = *in++;
        ++outSample;
      }
    }

    outPlane.reviseSamples();
    plane = outPlane;
    return true;
  }

  void knobs(Knob_Callback f) override
  {
    Float_knob(f, &_maxDepth, "max_depth", "max depth");
    Tooltip(f, "Samples with deep.front beyond this are removed.");
  }

  const char* Class() const override { return d.name; }
  const char* node_help() const override
  { return "Remove deep samples beyond a depth threshold."; }
  static const Description d;
};

static Op* build(Node* node) { return new DeepPrune(node); }
const Op::Description DeepPrune::d("DeepPrune", build);
