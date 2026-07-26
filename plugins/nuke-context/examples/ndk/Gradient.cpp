// Gradient — nuke-agent example (original code).
// category: 2D generator | teaches: a source Iop with no input, setting its own info_
// verified: compile
#include "DDImage/Iop.h"
#include "DDImage/Row.h"
#include "DDImage/Knobs.h"
#include "DDImage/Format.h"

using namespace DD::Image;

// A vertical gradient from 0 (bottom) to 1 (top). A generator has no input, so
// _validate builds info_ from a Format knob rather than copy_info(), and engine
// synthesises pixels from position alone.
class GradientIop : public Iop
{
  FormatPair formats;
public:
  GradientIop(Node* node) : Iop(node) { formats.format(nullptr); }

  void _validate(bool for_real) override
  {
    info_.full_size_format(*formats.fullSizeFormat());
    info_.format(*formats.format());
    info_.channels(Mask_RGB);
    info_.set(format());
  }

  void engine(int y, int x, int r, ChannelMask channels, Row& out) override
  {
    const float h = float(format().height());
    const float v = h > 1.0f ? y / (h - 1.0f) : 0.0f;
    foreach (z, channels) {
      float* OUT = out.writable(z) + x;
      for (int cur = x; cur < r; ++cur)
        *OUT++ = v;
    }
  }

  void knobs(Knob_Callback f) override
  {
    Format_knob(f, &formats, "format", "format");
  }

  const char* Class() const override { return d.name; }
  const char* node_help() const override { return "Vertical 0..1 gradient source."; }
  static const Description d;
};

static Op* build(Node* node) { return new GradientIop(node); }
const Op::Description GradientIop::d("Gradient", build);
