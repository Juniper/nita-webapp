# GitHub Workflows

This folder contains the workflow files for GitHub Actions. To run these workflows, simply go to the "Actions" link above.

## Creating a New Release

This is the GitHub Action ``Create Release Manually`` and is used to create (i.e. tag) a new NITA release. When you run this action, it requests a value that will be used as the Release Name and Tag Name, with the following input dialogue:

![Input dialogue box](images/run-workflow.jpg)

The same value will be used for both the Release and the Tag. Enter a number such as "24.09" for example. The workflow asks for it twice here, to help avoid the mistake of mistyping.

The workflow steps are defined in the file ``release_manual.yml`` and are described here:
 - Verify that both entries from the initial dialogue are the same. in case of any discrepancy teh workflow stops.
 - Checkout code from gitub repository
 - Take the tag and writes it to the file ``VERSION.txt``
 - Check the Software Bill of Materials (SBOM) for all Python code and generated docker container, and write the copyright details for each dependency to a file called ``NOTICES.spdx.json``
 - Generate ``LICENSE.txt`` and ``README.md`` by updatings the copyright message with the correct   year, using files in build-templates directory as templates
 - Commit changes and push them back to github repository
 - Create a release artifact based on the given tag
 
