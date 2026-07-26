// DeepGain — nuke-agent example (original code).
// category: deep | teaches: per-sample processing in a DeepPixelOp
// verified: compile
#include "DDImage/DeepPixelOp.h"
#include "DDImage/Knobs.h"

using namespace DD::Image;

// Multiply the colour of every deep sample by a gain, leaving depth and alpha
// untouched. A DeepPixelOp visits each sample of each deep pixel; you read the
// sample with getUnorderedSample and push the (possibly modified) value.
class DeepGain : public DeepPixelOp
{
  float _gain;
public:
  DeepGain(Node* node) : DeepPixelOp(node), _gain(1.0f) {}

  // Boilerplate wrappers so the base handles the deep plumbing.
  void in_channels(int, ChannelSet&) const override {}

  void _validate(bool for_real) override
  {
    DeepPixelOp::_validate(for_real);
  }

  void processSample(int y, int x,
                     const DD::Image::DeepPixel& deepPixel,
                     size_t sampleNo,
                     const DD::Image::ChannelSet& channels,
                     DeepOutPixel& output) const override
  {
    foreach (z, channels) {
      float v = deepPixel.getUnorderedSample(sampleNo, z);
      if (colourIndex(z) < 3)      // scale r, g, b only
        v *= _gain;
      output.push_back(v);
    }
  }

  void knobs(Knob_Callback f) override
  {
    Float_knob(f, &_gain, "gain", "gain");
  }

  const char* Class() const override { return d.name; }
  const char* node_help() const override { return "Scale deep sample colour."; }
  static const Description d;
};

static Op* build(Node* node) { return new DeepGain(node); }
const Op::Description DeepGain::d("DeepGain", build);
