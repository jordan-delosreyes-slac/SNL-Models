// -*-Mode: C++;-*-

#ifndef __AGENT_CNN_NETWORK_HH__
#define __AGENT_CNN_NETWORK_HH__

// -----------------------------------------------------------------------------
// agent_ml_training0 - 3-layer CNN for MNIST (matches train_cnn.py)
//
//   Input   : (28, 28, 1)
//   Conv2D  : 8  filters, 3x3, valid, ReLU    -> (26, 26,  8)   Layer0
//   MaxPool : 2x2, stride 2                   -> (13, 13,  8)   Layer1
//   Conv2D  : 16 filters, 3x3, valid, ReLU    -> (11, 11, 16)   Layer2
//   MaxPool : 2x2, stride 2                   -> ( 5,  5, 16)   Layer3
//   Flatten -> Dense(10, Softmax)                                Layer4
// -----------------------------------------------------------------------------

#include "snl/parameters/Conv2D-Parameters.hh"
#include "snl/parameters/MaxPooling2D-Parameters.hh"
#include "snl/parameters/Dense2D-Parameters.hh"

#include "snl/activator/Relu.hh"
#include "snl/activator/Softmax.hh"

#include "snl/support/Standard.hh"


/* ====================================================================== */
namespace agent_cnn {
/* ---------------------------------------------------------------------- */

static constexpr auto PrtLo  = snl::printer::Level::Lo;
static constexpr auto PrtMed = snl::printer::Level::Med;
static constexpr auto PrtHi  = snl::printer::Level::Hi;

using PrintMin = snl::printer::Options<PrtLo, PrtLo, PrtLo>;

using Type      = float;
using SrcStream = snl::Stream<Type, snl::Shape<28, 28, 1>>;


/* ====================================================================== */
// Layer0: Conv2D(8, 3x3, valid, ReLU)
/* ====================================================================== */
using Layer0 = snl::parameters::Conv2D
        <snl::LayerPosition::First,
         SrcStream,
         8,  3, 3,                      // filters, kernel_h, kernel_w
         Type,                          // weight dtype
         1,  1,                         // stride
         snl::Padding::Valid,
         1,  1,                         // dilation
         1,                             // groups
         snl::activator::Relu<>,
         Type,                          // bias dtype
         snl::datatype::Auto,
         PrintMin
         >;


/* ====================================================================== */
// Layer1: MaxPool2D(2x2, stride 2)
/* ====================================================================== */
using Layer1 = snl::parameters::MaxPooling2D
        <snl::LayerPosition::Middle,
         snl::SrcStream<Layer0>,
         2, 2,                          // pool
         2, 2,                          // stride
         snl::Padding::Valid,
         snl::datatype::Auto,
         PrintMin
         >;


/* ====================================================================== */
// Layer2: Conv2D(16, 3x3, valid, ReLU)
/* ====================================================================== */
using Layer2 = snl::parameters::Conv2D
        <snl::LayerPosition::Middle,
         snl::SrcStream<Layer1>,
         16, 3, 3,
         Type,
         1,  1,
         snl::Padding::Valid,
         1,  1,
         1,
         snl::activator::Relu<>,
         Type,
         snl::datatype::Auto,
         PrintMin
         >;


/* ====================================================================== */
// Layer3: MaxPool2D(2x2, stride 2)
/* ====================================================================== */
using Layer3 = snl::parameters::MaxPooling2D
        <snl::LayerPosition::Middle,
         snl::SrcStream<Layer2>,
         2, 2,
         2, 2,
         snl::Padding::Valid,
         snl::datatype::Auto,
         PrintMin
         >;


/* ====================================================================== */
// Layer4: Dense(10, Softmax)  -- flatten 5x5x16 = 400 -> 10
/* ====================================================================== */
using Layer4 = snl::parameters::Dense
        <snl::LayerPosition::Last,
         snl::SrcStream<Layer3>,
         true,                          // flatten
         10,                            // NUM_CLASSES
         Type,
         snl::activator::Softmax<>,
         Type,
         snl::datatype::Auto,
         snl::printer::Options<PrtLo, PrtLo, PrtHi>
         >;


constexpr char const *Name () { return "AgentCNN"; }
constexpr char const *File () { return  __FILE__; }

using AgentCNN = snl::Network<snl::NetworkName<Name, File>
                              ,Layer0
                              ,Layer1
                              ,Layer2
                              ,Layer3
                              ,Layer4
                              >;

/* ---------------------------------------------------------------------- */
} /* END: namespace agent_cnn                                             */
/* ---------------------------------------------------------------------- */

using SnlNetwork = agent_cnn::AgentCNN;

#endif
