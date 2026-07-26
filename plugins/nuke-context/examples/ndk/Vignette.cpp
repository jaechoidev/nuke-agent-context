// Vignette — nuke-agent example (original code).
// category: 2D per-pixel | teaches: position-aware PixelIop using the format
// verified: compile
#include "DDImage/PixelIop.h"
#include "DDImage/Row.h"
#include "DDImage/Knobs.h"
#include <cmath>

using namespace DD::Image;

// Darken toward the frame edges. Per-pixel, but the multiplier depends on the
// pixel's position relative to the format centre -- so the centre/radius are
// precomputed once in _validate and only read (never written) in pixel_engine,
// keeping the engine reentrant.
class VignetteIop : public PixelIop
{
  float _amount;
  double _cx, _cy, _inv_max2;      // set in _validate, read-only in engine
public:
  VignetteIop(Node* node) : PixelIop(node), _amount(0.5f),
                            _cx(0), _cy(0), _inv_max2(1) {}

  void _validate(bool for_real) override
  {
    copy_info();
    const Format& f = format();
    _cx = f.width() * 0.5;
    _cy = f.height() * 0.5;
    _inv_max2 = 1.0 / (_cx * _cx + _cy * _cy);
    set_out_channels(_amount == 0.0f ? Mask_None : Mask_RGB);
  }

  void in_channels(int, ChannelSet&) const override {}

  void pixel_engine(const Row& in, int y, int x, int r,
                    ChannelMask channels, Row& out) override
  {
    foreach (z, channels) {
      const float* IN = in[z] + x;
      float* OUT = out.writable(z) + x;
      for (int cur = x; cur < r; ++cur) {
        const double dx = cur - _cx, dy = y - _cy;
        const double d2 = (dx * dx + dy * dy) * _inv_max2;   // 0 centre .. 1 corner
        const float mult = 1.0f - _amount * float(d2);
        *OUT++ = *IN++ * mult;
      }
    }
  }

  void knobs(Knob_Callback f) override
  {
    Float_knob(f, &_amount, "amount", "amount");
    Tooltip(f, "Strength of the edge darkening.");
  }

  const char* Class() const override { return d.name; }
  const char* node_help() const override { return "Darken toward the frame edges."; }
  static const Description d;
};

static Op* build(Node* node) { return new VignetteIop(node); }
const Op::Description VignetteIop::d("Vignette", build);
