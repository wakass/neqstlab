cd "\Grsync\bin"
net use y: \\datahost\data_storage password /USER:user /PERSISTENT:YES
rsync -av --no-p --no-g --chmod=ug+rwx --exclude='*.hdf5' --exclude='*.dat' '/cygdrive/c/qtlab/data/%1/' /cygdrive/y/siqd_data/triton/data/%1/
