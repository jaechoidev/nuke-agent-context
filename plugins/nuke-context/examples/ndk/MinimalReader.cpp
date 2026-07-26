// MinimalReader — nuke-context example (original code).
// category: file IO | teaches: the smallest Reader subclass + Reader::Description registration
// verified: compile
#include "DDImage/Reader.h"
#include "DDImage/Row.h"

using namespace DD::Image;

// The smallest possible file reader: registers a fake ".solid" format and
// produces a constant mid-grey image for any such file. Everything
// format-specific in a real reader (parsing the header, decoding scanlines)
// happens where the constants are below; the *structure* — ctor calls
// set_info(), engine() fills scanlines on demand, a static test() sniffs the
// magic bytes, and a Reader::Description ties them together — is identical in
// every reader Foundry ships (see pngReader.cpp, dpxReader.cpp).
class solidReader : public Reader
{
public:
  solidReader(Read* r, int fd) : Reader(r)
  {
    // A real reader parses width/height/channels from the file header here.
    set_info(256, 256, 4);
  }

  // Called per scanline, on demand, possibly out of order — the same pull
  // model as an Iop. A real reader decodes the file's row y here.
  void engine(int y, int x, int r, ChannelMask mask, Row& row) override
  {
    foreach (z, mask) {
      float* out = row.writable(z);
      const float v = (z == Chan_Alpha) ? 1.0f : 0.5f;
      for (int X = x; X < r; X++)
        out[X] = v;
    }
  }

  static const Description d;
};

// Sniff the first bytes of the file. A real test() checks magic numbers
// (pngReader compares the PNG signature); returning true accepts the file.
static bool test(int, const unsigned char*, int)
{
  return true;
}

static Reader* build(Read* iop, int fd, const unsigned char*, int)
{
  return new solidReader(iop, fd);
}

// "solid\0" registers the file extension; Nuke routes Read nodes whose
// filename ends in .solid here. Reader::Description is a different type from
// Op::Description — a Reader is built per file by Read, not per node.
const Reader::Description solidReader::d("solid\0", build, test);
