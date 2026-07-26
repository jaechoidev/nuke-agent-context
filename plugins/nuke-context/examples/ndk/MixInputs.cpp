// MixInputs — nuke-agent example (original code).
// category: 2D multi-input | teaches: a two-input Iop reading both inputs per scanline
// verified: compile
#include "DDImage/Iop.h"
#include "DDImage/Row.h"
#include "DDImage/Knobs.h"

using namespace DD::Image;

// Cross-dissolve input 0 and input 1 by a knob. A multi-input op declares how
// many inputs it takes, then reads each into its own Row in engine().
class MixInputsIop : public Iop
{
  float _mix;
public:
  MixInputsIop(Node* node) : Iop(node), _mix(0.5f) {}

  int minimum_inputs() const override { return 2; }
  int maximum_inputs() const override { return 2; }

  void _validate(bool for_real) override
  {
    copy_info();
    merge_info(1);          // include input 1's bbox/channels in the output info
  }

  void _request(int x, int y, int r, int t, ChannelMask channels, int count) override
  {
    input(0)->request(x, y, r, t, channels, count);
    input(1)->request(x, y, r, t, channels, count);
  }

  void engine(int y, int x, int r, ChannelMask channels, Row& out) override
  {
    Row a(x, r), b(x, r);
    input0().get(y, x, r, channels, a);
    input1().get(y, x, r, channels, b);
    if (aborted())
      return;
    const float m = _mix;
    foreach (z, channels) {
      const float* A = a[z] + x;
      const float* B = b[z] + x;
      float* OUT = out.writable(z) + x;
      for (int cur = x; cur < r; ++cur)
        *OUT++ = *A++ * (1.0f - m) + *B++ * m;
    }
  }

  void knobs(Knob_Callback f) override
  {
    Float_knob(f, &_mix, "mix", "mix");
  }

  const char* Class() const override { return d.name; }
  const char* node_help() const override { return "Cross-dissolve two inputs."; }
  static const Description d;
};

static Op* build(Node* node) { return new MixInputsIop(node); }
const Op::Description MixInputsIop::d("MixInputs", build);
