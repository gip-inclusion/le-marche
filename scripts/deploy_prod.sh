#!/bin/bash

initial_branch=`git branch --show-current`

# Ensure working directory is clean
if ! git diff-index --quiet HEAD; then
  echo "Working directory not clean, please commit your changes first"
  exit
fi

# Rebase main into main_clever, then push main_clever
# Deployment to Clever Cloud is actually triggered via a hook
# on a push on this branch
git checkout main
git pull origin main
git checkout main_clever
git pull origin main_clever
echo "====="
git_diff_between_main_and_main_clever=`git log main_clever..main --oneline`
echo "$git_diff_between_main_and_main_clever"
echo "====="
git rebase main
git push origin main_clever

# When we are done, we want to restore the initial state
# (in order to avoid writing things directly on main_clever by accident)
if [ -z $initial_branch ]; then
  # The initial_branch is empty when user is in detached state, so we simply go back to main
  git checkout main
  echo
  echo "You were on detached state before deploying, you are back to main"
else
  git checkout $initial_branch
  echo
  echo "Back to $initial_branch"
fi
