# hlsBs Examples and Tutorial
This tutorial shows how to use the HLS build system tools using 5 examples HLS projects of increasing complexity, cleverly labeled *ex0, ex1, ex2, e3, ex4*.

|  Ex | Demonstrates |
| :-- | :------ |
| ex0 | The basics |
| ex1 | Adding multiple FPGAs |
| ex2 | Uses 2 build descriptions and 2 FPGAs |
| ex3 | Generating components by wildcarding include files |
| ex4 | Generating components with #defines values |


This documentation is not meant to be complete. See the READme.md in **hlsBs** subdirectory of `ruckus` for more of a reference style documentation.

## Where is the code?
The code is in the `hlsBs-examples` repository on `github` / `slaclab`. It uses `ruckus` as a submodule, so be sure to specify *--recursive* when cloning it.

## The 30,000ft / 9144m look at **hlsBs**
This illustrates a typical **hlsBs** workflow and some of its capabilities. Don't worry if some seems mysterious; that's for the rest of this document.

Assuming a fresh login:

#### One-time each login, could be captured in a project dependent script or alias.
These are site and project specific so cannot be part of **hlsBs**.

``` bash
$ bash              # Spawn a clean shell
$ hlsLocate         # Define the site specific search path for the Vitis version settings script
$ hlsBs-examples    # Setup the hlsBs examples tutorial, project specific
$ hlsVersion 2024.2 # Select Vitis Version 2024.2, this uses the path established by hlsLocate
$ exSelect ex0      # Select the ex0 project, only relevant because there are multiple examples
```

The order of `hlsBs-examples` and `hlsVersion` does not matter.
> If there are multiple projects under a common package (*e.g.* as does **hlsBs-examples**) then there would be something similar to *exSelect* to select the current target project.

#### hlsWs, hlsCfg, One-time each new project setup (**hlsWs**) or at a structural change to the project (**hlsCfg**), *e.g.* new or changed configuration
``` bash
$ hlsWs  --create # Create the workspace
$ hlsCfg --create # Create the configuration files and components
```
#### **hlsRun**, Used almost exclusively after creating the workspace and configuration files/components
``` bash
$ hlsRun --csim=make      # Make csim.exe
$ hlsRun --csim=run       # Run csim.exe
$ hlsRun --synthesis      # Create the synthesis
$ hlsRun --cosim          # Run the CoSim
$ hlsRun --package        # Create a .dcp
$ hlsRun --implementation # Create the implementation (the .zip file)
$ hlsRun --ip             # Rename the .dcp and augment the permissiable FPGA families
```
Any combination of these stages can be run with a single **hlsRun** command
``` bash
$ hlsRun --csim=m,r                      # Do the csim make and run, abbreviations are allowed
.. or..
$ hlsRun --package --implementation --ip # Run these stages
 ..or..
$ hlsRun --all --exclude=ip              # Run all but the ip stage
```

####  hlsVersion, (optional) changes Vitis Version, then redo the above sequence
``` bash
$ hlsVersion 2025.1
```

# The Tutorial Begins

## What does the code do?
While what the code actually does is unimportant, the terse description for the interested is
- Copies an input stream -> temporary stream -> output stream, adding some constants during each copy.

# Directory Layout
This section provides context which is somewhat tangential to **hlsBs**. For the impatient, it can be skipped (goto **Setup**) and revisited later.

This tutorial uses the following layout:

``` bash
hlsBs-examples/
               firmware/
                        scripts/setup_env.sh
                        shared/
                               include/streams/    -- Shared common includes
                                       Streams.hh
                               src/streams/        -- Shared common source code
                                       Streams.cc
                        ex0/
                            project/Streams.py     -- The ex0 project file
                        ex1/
                            project/Streams.py     -- The ex1 project file
                        ex2/
                            project/Streams.py     -- The ex2 project file
                        ex3/
                            project/Streams.py     -- The ex3 project file
                        ex4/
                            project/Streams.py     -- The ex4 project file
```

Many setups will only have 1 project, but this tutorial has 5.

## Creating your own project
The above is a recommended **hlsBs** layout.  While **hlsBs** can accomodate almost any directory structure, if you are at a loss where to start, **ruckus**, the same repository that **hlsBs** lives in, contains a nice script to produce a very similar directory layout. It is a great place to start and tailor to your needs.

By default, **hlsBs** assumes the project file, a file necessary to take full advantage of **hlsBs**'s capabilities, is located in the **/project** directory directly under the project root. The project file name can be named anything; select something meaningful, not, for example 'Project.py'.

