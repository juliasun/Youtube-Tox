#!/bin/sh

#  yt_shell.sh
#  
#
#  Created by juliasun on 1/18/13.
#

cat drugs | while read line
do
    python get_yt_comments.py $line
done