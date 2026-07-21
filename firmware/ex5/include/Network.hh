// -*-Mode: C++;-*-

#ifndef __EX5_MLP_NETWORK_HH__
#define __EX5_MLP_NETWORK_HH__

// -----------------------------------------------------------------------------
// ex5 - Simple 2-layer MLP for MNIST, matching ex5/train_mlp.py
//
//   Flatten(28x28x1=784) -> Dense(64, ReLU) -> Dense(10, Softmax)
//
// Layer0 output units (64) must equal HIDDEN_UNITS in train_mlp.py
// Layer1 output units (10) must equal NUM_CLASSES in train_mlp.py
//
// SNL headers are resolved from the snl submodule include path, which the
// project file (project/MLP.py) supplies via $SNL_ROOT/include.
// -----------------------------------------------------------------------------

#include "snl/parameters/Dense2D-Parameters.hh"

#include "snl/activator/Relu.hh"
#include "snl/activator/Softmax.hh"

#include "snl/support/Standard.hh"


/* ====================================================================== */
namespace ex5_mlp {
/* ---------------------------------------------------------------------- */

static constexpr auto PrtLo = snl::printer::Level::Lo;
static constexpr auto PrtHi = snl::printer::Level::Hi;

using SrcType   = float;
using SrcStream = snl::Stream<SrcType, snl::Shape<28, 28, 1>>;

using PrintMin  = snl::printer::Options<PrtLo, PrtLo, PrtLo>;

// Type of all weights / biases / intermediate data.
// NOTE: float is good for csim/cosim correctness but expensive on the FPGA.
//       For a resource-optimized build, switch to an ap_fixed<W,I> type.
using Type = float;


/* ====================================================================== */
// Layer0: Dense(64, ReLU) - flattens 28x28x1=784 inputs to 64 outputs
/* ====================================================================== */
using Layer0 = snl::parameters::Dense
        <snl::LayerPosition::First,
         SrcStream,
         true,                           // flatten 28x28x1 -> 784
         64,                             // output units  (== HIDDEN_UNITS)
         Type,                           // WEIGHT_TYPE
         snl::activator::Relu<>,         // ACTIVATOR
         Type,                           // BIAS_TYPE
         snl::datatype::Auto,            // DST_TYPE
         PrintMin
         >;


/* ====================================================================== */
// Layer1: Dense(10, Softmax) - 10 MNIST classes
/* ====================================================================== */
using Layer1 = snl::parameters::Dense
        <snl::LayerPosition::Last,
         snl::SrcStream<Layer0>,
         true,                           // flatten
         10,                             // output units  (== NUM_CLASSES)
         Type,                           // WEIGHT_TYPE
         snl::activator::Softmax<>,      // ACTIVATOR
         Type,                           // BIAS_TYPE
         snl::datatype::Auto,            // DST_TYPE
         snl::printer::Options<PrtLo, PrtLo, PrtHi>
         >;


constexpr char const *Name () { return "Ex5MLP"; }
constexpr char const *File () { return  __FILE__; }

using Ex5MLP = snl::Network<snl::NetworkName<Name, File>
                            ,Layer0
                            ,Layer1
                            >;

/* ---------------------------------------------------------------------- */
} /* END: namespace ex5_mlp                                               */
/* ---------------------------------------------------------------------- */

using SnlNetwork = ex5_mlp::Ex5MLP;

#endif
