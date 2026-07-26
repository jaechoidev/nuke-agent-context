// TimeOffset — nuke-agent example (original code).
// category: 2D temporal | teaches: reading a different frame via inputContext()
// verified: compile
#include "DDImage/Iop.h"
#include "DDImage/Row.h"
#include "DDImage/Knobs.h"
#include "DDImage/OutputContext.h"

using namespace DD::Image;

// Shift the input in time: output frame N shows input frame N + offset. The
// frame shift is declared by overriding inputContext(); the pixel path is a
// plain pass-through, because Nuke fetches the shifted frame for us.
class TimeOffsetIop : public Iop
{
  int _offset;
public:
  TimeOffsetIop(Node* node) : Iop(node), _offset(-1) {}

  const OutputContext& inputContext(int i, int offset, OutputContext& ctx) const override
  {
    ctx = outputContext();
    ctx.setFrame(ctx.frame() + _offset);
    return ctx;
  }

  void _validate(bool for_real) override { copy_info(); }

  void _request(int x, int y, int r, int t, ChannelMask channels, int count) override
  {
    input(0)->request(x, y, r, t, channels, count);
  }

  void engine(int y, int x, int r, ChannelMask channels, Row& out) override
  {
    input0().get(y, x, r, channels, out);
  }

  void knobs(Knob_Callback f) override
  {
    Int_knob(f, &_offset, "offset", "frame offset");
  }

  const char* Class() const override { return d.name; }
  const char* node_help() const override { return "Offset the input in time."; }
  static const Description d;
};

static Op* build(Node* node) { return new TimeOffsetIop(node); }
const Op::Description TimeOffsetIop::d("TimeOffset", build);
