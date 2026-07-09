import os

# ------------------------------------------------------------------------------
def get_project_root (project) :
    # Accept the default which is effectively the commented out value
    return None # os.path.split (os.path.split (__file__)[0])[0]
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def  get_products_root (project) :
    # Accept the default which is effectively the commented out value
    return None # os.path.join (project.root, 'products')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def get_workspace (project) :
    # Accept the default which is effectively the commented out value
    return None # os.path.join (project.products_root, 'ws', '{vitis_version}')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def get_products (project) :

    Product       = project.Product

    include_path  = os.path.join (project.root, '../', 'include')

    testbench    = os.path.join (project.root, '../src/streams/StreamsTb.cc')
    syn          = os.path.join (project.root, '../src/streams/StreamsHls.cc')
    includes     = [ {'paths' : include_path,
                      'type'  : 'rel_path'} ]

    # --------------------------------------------
    # Define the wildcard to select the Seed files
    # -------------------------------------------
    stream_seeds = os.path.join (include_path, "seeds", "Seed*.hh")

    # --------------------------------------------
    # These are included via a special #define
    # --------------------------------------------
    defines      = [ {'name'     : 'STREAM_SEED',   # #include STREAM_SEED
                      'value'    : '{seed_path}',   # The value of STREAM_SEED
                      'type'     :  'rel_path',     # Define as a relative path
                      'rel_path' : include_path } ] # Relative to this path

    build        = { 'top'       : 'doit',
                     'tb'        : [ { 'files'    : testbench,
                                       'includes' :  includes,
                                       'defines'  :   defines} ],
                     'syn'       : [ { 'files'    :       syn,
                                       'includes' :  includes} ],
                    'csim_argv'  : '',
                    'cosim_argv' : ''}

    # ------------------------------------
    # The following symbolics are exported to be used in
    # configuration and component name generation
    #     fpga_part fpga_clock and fpga_id
    # ------------------------------------
    fpgas        = [ Product.Fpga ('xcku115-flvb2104-2-i', '6',  None, '6ns'),
                     Product.Fpga ('xcku115-flvb2104-2-i', '5',  None, '5ns')]

    # --------------------------------------------------------------------------
    # The component is constructed for the build, the seed files, and FPGAs
    # The 'build', 'seed',  and 'fpga' act as prefixes for the attributes.
    #
    # Have already encountered the FPGAs attributes
    #     fpga                - The fully Fpga class
    #     fpga_part           - The Fpga part
    #     fpga_clock          - The fpga clock
    #     fpga_unceratinity.  - The fpga clock uncertainity
    #     fpga_id             - User assigned identifier
    #
    # For the files these attributes are
    #     seed_path          - Full path to the include file
    #     seed_dir           - The directory of the include file
    #     seed_name          - The file name of include file
    #     seed_ext           - The file extension of the inclde file
    # The 'defines' uses {seed_path} as the logical symbol for the include file
    #
    # Note that the Product.Builds,Files,Fpgas can be specified multiple times
    # as long as a unique prefix is given for each instance.
    # -------------------------------------------------------------------------
    components   = (Product.Builds ('build', [['stream', build]]),
                    Product.Files  ('seed',     stream_seeds),
                    Product.Fpgas  ('fpga',           fpgas))

    # -----------------------------------------------------------------------
    # Construct the configuration file name template to create a unique name.
    #
    # To ensure uniqueness, in general, it must contain a symbolic name
    # from each of the components classes, here Builds, Files, Fpgas.
    # The exception is if the class has only 1 member.
    #
    # In addition to being unique, it is good to select a name giving an
    # idea of what the component is all about. Here 'build_id' and 'fpga_id'
    # are specified in this file.  The 'seed_name' is taken from the file
    # name of the compile-time included files - chose wisely.
    #
    # NOTE: Text can also be included to help with clarity.
    #       B{build_id}-I{seed_name}-F{fpga_id}
    #
    #  e.g.  products/cfg/2024.2/streamA--Seed1-6ns.cfg
    # -----------------------------------------------------------------------
    cfg_template = (os.path.join (project.products_root,
                                  'cfg',
                                  '{vitis_version}',
                                  '{build_id}-{seed_name}-{fpga_id}.cfg'))

    # -----------------------------------------------
    # Name the component after the configuration file
    # -----------------------------------------------
    cmp_template = '{cfg_name}'


    targets      = [ { 'Components'        :   components,
                       'SourceFiles'       :       'seed',
                       'ConfigurationName' : cfg_template,
                       'ComponentName'     : cmp_template } ]

    package_ip   = Product.Package.Ip (name    = '{cfg_name}',
                                       vendor  = 'SLAC',
                                       version = '1.0.0',
                                       library = 'hls')

    package_output = Product.Package.Output (format    = 'ip_catalog',
                                             syn       = 'false')

    vivado         = Product.Vivado  (flow ='syn',     syn_dcp = '1')


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
