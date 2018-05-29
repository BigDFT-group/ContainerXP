# Fragment Analysis

In this folder of the notebook, I've included several tools for doing fragment
analysis for BigDFT. 

## Data Sets

There are three data sets included, both which deal with the mini-protein system
(1L2Y)[https://www.rcsb.org/structure/1L2Y]. First, there is the `Size` dataset,
which is the same protein, with a different size waterbox added to it. The second
is the `TimeStep` dataset, which is the same protein, but we've taken different
snapshots from a production MD run (each snapshot is 1ns apart). Finally there
is the `Single` test data set.

## PDB To Fragment

The PDB to Fragment notebook is used for converting a PDB file to a fragment list. This 
initial step generates fragment input files in the `FragmentInput` folder
using the data from the `Geometry` folders. This allows us to compute purity
values for the default PDB fragments as a starting point.

## Analysis

The analysis notebook provides a very basic analysis of the initial fragmentation
procedure. It will plot all the purity values (from `PurityData`) from the
various data sets. It also breaks down those purity values to different system
categories. Overall, we will see that the overall distribution of purity values do 
not differ substantially over a course of a run, or with changing waterbox size.

## Refragmentation

The refragmentation notebook is used to generate a new fragmentation with the goal
of driving down the overall purity values of the system. Note that this depends
on the results of the PDB to Fragment Notebook, and also running BigDFT on those
results.

One example run using the refragmentation procedure is included in the `PurityData`
results called `NewFragmentation`. In this example, all fragments with a purity
value greater than `0.05` were selected for analysis from a single snapshot of
the protein with a 2.0 angstrom waterbox. The fragments included three organic
molecules, and one chlorine atom. 0-5 new neighbors were included in those fragments,
and the purity value was analyzed. You can see the results using the Analysis notebook.

## Shell Visualization

There is also a notebook which allows one to look at the correlations between distance
and entries in the matrices produced by BigDFT. In particular, we create block matrices,
where are size number of fragments by number of fragments. For each fragment, there
are a certain set of basis functions that are contained within it. These basis functions
correspond to rows and columns of the full matrix. Then we can consider any pair of
framgnets `i,j`, and those define a set of rows and columns from the full matrix. We extract
the block corresponding to those two fragment's basis functions, and store the norm of that
block in the block matrix. Those values are then visualized.

Running this notebook requires the `hamiltonian_sparse.mtx` and
`density_kernel_sparse.mtx` files. Before running it, place them in the Matrices folder.
matrix, there is a value, which corresponds to the norm of the full full matrix 
