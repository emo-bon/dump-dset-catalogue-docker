# Contributions

This is a short guide for people seeking to contribute.

## Project Artefacts

The build-system and github workflow of this project is setup so it builds a docker image.
(What it actually does is explained in the main [ReadMe](../README.md))

This docker image-build can be executed locally by anyone having the source code of this repository checked-out.
Additionally the gh-actions workflow of this project will automatically build them and publish them.
This will make them generally available at https://github.com/orgs/emo-bon/packages

## Dependencies

This project relies on the use of:

- git
- make
- python3, including pip, and the venv module
- docker

You will need these (and some usage experience) to be able to build, test, ammend and participate.

Additionally, it uses the CI/CD support provided by [github's workflow actions](https://docs.github.com/en/actions/about-github-actions/understanding-github-actions) and their [package publication support](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry). These are less of direct worry for you working on the local checkout of this repo, but some appreciation and understanding of those might be beneficial in order to also help tune and drive those parts of the project.

## Makefile usage

The central `Makefile` in this project functions as the prime interaction-interface for all development actions.
It ensures a relatively low entrypoint and assures all involved to follow the same way of working.

The same flow is executed inside the github-workflow. This ensures this automated build reflects your manual build as much as possible.

### General make-targets

To list what can be built one can:

```sh
$ make
$ make help  # default target
```

To remove any build results from the local repository and possibly start over:

```sh
$ make clean
```

Note: this will not remove locally build docker images. See section below to clean those.

### Python related make-targets

To setup your local python environment, including needed dependencies:

```sh
$ make init
```

Note: This tracks if it already happened to avoid needless execution.

To avoid this check and force-built one can either `make clean` or fool the check through a carefull `touch requirements.txt`.
This is in fact the recommended way if one of the dependencies is known to have updates available.

To test the general operation of the python code (without the docker context):

```sh
$ make test
```

To check the syntax is conform to py-code conventions:

```sh
$ make check
```

To make the syntax be conform to py-code conventions:

```sh
$ make lint-fix
```

### Docker related make-targets

To locally build a docker-image for testing and execution:

```sh
$ make docker-build
```

Note:
The availability of your image can be veridied with `docker image -q 'emobon_ddcat'`. This will return the image-id when found, or nothing if it is not found.

To manage these locally build images, check the docker documentation.
In general the following commands could help out with at least listing and removing them

```sh
# list all images locally found
$ docker images
# limited to those matching this project
$ PRJ="emobon_ddcat"
$ docker images | grep ${PRJ}
# same in custom output format for further processing
$ docker images --format="{{.ID}}|{{.Repository}}" | grep ${PRJ}
# with the above trick, one can loop, substract the id and execute the actual delete
$ for iid in $(docker images --format="{{.ID}}|{{.Repository}}"|grep ${PRJ}|awk -F '|' '{print $1}'); do\
    docker rmi -f $iid && echo "  > removed ${iid}" || echo "  > removal failed.";\
  done

```

To test if the docker-image behaves as epxected:

```sh
$ make docker-test
```

Note: This will include an automatic build of the image if it does not already exist (and to avoid needless builds). Use the combined target `make docker-build docker-test` to test on a fresh build.

To push the docker-image to a container catalogue:

```sh
$ make docker-push
```

Note: excuting this will always include a fresh build and test.

This is typically not called locally as it requires special credentials. The intended use of this build target is left to the automated build in the CI/CD setup at github.

## Submitting contributions

We expect our 'main' branch to build at all times.
Therefor we recommend working either on your own fork, or on a dedicated branch first and present a PR (PullRequest) from there.

Before declaring your PR as "ready for review", please run these commands and assure a positive outcome

```sh
$ make check                    # --> assure alignment with py-code style
$ make test                     # --> assure local (docker-less) operation
$ make docker-build docker-test # --> assure docker-wrapped operation
```

or in one sweep:

```sh
$ make pr                       # --> assure all PR requirements are met
```

Thanks for considering to help out. And many happy coding!