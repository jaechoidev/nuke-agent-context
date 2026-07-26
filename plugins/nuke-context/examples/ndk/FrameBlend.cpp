// FrameBlend — nuke-context example (original code).
// category: 2D temporal | teaches: split_input + per-split inputContext for multi-frame access
// verified: compile
#include "DDImage/Iop.h"
#include "DDImage/Row.h"
#include "DDImage/Knobs.h"
#include "DDImage/OutputContext.h"

using namespace DD::Image;

// Average the current frame with the previous one — the minimal multi-frame
// op. Where TimeOffset *replaces* the frame (one input, shifted), this op
// needs two frames of the same input at once. The NDK's mechanism for that is
// input splitting: split_input() multiplexes one connection into N logical
// inputs, and inputContext() gives each split its own time. Nuke then treats
// input0() as "this frame" and input1() as "the previous frame" — caching,
// requests, and threading all just work (see Foundry's TemporalMedian.cpp).
class FrameBlend : public Iop
{
public:
  FrameBlend(Node* node) : Iop(node) {}

  // One wire in the graph becomes two logical inputs.
  int split_input(int) const override { return 2; }

  // Split n gets its own OutputContext: split 1 is one frame back.
  const OutputContext& inputContext(int, int n, OutputContext& ctx) const override
  {
    ctx = outputContext();
    if (n == 1)
      ctx.setFrame(ctx.frame() - 1);
    return ctx;
  }

  void _validate(bool) override { copy_info(); }

  // Declare the pull on BOTH logical inputs — miss one and its pixels are
  // silently black.
  void _request(int x, int y, int r, int t, ChannelMask channels, int count) override
  {
    input(0)->request(x, y, r, t, channels, count);
    input(1)->request(x, y, r, t, channels, count);
  }

  void engine(int y, int x, int r, ChannelMask channels, Row& out) override
  {
    Row cur(x, r), prev(x, r);
    input0().get(y, x, r, channels, cur);
    input1().get(y, x, r, channels, prev);
    foreach (z, channels) {
      const float* A = cur[z] + x;
      const float* B = prev[z] + x;
      float* O = out.writable(z) + x;
      for (int i = x; i < r; ++i)
        *O++ = (*A++ + *B++) * 0.5f;
    }
  }

  const char* Class() const override { return d.name; }
  const char* node_help() const override
  { return "Average this frame with the previous frame."; }
  static const Description d;
};

static Op* build(Node* node) { return new FrameBlend(node); }
const Op::Description FrameBlend::d("FrameBlend", build);
