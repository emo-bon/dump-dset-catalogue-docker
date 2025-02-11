#!/usr/bin/env bash

# get params or use defaults
dckr_cnt_nm=${1:-"emobon_ddcat"}
dckr_img_nm=${2:-"emobon_ddcat:latest"}

#build a temp space and fill it with the content
TMPDIR=$(mktemp -d) && echo "using TMPDIR=${TMPDIR}"
if [ -d "${TMPDIR}" ]; then
    explorer.exe $(cygpath -w ${TMPDIR})
else
    echo "Failed to create TMPDIR"
    exit 1
fi
(cd ./tests/data/ && cp -r . ${TMPDIR})
ls -R ${TMPDIR}



#check if an image exists and build it if not
if [[ "$(docker images -q ${dckr_img_nm} 2> /dev/null)" == "" ]]; then
  echo "building the image"
  docker build -t ${dckr_img_nm}:latest .
fi

#run the built container
docker run \
  --name emo-bon_${dckr_cnt_nm} \
  --volume ${TMPDIR}:/resultsroot \
${dckr_img_nm}

#verify the output
test -f ${TMPDIR}/results.ttl || (echo "mising output file" && exit 1)
ttl=$(which ttl)  # look for ttl validator
if [[ -x "${ttl}" ]]; then
  ${ttl} ${TMPDIR}/results.ttl || (echo "ttl validation failed" && exit 1)
fi

#say bye and clean up
echo "test passed, cleaning up"
#rm -rf ${TMPDIR}
exit 0