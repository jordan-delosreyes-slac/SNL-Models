// -*-Mode: C++;-*-
/* ---------------------------------------------------------------------- _//_!
  \author Jordan Delos Reyes - jdr@slac.stanford.edu
  \par
   This file is part of the ML_AI software platform. It is subject to
   the license terms in the LICENSE.txt file found in the top-level
   directory of this distribution and at:
   \verbatim
     https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
   \endverbatim
\* ---------------------------------------------------------------------- */

/* ---------------------------------------------------------------------- *\
 *
 * HISTORY
 * -------
 *
 * DATE       WHO WHAT
 * ---------- --- ---------------------------------------------------------
 * 2026.06.10 jdr Created from miniVGG Fashion-MNIST Keras model
 *                (8,434 params, 0.8854 test accuracy, "valid" padding)
 *
\* ---------------------------------------------------------------------- */

#ifndef MINIVGG_NETWORK_HH
#define MINIVGG_NETWORK_HH

// ---------------------------------------------------------------
// Should only include those layers, activators and types that are
// actually used.  Including more can increase compilation time.
// ---------------------------------------------------------------
#include "snl/parameters/Conv2D-Parameters.hh"
#include "snl/parameters/MaxPooling2D-Parameters.hh"
#include "snl/parameters/Dense2D-Parameters.hh"
#include "snl/activator/Relu.hh"
#include "snl/activator/Softmax.hh"
#include "snl/support/Standard.hh"

