// Premult — nuke-agent example (original code).
// category: 2D per-pixel | teaches: PixelIop channel math across channels
// verified: compile
#include "DDImage/PixelIop.h"
#include "DDImage/Row.h"
#include "DDImage/Knobs.h"

using namespace DD::Image;

// Multiply rgb by alpha. Reads alpha in addition to the channels it writes, so
// in_channels adds the alpha channel to the request.
class PremultIop : public PixelIop
{
public:
  PremultIop(Node* node) : PixelIop(node) {}

  void _validate(bool for_real) override
  {
    copy_info();
    set_out_channels(Mask_RGB);
  }

  void in_channels(int, ChannelSet& mask) const override
  {
    mask += Chan_Alpha;   // we also need alpha to premultiply
  }

  void pixel_engine(const Row& in, int, int x, int r,
                    ChannelMask channels, Row& out) override
  {
    const float* alpha = in[Chan_Alpha] + x;
    foreach (z, channels) {
      if (z == Chan_Alpha) {
        out.copy(in, z, x, r);      // pass alpha through unchanged
        continue;
      }
      const float* IN = in[z] + x;
      const float* A = alpha;
      float* OUT = out.writable(z) + x;
      for (int cur = x; cur < r; ++cur)
        *OUT++ = *IN++ * *A++;
    }
  }

  void knobs(Knob_Callback) override {}
  const char* Class() const override { return d.name; }
  const char* node_help() const override { return "Multiply rgb by alpha."; }
  static const Description d;
};

static Op* build(Node* node) { return new PremultIop(node); }
const Op::Description PremultIop::d("Premult", build);
