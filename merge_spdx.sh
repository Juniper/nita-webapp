#!/bin/bash
#
# Merges two json files together
#
# Usage:
# merge-sbom.sh file1 file2 > merged-file
# original is here: https://edgebit.io/blog/merge-two-sboms/

jq -s 'def deepmerge(a;b):
  reduce b[] as $item (a;
    reduce ($item | keys_unsorted[]) as $key (.;
      $item[$key] as $val | ($val | type) as $type | .[$key] = if ($type == "object") then
        deepmerge({}; [if .[$key] == null then {} else .[$key] end, $val])
      elif ($type == "array") then
        (.[$key] + $val | unique)
      else
        $val
      end)
    );
  deepmerge({}; .)' $1 $2