/* ====================================================================== */
namespace minivgg  {
/* ---------------------------------------------------------------------- */

// ----------
// Shorthands
// ----------
static constexpr auto PrtLo  = snl::printer::Level::Lo;
static constexpr auto PrtMed = snl::printer::Level::Med;
static constexpr auto PrtHi  = snl::printer::Level::Hi;

using SrcType   = float;
using SrcStream = snl::Stream<SrcType, snl::Shape<28,28,1>>;
using PrintMin  = snl::printer::Options<PrtLo, PrtLo, PrtMed>;

// -----------------------------------
// Types of all kernel weights, biases
// -----------------------------------
using Type     = float;

/* ====================================================================== */
/* Layer0: Conv2D - 8 filters, 3x3 kernel, valid padding, relu           */
/*         Input:  (28, 28, 1)                                            */
/*         Output: (26, 26, 8)                                            */
/* ====================================================================== */
using Layer0 = snl::parameters::Conv2D
        <snl::LayerPosition::First, // First layer
         SrcStream,                 // Input stream (28x28x1)
         8,3,3,Type,                // KERNEL  :  NFILTERS, NROWS, NCOLS, type
         1,1,                       // STRIDE  :  NROWS, NCOLS
         snl::Padding::Valid,       // PADDING
         1,1,                       // DILATION: NROWS, NCOLS
         1,                         // GROUPS,
         snl::activator::Relu<>,    // ACTIVATOR
         Type,                      // BIAS_TYPE
         snl::datatype::Auto,       // DST_TYPE,
         PrintMin
         >;
/* ---------------------------------------------------------------------- */
/* END: Layer0                                                            */
/* ====================================================================== */


/* ====================================================================== */
/* Layer1: Conv2D - 8 filters, 3x3 kernel, valid padding, relu           */
/*         Input:  (26, 26, 8)                                            */
/*         Output: (24, 24, 8)                                            */
/* ====================================================================== */
using Layer1 = snl::parameters::Conv2D
        <snl::LayerPosition::Middle,
         snl::SrcStream<Layer0>,     // Input Stream
         8,3,3,Type,                 // KERNEL  :  NFILTERS, NROWS, NCOLS, Type
         1,1,                        // STRIDE  :  NROWS, NCOLS
         snl::Padding::Valid,        // PADDING
         1,1,                        // DILATION: NROWS, NCOLS
         1,                          // GROUPS
         snl::activator::Relu<>,     // ACTIVATOR
         Type,                       // BIAS_TYPE
         snl::datatype::Auto,        // DST_TYPE
         PrintMin
         >;
/* ---------------------------------------------------------------------- */
/* END: Layer1                                                            */
/* ====================================================================== */


/* ====================================================================== */
/* Layer2: MaxPooling2D - 2x2 pool, stride 2x2, valid padding            */
/*         Input:  (24, 24, 8)                                            */
/*         Output: (12, 12, 8)                                            */
/* ====================================================================== */
using Layer2 = snl::parameters::MaxPooling2D
        <snl::LayerPosition::Middle,
         snl::SrcStream<Layer1>,     // Input stream
         2,2,                        // POOLING:  NROWS, NCOLS
         2,2,                        // STRIDE :  NROWS, NCOLS,
         snl::Padding::Valid,        // PADDING
         snl::datatype::Auto,        // DST_TYPE,
         PrintMin
       >;
/* ---------------------------------------------------------------------- */
/* END: Layer2                                                            */
/* ====================================================================== */


/* ====================================================================== */
/* Layer3: Conv2D - 16 filters, 3x3 kernel, valid padding, relu          */
/*         Input:  (12, 12, 8)                                            */
/*         Output: (10, 10, 16)                                           */
/* ====================================================================== */
using Layer3 = snl::parameters::Conv2D
        <snl::LayerPosition::Middle,
         snl::SrcStream<Layer2>,     // Input Stream
         16,3,3,Type,                // KERNEL  :  NFILTERS, NROWS, NCOLS, Type
         1,1,                        // STRIDE  :  NROWS, NCOLS
         snl::Padding::Valid,        // PADDING
         1,1,                        // DILATION: NROWS, NCOLS
         1,                          // GROUPS
         snl::activator::Relu<>,     // ACTIVATOR
         Type,                       // BIAS_TYPE
         snl::datatype::Auto,        // DST_TYPE
         PrintMin
         >;
/* ---------------------------------------------------------------------- */
/* END: Layer3                                                            */
/* ====================================================================== */


/* ====================================================================== */
/* Layer4: Conv2D - 16 filters, 3x3 kernel, valid padding, relu          */
/*         Input:  (10, 10, 16)                                           */
/*         Output: (8, 8, 16)                                             */
/* ====================================================================== */
using Layer4 = snl::parameters::Conv2D
        <snl::LayerPosition::Middle,
         snl::SrcStream<Layer3>,     // Input Stream
         16,3,3,Type,                // KERNEL  :  NFILTERS, NROWS, NCOLS, Type
         1,1,                        // STRIDE  :  NROWS, NCOLS
         snl::Padding::Valid,        // PADDING
         1,1,                        // DILATION: NROWS, NCOLS
         1,                          // GROUPS
         snl::activator::Relu<>,     // ACTIVATOR
         Type,                       // BIAS_TYPE
         snl::datatype::Auto,        // DST_TYPE
         PrintMin
         >;
/* ---------------------------------------------------------------------- */
/* END: Layer4                                                            */
/* ====================================================================== */


/* ====================================================================== */
/* Layer5: MaxPooling2D - 2x2 pool, stride 2x2, valid padding            */
/*         Input:  (8, 8, 16)                                             */
/*         Output: (4, 4, 16)                                             */
/* ====================================================================== */
using Layer5 = snl::parameters::MaxPooling2D
        <snl::LayerPosition::Middle,
         snl::SrcStream<Layer4>,      // Input Stream
         2,2,                         // POOLING:  NROWS, NCOLS
         2,2,                         // STRIDE :  NROWS, NCOLS
         snl::Padding::Valid,         // PADDING
         snl::datatype::Auto,         // DST_TYPE
         PrintMin
         >;
/* ---------------------------------------------------------------------- */
/* END: Layer5                                                            */
/* ====================================================================== */


/* ====================================================================== */
/* Layer6: Dense - 16 output neurons, relu activation                     */
/*         Input:  (4, 4, 16) flattened = 256                             */
/*         Output: (16)                                                   */
/* ====================================================================== */
using Layer6 = snl::parameters::Dense
        <snl::LayerPosition::Middle,
         snl::SrcStream<Layer5>,      // Input stream
         true,                        // Flatten input
         16,                          // Number of output columns
         Type,                        // WEIGHT_TYPE,
         snl::activator::Relu<>,      // ACTIVATOR,
         Type,                        // BIAS_TYPE,
         snl::datatype::Auto,         // DST_TYPE
         PrintMin
         >;
/* ---------------------------------------------------------------------- */
/* END: Layer6                                                            */
/* ====================================================================== */


/* ====================================================================== */
/* Layer7: Dense - 10 output neurons, softmax activation                  */
/*         Input:  (16)                                                   */
/*         Output: (10)                                                   */
/* ====================================================================== */
using Layer7 = snl::parameters::Dense
        <snl::LayerPosition::Last,   // Last layer
         snl::SrcStream<Layer6>,     // Input stream
         true,                       // Flatten input
         10,                         // Number of output columns
         Type,                       // WEIGHT_TYPE,
         snl::activator::Softmax<>,  // ACTIVATOR,
         Type,                       // BIAS_TYPE,
         snl::datatype::Auto,        // DST_TYPE
         snl::printer::Options<PrtLo,PrtLo,PrtHi>
         >;
/* ---------------------------------------------------------------------- */
/* END: Layer7                                                            */
/* ====================================================================== */


constexpr char const *Name ()  { return "miniVGG"; }
constexpr char const *File ()  { return  __FILE__; }

using     MiniVGG = snl::Network<snl::NetworkName<Name, File>
                                ,Layer0
                                ,Layer1
                                ,Layer2
                                ,Layer3
                                ,Layer4
                                ,Layer5
                                ,Layer6
                                ,Layer7
                                >;
/* ---------------------------------------------------------------------- */
} /* END: namespace minivgg                                               */
/* ---------------------------------------------------------------------- */

using SnlNetwork = minivgg::MiniVGG;

#endif
