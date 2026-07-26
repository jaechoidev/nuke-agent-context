// EdgeDetect — nuke-agent example (original code).
// category: 2D general | teaches: Iop reading neighbouring pixels via a Tile
// verified: compile
#include "DDImage/Iop.h"
#include "DDImage/Row.h"
#include "DDImage/Tile.h"
#include "DDImage/Knobs.h"
#include <cmath>

using namespace DD::Image;

// Sobel edge magnitude. Needs the 3x3 neighbourhood of each output pixel, so it
// pads the output bbox (_validate), requests the padded input (_request), and
// reads neighbours through a Tile (engine). This is the canonical "output needs
// nearby input" pattern -- distinct from PixelIop, which cannot see neighbours.
class EdgeDetectIop : public Iop
{
public:
  EdgeDetectIop(Node* node) : Iop(node) {}

  void _validate(bool for_real) override
  {
    copy_info();
    info_.pad(1);                 // one pixel of margin for the 3x3 kernel
  }

  void _request(int x, int y, int r, int t, ChannelMask channels, int count) override
  {
    input(0)->request(x - 1, y - 1, r + 1, t + 1, channels, count);
  }

  void engine(int y, int x, int r, ChannelMask channels, Row& out) override
  {
    Tile tile(input0(), x - 1, y - 1, r + 1, y + 1, channels);
    if (aborted())
      return;

    foreach (z, channels) {
      float* OUT = out.writable(z) + x;
      for (int cur = x; cur < r; ++cur) {
        const int cl = tile.clampx(cur - 1), cc = tile.clampx(cur), cr = tile.clampx(cur + 1);
        const int yb = tile.clampy(y - 1), yc = tile.clampy(y), yt = tile.clampy(y + 1);
        const float gx =
            -tile[z][yb][cl] - 2.0f * tile[z][yc][cl] - tile[z][yt][cl]
            + tile[z][yb][cr] + 2.0f * tile[z][yc][cr] + tile[z][yt][cr];
        const float gy =
            -tile[z][yb][cl] - 2.0f * tile[z][yb][cc] - tile[z][yb][cr]
            + tile[z][yt][cl] + 2.0f * tile[z][yt][cc] + tile[z][yt][cr];
        *OUT++ = std::sqrt(gx * gx + gy * gy);
      }
    }
  }

  void knobs(Knob_Callback) override {}
  const char* Class() const override { return d.name; }
  const char* node_help() const override { return "Sobel edge magnitude."; }
  static const Description d;
};

static Op* build(Node* node) { return new EdgeDetectIop(node); }
const Op::Description EdgeDetectIop::d("EdgeDetect", build);
