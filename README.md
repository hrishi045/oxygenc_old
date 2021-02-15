# USER MANUAL FOR OXYGEN COMPILER

## INSTALLING PREREQUISITES

Executing the Oxygen compiler requires the existenceof the following software:

1. Linux
2. Python 3.
3. Anaconda
4. LLVM Compiler Tools
5. GCC

## MAKING A CONDA ENVIRONMENT

Type this in the terminal:

```sh
conda create -n oxygen python=3.7 llvmlite=0.28.0 docopt=0.6.
```

## USING THE COMPILER

**To run code directly:**

1. Save the Oxygen code into a plain text file with the extension `.oxy`
2. Either install the external dependencies globally or switch to a conda environment with the dependencies installed:

```sh
conda activate oxygen
```

3. Use the `run` command of the Oxygen compiler to run the code directlyafter compilation:

```sh
(oxygen) $ python oxygenc.py run filename.oxy
```

**To compile code into LLVM IR:**

1. Save the oxygen file with a `.oxy` extension, and switch to the relevant conda environment

```sh
conda activate oxygen
```

2. Use the `compile` command of the Oxygen compiler to run the code directly after compilation:

```sh
(oxygen) $ python oxygenc.py compile filename.oxy -l
```

3. The LLVM IR will be saved into a file named `filename.ll`

**To run LLVM IR directly:**

1. Compile the Oxygen code into LLVM IR, saved into a file named `filename.ll`
2. Use the `lli` command to run the LLVM bytecode:

```sh
lli filename.ll
```

3. Or use the `llc` command to compile the file into object code and `gcc` to link the file into an executable.

```sh
$ llc –filetype=obj filename.ll
$ gcc filename.o
$ ./a.out
```
