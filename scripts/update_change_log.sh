#!/bin/bash
FOR_PROD=${1:-0}
REPOSITORY_URL=https://github.com/betagouv/itou-marche
DATE=$(date +"%Y.%m.%d")
# echo $FOR_PROD
NEW_TAG="v${DATE}"
git tag $NEW_TAG

GIT_TAGS=$(git tag -l --sort=-version:refname)
TAGS=($GIT_TAGS)
LATEST_TAG=${TAGS[0]}
PREVIOUS_TAG=${TAGS[1]}
echo $TAGS
# If you want to specify your own two tags to compare, uncomment and enter them below
# LATEST_TAG=v0.23.1
# PREVIOUS_TAG=v0.22.0

# Get a log of commits that occured between two tags
# We only get the commit hash so we don't have to deal with a bunch of ugly parsing
# See Pretty format placeholders at https://git-scm.com/docs/pretty-formats
COMMITS=$(git log $PREVIOUS_TAG..$LATEST_TAG --pretty=format:"%H")
# Store our changelog in a variable to be saved to a file at the end
MARKDOWN='\n'
MARKDOWN+="## ${DATE}"
MARKDOWN+='\n'

# Loop over each commit and look for merged pull requests
for COMMIT in $COMMITS; do
    # Get the subject of the current commit
    SUBJECT=$(git log -1 ${COMMIT} --pretty=format:"%s")
    # echo ${COMMIT:0:5}

    # Get the body of the commit
    BODY=$(git log -1 ${COMMIT} --pretty=format:"%b")
    MARKDOWN+='\n'
    MARKDOWN+=" - [#${COMMIT:0:5}]: $SUBJECT"
    echo " - [#${COMMIT:0:5}]: $SUBJECT"
done

# Save our markdown to a file
awk -v md="$MARKDOWN" 'NR==6{print md}1' CHANGELOG.md >CHANGELOG_tmp.md
rm CHANGELOG.md
mv CHANGELOG_tmp.md CHANGELOG.md

if [ !$FOR_PROD ]; then
    git tag -d $NEW_TAG
fi
