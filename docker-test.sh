#!/usr/bin/env bash

# get params or use defaults
dckr_cnt_nm=${1:-"emobon_ddcat"}
dckr_img_nm=${2:-"emobon_ddcat:latest"}

#check for .env file and use it if available
if [[ -f .env ]]; then
  source .env
fi
#create temp space if not provided from env
if [[ -z "${TEST_OUTPUTFOLDER}" ]]; then
  TMPDIR=$(mktemp -d) 
  TEST_OUTPUTFOLDER=${TMPDIR}
fi
echo "using TEST_OUTPUTFOLDER=${TEST_OUTPUTFOLDER}"

#check if an image exists and build it if not
if [[ "$(docker images -q ${dckr_img_nm} 2> /dev/null)" == "" ]]; then
  echo "building the image"
  docker build -t ${dckr_img_nm}:latest .
fi

#run the available container for output
docker run \
  --rm \
  --name emo-bon_${dckr_cnt_nm} \
  --volume ${TEST_OUTPUTFOLDER}:/resultsroot \
  ${dckr_img_nm}

#verify the output
OUTFILE=${TEST_OUTPUTFOLDER}/emobon-dcat-dump.ttl
test -f ${OUTFILE} || (echo "mising output file" && exit 1)
ttl=$(which ttl)  # look for ttl validator
if [[ -x "${ttl}" ]]; then
  ${ttl} ${OUTFILE} || (echo "ttl validation failed" && exit 1)
fi

#say bye and clean up
echo "test passed, cleaning up"
if [[ -d "${TMPDIR}" ]]; then 
  # if a tmpdir was created, remove it
  rm -rf ${TMPDIR}
fi

#done
echo "done"
exit 0;
