// -*-Mode: C++;-*-

/* ---------------------------------------------------------------------- *//*!
   \file   streams/StreamsTb.cc
   \brief  Defines the top level testbed file
   \author JJRussell - russell@slac.stanford.edu

   \par
    The test bench program of the project to demonstrate the hlsBs build
    system.  What is does is completely unimportant.

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
 * 2026.06.30 jjr Target of hlsBs demonstation/tutorial
\* ---------------------------------------------------------------------- */


#include "streams/Streams.hh"
#include "ap_axi_sdata.h"
#include "hls_stream.h"
#include <iostream>

#include <getopt.h>

// ----------------------------------------------------------------------
// If defined, include the file defining the constants seed value
// ----------------------------------------------------------------------
#ifdef   STREAM_SEED
#include STREAM_SEED
#else
static const char *source = "Internal";
constexpr int inc_seed = 0;
#endif

#ifdef DEF_SEED
static const auto def_seed = DEF_SEED;
#else
constexpr int     def_seed = 0;
#endif
// ----------------------------------------------------------------------


// ----------------------------------------------------------------------
// Local prototypes
// ----------------------------------------------------------------------
static void    fill (SrcStream   &srcStream, int n);
static int    check (DstStream       &dstStream,
                     Constants const &constants,
                     int                  ntest,
                     int                     n);
static void compose (SrcStream_t &src, int value, bool last);
// ----------------------------------------------------------------------


/* ---------------------------------------------------------------------- *//*!

  \brief Parses the command line parameters
                                                                          */
/* ---------------------------------------------------------------------- */
class Parameters
{
public:
   Parameters (int argc, char *const argv[]);

public:
   int m_ntests;
};
/* ---------------------------------------------------------------------- */


/* ---------------------------------------------------------------------- */
int main (int argc, char *const argv[])
{
   SrcStream srcStream;
   DstStream dstStream;
   static auto constants = std::make_tuple (Constants0(inc_seed),
                                            Constants0(def_seed));
   int           status = 0;
   Parameters    prms (argc, argv);
   auto ntests = prms.m_ntests;

   std::cout << '\n'
             << "Stream.source = " << source << '\n'
             << "      .incval = " << std::setw (3) << inc_seed << '\n'
             << "      .defval = " << std::setw (3) << def_seed << '\n'
             << "       ntests = " << std::setw (3) << ntests   << '\n'
             << std::endl;

   // ------------------
   // Load the constants
   // ------------------
   bool loadFlag = true;
   doit (srcStream, dstStream, constants, loadFlag);
   loadFlag = false;

   // -------------
   // Run the tests
   // -------------
   for (int itest = 0; itest < ntests; ++itest)
   {
      fill  (srcStream, NValues);
      doit  (srcStream, dstStream, constants, loadFlag);
      status = check   (dstStream, constants, itest, NValues);
      if (status)
      {
         break;
      }
   }

   std::cout << std::endl;
   return status;
}
/* ---------------------------------------------------------------------- */


/* ---------------------------------------------------------------------- *//*!

  \brief Parses the command line parameters

  \param[in] argc:  The command line argument count
  \param[in] argv:  the command line arugments
                                                                          */
/* ---------------------------------------------------------------------- */
Parameters::Parameters (int argc, char *const argv[])
{
   static struct option const Opts[] =
   {
      { "ntests", required_argument, 0, 'n'},
      {       0,                  0, 0,  0 }
   };


   // Default to 5 tests
   m_ntests = 5;

   // Extract the command line parameters
   while (1)
   {
      int odx;
      char c = getopt_long (argc, argv, "n:", Opts, &odx);
      if (c == '?') continue;
      if (c == -1 ) break;

      switch (c)
      {
      case 'n' :
      {
         m_ntests = atoi (optarg);
         break;
      }
      }
   }

   return;
}
/* ---------------------------------------------------------------------- */


/* ---------------------------------------------------------------------- *//*!

  \brief Fill the source stream

  \param[out] srcStream The stream to fill
  \param[in[          n The number of data elements to add
                                                                          */
/* ---------------------------------------------------------------------- */
static void fill (SrcStream &srcStream, int n)
{
   SrcStream_t src;

   for (int j = 0; j < n; ++j)
   {
      auto last = (j== (n - 1));
      compose (src, j, last);
      srcStream.write (src);
   }
}
/* ---------------------------------------------------------------------- */


/* ---------------------------------------------------------------------- *//*!

 \brief Checks the results match the computed expected results

 \param[in] dstStream The output/destination stream to check
 \param[in[ constants The constants giving the modification to the stream
 \param[in]     itest The test number
 \param[in]         n The number of elements to check
                                                                          */
/* ---------------------------------------------------------------------- */
static int check (DstStream       &dstStream,
                  Constants const &constants,
                  int                  itest,
                  int                      n)
{
   DstStream_t dst;
   int         nerrs = 0;

   for (int j = 0; j < n; ++j)
   {
      bool last = j == (n - 1);
      dstStream.read (dst);

      // ------------------------------------------------------------
      // Check that the gotten data value == the expected data value
      // ------------------------------------------------------------
      auto      got = dst;
      int add       = 1;
      auto expected = j
                    + std::get<0>(constants).m_values[j]
                    + std::get<1>(constants).m_values[j] + add;

      if (got != expected)
      {
         nerrs += 1;
         std::cerr << "ERROR: Results mismatch at " << j
                   << "       Expected " << expected << " Got " << got << '\n';
      }
   }


   const auto status = nerrs ? "Failed" : "Success";
   std::cout << std::setw (3) << itest << ". " << status << std::endl;
   return nerrs;
}
/* ---------------------------------------------------------------------- */


/* ---------------------------------------------------------------------- *//*!

  \brief Set the data value in the stream

 \param[in] srcStream The stream to add the data element to
 \param[in]     value The value to add
 \param[in]      last Is this the last value
                                                                          */
/* ---------------------------------------------------------------------- */
static void compose (SrcStream_t                    &src,
                     int                          value,
                     __attribute__ ((unused)) bool last)
{
   src = value;
   return;
}
/* ---------------------------------------------------------------------- */
