import os

# ------------------------------------------------------------------------------
# agent_ml_training0 - SNL project file for 3-layer MNIST CNN.
#
# Layout:
#   agent/agent_ml_training0/project/CNN.py    <- this file
#   agent/agent_ml_training0/include/Network.hh
#   agent/agent_ml_training0/data/{mnist_cnn.keras, mnist_cnn_test.npy,
#                                  mnist_cnn_golden.npy}
# ------------------------------------------------------------------------------


def get_project_root (project) :
    return None


def get_products_root (project) :
    return None


def get_workspace (project) :
    return None


def get_products (project) :

    snl     = project.include ('$SNL_ROOT/project/SNL.py').module.Snl (project)
    Product = project.Product

    input       = snl.preserve (os.path.join (project.root, 'data', 'mnist_cnn_test.npy'))
    constants   = snl.preserve (os.path.join (project.root, 'data', 'mnist_cnn.keras'))
    golden      = snl.preserve (os.path.join (project.root, 'data', 'mnist_cnn_golden.npy'))

    csim_argv   = snl.argv (input=input, constants=constants, golden=golden, ntests=5)
    cosim_argv  = snl.argv (input=input, constants=constants, golden=golden, ntests=5)

    fpgas       = [ Product.Fpga ('xcku115-flvb2104-2-i', '5', None, 'f0') ]

    networks     = os.path.join (project.root, 'include', 'Network.hh')
    cfg_template = os.path.join (project.products_root,
                                 'cfg', '{vitis_version}',
                                 '{network_name}-{fpga_id}.cfg')

    package_ip     = Product.Package.Ip (name    = 'agent_ml_training0-{cfg_name}',
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


def get_ip (project) :
    return project.Ip ()
