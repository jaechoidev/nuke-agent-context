// Exposure — nuke-agent example (original code).
// category: 2D per-pixel | teaches: PixelIop, output depends only on the input pixel
// verified: compile
#include "DDImage/PixelIop.h"
#include "DDImage/Row.h"
#include "DDImage/Knobs.h"
#include <cmath>

using namespace DD::Image;

class ExposureIop : public PixelIop
{
  float _stops;
public:
  ExposureIop(Node* node) : PixelIop(node), _stops(0.0f) {}

  void _validate(bool for_real) override
  {
    copy_info();
    set_out_channels(_stops == 0.0f ? Mask_None : Mask_All);
  }

  void in_channels(int, ChannelSet&) const override {}

  void pixel_engine(const Row& in, int, int x, int r,
                    ChannelMask channels, Row& out) override
  {
    const float gain = std::pow(2.0f, _stops);
    foreach (z, channels) {
      const float* IN = in[z] + x;
      const float* END = IN + (r - x);
      float* OUT = out.writable(z) + x;
      while (IN < END)
        *OUT++ = *IN++ * gain;
    }
  }

  void knobs(Knob_Callback f) override
  {
    Float_knob(f, &_stops, "stops", "stops");
    Tooltip(f, "Exposure adjustment in photographic stops.");
  }

  const char* Class() const override { return d.name; }
  const char* node_help() const override { return "Adjust exposure in stops."; }
  static const Description d;
};

static Op* build(Node* node) { return new ExposureIop(node); }
const Op::Description ExposureIop::d("Exposure", build);
