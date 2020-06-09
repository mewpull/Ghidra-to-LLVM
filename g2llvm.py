#!/usr/bin/python3

import importlib
import argparse
import subprocess

xmltollvm = importlib.import_module('src.xmltollvm')
opt_verify = importlib.import_module('src.lifting-opt-verify')

# These need to change in your local installation
ghidra_headless_loc = "/home/tej/buildsGhidra/ghidra_9.1.1_PUBLIC/support/analyzeHeadless"
prj_dir = "/home/tej/GhidraProjects/"

import sys
import os

# Locate path to Ghidra-to-LLVM directory.
ghidra2llvm_dir = os.path.realpath(sys.path[0])

# These shouldn't need to be changed
prj_name = "lifting"
xml_script = os.path.join(ghidra2llvm_dir, "src/GhidraToXML.java")

# Argument parsing
parser = argparse.ArgumentParser(description = 'This script lifts a binary from executable to LLVM IR.')
parser.add_argument('input_file', action='store')
parser.add_argument('-out', action='store_true', help='emit intermediate files', default=False, dest='out')
parser.add_argument('-opt', action='store', help='select optimization level 0-3', default=None, dest='opt')
parser.add_argument('-o', action='store', help='LLVM IR output path', default=None, dest='output')
parser.add_argument('-cfg', action='store_true', help='emit cfg', default=False, dest='cfg')
results = parser.parse_args()

# Check arguments
if results.opt is not None:
    opt_level = int(results.opt)
    if opt_level not in range(4):
        raise argparse.ArgumentTypeError("%s is an invalid optimization level, 0-3 only" % opt_level)
else:
    opt_level = results.opt

# Convert P-code to XML
subprocess.run([ghidra_headless_loc, prj_dir, prj_name, '-import', results.input_file,
                '-postScript', xml_script, '-overwrite', '-deleteProject'])
filename = results.input_file.split('/')[-1]
xmlfile = './' + filename + '.xml'
subprocess.run(['mv', '/tmp/output.xml', xmlfile])

# Lift to LLVM
module = xmltollvm.lift(xmlfile)
llvmlitefile = str(filename + '.llvmlite')
f = open(llvmlitefile, 'w')
f.write(str(module))
f.close()

# Optimization passes
module = opt_verify.optimize(module, opt_level)

# Verify
module = opt_verify.verify(module)
if results.output:
    llfile = results.output
else:
    llfile = str(filename + '.ll')
f = open(llfile, 'w')
f.write(str(module))
f.close()

# Output CFGs
if results.cfg:
    subprocess.run(['rm', '-rf', "graphs"])
    subprocess.run(['mkdir', "graphs"])
    graphs = opt_verify.graph(module)


# Cleanup
if not results.out:
    subprocess.run(['rm', xmlfile])
    subprocess.run(['rm', llvmlitefile])