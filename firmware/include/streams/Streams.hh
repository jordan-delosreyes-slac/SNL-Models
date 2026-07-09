#ifndef __STREAMS_DF_HH__
#define __STREAMS_DF_HH__

#include "ap_axi_sdata.h"
#include "hls_stream.h"

static constexpr auto NValues=100;


// Non-axis data type
using SrcStream_t = int;
using DstStream_t = int;
using TmpStream_t = int;


// Straight hls streams
using SrcStream = hls::stream<SrcStream_t>;
using DstStream = hls::stream<DstStream_t>;
using TmpStream = hls::stream<DstStream_t>;



class Constants0
{
public:
   Constants0 () { return; }
   Constants0 (int seed)
   {
      for (int idx = 0; idx < NValues; ++idx)
      {
         m_values[idx] = seed + idx;
      }

      return;
   }

public:
   int m_values[NValues];
};

using Constants=std::tuple<Constants0, Constants0>;

void doit (SrcStream                &src,
           DstStream                &dst,
           Constants const &in_constants,
           bool                    load);


#endif
