#include "streams/Streams.hh"

#include <iostream>
#include <iomanip>
#include <tuple>

template<typename SRC_STREAM,
         typename DST_STREAM,
         typename CONSTANTS>
class Layer
{
public:
   Layer () { return; }

   using DstStream = DST_STREAM;

public:
   static void  process (SRC_STREAM       &srcStream,
                         DST_STREAM       &dstStream,
                         CONSTANTS  const &constants);
};

using Layer0 = Layer<SrcStream, TmpStream, Constants0>;
using Layer1 = Layer<TmpStream, TmpStream, Constants0>;


using Network = std::tuple<Layer0, Layer1>;


static void load (Constants       &out, Constants const  &in);
static void calc (Network         &layers,
                  SrcStream       &srcStream,
                  DstStream       &dstStream,
                  Constants const &constants);

template <typename SRC_STREAM,   typename DST_STREAM>
static void  copy (SRC_STREAM &dstStream, DST_STREAM &srcStream);


/*  -------------------------------------------------------------------- *//*!
 *
 *  \brief HLS top level method
 *
 *  \param[ in]    srcStream The stream sourcing the data
 *  \param[out]    dstStream The stream sinking  the data
 *  \param[ in] in_constants Constants that are just added to the source data
 *  \param[ in]     loadFlag If true, just load the constants to local memory
 *                           If false, just to the calculation
 *
 *                                                                       */
/*  -------------------------------------------------------------------- */
void doit (SrcStream          &srcStream,
           DstStream          &dstStream,
           Constants const &in_constants,
           bool                 loadFlag)
{
   #pragma HLS INTERFACE mode=axis      port=srcStream
   #pragma HLS INTERFACE mode=axis      port=dstStream
   #pragma HLS INTERFACE mode=s_axilite port=in_constants
   #pragma HLS INTERFACE mode=s_axilite port=loadFlag

   // -----------------------------------------------------------
   // Local copy of the constants that persist after initial load
   // -----------------------------------------------------------
   static Constants constants;

   static Network layers;
   if (loadFlag)
   {
      load (constants, in_constants);
   }
   else
   {
      calc (layers, srcStream, dstStream, constants);
   }

   return;

}
/*  -------------------------------------------------------------------- */


/*  -------------------------------------------------------------------- *//*!
 *
 *  \brief Load the input constants into the local copy
 *
 *  \param[out] out The local copy of the constants to be loaded
 *  \param[ in]  in The source (input) constants
 *                                                                       */
/*  -------------------------------------------------------------------- */
static void load (Constants &out, Constants const &in)
{
   #pragma HLS INLINE off
   #pragma HLS STABLE variable=in

   out = in;

   return;
}
/*  -------------------------------------------------------------------- */




/*  -------------------------------------------------------------------- *//*!
 *
 *  \brief A dummy calcuation that just adds the constants to the input
 *         stream and pushes it to the output stream
 *
 *  \param[out] dstStream The output/destination stream
 *  \param[ in] srcStream The  input/source      stream
 *  \param[ in] constants The source of the constants to be added
 *                                                                       */
/*  -------------------------------------------------------------------- */
static void calc (Network           &layers,
                  SrcStream      &srcStream,
                  DstStream      &dstStream,
                  Constants const &constants)
{
//   #pragma HLS INLINE off
   #pragma HLS STABLE variable=constants
   #pragma HLS DATAFLOW

   typename std::tuple_element_t<0, Network>::DstStream l0_l1 ("l0_l1");
   typename std::tuple_element_t<1, Network>::DstStream l1_l2 ("l1_l2");

   auto const &c0 = std::get<0>(constants);
   auto const &c1 = std::get<1>(constants);

   std::get<0>(layers).process (srcStream, l0_l1, c0);
   std::get<1>(layers).process (l0_l1,     l1_l2, c1);
   copy    (l1_l2,     dstStream);

   return;
}
/*  -------------------------------------------------------------------- */

/*  -------------------------------------------------------------------- */
template   <typename SRC_STREAM,
            typename DST_STREAM,
            typename  CONSTANTS>
void Layer          <SRC_STREAM,
                     DST_STREAM,
                      CONSTANTS>::
process (SRC_STREAM       &srcStream,
         DST_STREAM       &dstStream,
         CONSTANTS  const &constants)
{
   add_loop: for (int idx = 0; idx < NValues; ++idx)
   {
      auto tmp = srcStream.read ();
      tmp     += constants.m_values[idx];
      dstStream.write (tmp);
   }

   return;
}
/*  -------------------------------------------------------------------- */


/*  -------------------------------------------------------------------- */
template<typename SRC_STREAM,  typename  DST_STREAM>
static void copy (SRC_STREAM &srcStream, DST_STREAM &dstStream)
{

   copy_loop: for (int idx = 0; idx < NValues; ++idx)
   {
      auto tmp = srcStream.read ();
      tmp += 1;
      dstStream.write (tmp);
   }

   return;
}
/*  -------------------------------------------------------------------- */
