# ------------------------------------------------------------------------
#
# Description:
#  Sets up the hlsBs-examples and changes the directory to hlsBs-examples
#
# Usage:
#   source <hlsBs-examples-dir>/scripts/setup_env.sh
#
# Parameters:
#   None
#
# Details:
#  A shell function called exSelect is defined which is used to select
#  the example project.  Currently there are 3 example projects,
#      ex0,ex1,ex2
#
# Usage:
# $ exSelect ex1  # Selects example project 'ex1'
# ------------------------------------------------------------------------


# ------------------------------------------------------------------------
#
# This function is merely a way to keep bash variables local. By default
# bash variables in a sourced script are made available in the calling
# scripts shell.  This can have deadly consequences if some other script
# is invoked which uses the same variable name.
#
# In this case, the ruckus setup script is invoked, which may or may not
# use the same variable names. By placing this in a function, the
# variables are kept local.
# ------------------------------------------------------------------------
function setup ()
{
    # --------------------------------
    # Get the full path of this script
    # --------------------------------
    called=${BASH_SOURCE[0]}

    # ------------------------------
    # Make sure the file was sourced
    # ------------------------------
    if [ $called != $0 ]; then
        # ---------------------------------------
        # Correctly called by sourcing the script
        # Get the absolute path to the script
        # ---------------------------------------
        if [ `uname` == Linux ]; then script_fn=`readlink -fn $called`
        else
            echo "This script only works on Linux"
            return -1
        fi
    else
        # ---------------------------------------------------
        # Incorrectly called by directly executing the script
        # ---------------------------------------------------
        echo "Error: This file must be sourced"
        return -1
    fi

    local script_dir=`dirname $script_fn`
    local prj_root=`dirname $script_dir`

    # Saved under a distinct name: sourcing the snl env below reassigns
    # `prj_root` in this dynamic scope, so keep our own copy for the final cd.
    local hlsbs_root=${prj_root}

    # ------------------------------
    # Source the ruckus setup script
    # ------------------------------
    source ${prj_root}/submodules/ruckus/vitis/hlsBs/scripts/setup_hls.sh

    # -----------------------------------------------------------
    # Make the names of the 3 example's Project scripts available
    # Design choice:
    #   1. Define as environment variables
    #      Advantage: Can more easily set the project on the
    #                 command line, i.e. --project=ex1
    #   2. Could also be defined in the exSelect function
    #      Advantage: Does not pollute the  environment variables
    # -----------------------------------------------------------
    export ex0=${prj_root}/ex0/project/Streams.py
    export ex1=${prj_root}/ex1/project/Streams.py
    export ex2=${prj_root}/ex2/project/Streams.py
    export ex3=${prj_root}/ex3/project/Streams.py
    export ex4=${prj_root}/ex4/project/Streams.py
    export ex5=${prj_root}/ex5/project/MLP.py

    # -----------------------------------------------------------
    # Source the SNL submodule env. Sets SNL_ROOT and adds the
    # acquirer/adapter build commands (SnlBuildAcquirerAll,
    # SnlBuildAdapter) needed by the ex5 SNL ML example.
    # -----------------------------------------------------------
    source ${prj_root}/submodules/snl/scripts/setup_env.sh

    # ---------------------------------------
    # Change to hlsBs-examples root directory
    # ---------------------------------------
    cd ${hlsbs_root}
}
# ------------------------------------------------------------------------


# ----------------------------------------------------
# Execute the setup
# Then unset the setup function name,
# This keeps 'setup' from polluting the caller's shell
# ----------------------------------------------------
setup;
unset -f setup
# ----------------------------------------------------


# ------------------------------------------------------------------------
#
# Description:
#  Shell function to select the example project
#
# Parameters
#  The example to select, i.e. one of ex0, ex1, ex2
#
# Usage:
#  $ exSelect [ ex0 | ex1 | ex2 | ex3 ]
#
# Example:
#  $ exSelect ex1
#  Select ex1 as the project
# ------------------------------------------------------------------------
function exSelect ()
{
    x=$1
    ex=${!x}
    echo "ex = $ex"
    if [[  -f "${ex}" ]]; then
        export HLSBS_PROJECT=${ex}
    else
        echo "ERROR: No project $ex found"
        return -1
    fi
}
# ------------------------------------------------------------------------