>To be technically correct, by default, **hlsBs** locates the project root with respect to the project file, *i.e.* it assumes the project root is one directory up from the project file. This means that directory containing the Project file need not be named *project/*. The import of the project root is typically file specifications (e.g. the source files, include paths) are made relative to the it. Again, this is more by convention than a requirement of **hlsBs**.

**SUGGESTIONS:**
- If you have more than one project under a common directory/repo, isolate the shared code as above.
- Create a root directory for each project, here these, *ex0, ex1, ex2, ex3, ex4*.
- Create a directory called *project/* under the project root directory to hold the Project definition file.
	- More on the Project file later.
- Create any project code specific directories in the same fashion as the shared code but under the project root.

**RECOMMENDATION:** While **hlsBs** does not require this layout, providing simple ways to specify any layout, there should be a good reason for not using it. Having conventions is good when others use your project.


# Setup
This is one of many different ways to do the setup.  It comes down to personal preference and project needs.  It has been found convenient and **hlsBs** friendly. A design goal was to have as few references to absolute file paths as possible and having them well contained. **hlsBs** requires only two such paths. This is the next's section topic.

## Define Site and User Specifics
Define 2 alliases. Neither can be part of the `hlsBs-examples` repository, since they must contain absolute file paths specific to the site and the project.

- hlsLocate - locates the directory tree(s) where the Xilinx installations are found.
	- The location of Xilinx installations is site specific.
- hlsBs-examples - sources the hlsBs-examples setup script.
	- The location of the `hlsBs-examples` project is user dependent.

**NOTE:** The names and even using aliases are merely suggestions. Any other means that accomplishes the same ends is fine.

### hlsLocate
This is used by **hlsVersion** to locate and source the settings script for a specified Vitis Version.
> For definitiveness, the values used are what would be used at SLAC.
```
alias hlsLocate='export HLSBS_XILINX_SETUP=/sdf/group/faders/tools/xilinx/\$\{version\}'
```
> Locating the correct settings involves a file search. Overly broad searches can be slow. The variable **version** translates to the Vitis version requested by **hlsVersion**

**Caution:** Note the escaping when specifying **version**.  This defers the translation till the invocation by **hlsVersion**.

### hlsBs-examples
This sources the project setup script.

``` bash
alias hlsBs-examples="source <path/to>/hlsBs-examples/firmware/scripts/setup_env.
```

**RECOMMENDATIONS:**
- Name the alias sourcing the project's setup script after your project.
- Since these paths are relatively stable, create a shell script where all your personal aliases are defined and enter these 2 into it.
	- Source this alias defining script in your login script, making the aliases available for use
- Since typically `ruckus` will be a submodule of the user's project,  source the **hlsBs** setup script by a relative path within the project's setup script.



# Let the Tutorial Begin
Presumably one has logged into a bash shell, defined the 2 above aliases and is ready to try the tutorial.

## The Commands -- A condensed rehash
This is same list of commands given at the beginning of this document, but now with a little more context. Look them over and then follow along in the next section which annotates each command.

#### One-time each login, could be captured in a project dependent script or alias.

``` bash
$ bash              # Spawn a clean shell
$ hlsLocate         # Define the site specific search path for the Vitis version settings script
$ hlsBs-examples    # Setup the hlsBs examples tutorial, this is project specific
$ hlsVersion 2024.2 # Select Vitis Version 2024.2, this uses the path established by hlsLocate
$ exSelect ex0      # Select the ex0 project
```
> The spawning of a new bash shell is strictly personal preference. It makes it easy to get back to a clean shell by simply exiting.  Try it, you may find you like it.

#### hlsWs, hlsCfg, One-time each new project setup or at a structural change to the project, **e.g.** new or changed configuration

The target project and Vits version are now establish
``` bash
$ hlsWs  --create # Create the workspace
$ hlsCfg --create # Create the configuration files and components
```
#### **hlsRun**, Used almost exclusively after creating the workspace and configuration files/components

With the target configuration files, workspace and components populating the workspace created, can now create the various output products
``` bash
$ hlsRun --csim=make      # Make csim.exe
$ hlsRun --csim=run       # Run csim.exe
$ hlsRun --synthesis      # Create the synthesis
$ hlsRun --cosim          # Run the CoSim
$ hlsRun --package        # Create a .dcp
$ hlsRun --implementation # Create the implementation (the .zip file)
$ hlsRun --ip             # Rename the .dcp and augment the permissiable FPGA families
```

####  hlsVersion, (optional) changes Vitis Version, then redo the above sequence

At this point, the Vitis Version could be changed and this sequence redone for that version, for example
``` bash
$ hlsVersion 2025.1
```

#### exSelect, (optional) changes to another **hlsBs-examples** project
``` bash
$ exSelect ex1
```

#### hlsBs, hlsCtx, hlsGui, other useful hlsBs commands
- There is a lot more to these commands
	- A manpage for each command can be had with the option *-h* or *--help*.
- A brief synopis of the all commands can be had by
	``` bash
	$ hlsBs
	```
- There is hidden context used by **hlsBs** (the reason the command line is terse) that can be checked on by
	``` bash
  	$ hlsCtx
	```
 - Once the configuration files and components have been created, if desired, the Vitis GUI can be activated by
	``` bash
	$ hlsGui
	```

Command line options can generally be abbreviated to uniqueness.


## The Commands -- The Annotated Version
If you have done the site and user specific setup, this part is an interactive type-along at the terminal.  Check your results with annotations.

### Create the Workspace
Before creating the workspace, check on its status

``` bash
$ hlsWs --status  # Check on the status of the workspace
==============================================================================
Workspace - Status
------------------
Workspace : <path/to>/hlsBs-examples/firmware/ex0/products/ws/2024.2
State     : Does not exist
==============================================================================
```
As expected it does not exist, so need to create it.
> If for some reason the workspace does exist it can be removed by ```$ hlsWs --remove```
``` bash
$ hlsWs --create
Vitis Server started on port '41429'.
==============================================================================
Workspace - Create
------------------
Workspace : <path/to>/hlsBs-examples/firmware/ex0/products/ws/2024.2
State     : Created
==============================================================================
Shutting down Vitis server running on port '41429'
```

The workspace has now been created.<br>**NOTE:** Sorry this is slow, but this invokes the Vitis utility to do the creation and anything involving Vitis is slow, even asking for the version number.


### Create the Configuration Files and Components
Before creating configuration files and components, check on their state
``` bash
$ hlsCfg --list
==============================================================================
Listing Configurations & Components
-----------------------------------
Workspace           : <path/to>/hlsBs-examples/firmware/ex0/products/ws/2024.2
Vitis Version       : 2024.2
Build time          : 20260625125755
Project.Root        : <path/to>/hlsBs-examples/firmware/ex0
       .File        : <path/to>/hlsBs-examples/firmware/ex0/project/Streams.py
Components          : *

Existing
     None

Missing
  1. Configuration  : <path/to>/hlsBs-examples/firmware/ex0/products/cfg/2024.2/stream.cfg
     Component      : <path/to>/hlsBs-examples/firmware/ex0/products/ws/2024.2/stream

Cruft
     None
==============================================================================
```
After some global information about the project setup, the listing classifies the configuration files and components into 3 categories

| Category | Meaning |
| :------- | :------ |
| Existing | Configuration files/components that exist. |
| Missing  | Configuration files/components that are missing |
| Cruft    | Configuration files/components that are not defined by the project file |

The *Existing* and *Missing* are self-explanatory and, as expected, all are *Missing*.

The *Cruft* category has been found to be useful.  Sooner or later, via typos, not cleaning up properly or changing the set in the project file, *Cruft* creeps in. For simple projects this is generally not an issue, but for multi-component projects it can be.

> The listing can be trimmed in 2 ways
>- *--list* option can accept category qualifiers (*existing, missing, cruft*)
>	- *e.g.* `--list=missing,cruft` or `list=e`
>- Using a postional parameter or `--components=<selection>`
>	- where \<*selection*\> can be an explicit, wildcarded or list of any comma separated combination of component names
>- For details do `$ hlsCfg --help`


If the *existing* category is not empty, clean it by `$ hlsCfg '*' --clean`

Now create the configurations/components.
``` bash
$ hlsCfg --create
Vitis Server started on port '46585'.
==============================================================================
Creating Configuration + Component
----------------------------------
Workspace     : <path/to>/hlsBs-examples/firmware/ex0/products/ws/2024.2
Vitis Version : 2024.2
Build time    : 20260625131240
Project.Root  : <path/to>/hlsBs-examples/firmware/ex0
       .File  : <path/to>/hlsBs-examples/firmware/ex0/project/Streams.py
Components    : *


Creating Missing -> Existing
  1. Configuration : <path/to>/hlsBs-examples/firmware/ex0/products/cfg/2024.2/stream.cfg
     Component     : <path/to>/hlsBs-examples/firmware/ex0/products/ws/2024.2/stream
==============================================================================
```
The configuration file and component have now been created.

2 flags of interest can be added
- *--verbose*  Gives more complete information on the global context and contents
- *--dry-run*  Tells what would have happened but does not do the action

Additional actions are:
- *--clean*    Removes configuration file(s) and component(s)
- *--replace*  Replaces configuration file(s) and component(s)

All actions target a default category and component selection, but can be explicitly specified.
- The categoies by *--\<action\>=\<categories of interest\>*
- The components by positional parameters or *--components=*\<*selection*\>

The defaults are:

| Action | Category | Component |
| :----- | :------- | :-------- |
| list   | all      |      '\*' |
| create | missing  |      '\*' |
| replace| existing |      '\*' |
| clean  | existing |      none |

**NOTE::** As a convenience one can create and replace all by
```
$ hlsCfg --replace=existing,missing
# or
# hlsCfg --replace=e,m
```


## hlsRun
Once the workspace and configuration files and components have been created, **hlsWs** and **hlsCfg** have done their work and recede into the backwaters until needed again.

**hlsRun** runs the various product creation stages either individually or in any combination that is permissible. (*e.g.* *cosim* cannot be run before *synthesis*.)

| Stage         | What |
| :------------ | :--- |
| csim          | The C simulation |
| synthesis     | The synthesis |
| cosim         | The CoSimulation |
| package       | The packaging (.dcp) |
| implementation| The bit file (generally .zip) |
| ip            | Modifications of the .dcp and .zip files that have been found to be useful |


### hlsRun --csim
To create/make the csim.exe

``` bash
$ hlsRun --csim=m
```
The first time this is run on a new component, Vitis is needed to create the make file.
> The Vitis output is too extensive and uninformative and not included here.

The *--csim* qualified accepts a list of *clean,make,run* to match your needs. They can be abbreivated to 1 character.

Once the make file has been created, **hlsBs** just uses it. This is much faster.  Try a *clean* and *make* just to observe. The *--verbose* flag was added to show what happened.

``` bash
$ hlsRun --csim=c,m --verbose  # Clean, Make, Run may be abbreviated to 1 character
==============================================================================
Workspace         : <path/to/>/hlsBs-examples/firmware/ex0/products/ws/2024.2
Component
Vitis Version     : 2024.2
Build time        : 20260625140702
Project.Root      : <path/to/hlsBs-examples/firmware/ex0
       .File      : <path/to/hlsBs-examples/firmware/ex0/project/Streams.py

Git    .repo      : hlsBs-examples
       .branch    : main
       .dirty     : Dirty

Run CSim          : Clean,Make (fast)
----------------------------------------
  1. Component           : <path/to>/hlsBs-examples/firmware/ex0/products/ws/2024.2/stream
     Removing
     obj/StreamsTb.o
     obj/StreamsHls.o
     obj/../../../../../../../../../src/streams/StreamsTb.d
     obj/../../../../../../../../../src/streams/StreamsHls.d
     csim.exe
     --------------------
     Building:
     Compiling ../../../../../../../../../src/streams/StreamsTb.cc in debug mode
     Compiling ../../../../../../../../../src/streams/StreamsHls.cc in debug mode
     Generating csim.exe
==============================================================================
```

The next logical step is to run it.  Of course any combination of *clean*, *make*, *run* can be used.  Since it was just made, only need *--csim=run*.
``` bash
$ hlsRun --csim=r
==============================================================================
Workspace         : <path/to>/hlsBs-examples/firmware/ex0/products/ws/2024.2
Component
Vitis Version     : 2024.2
Build time        : 20260625141032
Project.Root      : <path/to>/hlsBs-examples/firmware/ex0
       .File      : <path/to>/hlsBs-examples/firmware/ex0/project/Streams.py

Run CSim          : Run (fast)
----------------------------------------
  1. Component           : <path/to>/hlsBs-examples/firmware/ex0/products/ws/2024.2/stream

Stream.source = Internal
      .incval =   0
      .defval =   0
       ntests =   5
  0. Success
  1. Success
  2. Success
  3. Success
  4. Success

INFO [HLS SIM]: The maximum depth reached by any hls::stream() instance in the design is 100
==============================================================================
```
### Caveat
If the configuration composition, (*e.g.* a new source file was added or an existing one removed) that was used in building csim.exe, the configuration file needs to be rebuilt.  When doing this the component will be removed, taking the make file with it, so that when **hlsRun --csim** is executed, it will be have to go through the slow Vitis method.

> **hlsBs** has been designed to use the slow method when no make file exists and the fast method when it does.  Just in case there is a corner **hlsBs** missed, one can force the slow method by adding *--slow*, otherwise the default is to try the fast method and, if no make file, use the slow method.

### How Fast is Fast?

| Action         | Slow  | Fast  | Notes |
| :------------- | :---  | :---  | :---  |
| clean          | 10s   |   .25s| Vitis (slow method) insists on doing a make after a clean, fast only does what it is told |
| make           |  7.7s | 2.6s  |       |
| make (no need) |  9.8s |   .26s| Vitis (slow method) always does a make, wonder the purpose of a make file, fast only does what it is told |
| run            |  9.9s |  .24s |
| clean, make    |  10s  | 2.7s  |
| clean,make,run |  10s  | 2.5s  |


### hlsRun [ --synthesis | --cosim | --package | --implemntation |
Can now create these products. Unfortunately there is no *fast* method. These all invoke **Vitis** or **Vivado**, so get your favorite beverage.

**Recommendation:** While all can be combined on a single command, *.i.e.*
``` bash
 $ hlsRun --syn --cosim --package --impl # Can abbreviate to uniqueness
   ...or...
 $ hlsRun --all --exclude=csim,ip
```
it is not recommended unless this is a remake of a known working component. The amount of output makes it very easy to miss warning messages.  **hlsBs** has tried to abort the sequence on error, but never hurts to check.

### hlsRun --ip=zip,dcp
This stage selectively produces 2 output products that have been found to be useful.  They are modifications of the standard Vitis/Vivado *.dcp* and *.zip* build products. The default is to produce both.
- Renaming the internal name carried in *.dcp* file (from the *--implementation* stage)
	- The internal name of the standard *.dcp* file is fixed to a constant string.
	- This makes it difficult/impossible when the final FPGA image is composed of multiple *.dcp* files
	- This renames it. The default is after the component, but is user determined.
- Modify the families of acceptable FPGAs this can run on contained in the *.zip* file (from the *--package* stage).
	- At times the same FPGA image can be run on different families of FPGAs.
	- The knowledgeable user can set this set of families.
	- While *family* has a default, it may not be appropriate. It is the one parameter here that likely should not be defaulted.

Given the time involved in producing the original *.dcp* and *.zip*, by just modifying this file rather creating mulitple versions, this can save a lot of time. One is also assured it is the same image with just a name change.


## The Project File
This important file contains all the information necessary to produce the various products, *i.e.* the worksapce, configuration files, components, *etc* and where to place them in the directory structure.


The general features are documented in the *README.md* found in the *ruckus hlsBs* directory. But, much as one cannot document what a programming language (it is open-ended) can do, it is impossible to document all that can be done with the Project file. The fallback is to present a number of examples showing what is possible.  Hopefully the concepts are orthogonal, so mixing and matching is straight-forward.

Rather than annotate the Project files in this document, they have been verbosely internally documented. Take a look. Hopefully one of these is close enough to your project that it can serve as a template.

> The `README.md` in *hlsBs* subdirectory of *ruckus* does annotate a very simple example.

The examples are
- *ex0* - A very basic one component generator for a project with
	- 1 test bench file
	- 1 hls file
	- 1 include path
	- 1 target FPGA
- *ex1* - Expands on *ex0* to have 2 components, with the same code targeting 2 FPGAs
- *ex2* - Expands on *ex1* to have 4 components, 2 distinct sets of code each targeting to 2 FPGAs
- *ex3* - Uses normal file wildcarding to include a set include files into source code at compile time
	- SNL takes advantage of this
		- The testbench and hls source code are the same for all networks.
    	- The network(s) are then provided at compile-time using this technique.
- *ex4* - Similar to *ex3* except it uses values from a list in the project files to set *#defines* whose value can be used to steer the code.
	- Note the practical difference between the *#include* and *#define* methods.
		- The *#include* method is open-ended. Adding more include files that satisfy the wildcarding generates new components without touching any code or the Project file.
		- The *#define* requires cooperation between the values defined in the Project file and their use in the code.
	- Both have their uses and can be used separately or in combination.

Having done *ex0*, now explore *ex1*.

## ex1 - A 2 Component Example
Select this project
``` bash
$ exSelect ex1
```
and create its workspace

``` bash
$ hlsWs --create
```

*ex1* is just the *ex0* project file changed to have 2 FPGA targets for the same code.  In this example, the only difference between the two FPGA specifications is the clock speed.
``` python
                    #                               Part  Clock. Uncertainity    Id
    fpgas        = [ Product.Fpga ('xcku115-flvb2104-2-i',   '6',        None, '6ns'),
                     Product.Fpga ('xcku115-flvb2104-2-i',   '5',        None, '5ns')]
```
Bind the FPGAs to the build

``` python
    components   = (Product.Builds ('build',  build),
                    Product.Fpgas  ('fpga',   fpgas))
```

Modify the template defining the configuration file path to produce a unique name. Here the *fpga_id* (*6ns* or *5ns*) is used to accomplish this and also to convey meaning in the name.
``` python
    # --------------------------------------------------
    # Configuration file name template
    # Makes  products/cfg/{vitis_version}/{build_id}.cfg
    #  e.g.  products/cfg/2024.2/streams-5ns.cfg
    # --------------------------------------------------
    cfg_template = (os.path.join (project.products_root,
                                  'cfg',
                                  '{vitis_version}',
                                  '{build_id}{fpga_id}.cfg'))
```
3 symbolic labels have be used
- {*vitis_version*} - The Vitis Version number, *i.e.* 2024.2, 2025.1, *etc* ...
- {*build_id*}      - An identifier for the specific build that is being used.
	- The *build* prefix on '{*build*_id}' is user defined; it is the string '*build*' in the components definition
- {fpga_id}       - A user assigned identifier for the specific FPGA; think of it as a nickname. Including the *fpga_id* makes the configuration name unique. Other FPGA attributes listed below could also be used, provided they make the configuration file path unique.
    - The *fpga* prefix is user defined - it is the string '*fpga*' in the components definition. The complete list of FPGA attributes are
		- *fpga* - The full FPGA class (not terribly useful in this usage)
   		- *fpga_part*  - The specfic FPGA part
    	- *fpga_clock* - The FPGA clock
    	- *fpga_uncertainity* - The FPGA clock uncertainity
    	- *fpga_id*   - An arbitrary string to identify this FPGA specification (the '*6ns*' or '*5ns*').
		- **RECOMMENDATION**: While the *fpga_id* string can be anything, but given that it is often used in composing file paths, it is recommended to stick with the usual alphanumerics and limit symbols to '-' and '_'. Because the *fgpa_uncertainity* can contain *'+', '%', etc.*, it is not recommended to be used in the *cfg_template*. Better to reexpress it in the 'fpga_id'.

> Note: In this example the component name is taken from the configuration name. It could be reversed.  This ordering was chosen since the configuration file name need not be unique, only its path.  For example, the *fpga_id* could have been used as directory with only the *build_id* specifying the configuration file name.

**RECOMMENDATION:** While the configuration name and component name are entirely independent, sanity suggests making them related.

#### hlsCfg
Assuming **hlsWs** has created the *ex1* workspace, to create the 2 configuration files and their respective components
``` bash
$ hlsCfg --create
Vitis Server started on port '41953'.
==============================================================================
Creating Configuration + Component
----------------------------------
Workspace     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex1/products/ws/2024.2
Vitis Version : 2024.2
Build time    : 20260629124319
Project.Root  : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex1
       .File  : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex1/project/Streams.py
Components    : ['*']

Creating Missing -> Existing
  1. Configuration : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex1/products/cfg/2024.2/stream-5ns.cfg
     Component     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex1/products/ws/2024.2/stream-5ns

  2. Configuration : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex1/products/cfg/2024.2/stream-6ns.cfg
     Component     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex1/products/ws/2024.2/stream-6ns
==============================================================================
Shutting down Vitis server running on port '41953'
```
As expected, the 2 configuration files and components have been created. Note how the naming matches the template.

### hlsRun
To demonstrate a feature of **hlsBs**, **hlsRun** can target a single component or group of components. The following commands all build stream-6ns
``` bash
$ hlsRun stream-6ns --csim=m    # Explicit component name
$ hlsRun '*-6ns' --csim=m       # Wildcard the component name. The '' to prevents the shell from doing the wildcarding
$ hlsRun --comp=*-6ns --csim=m  # Safer way to prevent the shell from doing the wildcarding
==============================================================================
Workspace         : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex1/products/ws/2024.2
Component         : ['*-6ns']
Vitis Version     : 2024.2
Build time        : 20260629125145
Project.Root      : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex1
       .File      : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex1/project/Streams.py
Components        : ['*6ns']

Run CSim          : Make (fast)
----------------------------------------
  1. Component           : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex1/products/ws/2024.2/stream-6ns
  .
  .
```

Without a component specification, the default is to apply the specified action (here --csim=m) to all existing components.

==============================================================================

Handy options to remember which configuration/components exist is either
``` bash
$ hlsCfg --list           # Full listing of the existing, missing and cruft
$ hlsCfg --list=existing  # Full listing of only the existing
$ hlsRun --list           # Short listing of only the existing components
```

### hlsExe
**hlsExe** targets a single component.  A common use to explore the results when different command line parameters are used. This might be
- changing the number of tests
- changing the input test and golden files

``` bash
$ hlsExe stream-6ns --ntests=5
```
Here the command line parameters supercede those found in the configuration file.

### hlsGdb
**hlsGdb** invokes the *gdb* on an explicitly named component.
``` bash
$ hlsGdb stream-6ns --ntests=5
```

## ex2
Select the *ex2* project and create its workspace
``` bash
$ exSelect ex2
$ hlsWs --create
```

The *ex2* project defines
- 2 different builds (code sets)
- 2 FPGA configurations
- Yielding 4 components.

The FPGA specification is as the last example, but the *Builds* is now a list (tuples also work).
In this fabricated example the builds are the same. In a realistic example these would be different.

``` python
    components   = (Product.Builds ('build', [['streamA', build],
                                              ['streamB', build]]),
                    Product.Fpgas  ( 'fpga', fpgas))
```

### hlsCfg
Assuming the workspace has been created, create the 4 components
``` bash
$ hlsCfg --create
==============================================================================
Creating Configuration + Component
----------------------------------
Workspace     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex2/products/ws/2024.2
Vitis Version : 2024.2
Build time    : 20260629130941
Project.Root  : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex2
       .File  : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex2/project/Streams.py
Components    : ['*']


Creating Missing -> Existing
  1. Configuration : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex2/products/cfg/2024.2/streamA-5ns.cfg
     Component     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex2/products/ws/2024.2/streamA-5ns

  2. Configuration : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex2/products/cfg/2024.2/streamA-6ns.cfg
     Component     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex2/products/ws/2024.2/streamA-6ns

  3. Configuration : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex2/products/cfg/2024.2/streamB-5ns.cfg
     Component     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex2/products/ws/2024.2/streamB-5ns

  4. Configuration : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex2/products/cfg/2024.2/streamB-6ns.cfg
     Component     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex2/products/ws/2024.2/streamB-6ns
==============================================================================
```

The same configuration file path template has been used, but the names of the 2 builds are *streamA* and *streamB*, each built with the 2 FPGA configurations.

### hlsRun
Suppose all 4 have been built and had csim successfully run, but the synthesis is failing for the 5ns version of each. Might try something like:

```bash
$ hlsRun --comp=*5ns --syn --verbose
```

or you wish to just rebuild csim.exe for streamA variations
``` bash
$ hlsRun --comp=streamA* --csim=m
```

This selection of components (it can be any list of wildcards and explicit definitions) is a general feature.  The *--dry-run* option is available on most commands to see what would have happened.  It is useful when a project has many targets as a quick check that the targeted components are as intended.


## ex3
This examples shows how a generic piece of code can be tailored by providing a file to be included at compile-time. In this example, in the include directory is a subdirectory for 2 such include files:

<pre>
    include/seeds/
                  Seed1.hh
                  Seed2.hh
</pre>

In this toy example they only specify
- An integer used to seed the constants
- A  message indicating the include file's name

**RECOMMENDATION:** Create a dedicated directory, here *seeds*, to hold these include files. It allows the wildcarding to be narrowly defined, reducing the chance of an unintended include.

In the project file, these pieces have been modified


``` python
    # --------------------------------------------
    # Define the wildcard to select the Seed files
    # --------------------------------------------
    stream_seeds = os.path.join (include_path, "seeds", "Seed*.hh")

    # --------------------------------------------
    # These are included via a special #define
    # --------------------------------------------
    defines      = [ {'name'     : 'STREAM_SEED',   # In the StreamsTb.cc as #include STREAM_SEED
                      'value'    : '{seed_path}',   # The path of the include file
                      'type'     :  'rel_path',     # The file is included by a relative path
                      'rel_path' : include_path } ] # The relative path to use
```

Modify the components specification to include these compile-time loaded include files.
> **Note:**  All classes can be specified multiple times, but *all* class prefixes must be unique.
> - If necessary, **hlsBs** can be enhanced to make this more modular.

``` python

    components   = (Product.Builds ('build', [['stream', build]]),
                    Product.Files  ('seed',         stream_seeds),
                    Product.Fpgas  ('fpga',               fpgas))
```

And the configuration file path to include the file name of the compile-time loaded include files.


``` python
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
    # Note: Text can also be included to help with clarity.
    #       Note necessary in this case, but for illustration
    #       B{build_id}-I{seed_name}-F{fpga_id}
    #
    #       e.g.  products/cfg/2024.2/BstreamA--ISeed1-F6ns.cfg
    # -----------------------------------------------------------------------
    cfg_template = (os.path.join (project.products_root,
                                  'cfg',
                                  '{vitis_version}',
                                  '{build_id}-{seed_name}-{fpga_id}.cfg'))
```

#### *hlsCfg*
Assuming the *ex3* workspace has been created, now create the configurations/components.

``` bash
$ hlsCfg --create
Vitis Server started on port '40481'.
==============================================================================
Creating Configuration + Component
----------------------------------
Workspace     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3/products/ws/2024.2
Vitis Version : 2024.2
Build time    : 20260707141521
Project.Root  : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3
       .File  : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3/project/Streams.py
Components    : ['*']

Creating Missing -> Existing
  1. Configuration : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3/products/cfg/2024.2/stream-Seed1-5ns.cfg
     Component     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3/products/ws/2024.2/stream-Seed1-5ns

  2. Configuration : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3/products/cfg/2024.2/stream-Seed1-6ns.cfg
     Component     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3/products/ws/2024.2/stream-Seed1-6ns

  3. Configuration : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3/products/cfg/2024.2/stream-Seed2-5ns.cfg
     Component     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3/products/ws/2024.2/stream-Seed2-5ns

  4. Configuration : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3/products/cfg/2024.2/stream-Seed2-6ns.cfg
     Component     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3/products/ws/2024.2/stream-Seed2-6ns
==============================================================================
Shutting down Vitis server running on port '40481'
```

New components can be created just by adding more Seed*.hh files, *e.g.* Seed3.hh. This is a selling point of using compile-time loaded include files - new components can be created without touching the base code. In some sense, the base code acts as a super-template to construct variations.

#### hlsRun
Makie all the *csim.exe*'s with `hlsRun --csim=m`, then run only the stream-Seed2-5ns component

``` bash
$ hlsRun '*Seed1-5ns' --csim=r --verbose
==============================================================================
Workspace         : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3/products/ws/2024.2
Component         : ['*Seed1-5ns']
Vitis Version     : 2024.2
Build time        : 20260707141709
Project.Root      : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3
       .File      : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3/project/Streams.py

Git    .repo      : hlsBs-examples
       .branch    : main
       .dirty     : Dirty

Run CSim          : Run (fast)
----------------------------------------
  1. Component           : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex3/products/ws/2024.2/stream-Seed1-5ns
     Running:

Stream.source = /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/include/seeds/Seed1.hh
      .incval =   1
      .defval =   0
       ntests =   5

  0. Success
  1. Success
  2. Success
  3. Success
  4. Success

INFO [HLS SIM]: The maximum depth reached by any hls::stream() instance in the design is 100
==============================================================================
```

In the output, just to illustrate the effect of the compile-time include file, the test bench has printed
- The name of the included file
- Its seed value *incval*

The *.defval* is the subject of the next example.


## ex4
This example uses compile time *\#defines* to achieve similar results.

First specify the *\#defines* to be used.  In the code, the value, symbolically represented here by '{def_seed}', will be accessed by the *\#define* **DEF_SEED**. Its type is *string* to distinguish it from the include file specifcation of *ex3*.

``` python
    # --------------------------------------------
    # These are included via a special #define
    # --------------------------------------------
    defines      = [ {'name'     :  'DEF_SEED',  # Name of the #define
                      'type'     : 'string',     # It is just text string
                      'value'   : '{def_seed}'}] # The value of DEF_SEED

```

Modify the components specification to include the list of *\#define* values
``` python

    components   = (Product.Builds ('build', [['stream', build]]),
                    Product.Values ('def_seed',          (10,20)),
                    Product.Fpgas  ('fpga',                fpgas))
```

And the configuration file path to include the value of the '\#define`
``` python
    cfg_template = (os.path.join (project.products_root,
                                  'cfg',
                                  '{vitis_version}',
                                  '{build_id}-seed{def_seed}-{fpga_id}.cfg'))
```

Here is an example where adding some text helps. Instead of just a bare '10' or '20' appearing in the configuration file path and component name, it is prefixed with '*seed'*

#### *hlsCfg*
Assuming the workspace for *ex4* has been created, now create the configurations/components.

``` bash
$ hlsCfg --create
Vitis Server started on port '35083'.
==============================================================================
Creating Configuration + Component
----------------------------------
Workspace     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex4/products/ws/2024.2
Vitis Version : 2024.2
Build time    : 20260707152528
Project.Root  : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex4
       .File  : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex4/project/Streams.py
Components    : ['*']

Creating Missing -> Existing
  1. Configuration : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex4/products/cfg/2024.2/stream-seed10-5ns.cfg
     Component     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex4/products/ws/2024.2/stream-seed10-5ns

  2. Configuration : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex4/products/cfg/2024.2/stream-seed10-6ns.cfg
     Component     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex4/products/ws/2024.2/stream-seed10-6ns

  3. Configuration : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex4/products/cfg/2024.2/stream-seed20-5ns.cfg
     Component     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex4/products/ws/2024.2/stream-seed20-5ns

  4. Configuration : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex4/products/cfg/2024.2/stream-seed20-6ns.cfg
     Component     : /sdf/group/faders/users/russell/sandbox/hlsBs-examples/firmware/ex4/products/ws/2024.2/stream-seed20-6ns
==============================================================================
```

New components can be created just by adding values to '\#define`. This *\#define* technique has the disadvantage of modifying the global project definition file. Contrast this with the '\#include' technique of *ex3' where files are just added to the */seeds* directory.
> With some fairly straight forward Python code, these values could be read in from an external file, achieving the same results. This shows the flexiblity in the **hlsBs** approach plus some creativity.

