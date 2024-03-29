#!/bin/bash

initial_branch=`git branch --show-current`

# Ensure working directory is clean
if ! git diff-index --quiet HEAD; then
  echo "Working directory not clean, please commit your changes first"
  exit
fi

# Rebase master into master_clever, then push master_clever
# Deployment to Clever Cloud is actually triggered via a hook
# on a push on this branch
git checkout master
git pull origin master
git checkout master_clever
git pull origin master_clever
echo "====="
git_diff_between_master_and_master_clever=`git log master_clever..master --oneline`
echo "$git_diff_between_master_and_master_clever"
echo "====="
git rebase master
git push origin master_clever

# When we are done, we want to restore the initial state
# (in order to avoid writing things directly on master_clever by accident)
if [ -z $initial_branch ]; then
  # The initial_branch is empty when user is in detached state, so we simply go back to master
  git checkout master
  echo
  echo "You were on detached state before deploying, you are back to master"
else
  git checkout $initial_branch
  echo
  echo "Back to $initial_branch"
fi
