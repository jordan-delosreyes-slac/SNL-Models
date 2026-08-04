import os

# ------------------------------------------------------------------------------
# ex5 - Portable SNL project file for the Simple MLP example.
#
# Layout (all relative to project.root, which defaults to one dir up from this
# file, i.e. firmware/ex5/):
#   ex5/project/MLP.py    <- this file
#   ex5/include/Network.hh
#   ex5/data/{mnist_mlp.keras, mnist_test.npy, mnist_golden.npy}
#
# The SNL library itself is pulled in from $SNL_ROOT (source the snl submodule's
# scripts/setup_env.sh so $SNL_ROOT points at firmware/submodules/snl).
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def get_project_root (project) :
    # Accept the default: one directory up from this project file => firmware/ex5
    return None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def get_products_root (project) :
    # Accept the default => project.root/products
    return None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def get_workspace (project) :
    # Accept the default => products_root/ws/{vitis_version}
    return None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def get_products (project) :

    # -------------------------------------------------
    # Include the standard SNL build project definition
    # -------------------------------------------------
    snl     = project.include ('$SNL_ROOT/project/SNL.py').module.Snl (project)
    Product = project.Product

    # ------------------------------------------------------------------
    # Runtime files, all relative to project.root (firmware/ex5).
    # snl.preserve keeps any ${ENV} variables intact for the .cfg file.
    # ------------------------------------------------------------------
    input       = snl.preserve (os.path.join (project.root, 'data', 'mnist_test.npy'))
    constants   = snl.preserve (os.path.join (project.root, 'data', 'mnist_mlp.keras'))
    golden      = snl.preserve (os.path.join (project.root, 'data', 'mnist_golden.npy'))

    csim_argv   = snl.argv (input=input, constants=constants, golden=golden, ntests=5)
    cosim_argv  = snl.argv (input=input, constants=constants, golden=golden, ntests=5)

    # -----------------------------
    # Target FPGA(s). 'f0' = its id.
    # -----------------------------
    fpgas       = [ Product.Fpga ('xcku115-flvb2104-2-i', '6', None, 'f0') ]

    # ---------------------------------------------------
    # The SNL network definition and the cfg name template
    # ---------------------------------------------------
    networks     = os.path.join (project.root, 'include', 'Network.hh')
    cfg_template = os.path.join (project.products_root,
                                 'cfg', '{vitis_version}',
                                 '{network_name}-{fpga_id}.cfg')

    # --------------------
    # Package.ip & .output
    # --------------------
    package_ip     = Product.Package.Ip (name    = 'ex5-{cfg_name}',
                                         vendor  = 'SLAC',
                                         version = 'V1.0.0',
                                         library = 'hls')
    package_output = Product.Package.Output (format = 'ip_catalog', syn = 'false')
    package        = Product.Package (ip = package_ip, output = package_output)
    vivado         = Product.Vivado  (flow = 'syn', syn_dcp = '1')

    product = snl.create_product (networks     = networks,
                                  fpgas        = fpgas,
                                  cfg_template = cfg_template,
                                  cmp_template = '{cfg_name}',
                                  csim_argv    = csim_argv,
                                  cosim_argv   = cosim_argv,
                                  package      = package,
                                  vivado       = vivado)
    return product
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def get_ip (project) :
    # Accept all defaults (see Simple_MLP / snl SNL.py for the tunable fields).
    return project.Ip ()
# ------------------------------------------------------------------------------
