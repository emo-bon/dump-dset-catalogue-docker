# dump-dataset-catalogue-docker

The repository provides a dockerised executor of the sema.harvest module. This executor is used to dump the dataset catalogue from emobon.

## About 

The packaged artefacts from this work are available at https://github.com/orgs/emo-bon/packages. 

## Usage

To use this one only needs

1. to decide what image to run
   1. either a published release package
   2. or a local build
2. to set the i/o for the process
   1. mainly the ro-crate folder to work on (mapped as docker-volume `/resultsroot`)
   2. essential environment variables to pass
3. pass all of the above in a call to `docker run`

In detail:

### using one of the published packages (docker-image)

```sh
$ version="latest" # or pick an available release tag from https://github.com/orgs/emo-bon/packages

# (optionally) verify availability by manual pull
$ docker pull ghcr.io/emo-bon/emobon_ddcat:${version}  # should pull the image without errors

# variable setting to inject
$ rocrateroot="../path_to_analysis_results_repo/crate_results_folder_X"
$ source_mat_id="YourRefHere"

# actually run it
$ docker run --rm --name "emo-bon_ddcat" --volume ${rocrateroot}:/resultsroot ghcr.io/emo-bon/emobon_dcdat:${version}
```

## Developer info

To build your own local image, or to get involved in furthering this work:
See [Contributors Guide](./docs/contribute.md)
