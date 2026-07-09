import os


def get_project_root (project) :
    # -------------------------------------------------------------
    # This is the default.  It can be used  when the project file
    # is in a directory immediately below the project root. It is
    # shown here just to illustrate it.
    #
    # If the default is acceptable, this method can be omitted
    # or return None.  Returning None is preferred since it serves
    # a visual reminder that it can be set to anything.
    #
    # While the project file directory name is suggested to be
    # 'project/', it is not necessary. To accept the default, the
    # only requirement is that it is in a subdirectory of the
    # project root.
    # -------------------------------------------------------------
    return os.path.split (os.path.split (__file__)[0])[0]
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def  get_products_root (project) :
    # ------------------------------------------------------------
    # This is the default, but illustrates the recommended way is
    # locate it relative to the project root.
    # ------------------------------------------------------------
    return os.path.join (project.root, 'products')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def get_workspace (project) :
    # ------------------------------------------------------------
    # This is the default, but illustrates the recommended way is
    # locate it relative to the project's products root.
    # ------------------------------------------------------------
    return os.path.join (project.products_root, 'ws', '{vitis_version}')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def get_products (project) :

    Product       = project.Product

    testbench    = os.path.join (project.root, '../src/streams/StreamsTb.cc')
    syn          = os.path.join (project.root, '../src/streams/StreamsHls.cc')

    # --------------------------------------------------------
    # Define the include paths and make them a relative path.
    #
    # As the 'paths' key suggests this can be a list or tuple.
    #
    # Suggestions:
    #  1. Specify all includes with the same 'type' (eiher
    #     'abs_path' or 'rel_path' together as a single path,
    #      list or tuple.
    #
    #  2. Be specific, each file in the build specification
    #     that immediately follows, should only have the
    #     includes it needs. A common problem is not that an
    #     include file isn't found, but that a overly broad
    #     set of include paths finds the wrong thing.
    #     In this very simple example, there is only one
    #     common include path.
    # -------------------------------------------------------
    includes     = [ {'paths' : os.path.join (project.root,'../include'),
                      'type'  : 'rel_path'} ]

    # --------------------------------------------------------
    # This defines the ingredients to build the HLS test bench,
    # synthesis and cosim.
    # --------------------------------------------------------
    builds       = { 'top'        : 'doit',
                     'tb'         : [ { 'files'     : testbench,
                                        'includes' :  includes} ],
                     'syn'        : [ { 'files'     :       syn,
                                        'includes' :  includes} ],
                     'csim_argv'  : '',
                     'cosim_argv' : ''}

    # --------------------------------------------------
    # The following symbolics are exported to be used in
    # configuration and component name generation
    #     fpga_part fpga_clock and fpga_id
    # --------------------------------------------------
    fpgas        = [ Product.Fpga ('xcku115-flvb2104-2-i', '6',  None, 'f0')]

    # -----------------------------------------------
    # This binds a set of builds and a set of FPGAs.
    # The name 'components' is just a local variable,
    # so its only import is to a readability. Don't
    # think it has succeeded.
    # HELP: A better name is needed.
    #
    # As the plural 'components' suggests, this may be
    # a single, list or tuple of components. If there
    # is a need for multiple components, binding them
    # to the same configuration and component file path
    # templates, will ensure uniform naming.
    # ------------------------------------------------
    components   = ( Product.Builds ('build', ['streams', builds]),
                     Product.Fpgas  ('fpga',               fpgas) )

    # --------------------------------------------------
    # Configuration file name template
    # Generates the name of the configuration file.
    # Here:  products/cfg/{vitis_version}/{build_id}.cfg
    #  e.g.  products/cfg/2024.2/streams.cfg
    # --------------------------------------------------
    cfg_template = (os.path.join (project.products_root,
                                  'cfg',
                                  '{vitis_version}',
                                  '{build_id}.cfg'))

    # -----------------------------------------------
    # Name the component after the configuration file
    # -----------------------------------------------
    cmp_template = '{cfg_name}'


    # ---------------------------------------------------
    # The fully specified target is the components bound
    # to it configuration and component names
    #
    # As the plural 'targets' suggestions this may be a
    # single, list or tuple.
    # --------------------------------------------------
    targets      = { 'Components'        : components,
                     'ConfigurationName' : cfg_template,
                     'ComponentName'     : cmp_template }

    # --------------------------------------------------
    # Fill out the package IP description
    # The version can also be the symbolic {git_tag}
    # NOTE: Other suggestions are welcomed. For example
    #       a command line parameter (ip_version?) could
    #       be useful.
    # --------------------------------------------------
    package_ip   = Product.Package.Ip (name    = '{cfg_name}',
                                       vendor  = 'SLAC',
                                       version = '1.0.0',
                                       library = 'hls')

    # -------------------------------------------------
    # Is there any reason these could not be defaulted?
    # -------------------------------------------------
    package_output = Product.Package.Output (format = 'ip_catalog',
                                             syn    = 'false')

    vivado         = Product.Vivado  (flow ='syn',     syn_dcp = '1')


    # -----------------------------------------------------
    # As the plural 'get_products' suggests this may return
    # either a single, list or tuple of products.
    # -----------------------------------------------------
    return Product (project = project,
                    targets = targets,
                    package = Product.Package (ip     = package_ip,
                                               output = package_output),
                    vivado  = vivado)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def get_ip (project) :
    ip = project.Ip \
    (
        dir      =  os.path.join (project.products_root,
                                  'ip', '{vitis_version}'),
        zip_file = '{cmp_name}',
        family   = ('artix7,kintex7,virtex7,zynq,kintexu,virtexu,kintexuplus,'
                    'virtexuplus,virtexuplusHBM,zynqplus,zynquplusRFSOC,veral'),

        # The dcp rename pieces are
        #    dcp_rename : What to rename it to
        #                 By default this follows the cmp_name
        #
        #    dcp_file   : The new file name
        #                 Befault =  '{dcp_rename}'
        #                 '{cmp_name} is also permitted
        #
        #    dgn_dir    : The directory for the journal and log files
        #                 Default = '{dcp_rename}'
        #                 '{cmp_name} is also permitted
        #
        #    jou_file   : The journal file name
        #                 Default = '{dcp_name}' - i.e. the dcp file name
        #                 '{dcp_rename}' or '{cmp_name}' are also permitted
        #
        #    log_file   : The log file name
        #                 Default = '{dcp_name}' - i.e. the dcp_file name
        #                 '{dcp_rename}' or '{cmp_name}' are also permitted
        #
        # Using the defaults names everything after the component
        # -----------------------------------------------------------------

        # ----------------------------------------------------------------
        # The below are all the defaults and can be omitted or set to None
        # The are just provided here for illustration
        # ----------------------------------------------------------------
        #dcp_rename = '{cmp_name}',
        #dcp_file   = '{dcp_rename}',

        #dgn_dir    = 'dgn/',
        #jou_file   = '{dcp_name}',
        #log_file   = '{dcp_name}'
    )

    return ip
# ------------------------------------------------------------------------------