#### hlsExe
After making all the *csim.exe*'s with `hlsRun --csim=m`, run only the stream-seed10-5ns component using **hlsExe** instead of **hlsRun**. **hlsExe**'s advantage is parameters can be modified on the command line. Here the default of 5 tests was modified to 10 tests.

``` bash
$ hlsExe stream-seed10-5ns --ntests=10

Stream.source = Internal
      .incval =   0
      .defval =  10
       ntests =  10

  0. Success
  1. Success
  2. Success
  3. Success
  4. Success
  5. Success
  6. Success
  7. Success
  8. Success
  9. Success

INFO [HLS SIM]: The maximum depth reached by any hls::stream() instance in the design is 100
```

In the output, the test bench has printed
- No include file was used - the *incval* seed was defaulted internally to 0
- The define seed value, *defval* is 10

# Final Word
**hlsBs** will happily accept multiple builds, fpgas, includes and defines combined in any mix. This can produce 10s if not many 10s of components. The limitation is likely on the user to not be overwhelmed.

**hlsBs** has attempted to provide the tools to create, categorize and track multiple components, but the burden is still on the user to create a development roadmap.  For example, it may be that multiple workspaces are used in a single package to help separate different development paths, many of which are exploratory and will not be kept.

Think about your workflow.  If features to assist can be added to **hlsBs** make them known. For as much as **hlsBs** was an attempt to simplify the mechanics of building HLS components, it was also an attempt to help in the user implement a sensible workflow.
